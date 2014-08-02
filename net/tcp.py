import socket
import threading
import json

from common import Event, Address


class Server():

    def __init__(self, port, conn_limit, blocking=False):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET,
                              socket.SO_REUSEADDR,
                              conn_limit)
        self._sock.bind(('', port))
        self._sock.listen(conn_limit)
        self._clients = {}
        self.on_data = Event()
        if blocking:
            self.listen()
        else:
            self._thread = threading.Thread(target=self.listen)
            self._thread.daemon = True
            self._thread.start()

    def listen(self):
        while True:
            clientsock, addr = self._sock.accept()
            self._clients[addr] = clientsock
            print('Connected from:', addr)
            listenThread = threading.Thread(target=self.handler,
                                            args=(clientsock, addr[0]))
            listenThread.start()

    def handler(self, clientsock, addr):
        buf = 1024
        while True:
            try:
                data = clientsock.recv(buf)
                if not data:
                    print("Connection Broken", addr)
                    break
                data = json.loads(data.decode('UTF-8'))
                print("%s <- %s" % (addr, data))
                self.on_data(Address(addr[0], addr[1]), data)
            except Exception as e:
                print(e)
        clientsock.close()

    def send_data(self, address, data):
        data = json.dumps(bytes(data, 'UTF-8'))
        print("%s -> %s" % (address, data))
        self._clients[address.tuple].send(data)


class Client():

    def __init__(self, address):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(address.tuple)
        self._thread = threading.Thread(target=self.handler)
        self._thread.daemon = True
        self._thread.start()
        self.on_data = Event()

    def send_data(self, data):
        data = bytes(json.dumps(data), 'UTF-8')
        print("-> %s" % data)
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
                print(e)
