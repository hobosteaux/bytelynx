from datetime import datetime, timedelta

from common import List as list
from common import Contact
from common import Property

#: Time (in minutes) before a contact is removed.
EXPIRE_TIME = 10
#: Time (in minutes) between dead contact sweeps.
SWEEP_INTERVAL = 1.5


class ContactTable(Property):
    """
    Class that keeps track of all recently seen contact.
    Also provides translation from :class:`~common.Address`
    to :class:`~common.Contact`
    """

    _flatten_dicts = ['_contacts_by_addr', '_friends']

    def __init__(self, dh_group):
        """
        :param dh_group: The 'p' parameter for the group.
        """
        # Super weird init
        # Using self as the value so the serialization
        # is called on this base object
        super().__init__('contact_table', self)
        self._dh_p = dh_group
        self._contacts_by_addr = {}
        self._contacts_by_hash = {}
        self._friends = {}
        self._last_check = datetime.now()

    def __str__(self):
        """
        This must be overloaded since self._value = self
        Otherwise, Property.__str__() will infinitely recurse.
        """
        return ("ADDR: %s\nHASH: %s\nFRIENDS: %s" %
                (self._contacts_by_addr.values(),
                 self._contacts_by_hash.values(),
                 self._friends))

    @property
    def net_contacts(self):
        return [self._contacts_by_addr.values()]

    @property
    def friends(self):
        return [self._friends.values()]

    def update(self, contacts):
        """
        Does a mass translate of contacts made elsewhere.
        If they already exist, this will return the 'real' versions.
        """
        rlist = []
        for contact in contacts:
            try:
                rlist.append(self._contacts_by_hash[contact.hash.value])
            # If the hash has not been seen yet
            # TODO: this could error out with an AttributeError (no hash)
            except KeyError:
                try:
                    rcontact = self._contacts_by_addr[str(contact.address)]
                    rlist.append(rcontact)
                    if rcontact.needs_hash and not contact.needs_hash:
                        rcontact.hash = contact.hash
                # Happens if the contact is not made
                except KeyError:
                    contact.channels['bytelynx'].crypto.p = self._dh_p
                    contact.on_hash += self.on_contact_hash
                    contact.on_death += self.clean_contact
                    self._contacts_by_addr[str(contact.address)] = contact
                    if not contact.needs_hash:
                        self._contacts_by_hash[contact.hash.value] = contact
                    self._on_changed()
                    rlist.append(contact)
        return rlist

    def add_friend(self, friend):
        """
        Adds a friend to the translator.
        If this friend is seen, it will be associated.

        :param friend: The friend to add
        :type friend: :class:`~common.friend` or list(:class:`~common.friend`)
        """
        try:
            self._friends[friend.hash.value] = friend
        # If it is a friends list
        except AttributeError:
            self._friends.update({f.hash.value: f for f in friend})
        self._on_changed()

    def on_contact_hash(self, contact):
        """
        Event handler for when a contact gets a hash.
        This puts it into the _contacts_by_hash dict,
        which allows the virtual contacts to be translated
        """
        contact.on_hash -= self.on_contact_hash
        self._contacts_by_hash[contact.hash.value] = contact
        self._on_changed()

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
            contact = self._contacts_by_addr[str(address)]
            # Set the last time seen (to now)
            contact.last_seen = datetime.now()
            # Try associating the contact with a friend
            if not contact.needs_hash and not contact.has_friend:
                try:
                    self._friends[contact.hash.value].associate(contact)
                except KeyError:
                    pass
        # Errors if the contact does not exist
        except KeyError:
            contact = Contact(address)
            contact.channels['bytelynx'].crypto.p = self._dh_p
            contact.on_hash += self.on_contact_hash
            contact.on_death += self.clean_contact
            self._contacts_by_addr[str(address)] = contact
            self._on_changed()

        # Check for a sweep
        # TODO: Do we need to sweep contacts_by_hash?
        if datetime.now() - self._last_check > \
                timedelta(minutes=SWEEP_INTERVAL):
            self._last_check = datetime.now()
            del_time = datetime.now() - timedelta(minutes=EXPIRE_TIME)
            del_list = list(self._contacts_by_addr.values())\
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
            del(self._contacts_by_addr[str(contact.address)])
            self._on_changed()
        except KeyError:
            pass
