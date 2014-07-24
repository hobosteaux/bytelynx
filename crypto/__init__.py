import hashlib

from crypto.exceptions import CryptoError
from crypto.aesgcm import AESCrypto as AESCrypto
from crypto.diffiehellman import DHCrypto as DHCrypto
from crypto.rsa import RSACrypto as RSACrypto

#: All of the base transport modes and their encryption layer
Modules = {'bytelynx': DHCrypto,
           'aes-dht': AESCrypto,
           'rsa-ex': RSACrypto,
           'aes-net': AESCrypto}

#: Equating key bit size to sha hashes
SHAModes = {160: hashlib.sha1, 224: hashlib.sha224,
            256: hashlib.sha256, 384: hashlib.sha384,
            512: hashlib.sha512}


def sha_hash(data, bits):
    """
    Hash data

    :param data: The data to hash.
    :type data: bytes
    :param bits: The amount of bits to use.
    :type bits: int.
    """
    try:
        sha_func = SHAModes[bits]()
    except KeyError:
        raise CryptoError("Hash bitsize incorrect")
    sha_func.update(data)
    return sha_func.digest()
