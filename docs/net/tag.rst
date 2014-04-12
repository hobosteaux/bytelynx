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

Tag Interface
+++++++++++++

.. autoclass:: net.tag.Tag
	:noindex:
	:members: encoded, decoded, to_value, to_encoded

Creating a new tag
++++++++++++++++++

There are 2 things that must be overloaded, 1 that may:

.. method:: net.tag.Tag._encoded

	The getter for the encoded version of the tag.
	This is where the different struct.pack goes.

.. method:: net.tag.Tag.encoded.setter

	The setter for the value from an encoded bytes object.
	This is where the different struct.unpack goes.

.. method:: net.tag.Tag.__init__

	This is for making a tag always have a preset name.
	Useful for constructs such as the :class:`~net.tag.HashTag`
	where the name is a known constant.

Current Tags
++++++++++++

.. automodule:: net.tag
	:members: Tag, HashTag, AddressTag, NodeTag, StringTag, ListTag
