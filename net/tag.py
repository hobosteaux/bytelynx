import struct
from collections import namedtuple

from common import Hash, Address
from kademlia import B # Hashsize in bytes.
from .common import *

class Tag():
	"""
	Construct to transform a data value to encoded data and back.
	Stores one packed value of a given type.
	"""

	def __init__(self, name, tag_struct):
		self.name = name
		self.tag_struct = ENDIAN + tag_struct
		self._value = None
		self._header_size = struct.calcsize(SIZE_SYMBOL)

	@property
	def encoded(self):
		d = self._encoded
		return struct.pack(SIZE_SYMBOL, len(d)) + d

	@property
	def _encoded(self):
		return struct.pack(self.tag_struct, self._value)

	@encoded.setter
	def encoded(self, value):
		# Grab the first value.
		# Since this is a simple setter, there should only ever be one.
		self._value = struct.unpack(self.tag_struct, value)[0]

	def to_value(self, encoded):
		self.encoded = encoded
		return self.value

	def to_encoded(self, value):
		self.value = value
		return self.encoded

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, value):
		self._value = value

class HashTag(Tag):
	"""
	Tag that encapsulates a :class:`common.Hash` object.
	"""

	def __init__(self):
		super().__init__('hash', "%ss" %  (B // 8))

	@property
	def _encoded(self):
		return self._value.value

	@Tag.encoded.setter
	def encoded(self, value):
		self._value = Hash(value)

class AddressTag(Tag):
	"""
	Tag that encapsulates a :class:`common.Address` object.
	Serializes the ip address and the port.
	"""

	def __init__(self):
		super().__init__('address', '4BH')

	@property
	def _encoded(self):
		return struct.pack(self.tag_struct,
			*([int(x) for x in self._value.ip.split('.')] +
				[self._value.port]))

	@Tag.encoded.setter
	def encoded(self, value):
		raw = struct.unpack(self.tag_struct, value)
		self._value = Address('.'.join(str(x) for x in raw[:4]), raw[4])

Node = namedtuple('Node', 'hash address')
"""Quick struct for the output of :class:`~net.tag.NodeTag`"""

class NodeTag(Tag):
	"""
	Represents a Node.
	Encapsulates an :class:`common.Address` and a :class:`common.Hash`.

	.. note::
		This class breaks convention by taking a :class:`common.Contact`
		object, but returning the Node namedtuple.
		This is because the translation to a Contact object must be
		done by the kademlia contacts table.
	"""

	def __init__(self):
		super().__init__('contact', '%ss4BH' % (B // 8))

	@Tag.value.setter
	def value(self, contact):
		self._value = Node(contact.hash, contact.address)

	@property
	def _encoded(self):
		return struct.pack(self.tag_struct,
			*([self._value.hash.value] +
			[int(x) for x in self._value.address.ip.split('.')] +
			[self._value.address.port]))

	@Tag.encoded.setter
	def encoded(self, value):
		raw = struct.unpack(self.tag_struct, value)
		self._value = Node(Hash(raw[0]),
			Address('.'.join(str(x) for x in raw[1:5]), raw[5]))


class StringTag(Tag):
	"""
	Tag that encapsulates a variable-length string.
	"""
	
	def __init__(self, name):
		super().__init__(name, '')
	
	@property
	def _encoded(self):
		return bytes(self._value, 'utf-8')

	@Tag.encoded.setter
	def encoded(self, value):
		self._value = value.decode('utf-8')
		

class ListTag(Tag):
	"""
	Tag that encapsulates a list of single tag.
	"""

	def __init__(self, name, inner_tag):
		"""
		:param inner_tag: The tag inside the array.
		:type inner_tag: :class:`~net.tag.Tag` base
		"""
		super().__init__(name, '')
		self.inner_tag = inner_tag

	@property
	def _encoded(self):
		return b''.join(self.inner_tag.to_encoded(x) for x in self._value)

	@Tag.encoded.setter
	def encoded(self, in_bytes):
		a = []
		x = 0
		while x < len(in_bytes):
			# Grab the size.
			sz = struct.unpack(SIZE_SYMBOL,
							in_bytes[x : x + self._header_size])[0]
			x += self._header_size
			a.append(self.inner_tag.to_value(in_bytes[x : x + sz]))
			x += sz

class VarintTag(Tag):
	"""
	Tag that encapsulates a variable-length integer.
	Used for DH handshakes.
	"""
	
	def __init__(self, name):
		super().__init__(name, '')
	
	@property
	def _encoded(self):
		length = round((self._value.bit_length() / 8) + 0.5)
		return self._value.to_bytes(length, 'big')

	@Tag.encoded.setter
	def encoded(self, value):
		self._value = int.from_bytes(value, 'big')
