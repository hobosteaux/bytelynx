import socket
import threading
import json
import traceback

from common import Event, Address
import common.btlxlogger as logger

# TODO: allow datetimes across the wire


class Server():
    Logger = logger.get(__name__)

    def __init__(self, port, conn_limit, blocking=False):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET,
                              socket.SO_REUSEADDR,
                              conn_limit)
        self._sock.bind(('', port))
        self._sock.listen(conn_limit)
        self._clients = {}
        self.on_data = Event('tcp.server.on_data')
        self.on_cleanup = Event('tcp.server.on_cleanup')
        if blocking:
            self.listen()
        else:
            self._thread = threading.Thread(target=self.listen)
            self._thread.daemon = True
            self._thread.start()

    def listen(self):
        while True:
            clientsock, addr = self._sock.accept()
            address = Address(addr[0], addr[1])
            self._clients[str(address)] = clientsock
            self.Logger.info('Connected from:', addr)
            listenThread = threading.Thread(target=self.handler,
                                            args=(clientsock, address))
            listenThread.start()

    def handler(self, clientsock, address):
        buf = 1024
        while True:
            try:
                data = clientsock.recv(buf)
                if not data:
                    self.Logger.info("Connection Broken", address)
                    break
                data = json.loads(data.decode('UTF-8'))
                self.Logger.debug("%s -> %s" % (address, data))
                self.on_data(address, data)
            except Exception as e:
                self.Logger.error(traceback.format_exc())
        clientsock.close()
        self.on_cleanup(address)

    def send_data(self, address, data):
        data = json.dumps(data)
        self.Logger.debug("%s <- %s" % (address, data))
        self._clients[str(address)].send(bytes(data, 'UTF-8'))


class Client():

    def __init__(self, address):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(address.tuple)
        self._thread = threading.Thread(target=self.handler)
        self._thread.daemon = True
        self._thread.start()
        self.on_data = Event()

    def send_data(self, data):
        print("-> %s" % data)
        data = bytes(json.dumps(data), 'UTF-8')
        self._sock.send(data)

    def handler(self):
        buf = 1024
        while True:
            try:
                data = self._sock.recv(buf)
                if not data:
                    print('Client conn broken')
                    break
                data = json.loads(data.decode('UTF-8'))
                print("<- %s" % data)
                self.on_data(data)
            except Exception as e:
                print(traceback.format_exc())
