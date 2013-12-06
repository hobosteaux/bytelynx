import os
import struct

from contact import Contact, Address, Hash
import ipfinder

# Global state variables
SELF = None

DEFHASH = hash(b'12345678901234567890')
DEFPORT = 8906
RANDHASH = Hash(os.urandom(20))
RANDPORT = 0
DIR = 'tmp/' + RANDHASH.ToBase64()[:10] + '/'

os.makedirs(DIR)

def NewPort():
	global RANDPORT
	RANDPORT = struct.unpack('H',os.urandom(2))[0]
	while (RANDPORT < 10000):
		RANDPORT = struct.unpack('H',os.urandom(2))[0]

def Init():
	global SELF
	NewPort()

	addr = Address(ipfinder.check_in(), RANDPORT)
	SELF = Contact(addr, RANDHASH)
