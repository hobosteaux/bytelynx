#!/usr/bin/python3
from time import sleep
from udp import Server
import state
from contact import Address
import protocol

SERVER = None

def OnData(data, address):
	print('Received', data['type'], 'from', address)

def SendPing(addr):
	pingData = { protocol.TYPETAG : protocol.PINGMSG,\
		protocol.PKTIDTAG : 0,\
		protocol.HASHTAG : state.SELF.Hash }
	SERVER.Send(addr, pingData)

if __name__ == '__main__':
	state.Init()
	state.SELF.Address.Port = state.DEFPORT
	global SERVER
	SERVER = Server()
	SERVER.OnData += OnData

	address = input("Address: ")
	address = Address(address, state.SELF.Address.Port)
	while (True):
		SendPing(address)
		sleep(.1)
