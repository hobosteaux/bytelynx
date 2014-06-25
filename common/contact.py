from datetime import datetime

from .event import Event
from .list import List as list
from .channel import Channel


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
        self.hash = hash
        self.last_seen = datetime.now()
        self.pings = list()
        self.on_death = Event()

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
        """
        if not self.needs_hash:
            raise ValueError("Hash already set")
        self.hash = hash_
        self.needs_hash = False

    def create_channel(self, mode):
        """
        Creates and returns a channel to this client.

        :param mode: The connection mode of this channel.
        :type mode: str.
        """
        c = Channel(mode, self)
        c.on_pong += self.change_ping
        c.on_dead_packet += self.change_liveliness

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
