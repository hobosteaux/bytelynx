from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64decode
from Crypto.PublicKey import RSA
from Crypto import Random

def generate_RSA(bits=2048):
	'''
	Generate an RSA keypair with an exponent of 65537 in PEM format
	param: bits The key length in bits
	Return private key and public key
	'''
	new_key = RSA.generate(bits, e=65537)
	public_key = new_key.publickey().exportKey("PEM")
	private_key = new_key.exportKey("PEM")
	return private_key, public_key

def encrypt_RSA(public_key_loc, message):
	'''
	param: public_key_loc Path to public key
	param: message String to be encrypted
	return base64 encoded encrypted string
	'''
	key = open(public_key_loc, "r").read()
	rsakey = RSA.importKey(key)
	rsakey = PKCS1_OAEP.new(rsakey)
	encrypted = rsakey.encrypt(message)
	return encrypted.encode('base64')


def decrypt_RSA(private_key_loc, package):
	'''
	param: public_key_loc Path to your private key
	param: package String to be decrypted
	return decrypted string
	'''
	key = open(private_key_loc, "r").read()
	rsakey = RSA.importKey(key)
	rsakey = PKCS1_OAEP.new(rsakey)
	decrypted = rsakey.decrypt(b64decode(package))
	return decrypted

import os, random, struct
from Crypto.Cipher import AES

def encrypt_chunk(key, iv, inData):
	""" Encrypts a file using AES (CBC mode) with the
	given key.

	key:
	The encryption key - a string that must be
	either 16, 24 or 32 bytes long. Longer keys
	are more secure.
	"""
	encryptor = AES.new(key, AES.MODE_CBC, iv)

	data = b''
	for i in range(0, (int)(len(inData) / 16) + 1):
		chunk = inData[i*16 : min((i+1) * 16, len(inData) - 1)]
		if len(chunk) == 0:
			break
		#elif len(chunk) % 16 != 0:
		#	chunk += bytes(16 - len(chunk) % 16)

		data += encryptor.encrypt(chunk)
		
	return iv, data


def decrypt_chunk(key, iv, inData, length):
	""" Decrypts a file using AES (CBC mode) with the
	given key. Parameters are similar to encrypt_file,
	with one difference: out_filename, if not supplied
	will be in_filename without its last extension
	(i.e. if in_filename is 'aaa.zip.enc' then
	out_filename will be 'aaa.zip')
	"""

	data = b''
	decryptor = AES.new(key, AES.MODE_CBC, iv)

	#for i in range(0, (int)(len(inData) / 16)):
	#	chunk = inData[i*16 : (i+1) * 16]
	data += decryptor.decrypt(data)
	return data[0 : length - 1]

def get_aes_key():
	return (Random.get_random_bytes(32), Random.get_random_bytes(16))
