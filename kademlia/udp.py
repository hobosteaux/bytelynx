import socket
from protocol import Decoder, Encoder
from contact import Address
from event import Event
from threading import Thread
import state

class Server():
	_address = None
	_sock = None
	_listener = None
	OnData = None

	def __init__(self):
		self.OnData = Event()
		self._address = ('', state.SELF.Address.Port)
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._sock.bind(self._address)
		self._listener = Thread(target=self.Listen)
		self._listener.daemon = True
		self._listener.start()

		
	def Listen(self):
		#print("Waiting for message")
		while(True):
			data, address = self._sock.recvfrom(65536)
    			
			#print('received '+ str(len(data)) +' bytes from '+ str(address))

			#try:
			address = Address(address[0], address[1])
			data = Decoder(data)
			self.OnData(data, address)

			#except:
			#	print("ERROR:", address, data)

	def Send(self, address, tags):
		print(tags['type'], '->', address)
		data = Encoder(tags)
		self._sock.sendto(data, address.AsTuple())
