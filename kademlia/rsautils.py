from OpenSSL import crypto, SSL
from socket import gethostname
from time import gmtime, mktime
from os.path import exists, join

CERT_EXT = ".crt"
KEY_EXT = ".key"

def create_self_signed_cert(cert_dir, name):
	"""
	If datacard.crt and datacard.key don't exist in cert_dir, create a new
	self-signed cert and keypair and write them into that directory.
	"""
	certFile = name + CERT_EXT
	keyFile = name + KEY_EXT

	if not exists(join(cert_dir, certFile)) \
		or not exists(join(cert_dir, keyFile)):
		print("Making Certs")

		# create a key pair
		k = crypto.PKey()
		k.generate_key(crypto.TYPE_RSA, 4096)

		# create a self-signed cert
		cert = crypto.X509()
		cert.get_subject().O = "ByteLynx Client"
		cert.get_subject().CN = gethostname()
		cert.set_serial_number(1000)
		cert.gmtime_adj_notBefore(0)
		cert.gmtime_adj_notAfter(10*365*24*60*60)
		cert.set_issuer(cert.get_subject())
		cert.set_pubkey(k)
		cert.sign(k, 'sha1')

		print("Made Certs")
		print(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

	open(join(cert_dir, certFile), "wt").write(
		str(crypto.dump_certificate(crypto.FILETYPE_PEM, cert), 'UTF-8'))
	open(join(cert_dir, name + keyFile), "wt").write(
		str(crypto.dump_privatekey(crypto.FILETYPE_PEM, k), 'UTF-8'))
