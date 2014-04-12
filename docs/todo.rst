To Do List
==========

Crypto
++++++

Implement the DH exchange!!!!!

Implement PKI for AES exchange

Kademlia
++++++++
Refresh buckets after an expiration time

Fix bug w/ empty buckets.first()

Networking
++++++++++
RELEARN HOW RETRANSMITS WORK! -> Is there any even built in?

Enforce 'AT MOST ONCE' for dropped packets; stop replay attacks with stale requests

Put a max on retransmits

Implement firewall boring - STUN / upnp / nat-pmp | PCP

Database
++++++++
Add tables for ??

GUI
+++
Make properties that the gui can subscribe to

Make a TCP stack for pushing updates

Docs
++++

Make it easy for new devs to pick up

UI
++

Start architecting the ui properties & the tcp server to push changes

Blockers
++++++++

DH - The whole proto NEEDS this in order to test the new net system
	WORKAROUND: Commit a broken DH that functionally works. How good of an idea this is... yeah... Or implement stubs.

	WORKAROUND COMMENT: Need to figure out how the proto will work... what is the network password, the gen or exponent. How do we generate a 'safe' exponent?

Finding a newblood to read the docs / try using.
Identify docs weakponts (there are lots of them)
