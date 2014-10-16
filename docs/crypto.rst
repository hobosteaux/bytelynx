Crypto in ByteLynx
==================

The end goal is for no data to ever be leaked via transport.
To do this, there are three different crypto layers:

::

	The DH Exchange
	PKI
	AES-GCM Transport

Diffie-Hellman
++++++++++++++

Besides being one of the coolest crypto constructs made,
the DH exchange is primarily used to ensure group membership.

Because ByteLynx has n discreet networks with different bootstrap nodes, etc, it is imparative that a malicious user can not join two networks permanently.

The DH exponent is treated as a 'password' to each private network.
This ensures group membership, and while a malicious node could still bridge requests through themselves, it would be a tremendous effort.
The third party would also have to know both networks' passwords.

The first step to connecting to any node is a DH exchange.
A RSA exchange must also happen to verify node IDs.

This is vulverable to MitM attacks, as both checks can be defeated:
* Diffie-Hellman: The attacker can masquerade as the other party
* RSA: The attacker can pass this along, untouched

All DHT traffic is encapsulated in this.

PKI
+++

The use of PKI is two-fold: for node identity and initializing the AES connection.

After passing the DH group identity check, the node must pass the RSA identity check.
That is, the node must prove that it owns the cert belonging to the node id presented.
This is done by doing a handshake.
If this handshake is successful, then the hash of the public key is used as the DHT node id.
If the presented certificate is known as a friend, then the contact will be marked as so when this handshake occurs.

To elevate to 'secure' communications (friend <-> friend), the RSA channel is used once again.
An IV is negotiated over RSA and then used to begin the AES-GCM secure communication.

This layer is solely to address nodes and to provide an encrypted transport for a symmetric key.

AES-GCM
+++++++

The final layer is symmetric encryption, using the AES-GCM cipher.
This was chosen because it has authentication and works in a CTR mode, allowing for stateless communication over udp.

Each AES packet is structured in the following manner:

	IV | encrypted payload | tag

	:attr:`~crypto.aesgcm.IV_SIZE` | ... | :attr:`~crypto.aesgcm.TAG_SIZE`

This should be completely secure, as the IV is passed over a channel that identity of the remote party can be verified.
