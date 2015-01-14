import os

from common.exceptions import AbstractError
from common import Event

class CryptoModule():
    """
    Interface for all crypto modultes to follow.
    """
    def __init__(self):
        self.state = 'created'
        self.on_finalization = Event()

    def encrypt(self, data):
        """
        Interface to encrypt raw data

        :param data: Data to encrypt
        :type data: bytes
        :returns: Encrypted data
        :rtype: bytes
        """
        raise AbstractError()

    def decrypt(self, data):
        """
        Interface to decrypt raw data

        :param data: Data to decrypt
        :type data: bytes
        :returns: Decrypted data
        :rtype: bytes
        """
        raise AbstractError()

    def random_int(self, byte_length):
        """
        Gets a random integer

        .. warning:: Uses os.urandom

        :param byte_length: Bytes of randomness to use
        :type byte_length: int.
        :returns: A value of the given byte length.
        :rtype: int.
        """
        # TODO: Not use os.urandom?
        return int.from_bytes(os.urandom(byte_length), 'little')

    def random_bytes(self, byte_length):
        """
        Gets random bytes

        .. warning:: Uses os.urandom

        :param byte_length: Bytes of randomness to use
        :type byte_length: int.
        :returns: Random bytes
        :rtype: bytes
        """
        # TODO: Not use os.urandom?
        return os.urandom(byte_length)
