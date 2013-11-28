class MenuOption():
	Text = None
	Function = None

	def __init__(self, text, function):
		self.Text = text
		self.Function = function

class Menu():
	Options = None

	def __init__(self, options):
		self.Options = options

	def Display(self):
		while (True):
			self.Print()
			choice = self.GetChoice()
			if (choice == len(self.Options)):
				break
			else:
				self.Options[choice].Function()
			
	def GetChoice(self):
		number = -1
		while (number < 0) or (number > len(self.Options)):
			number = int(input('Enter your menu choice: '))
		return number		

	def Print(self):
		for idx, item in enumerate(self.Options):
			print(idx, '-', item.Text)
		print(len(self.Options), '- Exit')
