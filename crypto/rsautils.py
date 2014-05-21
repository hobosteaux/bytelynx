from OpenSSL import crypto, SSL
from socket import gethostname
from time import gmtime, mktime
from os.path import exists, join
from Crypto.PublicKey import RSA, DSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.asn1 import DerSequence
from binascii import a2b_base64, b2a_base64


CERT_EXT = ".crt"
KEY_EXT = ".key"

class RSAStore():
    pubkey = None
    _pubkey = None
    _privkey = None

    def __init__(self, pubkey, privkey):
        self.pubkey = pubkey
        self._pubkey = PKCS1_OAEP.new(RSA.importKey(pubkey))
        self._privkey = PKCS1_OAEP.new(RSA.importKey(privkey))

    def encrypt(self, plaintext, pubkey):
        rsakey = PKCS1_OAEP.new(RSA.importKey(pubkey))
        return rsakey.encrypt(plaintext)

    def decrypt(self, ciphertext):
        return self._privkey.decrypt(ciphertext)

def generate_keypair(bits=4096):
    key = RSA.generate(bits)
    return (key.publickey(), key)

def gen_export_keypair(publoc, privloc, bits=4096):
    pub, priv = generate_keypair(bits)
    open(join(publoc + CERT_EXT), "wt").write(
        str(b2a_base64(pub.exportKey('DER')), 'UTF-8'))
    open(join(privloc + KEY_EXT), "wt").write(
        str(b2a_base64(priv.exportKey('DER')), 'UTF-8'))

def import_keypair(publoc, privloc):
    pub = a2b_base64(bytes(open(join(publoc + CERT_EXT)).read(), 'UTF-8'))
    priv = a2b_base64(bytes(open(join(privloc + KEY_EXT)).read(), 'UTF-8'))
    return (pub, priv)

def pemtoder(pem):
    """This is needed for the PyOpenSSL cert gen"""
    # Convert from PEM to DER
    print(pem)
    lines = pem.replace(" ",'').split()
    print(lines)
    der = a2b_base64(bytes(''.join(lines[1:-1]), 'UTF-8'))

    # Extract subjectPublicKeyInfo field from X.509 certificate (see RFC3280)
    cert = DerSequence()
    cert.decode(der)
    tbsCertificate = DerSequence()
    tbsCertificate.decode(cert[0])
    #subjectPublicKeyInfo = tbsCertificate[6]

    return RSA.importKey(tbsCertificate)

def pydertopem(der):
    """This is needed for the PyOpenSSL cert gen"""
    return der.exportKey('PEM')
    
def create_self_signed_cert(cert_dir, name):
    """
    If datacard.crt and datacard.key don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    """
    # NOTE: This is broken ATM and does not work.
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

    open(join(cert_dir, certFile), "wt").write(
        str(crypto.dump_certificate(crypto.FILETYPE_PEM, cert), 'UTF-8'))
    open(join(cert_dir, keyFile), "wt").write(
        str(crypto.dump_privatekey(crypto.FILETYPE_PEM, k), 'UTF-8'))
