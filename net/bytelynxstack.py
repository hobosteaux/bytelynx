from .tagconstants import Tags
from .contacttable import ContactTable
from .prototree import Protocol
from .udp import Server
from common import SentPacket, PacketWatcher


class Stack():
    """
    Main accessor to the bytelynx networking stack.
    Translates all data to expected values, as well
    as houses the on_data events for parsed packets.
    """

    def __init__(self):
        self._server = Server()
        self._contacts = ContactTable()
        self.protocol = Protocol(self._contacts.translate)
        self.watcher = PacketWatcher()
        self.watcher.on_resend += self.resend

        # make packet watcher
        self._server.on_data += self.on_data

    def on_data(self, address, raw_data):
        """
        Primary access point for any raw data received by the server.
        This function translates from :class:`~common.Address`
        to a :class:`~common.Contact`, decodes the data,
        and then procs the event for that packet type.

        :param address: The address that the data was received from.
        :type address: :class:`~common.Address`
        :param raw_data: The raw data from the contact.
        :type raw_data: bytes
        """
        # Translate the ip to a contact
        contact = self._contacts.translate(address)

        # Decode the packet
        msg_name, data = self.protocol.decode(raw_data, contact.crypto)

        msg = self.protocol.messages[msg_name]
        # Do message housekeeping
        msg.on_dht(contact)
        if msg.is_pongable:
            self.watcher.rm_packet(data[Tags.pkt_id],
                                   contact.channels[msg.mode])

        # Proc the correct on_data event
        msg.on_data(contact, data)

    def resend(self, pkt):
        """
        Resends a previously sent packet.

        :param pkt: The sent packet
        :type pkt: :class:`~common.SentPacket`
        """
        pkt.refresh()
        self._server.send(pkt.contact.address, pkt.data)
        self.watcher.add_packet(pkt)

    def send_data(self, contact, msg_name, data):
        """
        Sends packet to a given contact.

        :param contact: The contact to send data to.
        :type contact: :class:`~common.contact`
        :param msg_name: The unique name of the message.
        :type msg_name: str.
        :param data: The data to send.
        :type data: dict.
        """
        msg = self.protocol.messages[msg_name]
        # Get a packet id for this message
        channel = contact.channels[msg.mode]
        pkt_id = channel.pkt_id
        data[Tags.PKTID] = pkt_id

        # Encode data
        payload = msg.encode(contact.crypto, data)

        # Send data to a contact
        self._server.send(contact.address, payload)

        # Check if this message is sent 'reliably'
        if msg.is_pongable:
            pkt = SentPacket(pkt_id, payload, contact, channel)
            self.watcher.add_packet(pkt)
