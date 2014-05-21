class MenuOption():
    """
    Option for a menu.

    .. attribute:: text
        The text to display to the user.
    .. attribute:: function
        The function to execute.
    """

    def __init__(self, text, function):
        """
        :param text: Text to display.
        :type text: str.
        :param function: Function to execute on selection.
        :type function: func()
        """
        self.text = text
        self.function = function


class Menu():
    """
    Simple wrapper for an interactive menu.

    .. attribute:: options
        A list of :class:`ui.MenuOption`s.
    """

    def __init__(self, options):
        """
        :param options: Options for the menu.
        :type options: [:class:`ui.MenuOption`]
        """
        self.options = options

    def display(self):
        """
        A while (True) wrapper for displaying options.
        Lets the user choose one.
        """
        while (True):
            self.print()
            choice = self.get_choice()
            if (choice == len(self.options)):
                break
            else:
                self.options[choice].function()

    def get_choice(self):
        """
        Gets a choice from the user and checks it for validity.
        """
        number = -1
        while (number < 0) or (number > len(self.options)):
            number = int(input('Enter your menu choice: '))
        return number

    def print(self):
        """
        Displays the menu.
        """
        for idx, item in enumerate(self.options):
            print(idx, '-', item.text)
        print(len(self.options), '- Exit')
