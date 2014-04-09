class CryptoHandlers(dict):
	def __init__(self, dh, pki, aes):
		self['diffie-hellman'] = dh
		self['pki'] = pki
		self['aes'] = aes

from crypto.aesgcm import AESCrypto as AESCrypto
from crypto.diffiehellman import DHCrypto as DHCrypto
