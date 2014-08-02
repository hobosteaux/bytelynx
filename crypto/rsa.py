#!/usr/bin/python3

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_traditional_openssl_private_key

from .cryptobase import CryptoModule
from .exceptions import UninitializedError


def gen_private(keysize=4096):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=keysize,
        backend=default_backend())
    return private_key


class PrivateKey():

    def __init__(self, key):
        try:
            # Keys are based off of an ABC, so classes change
            if key.__getattribute__('decrypt'):
                self.value = key
        except AttributeError:
            if type(key) is str:
                self.value = self.load(key)
            else:
                raise TypeError('Key is not a valid object')

    def load(self, blob):
        return load_pem_traditional_openssl_private_key(
            blob, password=None,
            backend=default_backend())

    def save(self):
        """
        Serializes the key into OpenSSL format
        """
        # TODO: This method
        raise NotImplementedError()


class PublicKey():

    def __init__(self, key):
        try:
            if key.__getattribute__('encrypt'):
                self.value = key
        except AttributeError:
            if type(key) is str:
                self.value = self.load(key)
            else:
                raise TypeError('Key is not a valid object')

    def load(self, blob):
        # TODO: This method
        raise NotImplementedError()

    def save(self):
        """
        Serializes the key into OpenSSL format
        """
        # TODO: This method
        raise NotImplementedError()


class KeyPair():

    def __init__(self, *, private=None, public=None):
        """
        Both private and public can be one of the following
        ::

            :class:`str`
            :class:`~crypto.rsa.PrivateKey` or :class:`~crypto.rsa.PublicKey`
            The appropriate hazmat pub/priv key class
        """
        if private is None and public is None:
            self._private = gen_private()
        else:
            if type(private) is PrivateKey:
                self._private = private
            else:
                self._private = PrivateKey(private)
            if type(public) is PublicKey:
                self._public = public
            else:
                self._public = PublicKey(public)
        # Set public to private's public
        if public is None:
            self._public = self._private.public_key()

    @property
    def private(self):
        if self._private is None:
            raise UninitializedError()
        return self._private

    @property
    def public(self):
        if self._public is None:
            raise UninitializedError()
        return self._public


class RSACrypto(CryptoModule):

    def seed(self, own_private, remote_public):
        self.keypair = KeyPair(own_private, remote_public)

    def encrypt(self, data):
        return self.public_key.encrypt(
            data, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )

    def decrypt(self, data):
        return self.private_key.decrypt(
            data, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )


def test():
    a_priv = gen_private(keysize=512)
    b_priv = gen_private(keysize=512)
    a = RSACrypto()
    b = RSACrypto()
    a.seed(a_priv, b_priv.public_key())
    b.seed(b_priv, a_priv.public_key())

    c = a.encrypt(b'hello world')
    print(c)
    print(b.decrypt(c))
