from threading import Lock, Thread
from functools import reduce
from datetime import datetime, timedelta

from net.tcp import Server
from ui import protocol


class Client():

    def __init__(self, address):
        self.address = address
        self.subscriptions = set()

    def __repr__(self):
        return "%s: %s" % (self.address, self.subscriptions)


class UIServer():

    def __init__(self, port, max_conns):
        self.server = Server(port, max_conns)
        self.server.on_data += self._data_handler
        self.server.on_cleanup += self._clean_contact
        self.subscribers = {}
        self.properties = {}
        self._properties_lock = Lock()
        self._subscriber_lock = Lock()
        self._updated_properties = set()
        # Update Vars
        self._last_update = datetime.now()
        self._updating = False
        self._update_lock = Lock()
        # Handlers
        self.proto = protocol.get()
        for x in filter(lambda y: y.mtype == protocol.client,
                        self.proto.values()):
            x.handler = self.__getattribute__('_%s_handler' % x.name)

    def add_property(self, name, path, object_root):
        obj = object_root
        for item in path.split('.'):
            obj = obj.__getattribute__(item)
        with self._properties_lock:
            if name not in self.properties:
                self.properties[name] = obj
                obj.on_changed += self.on_property_update

    def send_data(self, sub,  message_name, data):
        message = self.proto[message_name].pack(data)
        self.server.send_data(sub.address, message)

    #: Min time between updates
    UPDATE_DELTA = timedelta(seconds=2)

    def try_update(self):
        """
        Function that checks to see if an update needs to be started.
        This is locked for multithreading,
        and spawns another thread to do the update.
        """
        with self._update_lock:
            if (datetime.now() - self.UPDATE_DELTA > self._last_update
                    and not self._updating):
                self._updating = True
                self._last_update = datetime.now()
                # Get the party started
                t = Thread(target=self._update)
                t.daemon = True
                t.start()

    def _update(self):
        try:
            with self._properties_lock:
                props = self._updated_properties
                self._updated_properties = set()
            # Used because transforming some of these items is expensive.
            # This could be done in one huge ass expression,
            # but that may be unreadable.
            print(self.subscribers)
            with self._subscriber_lock:
                subbed_props = reduce(lambda x, y: x.union(y),
                                      (x.subscriptions for x
                                       in self.subscribers.values()),
                                      set()).intersection(props)
                cached_vals = {x: self.properties[x].flatten()
                               for x in subbed_props}
                # Check if anything changed
                if len(cached_vals) > 0:
                    for sub in self.subscribers.values():
                        # Collect all data the client is subscribed to.
                        data = reduce(lambda x, y: dict(x, **y),
                                      (cached_vals[x] for x in props
                                       if x in sub.subscriptions),
                                      {})
                        # Send data to the clients
                        if len(data) > 0:
                            self.send_data(sub, 'update', data)
        finally:
            self._updating = False

    def on_property_update(self, name, value):
        """
        Handler for when a watched property is updated.
        We only store the name, since the value may change a lot.
        The value is also of unknown type, not the json-compatible
        types needed.
        """
        with self._properties_lock:
            print("updating %s (%s)" % (name, value))
            self._updated_properties.add(name)
        self.try_update()

    def get_subscriber(self, address):
        """
        Gets the subscriber at the given address.
        If none exists, one is created.
        """
        try:
            client = self.subscribers[str(address)]
        except KeyError:
            client = Client(address)
            with self._subscriber_lock:
                self.subscribers[str(address)] = client
        return client

    def _clean_contact(self, address):
        """
        Handler for cleaning up a contact once they disconnect.
        This is processed from the quitting listener's thread.
        """
        with self._subscriber_lock:
            del(self.subscribers[str(address)])

    def _data_handler(self, address, payload):
        """
        Handler for when data is received.
        """
        subscriber = self.get_subscriber(address)
        try:
            cmd_name = payload['command']
            data = payload['values']
            self.proto[cmd_name].handler(subscriber, data)
        except Exception as e:
            print("UI ex: %s" % e)

    def _get_events_handler(self, subscriber, data):
        names = [x for x in self.properties.keys()]
        print(names)
        self.send_data(subscriber, 'events', names)

    def _subscribe_handler(self, subscriber, data):
        for value in (x for x in data if x in self.properties):
            # Check only to look for a data update
            if value not in subscriber.subscriptions:
                subscriber.subscriptions.add(value)
                self.send_data(subscriber, 'update',
                               self.properties[value].flatten())

    def _unsubscribe_handler(self, subscriber, data):
        for value in (x for x in data if x in self.properties):
            try:
                subscriber.subscriptions.remove(value)
            except KeyError:
                pass
