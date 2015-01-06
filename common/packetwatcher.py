
from threading import Lock, Thread
from time import sleep

from .list import List as list
from .event import Event

TIMEOUTMULT = 3
"""Multiplier as to how long it takes for a ping to time out"""


class PacketWatcher():
    """
    Watches all sent packets and resends if they are considered 'lost'.

    .. attribute:: on_resend

        Event thrown if a resend is detected.
        (:class:`~common.SentPacket) => ()
    """

    #: Time to sleep in between resend sweeps
    _sleep_time = 0.2

    def __init__(self):
        self._packets = list()
        self._action_list = list()
        self._rm_dict = list()
        self.on_resend = Event()

        self._lock = Lock()
        self._thread = Thread(target=self._sweep)
        self._thread.daemon = True
        self._thread.start()

    def _sweep(self):
        """
        Target for a separate thread.
        Only 1 thread may run this function.

        Sweeps through all of the recently sent packets.
        Checks for any that are stale (need resending)
        or any that have been awk'ed.
        """
        while True:
            with self._lock:
                for action, param in self._action_list:
                    action(param)
                self._action_list = list()
            # Remove awked packets
            removed, self._packets = self._packets.split(
                lambda x: x.info in self._rm_dict)
            self._rm_dict = {}
            for pkt in removed:
                pkt.contact.change_ping(pkt.rtt)
            # Remove dead packets
            dead, self._packets = self._packets.split(
                lambda x: x.ctt > x.contact.ping * TIMEOUTMULT)
            for pkt in dead:
                print("DEAD PACKET: %s > %s" % (pkt.ctt, pkt.contact.ping))
                pkt.contact.change_liveliness()
                if pkt.contact.is_alive:
                    self.on_resend(pkt)
            # Sleep a little bit before sweeping again
            sleep(self._sleep_time)

    def rm_packet(self, pkt_id, channel):
        with self._lock:
            self._action_list.append((self._rm_packet,
                                     (pkt_id, channel)))

    def _rm_packet(self, pkt_info):
        self._rm_dict[pkt_info] = True

    def add_packet(self, packet):
        with self._lock:
            self._action_list.append((self._add_packet,
                                      packet))

    def _add_packet(self, packet):
        """
        This has to be a separate function so the
        action in the action list refers to the correct list.
        self._packets gets rebuilt a lot as new lists.
        """
        self._packets.append(packet)
