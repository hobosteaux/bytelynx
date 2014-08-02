

class UIClient():

    def __init__(self, address):
        self.address = address
        self.subscriptions = set()
