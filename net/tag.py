import struct

from common import Hash, Address
from .common import ENDIAN, SIZE_SYMBOL


class Tag():
    """
    Construct to transform a data value to encoded data and back.
    Stores one packed value of a given type.

    .. TODO: Maybe reverse this with BytesTag as the base class
    """

    def __init__(self, name, tag_struct):
        self.name = name
        self.tag_struct = ENDIAN + tag_struct
        self._value = None
        self._header_size = struct.calcsize(SIZE_SYMBOL)

    @property
    def encoded(self):
        d = self._encoded
        return struct.pack(SIZE_SYMBOL, len(d)) + d

    @property
    def _encoded(self):
        return struct.pack(self.tag_struct, self._value)

    @encoded.setter
    def encoded(self, value):
        # Grab the first value.
        # Since this is a simple setter, there should only ever be one.
        self._value = struct.unpack(self.tag_struct, value)[0]

    def to_value(self, encoded):
        self.encoded = encoded
        return self.value

    def to_encoded(self, value):
        self.value = value
        return self.encoded

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class BoolTag(Tag):
    """
    Tag to encapsulate a single bool.
    This is quite inefficient, as it takes 1 byte for the bool
    as well as 2 bytes for the size before it
    """

    def __init__(self, name):
        super().__init__(name, '?')


class AddressTag(Tag):
    """
    Tag that encapsulates a :class:`common.Address` object.
    Serializes the ip address and the port.
    """

    def __init__(self):
        super().__init__('address', '4BH')

    @property
    def _encoded(self):
        return struct.pack(self.tag_struct,
                           *([int(x) for x
                              in self._value.ip.split('.')] +
                             [self._value.port]))

    @Tag.encoded.setter
    def encoded(self, value):
        raw = struct.unpack(self.tag_struct, value)
        self._value = Address('.'.join(str(x) for x in raw[:4]), raw[4])


class NodeTag(Tag):
    """
    Represents a Node.
    Encapsulates an :class:`common.Address` and a :class:`common.Hash`.
    """

    def __init__(self, translator):
        # TODO: Fix this to add the hash in
        super().__init__('contact', '4BH')
        self.translator = translator

    @property
    def _encoded(self):
        return self._value.hash.value + struct.pack(
            self.tag_struct,
           *([int(x) for x
              in self._value.address.ip.split('.')] +
             [self._value.address.port]))

    @Tag.encoded.setter
    def encoded(self, value):
        end_size = struct.calcsize(self.tag_struct)
        h = value[:-end_size]
        raw = struct.unpack(self.tag_struct, value[-end_size:])
        contact = self.translator(
            Address('.'.join(str(x) for x in raw[:4]), raw[4]))
        try:
            contact.set_hash(Hash(h))
        # Happens if the hash has already been set.
        except ValueError:
            pass
        self._value = contact


class ListTag(Tag):
    """
    Tag that encapsulates a list of single tag.
    """

    def __init__(self, name, inner_tag):
        """
        :param inner_tag: The tag inside the array.
        :type inner_tag: :class:`~net.tag.Tag` base
        """
        super().__init__(name, '')
        self.inner_tag = inner_tag

    @property
    def _encoded(self):
        return b''.join(self.inner_tag.to_encoded(x) for x in self._value)

    @Tag.encoded.setter
    def encoded(self, in_bytes):
        a = []
        x = 0
        while x < len(in_bytes):
            # Grab the size.
            sz = struct.unpack(SIZE_SYMBOL,
                               in_bytes[x: x + self._header_size])[0]
            x += self._header_size
            a.append(self.inner_tag.to_value(in_bytes[x: x + sz]))
            x += sz
        self._value = a


class BytesTag(Tag):
    """
    Base tag for any bytes-level values.

    Used for hashes, strings and varints
    """

    def __init__(self, name):
        super().__init__(name, '')

    @property
    def _encoded(self):
        return self._value

    @Tag.encoded.setter
    def encoded(self, value):
        self._value = value


class HashTag(BytesTag):
    """
    Tag that encapsulates a :class:`common.Hash` object.
    """

    def __init__(self):
        super().__init__('hash')

    @property
    def _encoded(self):
        return self._value.value

    @Tag.encoded.setter
    def encoded(self, value):
        self._value = Hash(value)


class StringTag(BytesTag):
    """
    Tag that encapsulates a variable-length string.
    """

    @property
    def _encoded(self):
        return bytes(self._value, 'utf-8')

    @Tag.encoded.setter
    def encoded(self, value):
        self._value = value.decode('utf-8')


class VarintTag(BytesTag):
    """
    Tag that encapsulates a variable-length integer.
    Used for DH handshakes.

    Will pad with null bits to reach a byte boundary.
    """

    @property
    def _encoded(self):
        length = round((self._value.bit_length() / 8) + 0.5)
        return self._value.to_bytes(length, 'big')

    @Tag.encoded.setter
    def encoded(self, value):
        self._value = int.from_bytes(value, 'big')
