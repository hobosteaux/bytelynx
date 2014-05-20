from datetime import datetime, timedelta

from common import Contact

#: Time (in minutes) before a contact is removed.
EXPIRE_TIME = 10
#: Time (in minutes) between dead contact sweeps.
SWEEP_INTERVAL = 1.5


class ContactTable():
    """
    Class that keeps track of all recently seen contact.
    Also provides translation from :class:`~common.Address`
    to :class:`~common.Contact`
    """

    def __init__(self):
        self._contacts = {}
        self._last_check = datetime.now()

    def translate(self, address):
        """
        Translates an :class:`~common.Address`
        a :class:`~common.Contact`.
        If no matching contact exists, one is created.

        :param address: The address data was received from.
        :type address: :class:`~common.Address`
        :param hash_: Given if this is a new client (on 'hello')
        :type hash_: :class:`~common.Hash`
        """

        # Get an existing contact
        try:
            contact = self._contacts[address]
            # Set the last time seen (to now)
            contact.last_seen = datetime.now()
        # Errors if the contact does not exist
        except KeyError:
            contact = Contact(address)
            contact.on_death += self.clean_contact
            self._contacts[address] = contact

        # Check for a sweep
        if datetime.now() - self._last_check > \
                timedelta(minutes=SWEEP_INTERVAL):
            self._last_check = datetime.now()
            del_time = datetime.now() - timedelta(minutes=EXPIRE_TIME)
            del_list = list(self._contacts.values())\
                .where(lambda x: x.last_seen < del_time)

            for item in del_list:
                item.on_death()

    def clean_contact(self, contact):
        """
        Event handler for when a contact has expired.
        Cleans the contact out of the associated lists.

        :param contact: The expiring contact.
        :type contact: :class:`~common.Contact`
        """

        try:
            del(self._clients[contact.address])
        except KeyError:
            pass
