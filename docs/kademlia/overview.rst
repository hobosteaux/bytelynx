How Kademlia Works
==================

There are many documents on this, but hopefully this is a simple enough first-glance.

Some Basics
+++++++++++

Your address on the DHT is a hash.
We use the hash of your public key.

Each message received from a client also acts as a keep-alive and a ping.
The awk for messages counts as a pong as well as from retransmit purposes.
If a node does not respond multiple times, then it is considered *dead* and dropped.

Buckets
+++++++

The majority of known contacts are kept in buckets.
Each client has :attr:`~kademlia.constants.B` buckets, the same as the keysize.

The bucket that a remote client belongs in is judged by:
	significant_bit(my.hash ^ your.hash)
aka, the largest bit of difference (distance) between us.

Each bucket has :attr:`~kademlia.constants.K` clients in it.
The metric to choose which clients stay in the bucket is the longevity.

Joining the Network
+++++++++++++++++++

To join, a node must know a *bootstrapping node*.
A bootstrap node is any node that is already part of the kademlia DHT.

After identifying a bootstrap node (we do this via caching in sqlite), the joining client asks this node to do a *find* on the joining node's hash.

Performing a Search
+++++++++++++++++++

When a node is attempting to find another by its hash, it 

On Receipt of a Search Request
++++++++++++++++++++++++++++++

On Data Receival
++++++++++++++++

1. Add to the shortlists
2. Do stuff with the received data
