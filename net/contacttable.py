from datetime import datetime, timedelta

from common import List as list
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

    def __init__(self, dh_group):
        """
        :param dh_group: The 'p' parameter for the group.
        """
        self._dh_p = dh_group
        self._contacts_by_addr = {}
        self._friends = {}
        self._last_check = datetime.now()

    def seed(self, contacts):
        """
        Puts initial contacts from the sqlite db into the table.
        These are all 'real', so there is no harm, even if they are dead.
        """
        for contact in contacts:
            contact.channels['bytelynx'].crypto.p = self._dh_p
            contact.on_death += self.clean_contact
            self._contacts[contact.address.tuple] = contact
            if contact.needs_hash:
                contact.on_hash_set += self.on_contact_hash
            else:
                self._contacts_by_hash[contact.hash.value] = contact

    def add_friend(self, friend):
        """
        Adds a friend to the translator.
        If this friend is seen, it will be associated.

        :param friend: The friend to add
        :type friend: :class:`~common.friend`
        """
        self._friends[friend.hash.value] = friend

    def on_contact_hash(self, contact):
        """
        Event handler for when a contact gets a hash.
        This puts it into the _contacts_by_hash dict,
        which allows the virtual contacts to be translated
        """
        contact.on_contact_hash -= self.on_contact_hash
        self._contacts_by_hash[contact.hash.value] = contact

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
            contact = self._contacts_by_addr[address.tuple]
            # Set the last time seen (to now)
            contact.last_seen = datetime.now()
            # It can only have a hash if it exists
            if not contact.needs_hash and contact.hash is not None:
                try:
                    self._friends[contact.hash.value].assiciate(contact)
                except KeyError:
                    pass
        # Errors if the contact does not exist
        except KeyError:
            contact = Contact(address, virtual=False)
            contact.channels['bytelynx'].crypto.p = self._dh_p
            contact.on_hash_set += self.on_contact_hash
            contact.on_death += self.clean_contact
            self._contacts[address.tuple] = contact

        # Check for a sweep
        if datetime.now() - self._last_check > \
                timedelta(minutes=SWEEP_INTERVAL):
            self._last_check = datetime.now()
            del_time = datetime.now() - timedelta(minutes=EXPIRE_TIME)
            del_list = list(self._contacts.values())\
                .where(lambda x: x.last_seen < del_time)

            for item in del_list:
                item.on_death()
        return contact

    def clean_contact(self, contact):
        """
        Event handler for when a contact has expired.
        Cleans the contact out of the associated lists.

        :param contact: The expiring contact.
        :type contact: :class:`~common.Contact`
        """
        contact.on_death -= self.clean_contact
        try:
            del(self._clients[contact.address.tuple])
        except KeyError:
            pass
