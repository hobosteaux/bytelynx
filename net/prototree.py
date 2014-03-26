from .tag import Tag, HashTag, AddressTag, NodeTag
from .common import *
from common.exceptions import *

class CryptoHandlers():
	def __init__(self, dh, pki, symmetric):
		self.dh = dh
		self.pki = pki
		self.symmetric = symmetric

class BaseMessage():

	def __init__(self, tags=None, submessages=None):
		"""
		:param tags: Tags to use to translate.
		:type tags: [:class:`net.tag.Tag`]
		:param submessages: Messages to fill the remaining data space.
		:type submessages: {int : :class:`~net.message.BaseMessage`}
		"""
		self.tags = [] if tags is None else tags
		self.submessages = {} if submessages is None else submessages

	def encode(self, data, crypto):
		"""
		:param data: Data to encode.
		:type data: bytes
		:param crypto: Crypto handlers for this contact.
		:type crypto: :class:`crypto.CryptoHandlers`
		"""
		raise AbstractException()

	def decode(self, data, crypto):
		raise AbstractException()
	

class CarrierMessage(BaseMessage):
	"""
	This is a special case messsage, as it deals with protocol headers.
	Everything must be based off of this, as it is the root.
	"""

	def encode(self, data, crypto):
		pass

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
		return {pkt_type : self.submessages[pkt_type].decode(data[offset:], crypto)}

class DHEncapsulated(BaseMessage):

class AESEncapsulated(BaseMessage):

class Message(BaseMessage):


PROTO = CarrierMessage(
	submessages={
		# DH select g
		1 : Message(tags=[g]),
		# DH pass mod
		2 : Message(tags=[]),
		3 : DHEncapsulated(submessages={
			1 : ping
			2 : 
			

			}),
		4 : AESEncapuslated()
		}
	)


