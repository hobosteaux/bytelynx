
class CryptoError(Exception):
    """Exception thrown if something is wrong with crypto"""
    pass


class StateError(CryptoError):
    """Exception thrown if a crypto module's state is odd"""
    pass


class KeySizeError(CryptoError):
    """Exception thrown if the key is an incorrect size"""
    pass


class UninitializedError(CryptoError):
    """Exception thrown if a parameter is uninitialized"""
    pass
