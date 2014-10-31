
from net.tcp import Client
from ui import protocol


class UIClient():
    """
    Basic client for the UI server.
    """

    def __init__(self, address):
        self.client = Client(address)
        # Set up the handlers
        self.proto = protocol.get()
        for x in filter(lambda y: y.mtype == protocol.server,
                        self.proto.values()):
            x.handler = self.__getattribute__('_%s_handler' % x.name)
        self.client.on_data += self.data_handler
        self._retrieve_events()

    def send_data(self, message_name, data=None):
        # if data is None:
        #    data = {}
        self.client.send_data(self.proto[message_name].pack(data))

    def data_handler(self, payload):
        try:
            cmd = payload['command']
            data = payload['values']
            self.proto[cmd].handler(data)
        except Exception as e:
            print(e)

    def subscribe(self, event):
        if event not in self.events:
            raise ValueError('%s not a valid event' % event)
        self.send_data('subscribe', [event])

    def _retrieve_events(self):
        self.send_data('get_events')

    def _events_handler(self, data):
        self.events = set(data)

    def _update_handler(self, data):
        print(data)
