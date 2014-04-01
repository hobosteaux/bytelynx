MAGIC_HEADER = b'btlx'
"""First bytes to identify bytelynx traffic."""
PROTO_VERSION = 1
"""Current protocol version. Just a placeholder for later."""


# Struct constants.
ENDIAN = '>'
"""The symbol for struct.[un]pack's endianess""" 
SIZE_SYMBOL = ENDIAN + 'H'
"""The tag preceeding every value for the size of it in bytes"""
VERSION_SYMBOL = ENDIAN + 'B'
"""The protocol version tag"""
TYPE_SYMBOL = ENDIAN + 'B'
"""The type of message"""
ID_SYMBOL = ENDIAN + 'I'
"""The pkt_id size"""
#TODO: find correct symbol

class ProtocolError(Exception)
"""Exception thrown if decoding goes awry."""
