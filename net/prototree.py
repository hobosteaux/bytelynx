import struct

from net.tag import (Tag, HashTag, VarintTag,
                     ListTag, NodeTag, StringTag)
from net.common import (MAGIC_HEADER, PROTO_VERSION,
                        TYPE_SYMBOL, SIZE_SYMBOL,
                        VERSION_SYMBOL, ID_SYMBOL)
import net.tagconstants as Tags
from common.exceptions import ProtocolError
from common import Event


class Message():
    """
    The base message.
    This is the most generic type that is used for basic protocols.
    It also defines the interface for encoding and decoding.

    .. note::

        ALL leaf messages must be made out of this.

    .. attribute:: msg_name

        The msg_name for this message.
    .. attribute:: tags

        The tags that this is comprised of.
    .. attribute:: submessages

        Any submessages that are encapsulated.
    .. attribute:: mode

        The parent link type of this message.
    .. attribute:: parent

        The encapsulating parent for this message.
    .. attribute:: is_pongable

        Determines whether to send a pong out when a message
        of this type is received. Also enables using this
        message type for calculating ping and enables
        reliable transport (resends).
    .. attribute:: on_dht

        The event to fire if a dht message is received.
        This will always be fired, but not always be subscribed to.
        (contact)
    .. attribute:: on_data

        The event to fire when data has come in.
        Only applies to this message.
        (contact, dict data)
    """

    def __init__(self, *, msg_name='', mode='',
                 is_pongable=False, tags=None,
                 submessages=None, dht_func=None):
        """
        :param msg_name: The name for this message.
        :type msg_name: str.
        :param mode: The protobol mode for children of this message.
        :type mode: str.
        :param is_pongable: If this message is is_pongable.
        :type is_pongable: bool.
        :param tags: Tags to use to translate.
        :type tags: [:class:`net.tag.Tag`]
        :param submessages: Messages to fill the remaining data space.
        :type submessages: {int : :class:`~net.message.Message`}
        """
        # msg_name mode
        #   T       T   Fail - bad
        #   T       F   use msg name
        #   F       T   used mode name
        #   F       F   Fail - bad
        if (len(msg_name + mode) > 0) and\
                (len(msg_name == 0) or len(mode) == 0):
            self.msg_name = msg_name + mode
        else:
            raise ValueError("A msg_name or mode must be provided")
        self.is_pongable = is_pongable
        self.tags = [] if tags is None else tags
        self.submessages = {} if submessages is None else submessages
        # Init params for submessages
        self.set_child_attrs(mode)
        # Set all events
        self.on_dht = Event()
        if dht_func is not None:
            self.on_dht += dht_func
        self.on_data = Event()

    def set_mode(self, mode):
        """
        Sets the protocol mode for a message and all children.
        Stops at a child if it has a different defined mode
        Example modes: 'aes-dht', 'aes-net'

        :param mode: Mode to set
        :type mode: str.
        """
        if self.mode is '':
            self.mode = mode
            for message in self.submessages.values():
                message.set_mode(mode)

    def set_child_attrs(self, mode, index=-1, parent=None):
        """
        Sets the parent so that protocols can backtrack up.
        This is needed for encoding messages.

        :param parent: The parent message for this submessage.
        :type parent: :class:`~net.prototree.Message` or None
        """
        # Check if the attr 'mode' exists
        # If not, set it.
        try:
            self.__getattribute__('mode')
        except AttributeError:
            self.mode = mode
        self.parent = parent
        self.index = index
        # Set children
        for idx, message in self.submessages.items():
            message.set_child_attrs(mode, idx, self)

    def encode(self, crypto, dict_data, bytes_data=b''):
        """
        :param crypto: Crypto handlers for this contact.
        :type crypto: :class:`crypto.CryptoHandlers`
        :param dict_data: Data to encode.
        :type dict_data: {}
        :param bytes_data: Raw encoded data so far.
        :type bytes_data: bytes
        """
        # Encode the msg type
        # self.index should never == -1 (default)
        # UNLESS this is the top level proto wrapper
        data = struct.pack(TYPE_SYMBOL, self.index)
        # Encode all tags for this level
        if len(self.tags) > 0:
            for tag in self.tags:
                data += tag.to_encoded(data[tag.name])
        return self.parent.encode(crypto, dict_data, data + bytes_data)

    def decode(self, data, crypto):
        """
        :param data: Data to decode.
        :type data: bytes
        :param crypto: Crypto handlers for this contact.
        :type crypto: :class:`crypto.CryptoHandlers`
        :returns: msg_name, data
        """
        msg_name = self.msg_name
        ret_data = {}
        offset = 0
        if len(self.tags) > 0:
            size_value_size = struct.calcsize(SIZE_SYMBOL)
            for tag in self.tags:
                size = struct.unpack(SIZE_SYMBOL,
                                     data[offset:offset +
                                          size_value_size])[0]
                offset += size_value_size
                ret_data[tag.name] = (tag.to_value(data[offset:offset + size]))
                offset += size
        if len(self.submessages) > 0:
            # Figure out what type of packet this is.
            pkt_type = struct.unpack(TYPE_SYMBOL,
                                     data[offset:offset +
                                          struct.calcsize(TYPE_SYMBOL)])[0]
            offset += struct.calcsize(TYPE_SYMBOL)
            ret_data[Tags.TYPE] = pkt_type
            msg_name, ret_data[Tags.PAYLOAD] = self.submessages[pkt_type]\
                .decode(data[offset:], crypto)
        return msg_name, ret_data


class CarrierMessage(Message):
    """
    This is a special case messsage, as it deals with protocol headers.
    Everything must be wrapped in this, as it is the root.
    """

    def encode(self, crypto, dict_data, bytes_data):
        """
        :param crypto: Crypto handlers for this contact.
        :type crypto: :class:`crypto.CryptoHandlers`
        :param dict_data: Data to encode.
        :type dict_data: {}
        :param bytes_data: Raw encoded data so far.
        :type bytes_data: bytes
        """
        header = (MAGIC_HEADER +
                  struct.pack(VERSION_SYMBOL, PROTO_VERSION))
        return header + bytes_data

    def decode(self, data, crypto):
        offset = 0
        # Check for magic string.
        if data[:len(MAGIC_HEADER)] != MAGIC_HEADER:
            raise ProtocolError("Magic string does not match")
        offset += len(MAGIC_HEADER)
        # Check for version number.
        version = struct.unpack(VERSION_SYMBOL,
                                data[offset:offset +
                                     struct.calcsize(VERSION_SYMBOL)])[0]
        if version != PROTO_VERSION:
            print(version, PROTO_VERSION)
            raise ProtocolError("Protocol is from a different version")
        offset += struct.calcsize(VERSION_SYMBOL)
        # Figure out what type of packet this is.
        pkt_type = struct.unpack(TYPE_SYMBOL,
                                 data[offset:offset +
                                      struct.calcsize(TYPE_SYMBOL)])[0]
        offset += struct.calcsize(TYPE_SYMBOL)
        # Get data out of it.
        msg_name, r_dict = self.submessages[pkt_type].decode(data[offset:],
                                                             crypto)
        r_dict[Tags.TYPE] = pkt_type
        return msg_name, r_dict


class Encrypted(Message):
    """
    Message for and encrypted data.
    The initializer must get a string for the encryption
    suite that it uses.
    """
    def __init__(self, suite, tags=[], submessages=None):
        pkt_id_tag = Tag(Tags.PKTID, ID_SYMBOL)
        super().__init__([pkt_id_tag] + tags, submessages)
        self.suite = suite

    def encode(self, crypto, dict_data, bytes_data):
        data = struct.pack(TYPE_SYMBOL, self.index)
        data += crypto[self.suite].encrypt(bytes_data)
        return self.parent.encode(crypto, dict_data, data)

    def decode(self, data, crypto):
        payload = crypto[self.suite].decrypt(data)
        return super().decode(payload, crypto)


class Protocol():
    """
    Container for the ByteLynx protocol.
    """

    def __init__(self, translator):
        self.on_dht = Event()
        self.on_dht_ping = Event()
        self.on_net_ping = Event()

        self.proto = None
        self.set_proto(translator)
        self.messages = self.get_messages(self.proto)

    def decode(self, data, crypto):
        """
        Shortcut to decode using the local protocol.

        :param data: Raw data to decode.
        :type data: bytes
        :param crypto: The crypto hander to use.
        :type crypto: :class:`~crypto.CryptoHandlers`
        """
        return self.proto.decode(data, crypto)

    def encode(self, data, crypto):
        """
        Shortcut to encode using the local protocol.

        :param data: Data to encode.
        :type data: dict
        :param crypto: The crypto hander to use.
        :type crypto: :class:`~crypto.CryptoHandlers`
        """
        return self.proto.encode(data, crypto)

    def get_messages(self, proto=None):
        """
        Transforms the protocol into a flat dict of the leaves.
        This allows events to be hooked into the encoding of data.
        This method is recursive across another object.
        """
        r_dict = {}
        if proto is None:
            proto = self.proto
        if len(proto.submessages) > 0:
            for item in proto.submessages.items:
                r_dict.update(self.get_decoders(item))
        else:
            r_dict[proto.msg_name] = proto
        return r_dict

    def set_proto(self, translator):
        """
        Gets an instance of the protocol.
        Not a global so that events can be hooked up to it.

        :param translator: The method to translate contacts.
        :type translator: :attr:`~net.contacttable.translate`
        """

        # Since the proto is held onto by events,
        # declaring a new instance would result in a leak.
        # It would also result in all messages being parsed 2 times.
        if self.proto is not None:
            return

        # start-after
        self.proto = CarrierMessage(
            mode='bytelynx',
            submessages={
                0: Message('hello', tags=[HashTag()]),
                1: Message('dh.g', tags=[VarintTag('dh_g')]),
                2: Message('dh.mix', tags=[VarintTag('dh_B')]),
                # DHT AES-encrypted messages.
                # Key comes from DH handshake.
                # All encrypted messages have a pkt_id innately.
                3: Encrypted(mode='aes-dht', submessages={
                    1: Message('dht.ping', is_pongable=True,
                               dht_func=self.on_dht),
                    2: Message('dht.pong',
                               tags=[Tag('pong_id', ID_SYMBOL)],
                               dht_func=self.on_dht),
                    # DHT Search
                    3: Message('dht.search', is_pongable=True,
                               tags=[HashTag()],
                               dht_func=self.on_dht),
                    # DHT Response
                    4: Message('dht.response', is_pongable=True,
                               tags=[HashTag(),
                                     ListTag('nodes',
                                             NodeTag(translator))],
                               dht_func=self.on_dht),
                    }),
                # Net AES-encrypted messages.
                # Key comes from PKI in AES-DHT layer.
                4: Encrypted('aes-net', submessages={
                    1: Message('net.pong', is_pongable=True,
                               dht_func=self.on_dht)
                    }),
                5: Message('testing',
                           tags=[Tag('int', 'I'),
                                 ListTag('strlist',
                                         StringTag('names'))])
                }
            )
        # end-before
