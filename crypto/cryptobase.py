import os

from common.exceptions import *

class CryptoModule():
	"""
	Interface for all crypto modultes to follow.
	"""

	def encrypt(self, data):
		"""
		Takes raw bytes and returns encrypted raw bytes.
		"""
		raise AbstractException()

	def decrypt(self, data):
		"""
		Takes encrypted raw bytes and returns raw bytes.
		"""
		raise AbstractException

	def random_int(self, byte_length):
		"""
		:returns: An int of the given byte length.
		"""
		return os.urandom(length)

	def random_bytes(self, byte_length):
		"""
		:returns: A bytes object of byte_length.
		"""
		return int.from_bytes(os.urandom(length), 'small')
