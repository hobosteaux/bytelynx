from datetime import datetime
from enum import Enum
from collections import defaultdict

from .config import get as get_config
from .event import Event
from .list import List as list
from .channel import Channel
from .exceptions import ProtocolError
from .hash import hash_from_pub
from .property import Property

DEATH_THRESHOLD = 0.1


class PingModes(Enum):
    #: ping = (old / 1.5) + (new / 3)
    geometric = 1
    #: ping = new
    absolute = 2


class Contact(Property):
    """
    .. attribute:: pings

        List of all pings sent and send time.
    .. attribute:: address

        Remote :class:`common.Address`.
    .. attribute:: hash

        Remote :class:`common.Hash`.
    .. attribute:: last_seen

        Last time a packet was seen from this address.
    .. attribute:: channels

        All currently established channels for this contact.
        {str.: :class:`common.Channel`}
    .. attribute:: has_friend

        If this contact is a friend.
    .. attribute:: on_hash

        Event thrown when the hash is found.
    .. attribute:: on_death

        Event thrown when the contact has died.
    """

    #: Sliding counter on ping response times
    ping = 1500
    #: Sliding counter on missed pings
    liveliness = 1
    #: Packet counter
    counter = 0
    #: If a hash has been scraped from the contact yet
    needs_hash = True

    _flatten_attrs = ['ping',
                      'liveliness',
                      'needs_hash']
    _flatten_funcs = ['hash',
                      'address']

    def __init__(self, addr, hash=None):
        self.address = addr
        self.last_seen = datetime.now()
        self.pings = list()
        self.channels = {}
        self.has_friend = False
        self.on_death = Event()
        self.on_hash = Event()
        self.channel_finalization = Event()
        self.needs_hash = True
        self.set_hash(hash)

        self.sent_msg_queue = defaultdict(list)
        self.recv_msg_queue = defaultdict(list)

        self.create_channel('bytelynx')

    def __str__(self):
        try:
            return '%s : %s' % (self.address, self.hash.base64)
        # If the hash is not set
        except AttributeError:
            return '%s : None' % (self.address)

    def __repr__(self):
        return '%s' % (self.address)

    @property
    def is_alive(self):
        """
        :return: If this contact is considered 'alive'
        :rtype: bool.
        """
        return self.liveliness > DEATH_THRESHOLD

    def set_hash(self, hash_):
        """
        Sets the contacts hash.

        :returns: If the hash was set
        :rtype: bool.
        """
        if self.needs_hash:
            if hash_ is not None:
                self.hash = hash_
                self.needs_hash = False
                self.on_hash(self)
                return True
            else:
                self.hash = None
        return False

    def create_channel(self, mode):
        """
        Creates and returns a channel to this client.

        :param mode: The connection mode of this channel.
        :type mode: str.
        :returns: The newly created channel.
        :rtype: :class:`~common.Channel`
        """
        from crypto import Modules
        if mode in self.channels:
            raise ProtocolError('Channel already exists')
        c = Channel(mode, Modules[mode]())
        self.channels[mode] = c
        c.on_finalization += self.on_channel_finalization
        return c

    def add_sent_msg(self, channel, msg_name, data):
        self.sent_msg_queue[channel].append((msg_name, data))

    def add_recv_msg(self, channel, addr, raw_data):
        self.recv_msg_queue[channel].append((addr, raw_data))

    def on_channel_finalization(self, channel):
        # If we had messages waiting on the creation of this channel
        if len(self.sent_msg_queue[channel.mode]) > 0:
            import state
            net = state.get().net
            for msg_name, data in self.sent_msg_queue[channel.mode]:
                net.send_data(self, msg_name, data)
        if len(self.recv_msg_queue[channel.mode]) > 0:
            import state
            net = state.get().net
            for addr, raw_data in self.recv_msg_queue[channel.mode]:
                net.on_data(addr, raw_data)
        self.channel_finalization(channel.mode)


    def change_ping(self, ping, mode=PingModes.geometric):
        """
        Modifies the ping of this contact.
        Also sets liveliness, as this is only called when
        a successful pong is received.

        :param ping: The ping, in ms.
        :type ping: int.
        :param mode: Mode to weight the ping
        :type mode: str.
        """
        if mode == PingModes.geometric:
            self.ping = (self.ping / 1.5) + (ping / 3)
        if mode == PingModes.absolute:
            self.ping = ping
        self.change_liveliness(degrade=False)

    def change_liveliness(self, degrade=True):
        """
        Degrades or improves liveliness by one packet value.

        :param degrade: If liveliness should be decreased
        :type degrade: bool.
        """
        self.liveliness *= 0.8
        if degrade:
            if not self.is_alive:
                self.on_death(self)
        else:
            self.liveliness += 0.2


class Friend():
    """
    A contact noted as a 'friend'.
    This begins detached for real contacts and
    must be associated with one seen over the wire.

    .. attribute:: hash

        The friend's hash
    """

    def __init__(self, pubkey, nick):
        self.pubkey = pubkey
        self.nick = nick
        # find hash
        # NastyImport
        bitsize = get_config()['kademlia']['keysize']
        # TODO: push this into the publickey object
        # REQ: cryptography 0.6
        self.hash = hash_from_pub(pubkey, bitsize)

        self.contact = None

    def associate(self, contact):
        """
        Associates a contact with this friend.
        Initializes the RSA crypto.

        :param contact: The contact to associate with
        :type contact: :class:`~common.Contact`
        """
        self.contact = contact
        chan = contact.create_channel('rsa-ex')
        # TODO
        # set child RSA crypo - get privkey somehow
        chan.seed(own_crypto, self.pubkey)
