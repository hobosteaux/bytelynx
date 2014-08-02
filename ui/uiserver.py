from time import sleep
from Threading import Lock
from functools import reduce

from .client import UIClient
from net.tcp import Server


class UIServer():

    def __init__(self, port, max_conns):
        self.server = Server(port, max_conns)
        self.server.on_data += self.data_handler
        self.subscribers = {}
        self.properties = {}
        self._properties_lock = Lock()
        self._updated_properties = set()
        self._handlers = {'get_events': self.get_events_handler,
                          'subscribe': self.subscribe_handler,
                          'unsubscribe': self.unsubscribe_handler}

    def send_data(self, sub,  message_name, data):
        message = {'command': message_name,
                   'version': 1,
                   'values': data}
        self.server.send_data(sub.address, message)

    def update_thread(self):
        while True:
            with self._properties_lock:
                props = self._updated_properties
                self._updated_properties = set()
            # Used because transforming some of these items is expensive.
            # This could be done in one huge ass expression,
            # but that may be unreadable.
            subbed_props = reduce(lambda x, y: x.union(y),
                                  (x.subscriptions for x in self.subscribers),
                                  set()).intersection(props)
            cached_vals = {x: self.properties[x].flattened
                           for x in subbed_props}
            for sub in self.subscribers.values():
                # Collect all data the client is subscribed to.
                data = reduce(lambda x, y: x.update(y),
                              (cached_vals[x] for x in props
                               if x in sub.subscriptions),
                              {})
                # Send data to the clients
                self.send_data('update', data)
            sleep(1)

    def on_property_update(self, name, value):
        """
        Handler for when a watched property is updated.
        We only store the name, since the value may change a lot.
        The value is also of unknown type, not the json-compatible
        types needed.
        """
        with self._properties_lock:
            self._updated_properties.add(name)

    def get_subscriber(self, address):
        """
        Gets the subscriber at the given address.
        If none exists, one is created.
        """
        try:
            client = self.subscribers[address.tuple]
        except KeyError:
            client = UIClient(address)
            self.subscribers[address.tuple] = client
        return client

    def data_handler(self, address, payload):
        """
        Handler for when data is received.
        """
        subscriber = self.get_subscriber(address)
        for instruction in payload:
            try:
                cmd_name = instruction['command']
                data = instruction['values']
                self._handlers[cmd_name](subscriber, data)
            except Exception as e:
                print("UI ex: %s" % e)

    def get_events_handler(self, subscriber, data):
        names = [x for x in self.properties.keys()]
        self.send_data(subscriber, 'events', names)

    def subscribe_handler(self, subscriber, data):
        for value in (x for x in data if x in self.properties):
            subscriber.subscriptions.add(value)

    def unsubscribe_handler(self, subscriber, data):
        for value in (x for x in data if x in self.properties):
            try:
                subscriber.subscriptions.remove(value)
            except KeyError:
                pass
