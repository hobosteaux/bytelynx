from .tagconstants import Tags
from .contacttable import ContactTable
from .prototree import Protocol
from .udp import Server
from net import protofuncs
from common import SentPacket, PacketWatcher
from common.exceptions import ChannelDNEError

class Stack():
    """
    Main accessor to the bytelynx networking stack.
    Translates all data to expected values, as well
    as houses the on_data events for parsed packets.
    """

    def __init__(self, port, dh_group):
        self._server = Server(port)
        self._contacts = ContactTable(dh_group)
        self.protocol = Protocol(self._contacts.translate)
        self.watcher = PacketWatcher()
        self.watcher.on_resend += self.resend

        # make packet watcher
        self._server.on_data += self.on_data
        self._handle_btlx()

    def _handle_btlx(self):
        msgs = self.protocol.messages
        msgs['hello'].on_data += protofuncs.on_hello
        msgs['dh.g'].on_data += protofuncs.on_dh_g
        msgs['dh.mix'].on_data += protofuncs.on_dh_B

    def update_contacts(self, contacts):
        return self._contacts.update(contacts)

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
        try:
            msg_name, data = self.protocol.decode(raw_data, contact)
        # Queue the message to be parsed when the channel is initialized fully
        except ChannelDNEError as e:
            contact.add_recv_msg(e.args[0], address, raw_data)
        else:
            msg = self.protocol.messages[msg_name]
            print("Recieved message: %s" % msg)
            channel = contact.channels[msg.mode]

            # Do message housekeeping
            msg.on_dht(contact)
            if msg.is_pongable:
                self.send_data(contact, msg.pong_msg,
                               {Tags.pongid.value: data[Tags.pktid.value]})
            # If this is a PONG
            elif msg.is_pong:
                payload = data[Tags.payload.value]
                channel.packets[payload[Tags.pongid.value]].ack()
                self.watcher.rm_packet(payload[Tags.pongid.value], channel)

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
        print("Sending message: %s" % msg)
        # Get a packet id for this message
        try:
            channel = contact.channels[msg.mode]
        # If we have not extablished a channel yet
        except KeyError as e:
            if msg.mode == 'aes-dht':
                print("Establishing AES-DHT channel")
                contact.add_sent_msg(msg.mode, msg_name, data)
                # Send a 'Hello'
                import state
                s = state.get()
                self.send_data(contact, 'hello', {'hash': s.contact.hash})
            else:
                raise e
        else:
            pkt_id = channel.pkt_id
            data[Tags.pktid.value] = pkt_id

            # Encode data
            payload = msg.encode(contact, data)

            # Send data to a contact
            self._server.send(contact.address, payload)

            # Check if this message is sent 'reliably'
            if msg.is_pongable:
                pkt = SentPacket(pkt_id, payload, contact, channel)
                channel.packets[pkt_id] = pkt
                self.watcher.add_packet(pkt)
