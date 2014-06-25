#!/usr/bin/python3
# Import structures
import state
from .bucket import Buckets
from .shortlist import Shortlists
from common import dbinterface
# import net.tagconstants as Tags


class Kademlia():
    """
    The main interface to the kademlia DHT.
    Because the DHT has to stay updated with all the
    packets transferred, this also must be the hub
    of all network traffic.

    .. attribute:: shortlists

        The kademlia :class:`~kademlia.Shortlists`
    .. attribute:: buckets

        The kademlia :class:`~kademlia.Buckets`
    .. db_conn

        Database handle :class:`common.dbinterface`
    """

    def __init__(self):
        self.db_conn = dbinterface(state.DIR)

        self.shortlists = Shortlists()
        self.shortlists.on_search += self.send_search
        self.shortlists.on_full_or_found += self.end_search

        self.buckets = Buckets()
        self.buckets.on_added += self.db_conn.add_contact
        self.buckets.on_removed += self.db_conn.rm_contact
        contacts = self.db_conn.contacts() + [state.SELF]
        self.buckets.seed(contacts)

        state.NET.protocol.on_dht += self.dht_handler

    def dht_handler(self, contact):
        """
        Updates the buckets when a bucket-eligible
        message is received.

        :param contact: The contact that data was received from
        :type contact: :class:`~common.Contact`
        """
        self.buckets.update(contact)

    def on_find_node_request(self, contact, data):
        """
        Event handler for when a request for a node arrives.
        """
        contacts = self.buckets.get_closest(data['hash'])
        retData = {'hash': data['hash'], 'nodes': contacts}
        state.NET.send_data(contact, 'dht.response', retData)

    def on_find_node_response(self, contact, data):
        contacts = data['nodes']
        self.shortlists.add_response(data['hash'],
                                     contact.address,
                                     contacts)

    def send_ping(self, contact):
        """
        Send a dht ping to a contact.
        Used to alert them to your presence.

        :param addr: Address to send it to.
        :type addr: :class:`~common.Contact`
        """
        state.NET.send_data(contact, 'dht.ping', {})

    def init_search(self, hash_):
        """
        Starts the searching fun on a shortlist.

        :param hash_: Hash to attempt to find.
        :type hash_: :class:`~common.Hash`
        """
        # Get closest contacts.
        contacts = self.buckets.get_closest(hash_)
        # Init the search.
        self.shortlists.start(hash_, contacts)

    def send_search(self, hash_, contact):
        """
        Sends a find node message out to a contact.

        :param hash_: Hash to search for.
        :type hash_: :class:`~common.Hash`
        :param contact: The contact to send the request to.
        :type contact: :class:`~common.Contact`
        """
        data = {'hash': hash_}
        state.NET.send_data(contact, 'dht.search', data)

    def end_search(self, hash_, contact):
        """
        Event proc'd on the end of a search.
        """
        print("Found Contact:", contact, hash_)
