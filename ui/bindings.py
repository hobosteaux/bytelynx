

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
get_events -> gets all subscribable events (with description?)
sub_event -> subscribes to an event
unsub_event -> removes sub
update -> data update


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

PROPERTIES
Shortlists?--\ These need to be serialized intelligently
Buckets?   --/ Potential for 159 * 20 clients per update
               -> NO. This would be very complex / who cares
                  This is for local web uis
                  One concern left is serialization time
                   / locking everything while serialization occurs
Clients? -> This would mean dynamic subscription
            Would a GET arch be better?
            Or - subscribe to all clients,
            use this to subscribe to others
Net stats


Should everything commit 'stats' to a dict somewhere that are subscriptable?
Everything is pre-serialized
Pros:
    Clean
Cons:
    Lots of data churn

TODO
----
find subscribable events

"""


class Bindings(dict):

    def __init__(self, state):
        # List all bindable properties here
        # This will then be made into a list
        properties = []

        for item in properties:
            self[item.name] = item
