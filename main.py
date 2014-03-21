#!/usr/bin/python3
import os
import base64

from kademlia import Kademlia
from ui import Menu, MenuOption
from common import Address, Contact, Hash
import state

KADEM = Kademlia()

def print_status():
	print('\t', state.SELF.address)
	print('\t', state.SELF.hash.base64)

def print_buckets():
	for idx, bucket in enumerate(KADEM.buckets._buckets):
		if (len(bucket.contacts) > 0):
			print(idx, bucket.contacts)

def print_shortlistss():
	for item in KADEM.shortlists._shortlists:
		print(KADEM.shortlists._shortlists[item])

def add_contact():
	ip = input("IP Address [127.0.0.1]: ")
	if (not ip):
		ip = '127.0.0.1'
	port = int(input("Port: "))
	addr = address(ip, port)
	KADEM.send_ping(addr)

def search_contact():
	hash_ = input("Enter the hash [rand]: ")
	if (not hash_):
		hash_ = Hash(os.urandom(20))
	else:
		hash_ = Hash(base64.b64decode(bytes(hash_, 'UTF-8')))
	KADEM.init_search(hash_)
	

if __name__ == '__main__':
	main_menu = Menu([\
		MenuOption('Client Status', print_status),\
		MenuOption('Bucket Status', print_buckets),\
		MenuOption('Shorty Status', print_shortlistss),\
		MenuOption('Add Contact', add_contact),\
		MenuOption('Search for Contact', search_contact)\
	])

	main_menu.display() 
