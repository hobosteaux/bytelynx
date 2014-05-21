class Address():
    """
    .. attribute:: ip

        str. ip address
    .. attribute:: port

        int. port number
    """

    def __init__(self, ip, port):
        """
        :param ip: IPv4 address.
        :type ip: str.
        :param port: Port number.
        :type port: int.
        """
        self.ip = ip
        self.port = port

    @property
    def tuple(self):
        """
        :returns: A tuple of (ip, port).
        """
        return (self.ip, self.port)

    def __str__(self):
        return '%s:%s' % (self.ip, self.port)
