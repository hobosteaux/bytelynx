#!/usr/bin/python3

from KademliaConstants import K, A
import state
from contact import Contact, Address, Hash
from event import Event
from listExt import ExtList

class Shortlist():
	SearchSpace = None	# [(contacted, contact)]
	Closest = None
	OwnHash = None
	TargetHash = None
	Searched = 0
	InProgress = None	# [(addr, datetime)]

	OnFullOrFound = None	# Event to fire when the list is full of answers
	
	def __init__(self, targetHash, initialContacts):
		self.SearchSpace = ExtList([False, x] for x in initialContacts)	# Can be a list or extList
		self.OwnHash = state.SELF.Hash
		self.TargetHash = targetHash
		self.OnFullOrFound = Event()
		self.InProgress = []
		# Ensure we start off increasing.
		self.Sort()
		self.Closest = self.FindMin(False)

	def Update(self, newContacts):
		# Sort incoming contacts.
		newContacts.sort(key=lambda x: x.Hash ^ self.TargetHash)

		for contact in newContacts:
			# Can not include self in shortlist.
			if (self.OwnHash != contact.Hash):
				# Stop if the desired contact is found.
				if (contact.Hash == self.TargetHash):
					self.OnFullOrFound(self.TargetHash, contact)
				else:
					self.TryAdd(contact)
	
	# Filters all searches to remove the one given to it.	
	def RemoveSearch(self, addr):
		# x[0] is an address, x[1] is a datetime.
		self.InProgress = ExtList(filter(lambda x: x[0] != addr, self.InProgress))

	# The algorithmic complexity of this function is a tad high.
	# Not terribly pertinent with K=20 though.
	def TryAdd(self, contact):
		# Check that the hash does not already exist.
		if not (self.SearchSpace.Any(lambda x: x.Hash == contact.Hash)):
			# if < K contacts, add to the list.
			if  (len(self.SearchSpace) < K):
				self.SearchSpace.append([False, contact])
			# if == K contacts, and < K contacted.
			elif (self.Searched < K):
				max = self.FindMax()
				if (contact.Hash ^ self.TargetHash < max[1].Hash ^ self.TargetHash):
					self.SearchSpace.remove(max)
					self.SearchSpace.append([False, contact])
					self.Sort()

	def Sort(self):
		self.SearchSpace.sort(key=lambda x: x[1].Hash ^ self.TargetHash)

	# Gets the next item from the shortlist.
	# Also marks as contacted.
	def GetNext(self):
		if (self.Searched <= K):
			item = self.FindMin()
			item[0] = True
			self.Searched += 1
			self.InProgress.append((item[1].Address, datetime.now()))
			return item[1]
		else:
			return None

	# Returns the minimum item from the shortlist.
	# TODO: Clean this up.
	def FindMin(self, uncontacted=True):
		searchLambda = lambda x: not x[0]
		# Find first uncontacted contact
		if (uncontacted):
			if (self.Searched > K):
				self.OnFullOrFound(self.TargetHash, self.Closest)
				return None
		else:
			searchLambda = None
		minCon = self.SearchSpace.first(searchLambda)

		for contact in self.SearchSpace:
			if (uncontacted and not contact[0]):
				if (contact[1].Hash ^ self.TargetHash < minCon[1].Hash ^ self.TargetHash):
					minCon = contact
			elif (not uncontacted):
				if (contact[1].Hash ^ self.TargetHash < minCon[1].Hash ^ self.TargetHash):
					minCon = contact
		return minCon


	# Returns the maximum item from the shortlist.
	# TODO: Clean this up.
	def FindMax(self, uncontacted=True):
		searchLambda = lambda x: not x[0]
		# Find first uncontacted contact
		if (uncontacted):
			if (self.Searched > K):
				return None
		else:
			searchLambda = None
		maxCon = self.SearchSpace.first(searchLambda)

		# Reversed because we should ALWAYS be increasing.
		for contact in reversed(self.SearchSpace):
			if (uncontacted and not contact[0]):
				if (contact[1].Hash ^ self.TargetHash > maxCon[1].Hash ^ self.TargetHash):
					maxCon = contact
			elif (not uncontacted):
				if (contact[1].Hash ^ self.TargetHash > maxCon[1].Hash ^ self.TargetHash):
					maxCon = contact
		return maxCon

	def __str__(self):
		return '%s : %s - %d/%d/%d' % (self.TargetHash, self.Closest, len(self.InProgress), self.Searched, K)

from threading import Thread
from datetime import datetime
from time import sleep
from queue import Queue

class Shortlists():
	Shortlists = None		# {ip : shortlist}
	OnSearch = None			# Event
	OnFullOrFound = None	# Event
	Watcher = None			# Thread
	TaskQueue = None		# Queue

	def __init__(self):
		self.Shortlists = {}
		self.TaskQueue = Queue()
		self.OnSearch = Event()
		self.OnFullOrFound = Event()
		self.Watcher = Thread(target=self.Watcher)
		self.Watcher.daemon = True
		self.Watcher.start()

	def Start(self, hash, contacts):
		self.TaskQueue.put((self.__Start, (hash, contacts)))

	def __Start(self, hash, contacts):
		self.Shortlists[hash] = Shortlist(hash, contacts)
		self.Shortlists[hash].OnFullOrFound += self.OnFullOrFound
		self.Shortlists[hash].OnFullOrFound += self.DelList

	def AddResponse(self, hash, requestAddr, responses):
		self.TaskQueue.put((self.__AddResponse, (hash, requestAddr, responses)))

	def __AddResponse(self, hash, requestAddr, responses):
		self.Shortlists[hash].RemoveSearch(requestAddr)
		self.Shortlists[hash].Update(responses)

	def DelList(self, hash, target):
		self.TaskQueue.put((self.__DelList,(hash,)))

	def __DelList(self, hash):
		# This should NOT cause a mem leak since it has the pointers to functions.
		del(self.Shortlists[hash])

	def __CleanLists(self):
		#print(self.Shortlists)
		for key, value in self.Shortlists.items():
			alive = ExtList(filter(lambda x: (datetime.now()-x[1]).seconds > 3, value.InProgress))
			# If any of the requests have timed out.
			if (len(alive) != len(value.InProgress)):
				value.InProgress = alive
			try:
				while (len(value.InProgress) < A):
					nextMin = value.GetNext()
					self.OnSearch(key, nextMin)
			# Happens if the list has no more matches.
			except ValueError:
				# List is not full, but all contacts have been used.
				# Also, no searches are currently in progress.
				if (value.InProgress == 0):
					self.OnFullOrFound(value.TargetHash, value.Closest)

	# This thread watches for any RPCs that must be made.
	# It is the only one that should modify the datavalues of the shorts.
	def Watcher(self):
		while (True):
			while (self.TaskQueue.qsize() > 0):
				task = self.TaskQueue.get()
			#	if (task[0] != self.__CleanLists):
			#		print('TASK:', task)
				task[0](*(task[1]))
			sleep(.2)
			self.TaskQueue.put((self.__CleanLists,()))

# Placeholder for when a search is triggered.
# Used for testing only.
def Search(contact):
	print('SEARCH:',contact)

from os import urandom
if (__name__ == '__main__'):
	shortie = Shortlists(Search)
	while(True):
		shortie.Start(Hash(urandom(20)), [Contact(Address('192.168.0.1', 4000), Hash(b'12345678901234567890'))])
		sleep(1)

