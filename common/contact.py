from datetime import datetime, timedelta

from .event import Event
from .list import List as list

TIMEOUTMULT = 3
"""Multiplier as to how long it takes for a ping to time out"""

class Contact():
	"""
	.. attribute:: pings

		List of all pings sent and send time.
	.. attribute:: address

		Remote :class:`common.Address`.
	.. attribute:: hash

		Remote :class:`common.Hash`.
	.. attribute:: last_seen

		Last time a packet was seen from this address.
	.. attribute:: on_death

		Event thrown when the contact has died.
	"""

	ping = 150
	"""Sliding counter on ping response times."""
	liveliness = 1
	"""Sliding counter on missed pings."""
	counter = 0
	"""Packet counter."""
	needs_hash = True
	"""If a hash has been scraped from the contact yet."""


	def __init__(self, addr, hash=None):
		self.needs_hash = hash == None
		self.address = addr
		self.hash = hash
		self.last_seen = datetime.now()
		self.pings = list()
		self.on_death = Event()

	def __str__(self):
		return '%s' % (self.address)

	def __repr__(self):
		return '%s' % (self.address)

	def set_hash(self, hash_):
		"""
		Sets the contacts hash.
		"""
		if not self.needs_hash:
			raise ValueError("Hash already set")
		self.hash = hash_
		self.needs_hash = False

	def add_ping(self):
		"""
		Adds a ping to the list.
		This means that it is send but not awk'ed.

		:returns: Packet id.
		:rtype: ushort
		"""
		pkt_id = self.counter
		self.counter += 1
		self.pings.append(ping(pkt_id, datetime.now()))
		if (self.counter > 65535):
			self.counter = 0
		return pkt_id

	def awk_ping(self, pkt_id):
		"""
		Awknowledge a previous ping.

		:param pkt_id: The packet to awk.
		:type pkt_id: int.
		"""
		try:
			# I would love to use PyLINQ, but we are cleaning any old pings too.
			oldpings = []
			for ping in self.pings:
				# If we found the ping that we are trying to awk.
				if (ping.pkt_id == pkt_id):
					time = ping.latency()
					time = time.seconds * 1000 + time.microseconds / 1000
					self.ping = (self.ping / 1.5) + (time / 3)
					self.liveliness = (self.liveliness * 0.8) + 0.2
					oldpings.append(ping)
					break
				elif (ping.latency() > timedelta(milliseconds=self.ping * TIMEOUTMULT)):
					oldpings.append(ping)
			map(lambda x: self.kill_ping(x), oldpings)
		# Happens if ... ?
		except StopIteration:
			pass

	def kill_ping(self, ping):
		"""
		Remove a ping from the list of pending ones.
		Decreases :attr:`~common.Contact.liveliness`.

		:param ping: ping to remove.
		:type ping: :class:`common.Ping`
		"""
		self.pings.remove(ping)
		self.liveliness *= 0.8
		if (self.liveliness <= 0):
			 self.on_death(self)
