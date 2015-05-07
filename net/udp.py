import socket
from threading import Thread
import traceback

from common import Address, Event
import common.btlxlogger as logger
Logger = logger.get(__name__)


class Server():
    """
    A simple threaded UDP server.
    Throws the :attr:`~net.Server.on_data` event when a packet is received.

    .. attribute:: on_data:
        A tuple of (:class:`net.Address`, raw_data)
    """

    def __init__(self, port):
        self.on_data = Event('udp.server.on_data')
        self._bind_address = ('', port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(self._bind_address)
        self._listener_thread = Thread(target=self.listen)
        self._listener_thread.daemon = True
        self._listener_thread.start()

    def listen(self):
        """
        Main while (True) loop to receive messages.
        """
        while (True):
            raw_data, address = self._sock.recvfrom(65536)

            # print('received '+ str(len(data)) +' bytes from '+ str(address))
            try:
                address = Address(address[0], address[1])
                self.on_data(address, raw_data)
            except:
                Logger.error("----- Receive Error -----")
                Logger.error("From: %s, Data: %s", address, raw_data)
                Logger.error(traceback.format_exc())

    def send(self, address, raw_data):
        """
        Sends a encoded data to an address.

        :param address: The destination address
        :type address: :attr:`~net.Address`
        :param data: Raw data
        :type tags: bytes
        """
        self._sock.sendto(raw_data, address.tuple)
