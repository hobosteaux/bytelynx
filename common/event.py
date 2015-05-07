#!/usr/bin/python3
from types import new_class
import traceback
import sys


def Event(name):
    """
    A mutator for events.

    Still unproven if it works, but *should*
    dynamically make classes for each unique event.
    This way, debugging is easier,
    since we can tell which event is which.
    """
    c = new_class(name, bases=(_Event,))(name)
    return c


class _Event():
    """
    C# style event.

    Example:

    >>> from common import Event
    >>> e = Event('test1')
    >>> e += lambda: print("fired")
    >>> e()

    >>> e = Event('test2')
    >>> e += lambda x: print("fired with arg %s" % x)
    >>> e('an arg')
    """

    def __init__(self, name):
        self.name = name
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, " +
                             "so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        # Copy the set
        # Prevents iteration errors if an event removes itself
        try:
            for handler in self.handlers.copy():
                handler(*args, **kargs)
        except Exception as e:
            #print(traceback.format_exc(), file=sys.stderr)
            print("Event: %s" % self.name, file=sys.stderr)
            print('-' * 20, file=sys.stderr)
            raise e

    def handler_count(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = handler_count
