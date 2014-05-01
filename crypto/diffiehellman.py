#!/usr/bin/python3
from .cryptobase import CryptoModule

class DHCrypto(CryptoModule):
	"""
	Crypto module for Diffie-Hellman handshakes.
	This module is built with the assumption that p (the modulus)
	is a pre-shared secret for the network.
	This serves to act as a password for the network to keep other
	non-authorized entities out.

	.. attribute:: p
		The modulus to use.
	.. attribute:: g
		The generator to use.
	.. attribute:: a
		This node's secret.
	.. attribute:: key
		The full key for a connection.
	"""

	def __init__(self, p):
		self.p = p
		self.private = self.random_int(512)

	def _check_g(self, g):
		"""
		Checks to see if a g is a good parameter for p.
		"""
		return True

	def generate_g(self):
		g = 3
		self.g = g
		return g

	def set_g(self, g):
		if self._check_g(g):
			self.g = g

	def get_A(self):
		"""
		Returns (g^a) % p
		"""
		return pow(self.g, self.private, self.p)

	def mix_B(self, b):
		"""
		Adds the remote mixture to the key.
		"""
		self.key = pow(b, self.private, self.p)



def test():
	alice = DHCrypto(23)
	bob = DHCrypto(23)

	bob.set_g(alice.generate_g())
	bob.mix_B(alice.get_A())
	alice.mix_B(bob.get_A())
	print("Alice: %s" % alice.key)
	print("Bob: %s" % bob.key)
	
if __name__ == '__main__':
	test()
