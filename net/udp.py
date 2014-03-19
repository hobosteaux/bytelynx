import socket
from protocol import Decoder, Encoder
from contact import Address
from event import Event
from threading import Thread
import state

class Server():
	"""
	A simple threaded UDP server.
	Throws the :attr:`~net.Server.on_data` event when a packet is received.

	.. attribute:: on_data:
		A tuple of ({data}, :class:`net.Address`)
	"""

	def __init__(self):
		self.on_data = Event()
		self._bind_address = ('', state.SELF.Address.Port)
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._sock.bind(self._bind_address)
		self._listener_thread = Thread(target=self.listen)
		self._listener_thread.daemon = True
		self._listener_thread.start()

	def listen(self):
		"""
		Main while (True) loop to receive messages.
		"""
		#print("Waiting for message")
		while (True):
			data, address = self._sock.recvfrom(65536)
    			
			#print('received '+ str(len(data)) +' bytes from '+ str(address))

			#try:
			address = Address(address[0], address[1])
			data = Decoder(data)
			self.on_data(data, address)

			#except:
			#	print("ERROR:", address, data)

	def send(self, address, tags):
		"""
		Sends a dictionary of tags to an address.

		:param address: The destination address.
		:type address:`~net.Address`
		:param tags: Tags to encode.
		:type tags: {}
		"""
		print(tags['type'], '->', address)
		data = Encoder(tags)
		self._sock.sendto(data, address.AsTuple())
