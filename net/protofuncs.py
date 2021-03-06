
from crypto.exceptions import StateError
from crypto.aesgcm import KEY_SIZE
from crypto import SHAModes


def on_hello(contact, data):
    """
    Handler for client hellos.
    Adds the client hash to the contact object.

    If the hash already exists, initiates a DH exchange.
    """
    import state
    s = state.get()
    crypto = contact.channels['bytelynx'].crypto
    if contact.set_hash(data['hash']):
        s.net.send_data(contact, 'hello', {'hash': s.contact.hash})
    elif crypto.is_free:
        s.net.send_data(contact, 'dh.g', {'dh_g': crypto.g})


def on_dh_g(contact, data):
    """
    Handler for Diffie-Hellman g params.
    Ensures the state is correct and mixes.
    """
    import state
    crypto = contact.channels['bytelynx'].crypto
    crypto.g = data['dh_g']
    state.get().net.send_data(contact, 'dh.mix', {'dh_B': crypto.A})


def on_dh_B(contact, data):
    """
    Handler for the Diffie-Hellman B param.
    Ensures the state is correct and mixes.
    Creates the next level of crypto (aes-dht).
    """
    import state
    dh_crypto = contact.channels['bytelynx'].crypto

    # Extract the key
    dh_crypto.B = data['dh_B']
    shared = contact.channels['bytelynx'].crypto.key
    sha_func = SHAModes[KEY_SIZE * 8]
    s_hash = sha_func(shared.to_bytes(KEY_SIZE, 'little')).digest()

    # Create our AES crypto
    aes_crypto = contact.create_channel('aes-dht').crypto
    aes_crypto.set_key(s_hash)
    # print("AES key: %s" % aes_crypto.key)

    # Try to send our A, if needed
    try:
        state.get().net.send_data(contact, 'dh.mix', {'dh_B': dh_crypto.A})
    # Happens if we have already sent an A
    # Send a DHT hello
    except StateError:
        state.get().net.send_data(contact, 'dht.ping', {})


def on_pubkey_request(contact, data):
    """
    Handler for when a public key is requested by a contact.
    """
    # TODO: This function


def on_pubkey_response(contact, data):
    """
    Handler for when a public key is received from a contact.
    """
    # TODO: This function


def on_rsa_exchange(contact, data):
    """
    Handler for an RSA nonce exchange.
    """
    # TODO: This function
