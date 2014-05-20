#!/usr/bin/python3
# Import structures
import state
from .bucket import Buckets
from .shortlist import Shortlists
from common import dbinterface, Address, List
from net import Server
import net.tagconstants as Tags


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
		self.db_conn = dbinterface()

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
		self.send_data(contact, retData)

	def on_find_node_response(self, contact, data):
		contacts = data['nodes']
		self.shortlists.add_response(data['hash'],
					contact.address, contacts)
		

	def on_data(self, data, address):
		"""
		Function called whenever new data comes in.

		:param data: Dictionary of the attributes and values.
		:type data: {}
		:param address: Remote address of the data.
		:type address: :class:`~common.Address`
		"""
		print(data[protocol.TYPETAG], '<-', address)
		contact = self.buckets.translate(address, data[protocol.HASHTAG])
		# update buckets.
		self.buckets.update(contact)
		# Deal with data.
		if (data[protocol.TYPETAG] == protocol.PONGMSG):
			contact.awk_ping(data[protocol.PKTIDTAG], data[protocol.HASHTAG])
		else:
			# Awk the packet.
			self.send_pong(contact, data[protocol.PKTIDTAG])
			# Find node message, send response.
			if (data[protocol.TYPETAG] == protocol.FINDNODEMSG):
				contacts = self.buckets.get_closest(data[protocol.TARGETHASHTAG])
				ret = ExtList()
				for i in contacts:
					ret.append({protocol.HASHTAG : i.Hash,\
						protocol.IPTAG : i.Address.IP,\
						protocol.PORTTAG : i.Address.Port})
				retData = { protocol.TYPETAG : protocol.FOUNDNODEMSG, protocol.EXTTAG : ret,\
					protocol.TARGETHASHTAG : data[protocol.TARGETHASHTAG] }
				self.send_data(contact, retData)
			# Found node message, add to the tables.
			elif (data[protocol.TYPETAG] == protocol.FOUNDNODEMSG):
				contacts = [self.buckets.translate(\
					Address(x[protocol.IPTAG], x[protocol.PORTTAG]),\
						x[protocol.HASHTAG])\
					for x in data[protocol.EXTTAG]]
				self.shortlists.add_response(data[protocol.TARGETHASHTAG],\
					contact.address, contacts)
		
			elif (data[protocol.TYPETAG] == protocol.PAYLOADMSG):
				pass

	def send_data(self, contact, data):
		"""
		Sends data to a remote contact and marks down a ping.

		:param contact: Contact to send data to.
		:type contact: :class:`~common.Contact`
		:param data: Dictionary of the attributes and values.
		:type data: {}
		"""
		# update pings.
		data[protocol.PKTIDTAG] = contact.add_ping()
		data[protocol.HASHTAG] = state.SELF.Hash
		#print('sending ', data, 'to', contact)
		self.udp_stack.send(contact.address, data)

	def send_ping(self, addr):
		"""
		Send a raw ping to a contact.
		Used to alert them to your presence.

		:param addr: Address to send it to.
		:type addr: :class:`~common.Address`
		"""
		pingData = { protocol.TYPETAG : protocol.PINGMSG,\
			protocol.PKTIDTAG : 0,\
			protocol.HASHTAG : state.SELF.Hash }
		self.udp_stack.send(addr, pingData)

	def send_pong(self, contact, pkt_id):
		"""
		A pong for the pings.

		:param contact: The contact to send the pong to.
		:type contact: :class:`~common.Contact`
		:param pkt_id: What packet to pong.
		:type pkt_id: int.
		"""
		data = { protocol.TYPETAG : protocol.PONGMSG,\
			protocol.PKTIDTAG : pkt_id,\
			protocol.HASHTAG : state.SELF.Hash }
		self.udp_stack.send(contact.Address, data)

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

	# sends out a packet to a single ip.
	def send_search(self, hash_, contact):
		"""
		Sends a find node message out to a contact.

		:param hash_: Hash to search for.
		:type hash_: :class:`~common.Hash`
		:param contact: The contact to send the request to.
		:type contact: :class:`~common.Contact`
		"""
		data = {protocol.TYPETAG : protocol.FINDNODEMSG,
				protocol.TARGETHASHTAG : hash_}
		self.send_data(contact, data)

	def end_search(self, hash_, contact):
		"""
		Event proc'd on the end of a search.
		"""
		print("Found Contact:", contact, hash_)
