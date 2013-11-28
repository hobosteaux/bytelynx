#!/usr/bin/python3

class ExtList(list):
	def first(self, exp = None):
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
		if (len(self) <= 0):
			raise ValueError("List is empty")
		return self[len(self) - 1]

	def where(self, exp):
		return (x for x in self if exp(x))

	def any(self, exp = None):
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
