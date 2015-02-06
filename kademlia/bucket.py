from datetime import datetime

from common import Event, List as list
from common import btlxlogger as logger

Logger = logger.get(__name__)


class Bucket:
    """
    .. attribute:: contacts

        :class:`list` of len :attr:`kademlia.K`
    .. attribute:: waitlist

        :class:`list` of len :attr:`kademlia.K`
    .. attribute:: on_added

        Event(:class:`common.Event`)
    .. attribute:: on_removed

        Event(:class:`common.Event`)
    """

    def __init__(self, K):
        self.K = K
        self.contacts = list()
        self.waitlist = list()
        self.on_added = Event()
        self.on_removed = Event()

    def update(self, contact, report=True):
        """
        Checks if a new contact is more up to date than one in the bucket.

        :param contact: Newly seen contact.
        :type contact: :class:`common.Contact`
        :param report: Pop the :func:`~common.Bucket.on_added` event or not.
        """
        if contact not in self.contacts:
            if (len(self.contacts) <= self.K):
                self.contacts.append(contact)
                contact.on_death += self.contact_death
                if (report):
                    self.on_added(contact)
            elif ((len(self.waitlist) <= self.K)
                    and (contact not in self.waitlist)):
                self.waitlist.append(contact)
                contact.on_death += self.waitlist_death
        if report:
            self.on_added(contact)

    def contact_death(self, contact):
        """
        Event handler for when a contact expires that is in a list.

        :param contact: Dieing contact.
        :type contact: :class:`common.Contact`
        """
        if contact in self.contacts:
            self.contacts.remove(contact)
            contact.on_death -= self.contact_death
            self.on_removed(contact)
        if len(self.waitlist) > 0:
            replacement = self.waitlist[len(self.waitlist) - 1]
            self.contacts.append(replacement)
            self.waitlist.on_death += self.contact_death
            self.waitlist.remove(replacement)
            self.waitlist.on_death -= self.waitlist_death

    def waitlist_death(self, contact):
        """
        Event fired if a contact on the waitlist dies.
        """
        if contact in self.waitlist:
            self.waitlist.remove(contact)
            contact.on_death -= self.waitlist_death

CHECK_MIN = 1.5
"""How often to check for dead clients."""
DEL_MIN = 10
"""Minutes of staleness allowed for clients."""


class Buckets():
    """
    Primary interface to the list of :class:`kademlia.Bucket`.

    .. attribute:: _buckets

        A list of buckets `~kademlia.K` big.
    .. attribute:: _conns

        All currently alive seen connections.
        {:class:`~common.Address`: :class:`~common.Contact`}
    .. attribute:: _last_check

        Last time that the _conns we checked for liveliness.
    .. attribute:: on_added

        Event called when a new contact is added to a bucket.
        Event(:class:`~common.Client`)
    .. attribute:: on_removed

        Event called when a contact is removed from bucket.
        Event(:class:`~common.Client`)
    """

    def __init__(self, own_hash, K, B):
        """
        :param own_hash: Our own hash
        :type own_hash: :class:`~common.Hash`
        :param K: Bucket size
        :type K: int.
        :param B: Key size
        :type B: int.
        """
        self.K = K
        self.B = B
        self.own_hash = own_hash
        self._last_check = datetime.now()
        self.on_added = Event()
        self.on_removed = Event()
        # B+1 buckets because 0 means perfect match
        # 1-320 represent the bit level difference (index + 1)
        self._buckets = [Bucket(K) for i in range(self.B + 1)]
        for bucket in self._buckets:
            bucket.on_added += self.on_added
            bucket.on_removed += self.on_removed
        self._conns = {}

    def seed(self, contacts):
        """
        Function for initial seeding of the _buckets.
        Will not proc the on_added event for the db's sake.

        :param contacts: The contacts to add.
        :type contacts: [:class:`common.Contact`]
        """
        for contact in contacts:
            self.update(contact, False)

    def update(self, contact, report=True):
        """
        Updates a contact within the correct bucket.

        :param contact: The seen contact.
        :type contact: :class:`common.Contact`
        :param report: Pop the :func:`~common.Bucket.on_added` event or not.
        """
        loc = (contact.hash ^ self.own_hash).significant_bit()
        self._buckets[loc].update(contact, report)

    def get_exact(self, hash, use_waitlist=False):
        """
        Gets an exact contact from the lists.

        :param hash: The hash to retreive.
        :type hash: :class:`common.Hash`
        :param use_waitlist: Search through the waitlists as well.
        :type use_waitlist: bool.
        """
        significant_bit = (self.own_hash ^ hash).significant_bit()
        if not use_waitlist:
            return self._buckets[significant_bit]\
                .contacts.first(lambda x: x.hash == hash)
        else:
            return (self._buckets[significant_bit].contacts +
                    self._buckets[significant_bit].waitlist)\
                .first(lambda x: x.hash == hash)

    def get_closest(self, hash, count=None):
        """
        Gets the closest n contacts to a hash.

        :param hash: The hash to compare to.
        :type hash: :class:`common.Hash`
        :param count: Number of contacts to return.
        :type count: int.
        """
        if count is None:
            count = self.K
        targethash = (self.own_hash ^ hash)
        significant_bit = targethash.significant_bit()
        contacts = list()

        # Sorted Indices (for prox to the contact).
        # Ignore the one that is its own bucket to avoid any recursion.
        si = sorted([x for x in range(1, self.B + 1)],
                    key=lambda x: abs(x - significant_bit))

        for dindex in si:
            contacts += self._buckets[dindex].contacts
            if (len(contacts) >= count):
                return sorted(contacts, key=lambda x:
                              targethash.AbsDiff(self.own_hash ^ x.hash))[:count]
        Logger.debug("GET_CLOSEST ret: %s" % contacts)
        return contacts
