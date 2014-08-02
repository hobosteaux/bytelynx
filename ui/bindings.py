

"""
Bindings arch
-------------
property changed for any properties

clients subscribe to events (tcp)
every 1s if the prop has changed the value is sent

make sure to unsub on conn closed!
How to handle resumed sessions?

Everything subscribable has on_changed(name, val)
Inherit from baseclass that flattens based on prop array?
serializable items have 'flatten' attr
serializable items must be threadsafe
Flatten format:
    {'propname': value[s]}

RPCS
----
update -> data update
get_events -> gets all subscribable events (with description?)
sub_event -> subscribes to an event
unsub_event -> removes sub

Control Messages
----------------
unknown

Packet Structure
----------------
[{'command': 'rpc_name',  'values': {}}]

Bindings / etc
--------------
on property change, add name to a list
on ship, {name: prop_val for x in list if x in client.subs}

TODO
----
make tcp server
find subscribable events

"""


class Bindings(dict):

    def __init__(self, state):
        # List all bindable properties here
        # This will then be made into a list
        properties = []

        for item in properties:
            self[item.name] = item
