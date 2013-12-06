#!/usr/bin/python3
import sqlite3
from contact import Contact, Address, Hash
import state

INITSTATEMENT = '''CREATE TABLE IF NOT EXISTS swarm
					(key INTEGER PRIMARY KEY, ip VARCHAR(15), port INTEGER, hash BLOB);
				   CREATE TABLE IF NOT EXISTS friends
					(key INTEGER PRIMARY KEY, nickname TEXT, publickey blob);

				'''

class dbinterface():

	def __init__(self):
		self.conn = sqlite3.connect(state.DIR + 'datastore.sqlite', check_same_thread=False)
		cur = self.conn.cursor()
		cur.executescript(INITSTATEMENT)
		self.conn.commit()
		cur.close()

	def Contacts(self):
		"""Returns all contacts in the db"""
		statement = 'SELECT * FROM swarm'
		cur = self.conn.cursor()
		cur.execute(statement)
		return list(map(lambda x: Contact(Address(x['ip'], x['port']), Hash(x['hash'])), cur.fetchall()))
		cur.close()

	def AddContact(self, contact):
		"""Adds a contact to the db"""
		statement = 'INSERT INTO swarm(ip, port, hash) VALUES(?,?,?)'
		cur = self.conn.cursor()
		cur.execute(statement, (contact.Address.IP, contact.Address.Port, contact.Hash.Value))
		self.conn.commit()
		cur.close()

	def RemoveContact(self, contact):
		"""Removes a contact from the db"""
		statement = 'DELETE FROM swarm WHERE ip=? and port=?'
		cur = self.conn.cursor()
		cur.execute(statement, contact.Address.AsTuple())
		self.conn.commit()
		cur.close()
