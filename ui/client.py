
from net.tcp import Client


class UIClient():

    def __init__(self, address):
        self.client = Client(address)
        self._handlers = {'events': self._on_events,
                          'update': self._on_update}
        self.client.on_data += self.data_handler
        self._retrieve_events()

    def send_data(self, message_name, data=None):
        if data is None:
            data = {}
        self.client.send_data({'command': message_name,
                               'version': 1,
                               'values': data})

    def data_handler(self, data):
        try:
            self._handlers[data['command']](data['values'])
        except Exception as e:
            print(e)

    def subscribe(self, event):
        if event not in self.events:
            raise ValueError('%s not a valid event' % event)
        self.send_data('subscribe', [event])

    def _retrieve_events(self):
        self.send_data('get_events')

    def _on_events(self, data):
        self.events = set(data)

    def _on_update(self, data):
        print(data)
