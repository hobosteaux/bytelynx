MAGIC_HEADER = b'btlx'
"""First bytes to identify bytelynx traffic."""
PROTO_VERSION = 1
"""Current protocol version. Just a placeholder for later."""


# Struct constants.
ENDIAN = '>'
"""The symbol for struct.[un]pack's endianess""" 
SIZE_SYMBOL = 'H'
"""The tag preceeding every value for the size of it in bytes"""
VERSION_SYMBOL = 'B'
"""The protocol version tag"""
TYPE_SYMBOL = 'B'
"""The type of message"""


class ProtocolError(Exception)
"""Exception thrown if decoding goes awry."""
