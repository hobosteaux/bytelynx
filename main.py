#!/usr/bin/python3
import os
import base64

from kademlia import Kademlia
from menu import Menu, MenuOption
from contact import Address, Contact, Hash
import state

KADEM = Kademlia()

def PrintStatus():
	print('\t', state.SELF.Address)
	print('\t', state.SELF.Hash.ToBase64())

def PrintBuckets():
	for idx, bucket in enumerate(KADEM.Buckets.Buckets):
		if (len(bucket.Contacts) > 0):
			print(idx, bucket.Contacts)

def PrintShortlists():
	for item in KADEM.ShortLists.Shortlists:
		print(KADEM.ShortLists.Shortlists[item])

def AddContact():
	ip = input("IP Address [127.0.0.1]: ")
	if (not ip):
		ip = '127.0.0.1'
	port = int(input("Port: "))
	addr = Address(ip, port)
	KADEM.SendPing(addr)

def SearchContact():
	hash = input("Enter the hash [rand]: ")
	if (not hash):
		hash = Hash(os.urandom(20))
	else:
		hash = Hash(base64.b64decode(bytes(hash, 'UTF-8')))
	KADEM.InitSearch(hash)
	

if __name__ == '__main__':
	mainMenu = Menu([\
		MenuOption('Client Status', PrintStatus),\
		MenuOption('Bucket Status', PrintBuckets),\
		MenuOption('Shorty Status', PrintShortlists),\
		MenuOption('Add Contact', AddContact),\
		MenuOption('Search for Contact', SearchContact)\
	])

	mainMenu.Display() 
