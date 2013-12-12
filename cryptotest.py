#!/usr/bin/python3
import crypto

ifile = input("filename: ")

with open(ifile, 'rb') as f:
	key, iv = crypto.get_aes_key()
	buf = f.read()

	print("key:", key)
	print("iv:", iv)
	print("len:", len(buf))

	data = crypto.encrypt_chunk(key, iv, buf)

	print("decrypted:", crypto.decrypt_chunk(key, data[0], data[1], len(buf)))
