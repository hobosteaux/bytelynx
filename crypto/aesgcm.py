from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)

from .cryptobase import CryptoModule
from .exceptions import KeySizeError

# TODO: Get these items from config

#: 96 bit IV
IV_SIZE = 12
#: 256 bit AES
KEY_SIZE = 32
#: 128 bit tag
TAG_SIZE = 16


class AESCrypto(CryptoModule):
    """
    A simple module to provide AES-GCM.
    Backended by the cryptography library.
    """

    def __init__(self):
        super().__init__()
        self.state = 'uninitialized'

    def set_key(self, key=None):
        """
        Sets this instance's secret.
        If none is provided, one will be generated.

        :param key: A bytes object secret.
        :type key: bytes
        """
        self.iv = self.random_bytes(IV_SIZE)
        if key is None:
            self.key = self.random_bytes(KEY_SIZE)
        else:
            if len(key) != KEY_SIZE:
                raise KeySizeError()
            self.key = key
        self.state = 'initialized'
        self.on_finalization()

    def encrypt(self, data):
        """
        .. warning::

            This should really have thread controls in it.
            If two threads are simutaneously encrypting,
            there is a small chance that the IVs would be the same.
            This would be **extremely** bad.

        :param data: The data to encrypt
        :type data: bytes
        :returns: IV + payload + TAG
        :rtype: bytes
        """
        # Grab && increment iv
        iv = self.iv
        self.iv = (int.from_bytes(iv, 'big') + 1).to_bytes(len(iv), 'big')

        # TODO: Do we have to make the encryptor every time?
        # Make the encryptor
        encryptor = Cipher(algorithms.AES(self.key),
                           modes.GCM(iv),
                           backend=default_backend()
                           ).encryptor()

        # Encrypt the data
        encryptor.authenticate_additional_data(iv)
        ciphertext = encryptor.update(data) + encryptor.finalize()

        return iv + ciphertext + encryptor.tag

    def decrypt(self, data):
        """
        Decrypts an AESGCM payload.

        Relies on constants:
            :attr:`~crypto.aesgcm.IV_SIZE`

            :attr:`~crypto.aesgcm.TAG_SIZE`

        :param data: The raw data to decrypt
        :type data: bytes
        :returns: Decrypted data
        :rtype: bytes
        """
        iv = data[:IV_SIZE]
        payload = data[IV_SIZE: -TAG_SIZE]
        tag = data[-TAG_SIZE:]

        decryptor = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()

        decryptor.authenticate_additional_data(iv)

        return decryptor.update(payload) + decryptor.finalize()
