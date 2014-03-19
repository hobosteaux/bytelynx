#!/usr/bin/python3
# Import structures
from bucket import Buckets
from shortlist import Shortlists
import state
import protocol
from common import dbinterface, Address, List
from net import Server

# Import Constants
from constants import K # Bucketsize
from constants import B	# Keysize
from constants import A # Paralellism


class Kademlia():
	"""
	The main interface to the kademlia DHT.
	Because the DHT has to stay updated with all the
	packets transferred, this also must be the hub
	of all network traffic.	
	"""
	ShortLists = None
	Buckets = None
	UDPStack = None
	DBConn = None

	def __init__(self):
		# Set global things
		state.Init()

		self.DBConn = dbinterface()

		self.ShortLists = Shortlists()
		self.ShortLists.OnSearch += self.SendSearch
		self.ShortLists.OnFullOrFound += self.EndSearch

		self.Buckets = Buckets()
		self.Buckets.OnAdded += self.DBConn.AddContact
		self.Buckets.OnRemoved += self.DBConn.RemoveContact
		contacts = self.DBConn.Contacts() + [state.SELF]
		self.Buckets.Seed(contacts)

		self.UDPStack = Server()
		self.UDPStack.on_data += self.on_data


	def on_data(self, data, address):
		"""
		Function called whenever new data comes in.

		:param data: Dictionary of the attributes and values.
		:type data: {}
		:param address: Remote address of the data.
		:type address: :class:`~common.Address`
		"""
		print(data[protocol.TYPETAG], '<-', address)
		contact = self.Buckets.Translate(address, data[protocol.HASHTAG])
		# Update Buckets.
		self.Buckets.Update(contact)
		# Deal with data.
		if (data[protocol.TYPETAG] == protocol.PONGMSG):
			contact.AwkPing(data[protocol.PKTIDTAG], data[protocol.HASHTAG])
		else:
			# Awk the packet.
			self.send_pong(contact, data[protocol.PKTIDTAG])
			# Find node message, send response.
			if (data[protocol.TYPETAG] == protocol.FINDNODEMSG):
				contacts = self.Buckets.GetClosest(data[protocol.TARGETHASHTAG])
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
				contacts = [self.Buckets.Translate(\
					Address(x[protocol.IPTAG], x[protocol.PORTTAG]),\
						x[protocol.HASHTAG])\
					for x in data[protocol.EXTTAG]]
				self.ShortLists.AddResponse(data[protocol.TARGETHASHTAG],\
					contact.Address, contacts)
		
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
		# Update pings.
		data[protocol.PKTIDTAG] = contact.AddPing()
		data[protocol.HASHTAG] = state.SELF.Hash
		#print('Sending ', data, 'to', contact)
		self.UDPStack.Send(contact.Address, data)

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
		self.UDPStack.Send(addr, pingData)

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
		self.UDPStack.Send(contact.Address, data)

	def init_search(self, hash_):
		"""
		Starts the searching fun on a shortlist.

		:param hash_: Hash to attempt to find.
		:type hash_: :class:`~common.Hash`
		"""
		# Get closest contacts.
		contacts = self.Buckets.GetClosest(hash_)
		# Init the search.
		self.ShortLists.Start(hash_, contacts)

	# Sends out a packet to a single ip.
	def SendSearch(self, hash_, contact):
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

	def EndSearch(self, hash_, contact):
		"""
		Event proc'd on the end of a search.
		"""
		print("Found Contact:", contact, hash_)
