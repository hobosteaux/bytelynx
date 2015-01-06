from datetime import datetime


class SentPacket():
    """
    Simple struct for sent packets.

    .. attribute:: pkt_id

        The ushort packet id.
    .. attribute:: data

        The data that was sent.
    .. attribute:: contact

        The contact that this packet was sent to.
    .. attribute:: channel

        The channel that it was sent over.
    .. attribute:: sent_time

        The datetime that it was sent.
    .. attribute:: awked

        If an answer to the packet has been seen.
    """

    def __init__(self, pktid, data, contact, channel):
        self.pkt_id = pktid
        self.data = data
        self.contact = contact
        self.channel = channel
        self.sent_time = datetime.now()
        self.awked = False

    def refresh(self):
        """
        'Refreshes' the sent time and any other attrs
        for when a packet is resent.
        """
        self.sent_time = datetime.now()

    def ack(self):
        self.received_time = datetime.now()

    @property
    def ctt(self):
        """
        :return: How long this ping has been active
        :rtype: float
        """
        td = datetime.now() - self.sent_time
        return td.total_seconds() * 1000

    @property
    def rtt(self):
        """
        :return: How old this ping is, in milliseconds.
        :rtype: float
        """
        td = self.received_time - self.sent_time
        return td.total_seconds() * 1000

    @property
    def info(self):
        """
        :return: Distiguishing characteristics for this packet.
        :rtype: Tuple(int., :class:`~common.Channel`)
        """
        return (self.pkt_id, self.channel)
