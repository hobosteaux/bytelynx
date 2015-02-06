#!/usr/bin/python3
from collections import namedtuple

from common import Contact, Address, Hash, Event
from common import List as list
from common import btlxlogger as logger
from .exceptions import NoContactsError

Logger = logger.get(__name__)


class SearchContact():
    """
    Simple struct for search contacts.
    Must be a class because namedtuples can not be modified.

    .. attribute:: contacted

         If a contact has been contacted yet
    .. attribute:: contact

        The contact
    """
    def __init__(self, contacted, contact):
        self.contacted = contacted
        self.contact = contact

    def __str__(self):
        return "<%s: %s>" % (self.contacted, self.contact)


class ClosestContact():
    """
    Simple struct to represent how close a contact is

    .. attribute:: votes

        How many votes this contact has
    .. attribute:: contact

        The contact
    .. attribute:: distance

        The significant bit of contact ^ target
    """
    def __init__(self, contact, distance):
        self.votes = 0
        self.contact = contact
        self.distance = distance

    def increment(self):
        self.votes += 1

    def __gt__(self, other):
        return (self.votes > other.votes
                or (self.votes == other.votes
                    and self.distance < other.distance
                ))


#: A representation of each node that has an
#: asynchronous operation in progress.
InProgress = namedtuple('InProgress', ['contact', 'time'])


class Shortlist():
    """
    Used when searching for a hash on the DHT.

    .. attribute:: search_space

        A list of the :class:`kademlia.SearchContact`.
    .. attribute:: closest

        The closest hash found so far.
    .. attribute:: own_hash

        This node's hash.
    .. attribute:: target_hash

        The hash that this shortlist is searching for.
    .. attribute:: in_progress

        List of :attr:`~kademlia.shortlist.InProgress` contacts
        that the shortlist is awaiting a response from.
    .. attribute:: on_full_or_found

        Fired when all closer contacts are exausted or the contact is found.
    """

    def __init__(self, own_hash, target_hash, initial_contacts, K):
        """
        :param target_hash: The :hash that this shortlist is seaching for.
        :type target_hash: :class:`common.Hash`
        :param initial_contacts: Contacts to start the shorlist with.
        :type initial_contacts: [:class:`common.Contact`]
        """
        self.K = K
        self.search_space = list(SearchContact(contacted=False, contact=x)
                                 for x in initial_contacts)
        self.own_hash = own_hash
        self.target_hash = target_hash
        self.on_full_or_found = Event()
        self.in_progress = []
        # Ensure we start off increasing.
        self.sort()
        self._closest = {}
        # Add the closest contact (our vote)
        # This only matters if there is 2 nodes
        c = self.find_min()
        if c is not None:
            self._add_closest(c.contact)

    @property
    def searched(self):
        """
        :returns: Number of clients the shortlist has searched.
        :rtype: int.
        """
        return self.search_space.count(lambda x: x.contacted)

    @property
    def closest(self):
        if len(self._closest) == 0:
            return None
        return max(self._closest.values()).contact

    def _add_closest(self, contact):
        distance = (contact.hash ^ self.target_hash).significant_bit()
        self._closest[contact.address.tuple] = self._closest.get(
            contact.address.tuple, ClosestContact(contact, distance))
        self._closest[contact.address.tuple].increment()

    def update(self, new_contacts):
        """
        Update the existing list with new contacts.

        :param new_contacts: Contacts returned by a search() operation.
        :type new_contacts: [:class:`common.Contact`]
        """
        # Sort incoming contacts
        new_contacts.sort(key=lambda x: x.hash ^ self.target_hash)

        # Do some upvoting
        if len(new_contacts) > 0:
            self._add_closest(new_contacts[0])

        # Add the contacts
        for contact in new_contacts:
            # Can not include self in shortlist
            if (self.own_hash != contact.hash):
                # Stop if the desired contact is found
                if (contact.hash == self.target_hash):
                    self.on_full_or_found(self.target_hash, contact)
                else:
                    self._try_add(contact)

    def rm_search(self, addr):
        """
        Filters all searches to remove the one given to it.

        :param addr: The address to remove.
        :type addr: :class:`common.Address`
        """
        self.in_progress = list(filter(lambda x: x.contact.address != addr,
                                       self.in_progress))

    def _try_add(self, contact):
        """
        Tries to add a contact to a shortlist.

        The algorithmic complexity of this function is a tad high.
        Not terribly pertinent with K=20 though.

        :param contact: The contact to add.
        :type contact: :class:`common.Contact`
        """
        # Check that the hash does not already exist.
        if not self.search_space.any(lambda x: x.contact.hash == contact.hash):
            # if < K contacts, add to the list.
            if (len(self.search_space) < self.K):
                self.search_space.append(SearchContact(False, contact))
            # if == K contacts, and < K contacted.
            elif (self.searched < self.K):
                # Set the max to the min so it must increment.
                max = self.find_min()
                if (contact.hash ^ self.target_hash <
                        max.contact.hash ^ self.target_hash):
                    self.search_space.remove(max)
                    self.search_space.append(SearchContact(False, contact))
                    self.sort()

    def sort(self):
        self.search_space.sort(key=lambda x: x.contact.hash ^ self.target_hash)

    def get_next(self):
        """
        Gets the next item from the shortlist.
        Also marks as contacted.
        """
        # We are below the count and have at least one useable contact still.
        if ((self.searched <= self.K) and
                (self.search_space.any(lambda x: not x.contacted))):
            item = self.find_min()
            item.contacted = True
            self.in_progress.append(InProgress(item.contact,
                                               datetime.now()))
            return item.contact
        else:
            return None

    def find_min(self, uncontacted=True):
        """
        Returns the minimum item from the shortlist.

        .. todo:: Clean this up.
        """
        searchLambda = lambda x: not x.contacted
        # Find first uncontacted contact
        if (uncontacted):
            if (self.searched >= self.K):
                self.on_full_or_found(self.target_hash, self.closest)
                return None
        else:
            searchLambda = None
        try:
            minCon = self.search_space.first(searchLambda)
        except ValueError:
            return None

        for contact in self.search_space:
            if (uncontacted and not contact.contacted):
                if (contact.contact.hash ^ self.target_hash <
                        minCon.contact.hash ^ self.target_hash):
                    minCon = contact
            elif (not uncontacted):
                if (contact.contact.hash ^ self.target_hash <
                        minCon.contact.hash ^ self.target_hash):
                    minCon = contact
        return minCon

    def find_max(self, uncontacted=True):
        """
        Returns the maximum item from the shortlist.

        .. todo::

            Clean this up.
        """
        searchLambda = lambda x: not x.contacted
        # Find first uncontacted contact
        if (uncontacted):
            if (self.searched > self.K):
                return None
        else:
            searchLambda = None
        maxCon = self.search_space.first(searchLambda)

        # Reversed because we should ALWAYS be increasing.
        for contact in reversed(self.search_space):
            if (uncontacted and not contact.contacted):
                if (contact.contact.hash ^ self.target_hash >
                        maxCon.contact.hash ^ self.target_hash):
                    maxCon = contact
            elif (not uncontacted):
                if (contact.contact.hash ^ self.target_hash >
                        maxCon.contact.hash ^ self.target_hash):
                    maxCon = contact
        return maxCon

    def __str__(self):
        return '%s : %s - P:%d F:%d T:%d' % (self.target_hash,
                                             self.closest,
                                             len(self.in_progress),
                                             self.searched,
                                             self.K)

from threading import Thread
from datetime import datetime
from time import sleep
from queue import Queue


class Shortlists():
    """
    Interface class for multiple
    :class:`~kademlia.shortlist.Shortlist`.

    .. attribute:: on_search

        Event for when a search message should be sent.
        (:class:`~common.Hash`, :class:`~common.Contact`)
    .. attribute:: on_full_or_found

        Event for when the list is either full or found the contact.
        Returns either the contact or the closest one found.
    """

    def __init__(self, own_hash, K, A):
        self.K = K
        self.A = A
        self._own_hash = own_hash
        self._shortlists = {}  # {hash : shortlist}
        self._task_queue = Queue()
        self.on_search = Event()
        self.on_full_or_found = Event()
        self._watcher_thread = Thread(target=self._watcher)
        self._watcher_thread.daemon = True
        self._watcher_thread.start()

    def start_search(self, hash_, contacts):
        """
        Adds a task to begin a search for a hash.

        :param hash_: The hash to search for.
        :type hash_: :class:`~common.Hash`
        :param contacts: The initial contacts.
        :type contacts: [:class:`~common.Contact`]
        """
        Logger.debug("Starting Search: %s", hash_)
        self._task_queue.put((self._start_search, (hash_, contacts)))

    def _start_search(self, hash_, contacts):
        self._shortlists[hash_] = Shortlist(self._own_hash, hash_, contacts, self.K)
        self._shortlists[hash_].on_full_or_found += self.on_full_or_found
        self._shortlists[hash_].on_full_or_found += self.rm_list

    def add_response(self, hash_, request_addr, responses):
        """
        Adds a task to the queue to respond to a search.

        :param hash_: The hash identifier for the target.
        :type hash_: :class:`common.Hash`
        :param request_addr: The responding address.
        :type request_addr: :class:`common.Address`
        :param responses: Contacts received.
        :type responses: [:class:`common.Contact`]
        """
        Logger.debug("Add Response: %s", request_addr)
        self._task_queue.put((self._add_response, (hash_, request_addr,
                                                   responses)))

    def _add_response(self, hash_, request_addr, responses):
        self._shortlists[hash_].rm_search(request_addr)
        self._shortlists[hash_].update(responses)

    def rm_list(self, hash_, *args):
        """
        Adds a task to the queue to remove a search for a hash.

        :param hash_: The hash identifier for the target.
        :type hash_: :class:`common.Hash`
        """
        self._task_queue.put((self._rm_list, (hash_, )))

    def _rm_list(self, hash_):
        # This should NOT cause a mem leak
        # since it has the pointers to functions.
        del(self._shortlists[hash_])

    def _clean_lists(self):
        for hash_, shortlist in self._shortlists.items():
            # Magic Number [1000]: convert seconds to ms
            # Magic Number [5]: tweakable to set how long to timeout requests
            alive = list(filter(lambda x: (datetime.now()-x.time).total_seconds() * 1000
                                           < x.contact.ping * 5,
                                shortlist.in_progress))
            # If any of the requests have timed out.
            if (len(alive) != len(shortlist.in_progress)):
                shortlist.in_progress = alive
            # Add any needed more requests to reach the parallel param A.
            while (len(shortlist.in_progress) < self.A):
                next_min = shortlist.get_next()
                # We have no more useable responses.
                if (next_min is None):
                    # No searches are in progress.
                    if (len(shortlist.in_progress) == 0):
                        shortlist.on_full_or_found(shortlist.target_hash,
                                                   shortlist.closest)
                    break
                else:
                    self.on_search(hash_, next_min)

    def _watcher(self):
        """
        This function watches for any RPCs that must be made.
        It is the only one that should modify the datavalues of the shorts.

        .. note:: This call is blocking, so run it threaded.
        """
        while (True):
            while (self._task_queue.qsize() > 0):
                task = self._task_queue.get()
                if (task[0] != self._clean_lists):
                    Logger.debug('TASK: %s', str(task))
                task[0](*(task[1]))
            sleep(0.5)
            self._task_queue.put((self._clean_lists, ()))


# Placeholder for when a search is triggered.
# Used for testing only.
def Search(contact):
    print('SEARCH:', contact)

from os import urandom
if (__name__ == '__main__'):
    shortie = Shortlists(Search)
    while(True):
        shortie.start_search(Hash(urandom(20)),
                             [Contact(Address('192.168.0.1', 4000),
                                      Hash(b'12345678901234567890'))])
        sleep(1)
