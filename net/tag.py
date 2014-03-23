import struct

from common import Hash, Address
from kademlia import B # Hashsize in bytes.

ENDIAN = '>'
"""The symbol for struct.[un]pack's endianess"""
SIZE_SYMBOL = ENDIAN + 'H'
"""The tag preceeding every value for the size of it in bytes"""

class Tag():
	"""
	Construct to transform a data value to encoded data and back.
	"""

	def __init__(self, tag_string, tag_encoded):
		self.tag_string = tag_string
		self.tag_encoded = ENDIAN + tag_encoded
		self._value = None
		self._header_size = struct.calcsize(SIZE_SYMBOL)

	@property
	def encoded(self):
		"""
		Primary getter for the struct.
		Calls self._encoded (overloaded) and cats the len on the front.
		"""
		d = self._encoded
		return struct.pack(SIZE_SYMBOL, len(d)) + d

	@property
	def _encoded(self):
		return struct.pack(self.tag_encoded, self._value)

	@encoded.setter
	def encoded(self, value):
		# Grab the first value.
		# Since this is a simple setter, there should only ever be one.
		self._value = struct.unpack(self.tag_encoded)[0]

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

	def __init__(self):
		super().__init__('hash', "%ss" %  B / 8)

	@property
	def _encoded(self):
		return self._value.value

	@Tag.encoded.setter
	def encoded(self, value):
		self._value = Hash(value)

class AddressTag(Tag):

	def __init__(self):
		super().__init__('address', '4BH')

	@property
	def _encoded(self):
		return struct.pack(self.tag_encoded,
			*([int(x) for x in self._value.ip.split('.')] +
				[self._value.port]))

	@Tag.encoded.setter
	def encoded(self, value):
		raw = struct.unpack(self.tag_encoded, value)
		self._value = Address('.'.join(str(x) for x in raw[:4]), raw[4])

class ListTag(Tag):
	"""
	A tag that stands for a list of items.
	"""

	def __init__(self, tag_string, inner_tag):
		"""
		:param inner_tag: The tag inside the array.
		:type inner_tag: :class:`~net.tag.Tag` base
		"""
		super().__init__(tag_string, '')
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
			print(x)
			sz = struct.unpack(SIZE_SYMBOL,
							in_bytes[x : x + self._header_size])[0]
			x += self._header_size
			a.append(self.inner_tag.to_value(in_bytes[x : x + sz]))
			x += sz

