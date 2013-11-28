from datetime import datetime, timedelta

from contact import Contact
from KademliaConstants import K, B
from listExt import ExtList
import state

class Bucket:
	Contacts = None
	Waitlist = None

	def __init__(self):
		self.Contacts = ExtList()
		self.Waitlist = ExtList()

	def Update(self, contact):
		if (contact not in self.Contacts):
			if (len(self.Contacts) <= K):
				self.Contacts.append(contact)
				contact.OnDeath += self.ContactDeath
			elif (len(self.Waitlist) <= K) and (contact not in self.Waitlist):
				self.Waitlist.append(contact)
				contact.OnDeath += self.WaitlistDeath
		
	def ContactDeath(self, contact):
		if (contact in self.Contacts):
			self.Contacts.remove(contact)
			contact.OnDeath -= self.ContactDeath
		if (len(self.Waitlist > 0)):
			replacement = self.Waitlist[len(self.Waitlist) - 1]
			self.Contacts.append(replacement)
			waitlist.OnDeath += self.ContactDeath
			self.Waitlist.remove(replacement)
			waitlist.OnDeath -= self.WaitlistDeath

	def WaitlistDeath(self, contact):
		if (contact in self.Waitlist):
			self.Waitlist.remove(contact)
			contact.OnDeath -= self.WaitlistDeath

class Buckets():
	Buckets = None
	Conns = None
	ConnList = None
	LastCheck = datetime.now()

	def __init__(self):
		self.Buckets = [Bucket() for i in range(B+1)]
		self.Conns = {}
		self.ConnList = ExtList()

	def Update(self, contact):
		loc = (contact.Hash ^ state.SELF.Hash).SigBit()
		self.Buckets[loc].Update(contact)

	def GetExact(self, hash, backupLists=False):		
		sigBit = (state.SELF.Hash ^ hash).SigBit()
		if (backupLists):
			return self.Buckets[sigBit].Contacts.first(lambda x: x.Hash == hash)
		else:
			return (self.Buckets[sigBit].Contacts + self.Buckets[sigBit].Waitlist).first(lambda x: x.Hash == hash)

	def GetClosest(self, hash, count=K):
		targetHash = (state.SELF.Hash ^ hash)
		sigBit = targetHash.SigBit()
		contacts = ExtList(self.Buckets[sigBit].Contacts)
		# If we have a perfect bucket size, return all.
		# This will NEVER proc for own bucket unless 20 key collisions.
		# Aka never
		if (len(self.Buckets[sigBit].Contacts) == count):
			return contacts

		# Sorted Indices (for prox to the contact).
		# Ignore the one that is its own bucket to avoid any recursion.
		si = sorted([x for x in range(1,B)], key=lambda x: abs(x - sigBit))[1:]

		# Yeah, yeah, we are ignoring the farthest away contact.
		for dindex in range(0, len(si) // 2):
			contacts += self.Buckets[si[dindex * 2]].Contacts
			contacts += self.Buckets[si[(dindex * 2) + 1]].Contacts
			if (len(contacts) >= B):
				return sorted(contacts, key=lambda x: targetHash.AbsDiff(state.SELF.Hash ^ x.Hash))[:20]
		return contacts

	def Translate(self, address, hash):
		# We have seen this one before and it has not expired.
		if (address in self.Conns):
			contact = self.Conns[address]
		else:
			try:
				# Check if it is in the buckets.
				contact = self.GetExact(hash, True)
			except:
				# Make a new one
				contact = Contact(address, hash)
				contact.OnDeath += self.Cleanup
				self.Conns[address] = contact
		contact.LastSeen = datetime.now()

		if (datetime.now() - self.LastCheck > timedelta(minutes=1)):
			self.LastCheck = datetime.now()
			delTime = timedelta(minutes=10)
			delList = self.ConnList.where(lambda x: datetime.now() - x.LastSeen > delTime)
			self.ConnList = self.ConnList.where(lambda x: datetime.now() - x.LastSeen <= delTime)

			for item in delList:
				item.OnDeath -= self.Cleanup
				del(self.Conns[item.Address])

		return contact

	def Cleanup(self, contact):
		if (contact.Address in self.Conns):
			self.ConnList.remove(contact)
			del(self.Conns[contact.Address])
		contact.OnDeath -= self.Cleanup

