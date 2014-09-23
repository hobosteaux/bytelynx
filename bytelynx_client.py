#!/usr/bin/python3

from ui import Client, Menu, MenuOption
from common import Address


CLIENT = None


def connect():
    ipaddr = input("Enter the ip address [127.0.0.1]: ")
    if not ipaddr:
        ipaddr = '127.0.0.1'
    port = input("Enter the port number [2983]: ")
    if not port:
        port = '2983'
    addr = Address(ipaddr, int(port))

    global CLIENT
    CLIENT = Client(addr)


def print_events():
    if CLIENT is None:
        print("No client connected")
    else:
        print(CLIENT.events)


def subscribe():
    if CLIENT is None:
        print("No client connected")
    else:
        event = input("Enter the event name: ")
        CLIENT.subscribe(event)


if __name__ == '__main__':
    main_menu = Menu([
        MenuOption('Connect', connect),
        MenuOption('Print Events', print_events),
        MenuOption('Subscribe', subscribe)])
    main_menu.display()
