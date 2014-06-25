#!/usr/bin/python3
import sqlite3

from .contact import Contact
from .address import Address
from .hash import Hash

#: Table creation schema
INITSTATEMENT = '''CREATE TABLE IF NOT EXISTS swarm
                    (key INTEGER PRIMARY KEY, ip VARCHAR(15), port INTEGER, hash BLOB);
                   CREATE TABLE IF NOT EXISTS friends
                    (key INTEGER PRIMARY KEY, nickname TEXT, publickey blob);
                '''


class dbinterface():
    """
    Abstraction layer for the sqlite db.
    """

    def __init__(self, state_dir):
        self.conn = sqlite3.connect(state_dir + 'datastore.sqlite',
                                    check_same_thread=False)
        cur = self.conn.cursor()
        cur.executescript(INITSTATEMENT)
        self.conn.commit()
        cur.close()

    def contacts(self):
        """
        :returns: All contacts in the db.
        :rtype: [:class:`common.Contact`]
        """
        statement = 'SELECT * FROM swarm'
        cur = self.conn.cursor()
        cur.execute(statement)
        return list(map(lambda x: Contact(Address(x['ip'], x['port']),
                                          Hash(x['hash'])),
                        cur.fetchall()))
        cur.close()

    def add_contact(self, contact):
        """
        Adds a contact to the db.

        :param contact: Contact to add.
        :type contact: [:class:`common.Contact`]
        """
        statement = 'INSERT INTO swarm(ip, port, hash) VALUES(?,?,?)'
        cur = self.conn.cursor()
        cur.execute(statement, (contact.Address.IP,
                                contact.Address.Port,
                                contact.Hash.Value))
        self.conn.commit()
        cur.close()

    def rm_contact(self, contact):
        """
        Removes a contact from the db.

        :param contact: Contact to remove.
        :type contact: [:class:`common.Contact`]
        """
        statement = 'DELETE FROM swarm WHERE ip=? and port=?'
        cur = self.conn.cursor()
        cur.execute(statement, contact.Address.AsTuple())
        self.conn.commit()
        cur.close()
