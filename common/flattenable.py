

class Flattenable():
    """
    Base class for any item that can be flattened.

    .. attribute: _flatten_attrs

        Attributes that are contained that must be flattened.
        List of variable names.
    .. attribute: _flatten_funcs

        Functions that must be called to flatten the data members
        All values are strings so they can be resolved at runtime
    """

    _flatten_attrs = []
    _flatten_funcs = []
    _flatten_lists = []
    _flatten_dicts = []

    def flatten(self):
        d = {x: self.__getattribute__(x)
             for x in self._flatten_attrs}
        d.update({x: self.__getattribute__(x).flatten()
                  for x in self._flatten_funcs
                  if self.__getattribute__(x) is not None})
        d.update({x: [y.flatten() for y in self.__getattribute__(x)]
                  for x in self._flatten_lists})
        d.update({x: {key: val.flatten() for key, val
                      in self.__getattribute__(x).items()}
                  for x in self._flatten_dicts})
        return d
