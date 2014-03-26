


from common.exceptions import *


class CryptoModules():
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
