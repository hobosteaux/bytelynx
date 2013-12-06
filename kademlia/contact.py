from datetime import datetime, timedelta
import base64

from event import Event
from listExt import ExtList
from KademliaConstants import B

TIMEOUTMULT = 3

class Contact():
	Ping = 150		# Sliding counter on ping response times
	PingList = None	# List of all pings sent and send time
	Liveliness = 1	# Sliding counter on missed pings
	Counter = 0		# Packet Counter
	Address = None	# Remote Address
	Hash = None		# Remote Hash
	LastSeen = None	# Last time a packet was seen from this address
	NeedHash = False

	OnDeath = None	# Event when the contact has died

	def __init__(self, addr, hash=None):
		self.NeedHash = hash == None
		self.Address = addr
		self.Hash = hash
		self.LastSeen = datetime.now()
		self.PingList = ExtList()
		self.OnDeath = Event()

	def __str__(self):
		return '%s' % (self.Address)

	def __repr__(self):
		return '%s' % (self.Address)

	def AddPing(self):
		pktID = self.Counter
		self.Counter += 1
		self.PingList.append(Ping(pktID, datetime.now()))
		if (self.Counter > 65535):
			self.Counter = 0
		return pktID

	def AwkPing(self, pktID, hash):
		if (self.NeedHash):
			self.Hash = hash
		try:
			# I would love to use PyLINQ, but we are cleaning any old pings too.
			oldPings = []
			for ping in self.PingList:
				# If we found the ping that we are trying to awk.
				if (ping.PktID == pktID):
					time = ping.Latency()
					time = time.seconds * 1000 + time.microseconds / 1000
					self.Ping = (self.Ping / 1.5) + (time / 3)
					self.Liveliness = (self.Liveliness * 0.8) + 0.2
					oldPings.append(ping)
					break
				elif (ping.Latency() > timedelta(milliseconds=self.Ping * TIMEOUTMULT)):
					oldPings.append(ping)
			map(lambda x: self.KillPing(x), oldPings)
		# Happens if ... ?
		except StopIteration:
			pass

	def KillPing(self, ping):
		self.PingList.remove(ping)
		self.Liveliness *= 0.8
		if (self.Liveliness <= 0):
			 self.OnDeath(self)

class Ping():
	PktID = 0
	SentTime = None

	def __init__(self, pktid, time):
		self.PktID = pktid
		self.SentTime = time

	def Latency(self):
		return datetime.now() - self.SentTime

class Hash():
	Value = None	# Bytes object

	def __init__(self, value):
		self.Value = value

	def __len__(self, other):
		return len(self.Value)
	
	def __str__(self):
		return '%s:%s' % ('h', self.Value)
	
	def __hash__(self):
		return hash(self.Value)

	def __lt__(self, other):
		return self.Value < other.Value 

	def __gt__(self, other):
		return self.Value > other.Value

	def __eq__(self, other):
		try:
			return self.Value == other.Value
		except AttributeError:
			return False

	def __ne__(self, other):
		return self.Value != other.Value

	def AbsDiff(self, other):
		if (other > self):
			return other - self
		return self - other

	def __sub__(self, other):
		if (len(self.Value) != len(other.Value)):
			raise ValueError("Hashes are not of the same length.")
		i = int.from_bytes(self.Value, 'little') - int.from_bytes(other.Value, 'little')
		return Hash(i.to_bytes(len(self.Value), 'little'))

	def __xor__(self, other):
		if (len(self.Value) != len(other.Value)):
			raise ValueError("Hashes are not of the same length.")
		i = int.from_bytes(self.Value, 'little') ^ int.from_bytes(other.Value, 'little')
		return Hash(i.to_bytes(len(self.Value), 'little'))

	def SigBit(self):
		for i in range(0, len(self.Value)):
			b = 128
			for j in range(0,8):
				if (self.Value[i] & b != 0):
					return ((len(self.Value) * 8) - (i * 8) - j)
				b //= 2
		return 0

	def ToBitString(self):
		str_data = ''
		for i in range(0, len(self.Value)):
			b = 128
			for j in range(0,8):
				if (self.Value[i] & b != 0):
					str_data += '1'
				else:
					str_data += '0'
				b //= 2
		return str_data


	def ToBase64(self):
		return str(base64.b64encode(self.Value), 'UTF-8')

class Address():
	IP = ''
	Port = 0

	def __init__(self, ip, port):
		self.IP = ip
		self.Port = port

	def AsTuple(self):
		return (self.IP, self.Port)

	def __str__(self):
		return '%s:%s' % (self.IP, self.Port)
