Bucket objects
==============

The buckets are the primary datastore for contacts in the kademlia DHT.
Each `~kademlia.bucket.Buckets` object holds multiple `~kademlia.bucket.Bucket` s and provides a primary interface to manipulate them

Constants
+++++++++
.. automodule:: kademlia.bucket
	:members: CHECK_MIN, DEL_MIN

Bucket Structures
+++++++++++++++++

.. autoclass:: kademlia.bucket.Buckets
	:members:
	:undoc-members:

.. autoclass:: kademlia.bucket.Bucket
	:members:
	:undoc-members:
