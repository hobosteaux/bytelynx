from threading import RLock

from .event import Event
from .list import List
from .flattenable import Flattenable


class Property(Flattenable):

    def __init__(self, name, value):
        self.name = name
        self.on_changed = Event()
        self._value = value

    def __str__(self):
        return '<%s>' % self._value

    def _on_changed(self):
        self.on_changed(self.name, self.value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if self._value != val:
            self._value = val
            self._on_changed()


class AtomicProperty(Property):

    def __init__(self, name, value):
        self._l = RLock()
        super().__init__(name, value)

    @property
    def value(self):
        with self._l:
            return self._value

    @value.setter
    def value(self, val):
        with self._l:
            if self._value != val:
                self._value = val
                self._on_changed()


class StrAccumProperty(AtomicProperty):

    def __iadd__(self, value):
        with self._l:
            self.value = self._value + value
            return self

    def flatten(self):
        with self._l:
            d = {self.name: self.value}
            self._value = ''
        return d


class ListProperty(Property):

    def append(self, value):
        self._value.append(value)
        self._on_changed()

    def remove(self, value):
        self._value.remove(value)
        self._on_changed()

    def __len__(self):
        return len(self._value)

    @property
    def value(self):
        return List(self._value)


class DictProperty(Property):

    def __getitem__(self, value):
        return self._value[value]

    def __setitem__(self, v1, v2):
        if v1 not in self._value or self._value[v1] != v2:
            self._value[v1] = v2
            self._on_changed()

    def items(self):
        return self._value.items()

    def keys(self):
        return self._value.keys()

    def values(self):
        return self._value.values()

    def get(self, k, d=None):
        return self._value.get(k, d)
