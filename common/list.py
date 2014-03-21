#!/usr/bin/python3

class List(list):
	"""
	Extension of the List class.
	Attempts to add some of the fancy LINQ features from c# into python.
	"""

	def first(self, exp = None):
		"""
		:param exp: Conditional for the elements to meet.
		:return: First element from a list.
		"""
		if (exp == None):
			item = next(iter(self), None)
			if (item == None):
				raise ValueError("List is empty.")
			return item

		else:
			item = next((x for x in self if exp(x)), None)
			if (item == None):
				raise ValueError("List does not contain any matches.")
			return item
	
	def last(self):
		"""
		:return: Last item from the list.
		"""
		if (len(self) <= 0):
			raise ValueError("List is empty")
		return self[len(self) - 1]

	def where(self, exp):
		"""
		:param exp: Conditional for the elements to meet.
		:return: Filtered version of the list.
		:rtype: :class:`ExtList`
		"""
		return ExtList(x for x in self if exp(x))

	def count(self, exp=None):
		"""
		:param exp: Conditional for the elements to meet.
		:return: Count of the filtered version of the list.
		:rtype: int.
		"""
		if (exp == None):
			return len(self)
		else:
			return len([x for x in self if exp(x)])

	def any(self, exp = None):
		"""
		:param exp: Conditional for the elements to meet.
		:return: If any elements exist.
		:rtype: bool.
		"""
		if (exp == None):
			return len(self) != 0
		else:
			item = next((x for x in self if exp(x)), None)
			if (item == None):
				return False
			return True

	def select(self, exp):
		pass



if __name__ == "__main__":
	l = ExtList()
	l.append(1)
	l.append(2)
	l.append(3)
	l.append(4)
	print(l.first(lambda x: x == 2))

	print(l.where(lambda x: x > 2))
