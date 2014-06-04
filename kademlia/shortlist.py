#!/usr/bin/python3
from collections import namedtuple

from .constants import K, A
import state
from common import Contact, Address, Hash, Event
from common import List as list


class SearchContact():
    """
    Simple struct for search contacts.

    .. attribute:: contacted

        If a contact has been contacted yet.
    .. attribute:: contact

        The contact's address.
    """

    def __init__(self, contacted, contact):
        self.contacted = contacted
        self.contact = contact

#: A representation of each node that has an
#: asynchronous operation in progress.
InProgress = namedtuple('InProgress', ['address', 'time'])


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

    def __init__(self, target_hash, initialContacts):
        """
        :param target_hash: The :hash that this shortlist is seaching for.
        :type target_hash: :class:`common.Hash`
        :param initialContacts: Contacts to start the shorlist with.
        :type initialContacts: [:class:`common.Contact`]
        """
        self.search_space = list(SearchContact(False, x)
                                 for x in initialContacts)
        self.own_hash = state.SELF.hash_
        self.target_hash = target_hash
        self.on_full_or_found = Event()
        self.in_progress = []
        # Ensure we start off increasing.
        self.sort()
        self.closest = self.find_min(False)

    @property
    def searched(self):
        """
        :returns: Number of clients the shortlist has searched.
        :rtype: int.
        """
        return self.search_space.count(lambda x: x.contacted)

    def update(self, new_contacts):
        """
        Update the existing list with new contacts.

        :param new_contacts: Contacts returned by a search() operation.
        :type new_contacts: [:class:`common.Contact`]
        """
        # sort incoming contacts.
        new_contacts.sort(key=lambda x: x.hash_ ^ self.target_hash)

        for contact in new_contacts:
            # Can not include self in shortlist.
            if (self.own_hash != contact.hash_):
                # Stop if the desired contact is found.
                if (contact.hash_ == self.target_hash):
                    self.on_full_or_found(self.target_hash, contact)
                else:
                    self._try_add(contact)

    def rm_search(self, addr):
        """
        Filters all searches to remove the one given to it.

        :param addr: The address to remove.
        :type addr: :class:`common.Address`
        """
        self.in_progress = list(filter(lambda x: x.address != addr,
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
        if not (self.search_space.Any(lambda x: x.hash_ == contact.hash_)):
            # if < K contacts, add to the list.
            if (len(self.search_space) < K):
                self.search_space.append([False, contact])
            # if == K contacts, and < K contacted.
            elif (self.searched < K):
                # Set the max to the min so it must increment.
                max = self.find_min()
                if (contact.hash_ ^ self.target_hash <
                        max.contact.hash_ ^ self.target_hash):
                    self.search_space.remove(max)
                    self.search_space.append([False, contact])
                    self.sort()

    def sort(self):
        self.search_space.sort(key=lambda x: x[1].hash_ ^ self.target_hash)

    def get_next(self):
        """
        Gets the next item from the shortlist.
        Also marks as contacted.
        """
        # We are below the count and have at least one useable contact still.
        if ((self.searched <= K) and
                (self.search_space.any(lambda x: not x.contact))):
            item = self.find_min()
            item.contacted = True
            self.searched += 1
            self.in_progress.append(InProgress(item.contact.Address,
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
            if (self.searched > K):
                self.on_full_or_found(self.target_hash, self.closest)
                return None
        else:
            searchLambda = None
        minCon = self.search_space.first(searchLambda)

        for contact in self.search_space:
            if (uncontacted and not contact.contacted):
                if (contact.contact.hash_ ^ self.target_hash <
                        minCon.contact.hash_ ^ self.target_hash):
                    minCon = contact
            elif (not uncontacted):
                if (contact.contact.hash_ ^ self.target_hash <
                        minCon.contact.hash_ ^ self.target_hash):
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
            if (self.searched > K):
                return None
        else:
            searchLambda = None
        maxCon = self.search_space.first(searchLambda)

        # Reversed because we should ALWAYS be increasing.
        for contact in reversed(self.search_space):
            if (uncontacted and not contact.contacted):
                if (contact.contact.hash_ ^ self.target_hash >
                        maxCon.contact.hash_ ^ self.target_hash):
                    maxCon = contact
            elif (not uncontacted):
                if (contact.contact.hash_ ^ self.target_hash >
                        maxCon.contact.hash_ ^ self.target_hash):
                    maxCon = contact
        return maxCon

    def __str__(self):
        return '%s : %s - P:%d F:%d T:%d' % (self.target_hash,
                                             self.closest,
                                             len(self.in_progress),
                                             self.searched,
                                             K)

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

    def __init__(self):
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
        self._task_queue.put((self._start_search, (hash_, contacts)))

    def _start_search(self, hash_, contacts):
        self._shortlists[hash_] = Shortlist(hash_, contacts)
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
        self._task_queue.put((self._add_response, (hash_, request_addr,
                                                   responses)))

    def _add_response(self, hash_, request_addr, responses):
        self._shortlists[hash_].rm_search(request_addr)
        self._shortlists[hash_].update(responses)

    def rm_list(self, hash_):
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
            alive = list(filter(lambda x: (datetime.now()-x.time).seconds > 3,
                                shortlist.in_progress))
            # If any of the requests have timed out.
            if (len(alive) != len(shortlist.in_progress)):
                shortlist.in_progress = alive
            # Add any needed more requests to reach the parallel param A.
            while (len(shortlist.in_progress) < A):
                next_min = shortlist.get_next()
                # We have no more useable responses.
                print('Next Min:', next_min)
                print('in_progress:', shortlist.in_progress)
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
            #   if (task[0] != self._clean_lists):
            #       print('TASK:', task)
                task[0](*(task[1]))
            sleep(.2)
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
