from os import urandom
from threading import Lock

from .event import Event

def get_maxint(byte_size):
    """
    Helper function to get the max int for a given size.

    :param byte_size: The amount of bytes to use
    :type byte_size: int.
    :returns: The max int for given size
    :rtype: int.
    """
    if byte_size <= 0:
        return 0
    val = 0xff
    for i in range(1, byte_size):
        val = (val << 8) + 0xff
    return val


#: The byte size of a packet id
ID_SIZE = 16
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

    def __init__(self, mode, crypto):
        """
        :param mode: The encryption object.
        :type mode: Class derived from :class:`~crypto.CryptoModule`
        """

        self.state = 'idle'
        self.mode = mode
        self._lock = Lock()
        # TODO: Will this orphan packets if one is resent?
        self.packets = {}
        self.on_finalization = Event()
        crypto.on_finalization += (lambda: self.on_finalization(self))

        # Random packet id so it is not predictable.
        self._pkt_id = ID_MAX
        while self._pkt_id > 0.75 * ID_MAX:
            self._pkt_id = int.from_bytes(urandom(ID_SIZE), 'little')
        self.crypto = crypto

    @property
    def pkt_id(self):
        """
        Gets a packet id and increments the current counter.
        :returns: A thread-safe packet id
        :rtype: int.
        """
        with self._lock:
            id_ = self._pkt_id
            self._pkt_id += 1
        if self._pkt_id > ID_WARNING:
            self.renegotiate()
            if self._pkt_id >= ID_MAX:
                # TODO: Make this a good exception
                raise Exception('Packet counter above max')
        return id_

    def renegotiate(self):
        """
        Begins a renegotiation on this channel.
        Currently not implemented.
        """
        if self.state is 'active':
            # TODO: Renegotiate:
            raise NotImplementedError()
        else:
            # TODO: Make this a good exception
            raise Exception('Can not renegotiate if not active')
