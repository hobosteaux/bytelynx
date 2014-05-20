import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)

from .cryptobase import CryptoModule
from common import exceptions

#: 96 bit IV
IV_SIZE = 12
#: 256 bit AES
KEY_SIZE = 32
#: 128 bit tag
TAG_SIZE = 16

class AESCrypto(CryptoModule):
	"""
	A simple module to provide AES-GCM.
	Backended by the cryptography library.
	"""

	def __init__(self):
		self.state = 'uninitialized'

	def set_key(self, key=None)
		"""
		Sets this instance's secret.
		If none is provided, one will be generated.

		:param key: A bytes object secret.
		:type key: bytes
		"""
		self.iv = self.random_bytes(IV_SIZE)
		if key is None:
			self.key = self.random_bytes(KEY_SIZE)
		else:
			if len(key) != KEY_SIZE:
				raise exceptions.KeySizeError()
			self.key = key
		self.state = 'initialized'

	def encrypt(self, data):
		"""
		.. warning::

			This should really have thread controls in it.
			If two threads are simutaneously encrypting,
			there is a small chance that the IVs would be the same.
			This would be **extremely** bad.

		Return format: :attr:`IV_SIZE` + payload + :attr:`TAG_SIZE`
		"""
		# Grab && increment iv
		iv = self.iv
		self.iv = (int.from_bytes(iv, 'big') + 1).to_bytes(len(iv), 'big')

		# Make the encryptor
		encryptor = Cipher(
		algorithms.AES(self.key),
			modes.GCM(iv),
			backend=default_backend()
		).encryptor()

		# Encrypt the data
		encryptor.authenticate_additional_data(iv)
		ciphertext = encryptor.update(data) + encryptor.finalize()

		return iv + ciphertext + encryptor.tag
		
	def decrypt(self, data):
		iv = data[:IV_SIZE]
		payload = data[IV_SIZE: -TAG_SIZE]
		tag = data[-TAG_SIZE:]

		decryptor = Cipher(
			algorithms.AES(self.key),
			modes.GCM(iv, tag),
			backend=default_backend()
		).decryptor()

		decryptor.authenticate_additional_data(iv)

		return decryptor.update(payload) + decryptor.finalize()
