
from common.exceptions import ProtocolError
from crypto.aesgcm import KEY_SIZE
from crypto import SHAModes, Modules


def on_hello(contact, data):
    """
    Handler for client hellos.
    Adds the client hash to the contact object.
    """
    contact.set_hash(data['hash'])


def on_dh_g(contact, data):
    """
    Handler for Diffie-Hellman g params.
    Ensures the state is correct and mixes.
    """
    contact.channels['bytelynx'].crypto.g = data['dh_g']


def on_dh_B(contact, data):
    """
    Handler for the Diffie-Hellman B param.
    Ensures the state is correct and mixes.
    Creates the next level of crypto (aes-dht).
    """
    contact.channels['bytelynx'].crypto.B = data['dh_B']
    shared = contact.channels['bytelynx'].crypto.key
    sha_func = SHAModes[KEY_SIZE * 8]
    s_hash = sha_func(shared.to_bytes(KEY_SIZE, 'little')).digest()

    if 'aes-dht' in contact.channels:
        # TODO: This errors on renegotiations
        raise ProtocolError('Channel already exists')
    aes_crypto = Modules['aes-dht']()
    aes_crypto.set_key(s_hash)
    contact.channels['aes-dht'] = aes_crypto
