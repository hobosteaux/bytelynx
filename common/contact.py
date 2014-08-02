from datetime import datetime

from .event import Event
from .list import List as list
from .channel import Channel
from .exceptions import ProtocolError
from .hash import hash_from_pub


class Contact():
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
    ping = 150
    #: Sliding counter on missed pings
    liveliness = 1
    #: Packet counter
    counter = 0
    #: If a hash has been scraped from the contact yet
    needs_hash = True

    def __init__(self, addr, hash=None):
        self.needs_hash = hash is None
        self.address = addr
        self.set_hash(hash)
        self.last_seen = datetime.now()
        self.pings = list()
        self.on_hash = Event()
        self.on_death = Event()
        self.channels = {}
        self.has_friend = False

        self.create_channel('bytelynx')

    def __str__(self):
        return '%s' % (self.address)

    def __repr__(self):
        return '%s' % (self.address)

    @property
    def is_alive(self):
        """
        :return: If this contact is considered 'alive'
        :rtype: bool.
        """
        return self.liveliness > 0

    def set_hash(self, hash_):
        """
        Sets the contacts hash.

        :returns: If the hash was set
        """
        if self.needs_hash and hash_ is not None:
            self.hash = hash_
            self.needs_hash = False
            self.on_hash(self)
            return True
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
        c = Channel(Modules[mode]())
        self.channels[mode] = c
        return c

    class ping_modes():
        """
        Modes which the ping of a class can be modified.
        """
        #: (old / 1.5) + (new / 3)
        geometric = 'geometric'
        #: new
        absolute = 'absolute'

    def change_ping(self, ping, mode='geometric'):
        """
        Modifies the ping of this contact.
        Also sets liveliness, as this is only called when
        a successful pong is received.
        """
        if mode == 'geometric':
            self.ping = (self.ping / 1.5) + (ping / 3)
        if mode == 'absolute':
            self.ping = ping
        self.change_liveliness(degrade=False)

    def change_liveliness(self, degrade=True):
        """
        Degrades or improves liveliness by one packet value.

        :param degrade: If liveliness should be decreased.
        :type degrade: bool.
        """
        self.liveliness *= 0.8
        if degrade:
            if (self.liveliness <= 0.1):
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
        import state
        bitsize = state.get().bitsize
        # TODO: push this into the publickey object
        # REQ: cryptography 0.6
        self.hash = hash_from_pub(pubkey, bitsize)

        self.contact = None

    def associate(self, contact):
        self.contact = contact
        chan = contact.create_channel('rsa-ex')
        # TODO
        # set child RSA crypo - get privkey somehow
        chan.seed(own_crypto, self.pubkey)
