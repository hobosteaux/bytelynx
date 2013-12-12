#!/usr/bin/python3
from rsautils import create_self_signed_cert
import sys
import os
from os.path import join
import ssl
from socket import socket, AF_INET, SOCK_DGRAM
from dtls import do_patch
do_patch()

CERTNAME = 'blynx'

def CheckCerts(path, name):
	if (not os.path.exists(path)):
		os.makedirs(path)
		create_self_signed_cert(path, name)


if __name__ == '__main__':
	certloc = sys.argv[1]
	#lport = sys.argv[1]
	server = sys.argv[2]
	print(sys.argv)

	# make cert
	CheckCerts(certloc, CERTNAME)

	# test dtls
	if (server == 'true'):
		sock = ssl.wrap_socket(socket(AF_INET, SOCK_DGRAM),
			cert_reqs=ssl.CERT_REQUIRED, do_handshake_on_connect=False,
			certfile = join(path, CERTNAME+'pem'),ciphers="ALL")
		sock.bind(('', 1234))
		sock.listen(0)
		while(True):
			data, address = sock.recvfrom(65536)
			print(data, address)

	else:
		sock = ssl.wrap_socket(socket(AF_INET, SOCK_DGRAM),\
			 cert_reqs=ssl.CERT_REQUIRED, do_handshake_on_connect=True, ciphers="ALL")
		sock.connect(('127.0.0.1', 1234))
