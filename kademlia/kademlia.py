#!/usr/bin/python3
from .bucket import Buckets
from .shortlist import Shortlists
from common import dbinterface


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

    def __init__(self, net, own_contact, dir_, K, B, A):
        """
        :param net:
        :type net: :class:`~net.BytelynxStack`
        :param own_contact:
        :type own_contact: :class:`~common.Contact`
        :param dir_:
        :type dir_:
        :param K: Bucket size
        :type K: int.
        :param B: Key size
        :type B: int.
        :param A: Paralellism
        :type A: int.
        """
        self.db_conn = dbinterface(dir_)
        self.net = net
        self.K = K
        self.own_contact = own_contact

        self.shortlists = Shortlists(own_contact.hash, K, A)
        self.shortlists.on_search += self.send_search
        self.shortlists.on_full_or_found += self.end_search

        self.buckets = Buckets(own_contact.hash, K, B)
        self.buckets.on_added += self.db_conn.add_contact
        self.buckets.on_removed += self.db_conn.rm_contact
        db_contacts = self.net.update_contacts(self.db_conn.contacts())

        all_contacts = db_contacts + [own_contact]
        self.buckets.seed(all_contacts)

        self._register_protocol()

    def _register_protocol(self):
        self.net.protocol.on_dht += self.dht_handler

        msgs = self.net.protocol.messages
        msgs['dht.search'].on_data += self.on_find_node_request
        msgs['dht.response'].on_data += self.on_find_node_response

    def dht_handler(self, contact):
        """
        Updates the buckets when a bucket-eligible
        message is received.

        :param contact: The contact that data was received from
        :type contact: :class:`~common.Contact`
        """
        print("DHT for %s" % contact)
        self.buckets.update(contact)

    def on_find_node_request(self, contact, data):
        """
        Event handler for when a request for a node arrives.
        """
        contacts = self.buckets.get_closest(data['payload']['hash'],
                                            count=self.K + 2)
        # Filter out self and requesting contacts
        contacts = [x for x in contacts
                    if x != contact
                    and x != self.own_contact][:self.K]
        print("FIND_CONTACTS: %s" % contacts)
        retData = {'hash': data['payload']['hash'], 'nodes': contacts}
        self.net.send_data(contact, 'dht.response', retData)

    def on_find_node_response(self, contact, data):
        # Translate to 'real' contacts first
        print("INDATA %s" % data['payload']['nodes'])
        contacts = self.net.update_contacts(data['payload']['nodes'])
        print("INCONTACTS: %s" % contacts)
        self.shortlists.add_response(data['payload']['hash'],
                                     contact.address,
                                     contacts)

    def send_ping(self, contact):
        """
        Send a dht ping to a contact.
        Used to alert them to your presence.

        :param addr: Address to send it to.
        :type addr: :class:`~common.Contact`
        """
        self.net.send_data(contact, 'dht.ping', {})

    def init_search(self, hash_):
        """
        Starts the searching fun on a shortlist.

        :param hash_: Hash to attempt to find.
        :type hash_: :class:`~common.Hash`
        """
        # Get closest contacts.
        contacts = self.buckets.get_closest(hash_)
        # Init the search.
        self.shortlists.start_search(hash_, contacts)

    def send_search(self, hash_, contact):
        """
        Sends a find node message out to a contact.

        :param hash_: Hash to search for.
        :type hash_: :class:`~common.Hash`
        :param contact: The contact to send the request to.
        :type contact: :class:`~common.Contact`
        """
        data = {'hash': hash_}
        self.net.send_data(contact, 'dht.search', data)

    def end_search(self, hash_, contact):
        """
        Event proc'd on the end of a search.
        """
        print("Found Contact:", contact, hash_)
