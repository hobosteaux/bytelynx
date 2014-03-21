from datetime import datetime, timedelta

from common import Contact, Event, List as list
from .constants import K, B
import state

class Bucket:
	"""
	.. attribute:: contacts
		:class:`list` of len :attr:`KademliaConstants.K`
	.. attribute:: waitlist
		:class:`list` of len :attr:`KademliaConstants.K`
	.. attribute:: on_added
		Event(:class:`event.Event`)
	.. attribute:: on_removed
		Event(:class:`event.Event`)
	"""

	def __init__(self):
		self.contacts = list()
		self.waitlist = list()
		self.on_added = Event()
		self.on_removed = Event()

	def update(self, contact, report=True):
		"""
		Checks if a new contact is more up to date than one in the bucket.

		:param contact: Newly seen contact.
		:type contact: :class:`contact.Contact`
		:param report: Pop the :func:`~bucket.Bucket.on_added` event or not.
		"""
		if (contact not in self.contacts):
			if (len(self.contacts) <= K):
				self.contacts.append(contact)
				contact.on_death += self.contact_death
				if (report):
					self.on_added(contact)
			elif (len(self.waitlist) <= K) and (contact not in self.waitlist):
				self.waitlist.append(contact)
				contact.on_death += self.waitlist_death
		
	def contact_death(self, contact):
		"""
		Event handler for when a contact expires that is in a list.

		:param contact: Dieing contact.
		:type contact: :class:`contact.Contact`
		"""
		if (contact in self.contacts):
			self.contacts.remove(contact)
			contact.on_death -= self.contact_death
			self.on_removed(contact)
		if (len(self.waitlist > 0)):
			replacement = self.waitlist[len(self.waitlist) - 1]
			self.contacts.append(replacement)
			waitlist.on_death += self.contact_death
			self.waitlist.remove(replacement)
			waitlist.on_death -= self.waitlist_death

	def waitlist_death(self, contact):
		if (contact in self.waitlist):
			self.waitlist.remove(contact)
			contact.on_death -= self.waitlist_death

CHECK_MIN = 1.5
"""How often to check for dead clients."""
DEL_MIN = 10
"""Minutes of staleness allowed for clients."""

class Buckets():
	"""
	Primary interface to the list of :class:`kademlia.Bucket`.

	.. attribute:: _buckets
		A list of buckets `~kademlia.K` big.
	.. attribute:: _conns
		All currently alive seen connections.
		{:class:`~common.Address` : :class:`~common.Contact}
	.. attricute:: _last_check
		Last time that the _conns we checked for liveliness.
	.. attribute:: on_added
		Event called when a new contact is added to a bucket.
		Event(:class:`~common.Client`)
	.. attribute:: on_removed
		Event called when a contact is removed from bucket.
		Event(:class:`~common.Client`)
	"""

	def __init__(self):
		self._last_check = datetime.now()
		self.on_added = Event()
		self.on_removed = Event()
		self._buckets = [Bucket() for i in range(B+1)]
		for bucket in self._buckets:
			bucket.on_added += self.on_added
			bucket.on_removed += self.on_removed
		self._conns = {}

	def seed(self, contacts):
		"""
		Function for initial seeding of the _buckets.
		Will not proc the on_added event for the db's sake.

		:param contacts: The contacts to add.
		:type contacts: [:class:`contact.Contact`]
		"""
		for contact in contacts:
			self.update(contact, False)

	def update(self, contact, report = True):
		"""
		Updates a contact within the correct bucket.

		:param contact: The seen contact.
		:type contact: :class:`contact.Contact`
		:param report: Pop the :func:`~bucket.Bucket.on_added` event or not.
		"""
		loc = (contact.hash ^ state.SELF.hash).significant_bit()
		self._buckets[loc].update(contact, report)

	def get_exact(self, hash, use_waitlist=False):
		"""
		Gets an exact contact from the lists.

		:param hash: The hash to retreive.
		:type hash: :class:`common.Hash`
		:param use_waitlist: Search through the waitlists as well.
		:type use_waitlist: bool.
		"""		
		significant_bit = (state.SELF.hash ^ hash).significant_bit()
		if (not use_waitlist):
			return self._buckets[significant_bit].contacts.first(lambda x: x.hash == hash)
		else:
			return (self._buckets[significant_bit].contacts + self._buckets[significant_bit].waitlist).first(lambda x: x.hash == hash)

	def get_closest(self, hash, count=K):
		"""
		Gets the closest n contacts to a hash.

		:param hash: The hash to compare to.
		:type hash: :class:`common.Hash`
		:param count: Number of contacts to return.
		:type count: int.
		"""
		targethash = (state.SELF.hash ^ hash)
		significant_bit = targethash.significant_bit()
		contacts = list(self._buckets[significant_bit].contacts)
		# If we have a perfect bucket size, return all.
		# This will NEVER proc for own bucket unless 20 key collisions.
		# Aka never
		if (len(self._buckets[significant_bit].contacts) == count):
			return contacts

		# Sorted Indices (for prox to the contact).
		# Ignore the one that is its own bucket to avoid any recursion.
		si = sorted([x for x in range(1,B)], key=lambda x: abs(x - significant_bit))[1:]

		# Yeah, yeah, we are ignoring the farthest away contact.
		for dindex in range(0, len(si) // 2):
			contacts += self._buckets[si[dindex * 2]].contacts
			contacts += self._buckets[si[(dindex * 2) + 1]].contacts
			if (len(contacts) >= B):
				return sorted(contacts, key=lambda x: targethash.AbsDiff(state.SELF.hash ^ x.hash))[:20]
		return contacts

	def translate(self, address, hash_):
		"""
		Translates an address and hash to a client handle.

		:return: A cached client.
		:rtype: :class:`contact.Contact`
		"""
		# We have seen this one before and it has not expired.
		if (address in self._conns):
			contact = self._conns[address]
		else:
			try:
				# Check if it is in the buckets.
				contact = self.get_exact(hash_, True)
			except:
				# Make a new one
				contact = Contact(address, hash_)
				contact.on_death += self.cleanup
				self._conns[address] = contact
		contact.last_seen = datetime.now()

		if (datetime.now() - self.last_check > timedelta(minutes=CHECK_MIN)):
			self.last_check = datetime.now()
			delTime = timedelta(minutes=DEL_MIN)
			delList = list(self._conns.values()).where(lambda x: datetime.now() - x.last_seen > delTime)

			for item in delList:
				item.on_death -= self.cleanup
				del(self._conns[item.Address])

		return contact

	def cleanup(self, contact):
		"""
		Removes a contact from the connection list.
		Calls contact.on_death no matter what.

		:param contact: Contact to remove.
		:type contact: :class:`contact.Contact`
		"""
		if (contact.address in self._conns):
			del(self._conns[contact.address])
		contact.on_death -= self.cleanup

