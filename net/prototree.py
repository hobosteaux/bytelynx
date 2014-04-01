from .tag import Tag, HashTag, AddressTag, NodeTag
from .common import *
from common.exceptions import *

class CryptoHandlers():
	def __init__(self, dh, pki, symmetric):
		self.dh = dh
		self.pki = pki
		self.symmetric = symmetric

class Message():

	def __init__(self, tags=None, submessages=None):
		"""
		:param tags: Tags to use to translate.
		:type tags: [:class:`net.tag.Tag`]
		:param submessages: Messages to fill the remaining data space.
		:type submessages: {int : :class:`~net.message.Message`}
		"""
		self.tags = [] if tags is None else tags
		self.submessages = {} if submessages is None else submessages

	def encode(self, data, crypto):
		"""
		:param data: Data to encode.
		:type data: []
		:param crypto: Crypto handlers for this contact.
		:type crypto: :class:`crypto.CryptoHandlers`
		"""
		ret_data = b''
		if len(self.tags) > 0:
			for tag in tags:
				ret_data += tag.to_encoded(data[tag.name])
		if len(self.submessages) > 0:
			# Encode the msg type.
			mtype = data[TYPETAG]
			ret_data += struct.pack(TYPE_SYMBOL, mtype)
			ret_data += self.submessages[mtype].encode(data[PAYLOAD], crypto)
		return ret_data

	def decode(self, data, crypto):
		"""
		:param data: Data to decode.
		:type data: bytes
		:param crypto: Crypto handlers for this contact.
		:type crypto: :class:`crypto.CryptoHandlers`
		"""
		ret_data = {}
		offset = 0
		if len(self.tags) > 0:
			size_value_size = struct.calcsize(SIZE_SYMBOL)
			for tag in self.tags:
				size = struct.unpack(ENDIAN+SIZE_SYMBOL, data[offset:offset + size_value_size])
				offset += size_value_size
				ret_data[tag.name] = (x.to_value(data[offset:offset + size]))
				offset += size
		if len(self.submessages) > 0:
			# Figure out what type of packet this is.
			pkt_type = struct.unpack(ENDIAN + TYPE_SYMBOL,
					data[offset:offset + stuct.calcsize(TYPE_SYMBOL]))
			offset += struct.calcsize(TYPE_SYMBOL)
			ret_data[TYPETAG] = pkt_type
			ret_data[PAYLOAD] = self.submessages[pkt_type].decode(data[offset:], crypto)

class CarrierMessage(Message):
	"""
	This is a special case messsage, as it deals with protocol headers.
	Everything must be based off of this, as it is the root.
	"""

	def encode(self, data, crypto):
		dtype = data[TYPETAG]
		ret_data = MAGIC_HEADER
		ret_data += struct.pack(VERSION_SYMBOL, PROTO_VERSION)
		ret_data += struct.pack(TYPE_SYMBOL, dtype)
		ret_data += self.submessages[dtype].encode(data, crypto)
		return ret_data

	def decode(self, data, crypto):
		offset = 0
		# Check for magic string.
		if data[:len(MAGIC_HEADER)] != MAGIC_HEADER:
			raise ProtocolError("Magic string does not match")
		offset += len(MAGIC_HEADER)
		# Check for version number.
		if struct.unpack(ENDIAN + VERSION_SYMBOL,
				data[offset:offset + stuct.calcsize(VERSION_SYMBOL])\
				!= PROTO_VERSION:
			raise ProtocolError("Protocol is from a different version")
		offset += struct.calcsize(VERSION_SYMBOL)
		# Figure out what type of packet this is.
		pkt_type = struct.unpack(ENDIAN + TYPE_SYMBOL,
				data[offset:offset + stuct.calcsize(TYPE_SYMBOL]))
		offset += struct.calcsize(TYPE_SYMBOL)
		# Get data out of it.
		r_dict = self.submessages[pkt_type].decode(data[offset:], crypto)
		r_dict[TYPETAG] = pkt_type
		return r_dict


class Encrypted(Message):
	def __init__(self, suite, tags=[], submessages=None):
		pkt_id_tag = Tag(PKTID, ID_SYMBOL)
		super().__init__([pkt_id_tag] + tags, submessages)
		self.suite = suite

	def encode(self, data, crypto):
		payload = super().encode(data)
		return crypto[self.suite].encrypt(payload)

	def decode(self, data, crypto):
		payload = crypto[self.suite].decrypt(data)
		return super().decode(payload, crypto)


PROTO = CarrierMessage(
	submessages={
		# DH select g
		1 : Message(tags=[Tag('dh_g', 'struct')]),
		# DH pass mod
		2 : Message(tags=[Tag('dh_p', 'struct')]),
		# DH encrypted messages.
		# All encrypted messages have a pkt_id innately.
		3 : Encrypted('diffie-hellman', submessages={
			# Ping
			1 : Message(),
			# Pong
			2 : Message(tags=[Tag('pong_id', ID_SYMBOL)]),
			# DHT Search
			3 : Message(tags=[HashTag()]),
			# DHT Response
			4 : Message(tags=[HashTag(), ListTag('nodes', NodeTag())])
			}),
		4 : Encrypted('aes', submessages={
			1 : Message()
			}
		}
	)


