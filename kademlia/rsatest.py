#!/usr/bin/python3
from rsautils import *
import os
from os.path import join

dir = '/tmp/blynx'
c1 = 'client1'
c2 = 'client2'

if (not os.path.exists(dir)):
	os.makedirs(dir)
	gen_export_keypair(join(dir, c1),join(dir, c1),4096) 
	gen_export_keypair(join(dir, c2),join(dir, c2),4096) 

c1store = RSAStore(
	*import_keypair(join(dir, c1), join(dir, c1)))

c2store = RSAStore(
	*import_keypair(join(dir, c2), join(dir, c2)))

enc = c1store.encrypt(b"hello", c2store.pubkey)
print(c2store.decrypt(enc))
