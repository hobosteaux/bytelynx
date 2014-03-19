import os
import struct

from contact import Contact, Address, Hash
import ipfinder

# Global state variables
SELF = None

DEFHASH = hash(b'12345678901234567890')
"""Default hash for testing."""
DEFPORT = 8906
"""Default port."""
RANDHASH = Hash(os.urandom(20))
"""Random hash, also for testing."""
RANDPORT = 0
"""Placeholder for arandom port."""
DIR = 'tmp/' + RANDHASH.ToBase64()[:10] + '/'
"""Virtual root dir for the instance."""

os.makedirs(DIR)

def new_port():
	"""
	Gets a random free port > 10000.

	.. todo::
		Check if the port is free.
		And if it is < 65000.
	"""
	global RANDPORT
	RANDPORT = struct.unpack('H',os.urandom(2))[0]
	while (RANDPORT < 10000):
		RANDPORT = struct.unpack('H',os.urandom(2))[0]

def init():
	"""
	Sets up the global variables including:
	::
		Port
		Hash
		Own address
		Own Contact

	.. todo:: Init own hash.
	"""
	global SELF
	new_port()

	addr = Address(ipfinder.check_in(), RANDPORT)
	SELF = Contact(addr, RANDHASH)
