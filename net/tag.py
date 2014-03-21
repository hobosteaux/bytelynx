import struct

from common import Hash, Address
from kademlia import B # Hashsize in bytes.

ENDIAN = '>'
"""The symbol for struct.[un]pack's endianess"""

class Tag():
	"""
	Construct to transform a data value to binary data and back.
	"""

	def __init__(self, tag_struct):
		self.tag_struct = ENDIAN + tag_struct
		self._value = None

	@property
	def size(self):
		return struct.calcsize(self.tag_struct)

	@property
	def struct(self):
		return struct.pack(self.tag_struct, self._value)

	@struct.setter
	def struct(self, value):
		# Grab the first value.
		# Since this is a simple setter, there should only ever be one.
		self._value = struct.unpack(self.tag_struct)[0]

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, value):
		self._value = value

class HashTag(Tag):

	def __init__(self):
		self.tag_struct = "%s%ss" % (ENDIAN, B / 8)

	@property
	def struct(self):
		return self._value.value

	@struct.setter
	def struct(self, value):
		self._value = Hash(value)

class AddressTag(Tag):

	def __init__(self):
		self.tag_struct = ENDIAN + '4BH'

	@property
	def struct(self):
		return struct.pack(self.tag_struct,
			*([int(x) for x in self._value.ip.split('.')] +
				[self._value.port]))

	@struct.setter
	def struct(self, value):
		raw = struct.unpack(self.tag_struct, value)
		self._value = Address('.'.join(raw[:4]), raw[4])
