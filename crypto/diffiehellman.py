#!/usr/bin/python3
from .cryptobase import CryptoModule
from .exceptions import CryptoError, StateError


class DHCrypto(CryptoModule):
    """
    Crypto module for Diffie-Hellman handshakes.
    This module is built with the assumption that p (the modulus)
    is a pre-shared secret for the network.
    This serves to act as a password for the network to keep other
    non-authorized entities out.

    .. attribute:: key
        The full key for a connection.
    """

    def __init__(self):
        super().__init__()
        self._private = None
        self._sent_a = False

    @property
    def private(self):
        """
        The local private key
        """
        # TODO: Make this a dynamic size / etc
        if self._private is None:
            self._private = self.random_int(512)
        return self._private

    @property
    def p(self):
        """
        Returns the current value of p.
        """
        return self._p

    @p.setter
    def p(self, value):
        """
        Sets the value of p.

        State: created -> p_set

        :raises: :class:`~crypto.exceptions.StateError`
        """
        if self.state != 'created':
            raise StateError('Crypto state is incorrect')
        self._p = value
        self.state = 'p_set'

    def _check_g(self, g):
        """
        Checks to see if a g is a good parameter for p
        """
        # TODO: Make this a realistic check
        return True

    def _set_g(self, value):
        if self.state != 'p_set':
            raise StateError('Crypto state is incorrect')
        if not self._check_g(value):
            raise CryptoError('G value is weak')
        self.state = 'g_set'
        self._g = value

    @property
    def g(self):
        """
        State: p_set -> g_set

        :returns: A random g
        :raises: :class:`~crypto.exceptions.CryptoError`
        :raises: :class:`~crypto.exceptions.StateError`
        """
        # TODO: Make g change.
        self._set_g(3)
        return self._g

    @g.setter
    def g(self, value):
        """
        State: p_set -> g_set

        :raises: :class:`~crypto.exceptions.CryptoError`
        :raises: :class:`~crypto.exceptions.StateError`
        """
        self._set_g(value)

    @property
    def A(self):
        """
        Returns (g^a) % p

        State: p_set | initialized -> N/A

        :raises: :class:`~crypto.exceptions.CryptoError`
        """
        if self._sent_a:
            raise StateError("A has already been sent")
        if self.state == 'g_set' or self.state == 'initialized':
            self._sent_a = True
            return pow(self._g, self.private, self.p)
        else:
            raise StateError('Crypto state is incorrect')

    @property
    def B(self):
        raise NotImplementedError('This should never be read')

    @B.setter
    def B(self, value):
        """
        Adds the remote mixture to the key.

        State: g_set -> initialized

        :raises: :class:`~crypto.exceptions.CryptoError`
        """
        if self.state == 'g_set':
            self.state = 'initialized'
            self.key = pow(value, self.private, self.p)
            # This *should* work here.
            # Although... this may send queued packets before
            # we mix on the other side.
            self.on_finalization()
        else:
            raise StateError('Crypto state is incorrect')

    @property
    def is_inited(self):
        """
        :returns: If this dh module is fully initialized.
        """
        return self.state == 'initialized'

    @property
    def is_free(self):
        """
        :returns: If this dh module is free to begin handshaking.
        """
        return self.state == 'p_set'


def test():
    alice = DHCrypto()
    bob = DHCrypto()

    alice.p = 23
    print("A: %s, B: %s" % (alice.state, bob.state))
    bob.p = 23
    print("A: %s, B: %s" % (alice.state, bob.state))
    bob.g = alice.g
    print("A: %s, B: %s" % (alice.state, bob.state))
    bob.B = alice.A
    print("A: %s, B: %s" % (alice.state, bob.state))
    alice.B = bob.A
    print("A: %s, B: %s" % (alice.state, bob.state))
    print("Alice: %s" % alice.key)
    print("Bob: %s" % bob.key)

if __name__ == '__main__':
    test()
