#!/usr/bin/python3


class Event:
    """
    C# style event.

    Example:

    >>> from common import Event
    >>> e = Event()
    >>> e += lambda: print("fired")
    >>> e()

    >>> e = Event()
    >>> e += lambda x: print("fired with arg %s" % x)
    >>> e('an arg')
    """

    def __init__(self):
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
        for handler in self.handlers.copy():
            handler(*args, **kargs)

    def getHandlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = getHandlerCount


# --- EXAMPLE ---
class MockFileWatcher:
    def __init__(self):
        self.fileChanged = Event()

    def watchFiles(self):
        source_path = "foo"
        self.fileChanged(source_path)


def log_file_change(source_path):
    print("%r changed." % (source_path,))


def log_file_change2(source_path):
    print("%r changed!" % (source_path,))

if (__name__ == '__main__'):
    watcher = MockFileWatcher()
    watcher.fileChanged += log_file_change2
    watcher.fileChanged += log_file_change
    watcher.fileChanged -= log_file_change2
    watcher.watchFiles()
