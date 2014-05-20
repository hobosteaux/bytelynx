from .tagconstants import Tags
from .contacttable import ContactTable
from .prototree import Protocol
from .udp import Server


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
        self.decoders = self.protocol.get_decoders()

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

        decoder = self.decoders[msg_name]
        # Do message housekeeping
        decoder.on_dht(contact)
        try:
            decoder.on_ping(contact, data[Tags.pkt_id])
        # Happens if this packet does not have an ID
        except KeyError:
            pass

        # Proc the correct on_data event
        decoder.on_data(contact, contact, data)

    def send_data(self, contact, data):
        # Encode the data
        pass
        # Get pkt_it

        # Encryption?
