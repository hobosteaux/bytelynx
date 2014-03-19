import socket
import struct
import sys
import datetime
import common
import protos

class Server():
	_address = ('', 9000)
	State = None
	Run = True

	def __init__(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(self._address)
		self.State = common.State(sock)
		
	def Listen(self):
		while self.Run:
			print("Waiting for message")
			#self.Log('waiting to receive message')
			data, address = self._sock.recvfrom(65536)
    			
			print('received '+ str(len(data)) +' bytes from '+ str(address))
			#self.Log('received '+ str(len(data)) +' bytes from '+ str(address))
			#self.Log('DATA - '+ str(data))

			try:
				data = protos.Unpack(data)
				# if we have an array object
				if len(data) == 3:
					protos.Protos[data[0]][1](data[1:], self.State, address)
				elif len(data) == 2:
					protos.Protos[data[0]][1](data[1], self.State, address)
			except:
				print("ERROR")		

	def Log(self, message):
		logger = open('log.txt', 'a')
		logger.write(str(datetime.datetime.now()) + " - " + message +"\n")
		logger.close()
		

