from os import urandom

from crypto import MODULES as crypt_mods

"""
ARCH:

Contact
    dict[mode] = Channel


Channel
    cryptomodule
    pkt_ctr
    resend_watcher
    on_pong

CryptoModule

"""


class Channel():
    """
    Container for a mode of communication with a client.
    Each one contains the crypto and packet counter needed,
    along with the resend watcher and pong lists.

    .. attribute:: conn_id

        A unique identifier for this connection.
        Must be unique in the set of all channels to this contact.
    .. attribute:: _pkt_id

        The current packet id for this connection.
    """

    """
    crypto
    pkt_ctr
    packets
    connection id? -> used to describe which channel is being used
        Where would this be in the packet?
        could there be a data leak if this is maliciously changed
            / matches another one's
        Could make it so post renegotiation old packets could be used
    """

    def __init__(self, mode):
        # Get the main bytelynx stack
        from state import NET
        self.net = NET

        # Random packet id so it is not predictable.
        self._pkt_id = int.from_bytes(urandom(8), 'little')
        self.crypto = crypt_mods[mode]()

    @property
    def pkt_id(self):
        """
        Gets a packet id and increments the current counter.
        .. note:: This is not locked and is not atomic.
        """
        # TODO: check if pkt_id is too high / renegotiate
        id_ = self._pkt_id
        self._pkt_id += 1
        return id_

    def renegotiate(self):
        pass
