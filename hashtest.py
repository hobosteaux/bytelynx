#!/usr/bin/python3
import hashlib

ifile = input("filename: ")

SHA1Hash = hashlib.sha1()
with open(ifile, 'rb') as f:
	buf = f.read()
	SHA1Hash.update(buf)
	print(SHA1Hash.hexdigest())
