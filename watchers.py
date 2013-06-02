import common
import threading
from time import sleep
from struct import pack

class ChunkWatcher():
	State = None
	Thread = None
	SleepTime = .01 # Adjust for flow control.

	def __init__(self, state):
		self.State = state
		self.Thread = threading.Thread(target = Process)
		self.Thread.start()

	def Process(self):
		while self.State.Active:
			if len(self.State.SlicesToSend) > 0:
				self.State.SliceLock.aquire()
				data = self.State.SlicesToSend[0].Chunk.ReadSlice(self.State.SlicesToSend[0].Slice)
				# fhash, chunkno, sliceno, data
				data = pack(">16sHH", self.State.SlicesToSend[0].File.Hash,\
					self.State.SlicesToSend[0].Chunk, self.State.SlicesToSend[0].Slice) + data
				addr = self.State.SlicesToSend[0].Addr
				del(self.State.SlicesToSend[0])
				self.State.SliceLock.release()
				self.State.Connections[addr].SendData(9, data)
			sleep(self.SleepTime)

class ResendWatcher():
	State = None
	Thread = None
	SleepTime = .01 # Adjust if packets are being resent or burning too much CPU.

	def __init__(self, state):
		self.State = state
		self.Thread = threading.Thread(target = Process)
		self.Thread.start()

	def Process(self):
		while self.State.Active:
			for conn in self.State.Connections;
				for pktID in conn.RecentlySent:
					if conn.RecentlySent[pktID].Sent - datetime.datetime.now()\
						 > timedelta(milliseconds=(conn.AvePing * 3)):
						conn.ResendData(conn.RecentlySent[pktID].Data, pktID)
			sleep(self.SleepTime)
