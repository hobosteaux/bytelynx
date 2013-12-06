#!/usr/bin/python3
# Import structures
from bucket import Buckets
from shortlist import Shortlists
from udp import Server
import state
import protocol
from listExt import ExtList
from contact import Address
from sqlite import dbinterface

# Import Constants
from KademliaConstants import K # Bucketsize
from KademliaConstants import B	# Keysize
from KademliaConstants import A # Paralellism


class Kademlia():
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
		self.UDPStack.OnData += self.OnData


	def OnData(self, data, address):
		print(data[protocol.TYPETAG], '<-', address)
		contact = self.Buckets.Translate(address, data[protocol.HASHTAG])
		# Update Buckets.
		self.Buckets.Update(contact)
		# Deal with data.
		if (data[protocol.TYPETAG] == protocol.PONGMSG):
			contact.AwkPing(data[protocol.PKTIDTAG], data[protocol.HASHTAG])
		else:
			# Awk the packet.
			self.SendPong(contact, data[protocol.PKTIDTAG])
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
				self.SendData(contact, retData)
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

	def SendData(self, contact, data):
		# Update pings.
		data[protocol.PKTIDTAG] = contact.AddPing()
		data[protocol.HASHTAG] = state.SELF.Hash
		#print('Sending ', data, 'to', contact)
		self.UDPStack.Send(contact.Address, data)

	def SendPing(self, addr):
		pingData = { protocol.TYPETAG : protocol.PINGMSG,\
			protocol.PKTIDTAG : 0,\
			protocol.HASHTAG : state.SELF.Hash }
		self.UDPStack.Send(addr, pingData)

	def SendPong(self, contact, pktID):
		data = { protocol.TYPETAG : protocol.PONGMSG,\
			protocol.PKTIDTAG : pktID,\
			protocol.HASHTAG : state.SELF.Hash }
		self.UDPStack.Send(contact.Address, data)

	# Starts the searching fun on a shortlist.
	def InitSearch(self, hash):
		# Get closest contacts.
		contacts = self.Buckets.GetClosest(hash)
		# Init the search.
		self.ShortLists.Start(hash, contacts)

	# Sends out a packet to a single ip.
	def SendSearch(self, hash, contact):
		data = { protocol.TYPETAG : protocol.FINDNODEMSG,\
			protocol.TARGETHASHTAG : hash }
		self.SendData(contact, data)

	def EndSearch(self, hash, contact):
		print("Found Contact:", contact, hash)
