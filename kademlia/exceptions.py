
class KademliaError(Exception):
    """Base kademlia exception"""
    pass


class NoContactsError(KademliaError):
    """
    Thrown if the user tries a DHT operation before any contacts are known
    """
    pass
