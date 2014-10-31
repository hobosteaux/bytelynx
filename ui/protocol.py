

#: Current version of the ui protocol
PROTO_VER = 1

# TODO: replace these
# Quick and dirty enum
# Requires >= python3.4
server = 'server'
client = 'client'


class UIMessage():
    """
    Basic message for UI communication
    """

    def __init__(self, name, mtype):
        """
        :param name: The name of the message
        :type name: str.
        :param mtype: The sender of the message
        """
        self.name = name
        self.mtype = mtype
        self._handler = None

    @property
    def handler(self):
        """
        Event to call for this message.
        This makes it so that if multiple clients or
        servers are needed, then the protocol needs
        to be duplicated, else events will be hit many times.
        """
        if self._handler is None:
            raise ValueError("handler not set")
        return self._handler

    @handler.setter
    def handler(self, value):
        self._handler = value

    def pack(self, data=None):
        """
        Gets a wire-ready version of the data.
        """
        return {'command': self.name,
                'version': 1,
                'values': data}


PROTOCOL = None


def get():
    """
    Singleton-enforcing method to get the UI protocol.

    :returns: The protocol messages
    :rtype: list
    """
    global PROTOCOL
    if PROTOCOL is None:
        # start-after
        proto = [
            UIMessage('get_events', 'client'),
            UIMessage('events', 'server'),
            UIMessage('subscribe', 'client'),
            UIMessage('unsubscribe', 'client'),
            UIMessage('update', 'server')
            ]
        # end-before
        proto = {x.name: x for x in proto}
        PROTOCOL = proto
    return PROTOCOL
