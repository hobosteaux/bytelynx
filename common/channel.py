from os import urandom

from crypto import MODULES as crypt_mods


def get_maxint(bit_size):
    if bit_size <= 0:
        return 0
    val = 0xf
    for i in range(1, bit_size):
        val = (val << 4) + 0xf
    return val


#: The byte size of a packet id
ID_SIZE = 8
#: The max value of a packet id
ID_MAX = get_maxint(ID_SIZE)
#: The level at which a renegotiate is started
ID_WARNING = int(0.95 * ID_MAX)


class Channel():
    """
    Container for a mode of communication with a client.
    Each one contains the crypto and packet counter needed,
    along with the resend watcher and pong lists.

    .. attribute:: conn_id

        A unique identifier for this connection.
        Must be unique in the set of all channels to this contact.
    .. attribute:: state

        Current state of this channel.
        ['idle', 'active', 'reneg_issued', 'closed']
    """

    def __init__(self, mode):
        # Get the main bytelynx stack
        from state import NET
        self.net = NET
        self.state = 'idle'

        # Random packet id so it is not predictable.
        self._pkt_id = int.from_bytes(urandom(ID_SIZE), 'little')
        self.crypto = crypt_mods[mode]()

    @property
    def pkt_id(self):
        """
        Gets a packet id and increments the current counter.
        .. note:: This is not locked and is not atomic.
        """
        id_ = self._pkt_id
        self._pkt_id += 1
        if self._pkt_id > ID_WARNING:
            self.renegotiate()
            if self._pkt_id >= ID_MAX:
                # TODO: Make this a good exception
                raise Exception('Packet counter above max')
        return id_

    def renegotiate(self):
        if self.state is 'active':
            # TODO: Renegotiate:
            pass
        else:
            # TODO: Make this a good exception
            raise Exception('Can not renegotiate if not active')
