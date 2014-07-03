import os

from common.exceptions import AbstractError


class CryptoModule():
    """
    Interface for all crypto modultes to follow.
    """
    def __init__(self):
        self.state = 'created'

    def encrypt(self, data):
        """
        Takes raw bytes and returns encrypted raw bytes.
        """
        raise AbstractError()

    def decrypt(self, data):
        """
        Takes encrypted raw bytes and returns raw bytes.
        """
        raise AbstractError()

    def random_int(self, byte_length):
        """
        :returns: An int of the given byte length.
        """
        return int.from_bytes(os.urandom(byte_length), 'little')

    def random_bytes(self, byte_length):
        """
        :returns: A bytes object of byte_length.
        """
        return os.urandom(byte_length)
