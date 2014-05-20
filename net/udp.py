import socket
from threading import Thread

from common import Address, Event
import state


class Server():
    """
    A simple threaded UDP server.
    Throws the :attr:`~net.Server.on_data` event when a packet is received.

    .. attribute:: on_data:
        A tuple of (:class:`net.Address`, raw_data)
    """

    def __init__(self):
        self.on_data = Event()
        self._bind_address = ('', state.SELF.address.port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(self._bind_address)
        self._listener_thread = Thread(target=self.listen)
        self._listener_thread.daemon = True
        self._listener_thread.start()

    def listen(self):
        """
        Main while (True) loop to receive messages.
        """
        # print("Waiting for message")
        while (True):
            raw_data, address = self._sock.recvfrom(65536)

            # print('received '+ str(len(data)) +' bytes from '+ str(address))

            try:
                address = Address(address[0], address[1])
                self.on_data(address, raw_data)

            except:
                print("ERROR:", address, raw_data)

    def send(self, address, raw_data):
        """
        Sends a encoded data to an address.

        :param address: The destination address.
        :type address:`~net.Address`
        :param data: Raw data.
        :type tags: bytes
        """
        self._sock.sendto(raw_data, address.AsTuple())
