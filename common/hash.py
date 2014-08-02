import base64


def hash_from_pub(pubkey, bitsize):
    """
    Constucts a hash from a public key.

    :param pubkey: The public key to hash.
    :type pubkey: bytes
    :param bitsize: The amount of bits to hash with.
    :type bitsize: int.
    """
    # TODO: This should really be pushed into the crypto layer.
    # It would fit well as a property on pub / priv key objs
    # NastyImport
    from crypto import sha_hash
    return Hash(sha_hash(pubkey, bitsize))


class Hash():
    """
    Container for a hash.
    Lots of overloaded operators.

    .. attribute:: value

        The :class:`bytes` object that is the raw hash.
    """

    def __init__(self, value):
        self.value = value

    def __len__(self, other):
        return len(self.value)

    def __str__(self):
        return '%s:%s' % ('h', self.value)

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            return False

    def __ne__(self, other):
        return self.value != other.value

    def abs_diff(self, other):
        """
        :returns: the absolute difference between two hashes.
        """
        if (other > self):
            return other - self
        return self - other

    def __sub__(self, other):
        if (len(self.value) != len(other.value)):
            raise ValueError("Hashes are not of the same length.")
        i = (int.from_bytes(self.value, 'little') -
             int.from_bytes(other.value, 'little'))
        return Hash(i.to_bytes(len(self.value), 'little'))

    def __xor__(self, other):
        if (len(self.value) != len(other.value)):
            raise ValueError("Hashes are not of the same length.")
        i = (int.from_bytes(self.value, 'little') ^
             int.from_bytes(other.value, 'little'))
        return Hash(i.to_bytes(len(self.value), 'little'))

    def significant_bit(self):
        """
        :returns: The most significat bit place.
        """
        for i in range(0, len(self.value)):
            b = 128
            for j in range(0, 8):
                if (self.value[i] & b != 0):
                    return ((len(self.value) * 8) - (i * 8) - j)
                b //= 2
        return 0

    @property
    def bit_string(self):
        """
        :returns: String of 0's and 1's.
        """
        str_data = ''
        for i in range(0, len(self.value)):
            b = 128
            for j in range(0, 8):
                if (self.value[i] & b != 0):
                    str_data += '1'
                else:
                    str_data += '0'
                b //= 2
        return str_data

    @property
    def base64(self):
        """
        :returns: B64 encoded string.
        """
        return str(base64.b64encode(self.value), 'UTF-8')
