import datetime
import ChunkedFile
import struct
from threading import lock

class TransferSlice():
	File = None
	Chunk = None
	Slice = None
	Addr = None

	def __init__(self, f, chunk, sliceNo, addr):
		self.File = f
		self.Chunk = chunk
		self.Slice = sliceNo
		self.Addr = addr

class RecentPacket():
	Sent = datetime.datetime.now()	
	Data = None

	def __init__(self, data):
		self.Data = data

class Connection():
	RemoteAddr = None
	PktCounter = 0
	RecentlySent = None
	Pings = None
	Sock = None
	AvePing = 500 #Running filter of geometrically reducing samples

	def __init__(self, sock, remoteAddr):
		self.Sock = sock
		self.RecentlySent = {}
		self.Pings = {}
		self.RemoteAddr = remoteAddr

	def SendData(self, typeNum, data):
		pktID = self.PktCounter
		self.PktCounter += 1
		if self.PktCounter > 65000: # TODO: Find exact max
			self.PktCounter = 0
		d = (struct.pack('>BH', typeNum, pktID) + data)
		self.RecentlySent[pktID] = RecentPacket(data)
		self.Sock.sendto(data, self.RemoteAddr)

	def ResendData(self, data, pktID):
		self.RecentlySent[pktID] = RecentPacket(data)
		self.Sock.sendto(data, self.RemoteAddr)
	
	def AddPing(self, pktID):
		self.Pings[pktID] = datetime.datetime.now()

	def PingCallback(self, pktID):
		time = datetime.datetime.now() - self.Pings[num]
		del(self.Pings[num])
		time = time.seconds * 1000 + time.microseconds / 1000
		self.AvePing = (self.AvePing / 1.5) + (time / 3)

	def SendAwk(self, num):
		self.SendData(('>BH', 0, self.PktCounter))

	def AwkPkt(self, num):
		del self.RecentlySent[num]
		# TODO: Fix w/ try catch once del error is known
		

class State():
	Connections = {}
	Sock = None
	Files = None
	SlicesToSend = []
	SliceLock = None
	Active = True
	
	def __init__(self, sock):
		self.Sock = sock
		self.SliceLock = threading.Lock()
		Files = ChunkedFile.Directory('./files')

	def NewConn(self, addr):
		self.Connections[addr] = Connection(self.Sock, addr)

