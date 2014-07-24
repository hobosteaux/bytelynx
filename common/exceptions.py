class AbstractError(Exception):
    """Thrown when a base class has a function that mut be overridden"""
    def __init__(self, message=None):
        if message is None:
            message = "This function must be overridden by the inheriting class"
        super().__init__(message)


class ProtocolError(Exception):
    """Exception thrown if decoding goes awry."""
    pass
