Protocol Tags
=============

Protocol tags were designed to be an easy method to encode and decode different data types.

.. note::
	Each tag stores data in the python form, not the network bytes form.
	This makes it much more efficient to get the python structures than to get the bytes version, since it must convert it each time.

.. note::
	No base :class:`~net.tag.Tag` class may have multiple members.
	This is due to the behavior of struct.unpack always returning a tuple.

.. todo:: Make struct.unpack behave consistently for 1 or more variables.

Creating a new tag
++++++++++++++++++

There are 2 things that must be overloaded, 1 that may:

.. method:: net.tag.Tag._encoded

.. method:: net.tag.Tag.encoded.setter
