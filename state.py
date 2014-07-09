import os
import struct

from common import Contact, Address, Hash
from net import Stack
import net.ipfinder
from kademlia import Kademlia

STATE = None


class _State():
    """
    Class for holding all the global state.

    .. attribute:: contact

        This instance's :class:`~common.Contact`
    .. attribute:: net

        This instance's :class:`~net.Stack`
    .. attribute:: kademlia

        This instance's :class:`~kademlia.Kademlia`
    .. attribute:: dh_group

        The group id that this node is a member of
    .. attribute:: dir

        Where all atrifacts from this instance are kept
    """

    # TODO: Make these count
    USE_RAND_PORT = True
    USE_RAND_HASH = True
    DEFHASH = hash(b'12345678901234567890')
    DEFPORT = 8906

    def __init__(self):

        print("Initing globals")
        hash_ = Hash(os.urandom(20))
        # Set up dir first for artifacts
        self.dir = 'tmp/' + hash_.base64[:10] + '/'
        os.makedirs(self.dir)

        # TODO: load this from config
        self.dh_group = 721283716213

        # Set up the networking core
        port = self.new_port()

        addr = Address(net.ipfinder.check_in(), port)
        self.contact = Contact(addr, hash_)
        self.net = Stack(port, self.dh_group)
        self.kademlia = Kademlia(self.net, self.contact,
                                 self.dir)

    def new_port(self):
        """
        Gets a random free port > 10000.

        .. TODO::
            Check if the port is free.
            And if it is < 65000.
        """
        rport = struct.unpack('H', os.urandom(2))[0]
        while (rport < 10000):
            rport = struct.unpack('H', os.urandom(2))[0]
        return rport


def get():
    """
    Accessor for the state singleton
    """
    global STATE
    if STATE is None:
        STATE = _State()
    return STATE
