from datetime import datetime


class Ping():
    """
    Simple struct for pings.

    .. attribute:: pkt_id

        The ushort packet id.
    .. attribute:: sent_time

        The datetime that it was sent.
    """

    def __init__(self, pktid, time):
        self.pkt_id = pktid
        self.sent_time = time

    @property
    def latency(self):
        """
        :return: How old this ping is.
        :rtype: :class:`datetime.timedelta`
        """
        return datetime.now() - self.sent_time
