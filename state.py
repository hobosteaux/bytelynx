import os
import struct

from common import Contact, Address, Hash
import net.ipfinder
from net import Stack

# Global state variables
#: This instance's :class:`~common.Contact`
SELF = None
#: This instance's :class:`~net.Stack`
NET = None

#: Default hash for testing
DEFHASH = hash(b'12345678901234567890')
#: Default port
DEFPORT = 8906
#: Random hash, also for testing
RANDHASH = Hash(os.urandom(20))
#: Placeholder for arandom port
RANDPORT = 0
#: Virtual root dir for the instance
DIR = 'tmp/' + RANDHASH.base64[:10] + '/'

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

def __init__():
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
	global NET

	if SELF == None:
		print("Initing globals")
		new_port()

		addr = Address(net.ipfinder.check_in(), RANDPORT)
		SELF = Contact(addr, RANDHASH)
		NET = Stack()

__init__()
