#!/usr/bin/python3
import os
import base64

import state
from ui import Menu, MenuOption
from common import Hash, Address, Contact


def print_status():
    s = state.get()
    print('\t', s.contact.address)
    print('\t', s.contact.hash.base64)


def print_buckets():
    s = state.get()
    for idx, bucket in enumerate(s.kademlia.buckets._buckets):
        if (len(bucket.contacts) > 0):
            print(idx, bucket.contacts)


def print_shortlists():
    s = state.get()
    for item in s.kademlia.shortlists._shortlists:
        print(s.kademlia.shortlists._shortlists[item])

def print_contacts():
    s = state.get()
    for contact in s.net._contacts.net_contacts:
        print(contact)
        print("Last Seen: %s" % contact.last_seen)
        print("Liveliness: %s" % contact.liveliness)
        print("Ping: %s" % contact.ping)
        print("Channels")
        for name, channel in contact.channels.items():
            print('\t%s: Ct:%s ID:%s' % (name, len(channel.packets), channel._pkt_id))
        print('-' * 20)

def add_contact():
    s = state.get()
    ip = input("IP Address [127.0.0.1]: ")
    if (not ip):
        ip = '127.0.0.1'
    port = int(input("Port: "))
    addr = Address(ip, port)
    s.net.send_data(Contact(addr),
                    'hello',
                    {'hash': s.contact.hash})


def search_contact():
    hash_ = input("Enter the hash [rand]: ")
    if (not hash_):
        size = state.get().config['kademlia']['keysize'] // 8
        hash_ = Hash(os.urandom(size))
    else:
        hash_ = Hash(base64.b64decode(bytes(hash_, 'UTF-8')))
    s = state.get()
    s.kademlia.init_search(hash_)


# TODO: cmd arg for config path
if __name__ == '__main__':
    state.get()

    main_menu = Menu([
        MenuOption('Client Status', print_status),
        MenuOption('Bucket Status', print_buckets),
        MenuOption('Shorty Status', print_shortlists),
        MenuOption('Add Contact', add_contact),
        MenuOption('Search for Contact', search_contact),
        MenuOption('Print Contacts', print_contacts)
    ])

    main_menu.display()
