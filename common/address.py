from .property import Property


class Address(Property):
    """
    Container struct for an IPv4 address / port
    """

    _flatten_attrs = ['ip', 'port']

    def __init__(self, ip, port):
        """
        :param ip: IPv4 address
        :type ip: str.
        :param port: Port number
        :type port: int.
        """
        super().__init__('address', (ip, port))

    def _on_changed(self):
        """
        Overriding this from the base class so we can
        throw ourselves instead of the backing value.
        """
        self.on_changed(self.name, self)

    @property
    def ip(self):
        """
        :returns: IPv4 address
        :rtype: str.
        """
        return self._value[0]

    @ip.setter
    def ip(self, value):
        """
        :param value: The ip
        :type value: str.
        .. warning: NOT threadsafe!
        """
        self.value = (value, self._value[1])

    @property
    def port(self):
        """
        :returns: The port
        :rtype: int.
        """
        return self._value[1]

    @port.setter
    def port(self, value):
        """
        :param value: The port
        :type value: int.
        .. warning: NOT threadsafe!
        """
        self.value = (self._value[0], value)

    @property
    def tuple(self):
        """
        :returns: The ip and port
        :rtype: Tuple(ip, port)
        """
        return self._value

    def __str__(self):
        return '%s:%s' % self._value
