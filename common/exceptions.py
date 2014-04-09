class AbstractException(Exception):
	"""Thrown when a base class has a function that mut be overridden"""
	def __init__(self, message=None):
		if message is None:
			message = "This function must be overridden by the inheriting class"
		super().__init__(message)

class ProtocolError(Exception):
	"""Exception thrown if decoding goes awry."""
	pass

class CryptoError(Exception):
	"""Exception thrown if something is wrong with crypto."""
	pass

class KeySizeError(CryptoError):
	"""Exception thrown if the key is an incorrect size."""
