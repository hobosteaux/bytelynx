import hashlib

from crypto.aesgcm import AESCrypto as AESCrypto
from crypto.diffiehellman import DHCrypto as DHCrypto

#: All of the base transmore modes and their encryption layer
Modules = {'bytelynx': DHCrypto,
           'aes-dht': AESCrypto,
           'aes-net': AESCrypto}

#: Equating key bit size to sha hashes
SHAModes = {160: hashlib.sha1, 224: hashlib.sha224,
            256: hashlib.sha256, 384: hashlib.sha384,
            512: hashlib.sha512}
