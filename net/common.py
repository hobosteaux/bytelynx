#: First bytes to identify bytelynx traffic.
MAGIC_HEADER = b'btlx'
#: Current protocol version. Just a placeholder for later.
PROTO_VERSION = 1


# Struct constants.
#: The symbol for struct.[un]pack's endianess
ENDIAN = '>'
#: The tag preceeding every value for the size of it in bytes
SIZE_SYMBOL = ENDIAN + 'H'
#: The protocol version tag
VERSION_SYMBOL = ENDIAN + 'B'
#: The type of message
TYPE_SYMBOL = ENDIAN + 'B'
#: The pkt_id
ID_SYMBOL = ENDIAN + 'Q'
