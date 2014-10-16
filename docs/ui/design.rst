UI Design
=========

The UI is designed to provide updates in a pub-sub architecture.
Therefore, the workflow for getting values for a given item is as follows:
* Connect to the server
* Send a SUBSCRIBE message about a given property
* Receive initial state
* Receive any updates that may happen

To prevent flooding, updates are only sent at a rate slower or at
:attr:`~ui.server.UIServer.UPDATE_DELTA`.
If updates rapidly accumulate, the behavior is dependant on the property class overridden.

Creating 'Bindable' Objects
+++++++++++++++++++++++++++


UI Protocol
+++++++++++
