#!/usr/bin/python3


class List(list):
    """
    Extension of the List class.
    Attempts to add some of the fancy LINQ features from c# into python.
    """

    def first(self, exp=None):
        """
        :param exp: Conditional for the elements to meet.
        :return: First element from a list.
        """
        if (exp is None):
            item = next(iter(self), None)
            if (item is None):
                raise ValueError("List is empty.")
            return item

        else:
            item = next((x for x in self if exp(x)), None)
            if (item is None):
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
        return List(x for x in self if exp(x))

    def count(self, exp=None):
        """
        :param exp: Conditional for the elements to meet.
        :return: Count of the filtered version of the list.
        :rtype: int.
        """
        if (exp is None):
            return len(self)
        else:
            return len([x for x in self if exp(x)])

    def any(self, exp=None):
        """
        :param exp: Conditional for the elements to meet.
        :return: If any elements exist.
        :rtype: bool.
        """
        if (exp is None):
            return len(self) != 0
        else:
            item = next((x for x in self if exp(x)), None)
            if (item is None):
                return False
            return True

    def select(self, exp):
        """
        .. todo:: Implement.
        """
        raise NotImplemented()

    def split(self, exp):
        """
        Splits a list into two lists.
        :return: Matching and non-matching elements.
        :rtype: Tuple(list, list)
        """
        match = List()
        nonmatch = List()
        for item in self:
            if exp(item):
                match.append(item)
            else:
                nonmatch.append(item)
        return (match, nonmatch)
