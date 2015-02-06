import os
import struct
import socket

STATE = None

class _State():
    """
    Class for holding all the global state.

    .. attribute:: contact

        This instance's :class:`~common.Contact`
    .. attribute:: net

        This instance's :class:`~net.Stack`
    .. attribute:: kademlia

        This instance's :class:`~kademlia.Kademlia`
    .. attribute:: dh_group

        The group id that this node is a member of
    .. attribute:: dir

        Where all artifacts from this instance are kept
    """

    def __init__(self):
        import common.config as config
        self.config = config.get()

        from common import Contact, Address, Hash
        self.dir = self.config['general']['config_dir']
        self.bitsize = self.config['kademlia']['keysize']

        print("Using dir: %s" % self.dir)

        from crypto.rsa import KeyPair
        # TODO: Re-enable cert loading
        # Get the cert and the hash for it
        # keyblob = open(self.config['kademlia']['keyfile'], 'r').read()
        # self.keypair = KeyPair(private=keyblob)

        # TODO: Load pub / priv, base hash off of this.
        hash_ = Hash(os.urandom(self.bitsize // 8))

        # TODO: load this from config
        self.dh_group = self.config['kademlia']['group']

        # Set up the networking core
        if self.config['net']['randomize_port']:
            port = self.new_port()
        else:
            port = self.config['net']['port']

        import net.ipfinder
        from net import Stack
        from kademlia import Kademlia
        addr = Address(net.ipfinder.check_in(), port)
        self.contact = Contact(addr, hash_)
        self.net = Stack(port, self.dh_group)
        self.kademlia = Kademlia(self.net, self.contact, self.dir,
                                 self.config['kademlia']['bucket_size'],
                                 self.bitsize,
                                 self.config['kademlia']['paralellism'])
        try:
            from ui.server import UIServer
            self.uiserver = UIServer(self.config['net']['ui_port'],
                                     self.config['net']['max_ui_conns'])
            # Bind all the properties
            # This should probably be moved to a model somewhere
            props = {'contact_table': 'net._contacts'}
            for name, var_path in props.items():
                self.uiserver.add_property(name, var_path, self)
        except socket.error:
            print("UI server port taken. Starting without UI")

    def gen_testing_key(privloc, bits=512):
        # TODO: push this into the crypto area
        # Also,use cryptography when 0.6 comes out
        # Putting imports in here so they are destroyed later
        from Crypto.PublicKey import RSA
        from binascii import b2a_base64
        priv = RSA.generate(bits)
        open(privloc, "wt").write(
            str(b2a_base64(priv.exportKey('PEM')), 'UTF-8'))

    def new_port(self):
        """
        Gets a random free port > 10000.

        .. TODO::
            Check if the port is free.
            And if it is < 65000.
        """
        rport = struct.unpack('H', os.urandom(2))[0]
        while (rport < 10000):
            rport = struct.unpack('H', os.urandom(2))[0]
        return rport


def get():
    """
    Accessor for the state singleton
    """
    global STATE
    if STATE is None:
        STATE = _State()
    return STATE
