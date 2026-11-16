"""The records of the view calls, taken from the library in the order of
the calls: drawing records go to the picture of their view, messages,
notifications and the end of a view to its window, at the moment the core
makes the call (the library calls back after each of them).

Handling a notification may call the core again, which adds records and
calls back: process() is re-entrant and empties the list of the library
only when the outermost call ends."""

import numpy as np

from ..core import api

PYF_HIDDEN, PYF_CLIPPED, PYF_HLMODE = 1, 2, 4
EVENT_OPS = np.array([ord(c) for c in "SNFU"])


class Pump:
    def __init__(self, lib):
        self.lib = lib
        self.views = {}          # number of the view -> its window
        self.done = 0
        self.depth = 0
        self.recorders = []      # functions(recs, text) seeing every record
        self._proc = api.EVENTPROC(self._event)
        lib.dll.SetPyEventProc(self._proc)

    def _event(self, view_ptr):
        self.process()

    def process(self):
        """Draws and handles the records made since the last call."""
        self.depth += 1
        try:
            while True:
                recs, text = self.lib.take_records(self.done)
                if not len(recs):
                    break
                events = np.nonzero(np.isin(recs["op"], EVENT_OPS))[0]
                upto = int(events[0]) + 1 if len(events) else len(recs)
                chunk = recs[:upto]
                self.done += upto
                for rec in self.recorders:
                    rec(chunk, text)
                for vid in np.unique(chunk["view"]):
                    window = self.views.get(int(vid))
                    if window is not None:
                        window.draw_records(chunk, text, int(vid))
                if len(events):
                    self._handle(chunk[-1], text)
        finally:
            self.depth -= 1
        if self.depth == 0:
            self.lib.dll.ResetPyRecs()
            self.done = 0

    def _handle(self, r, text):
        window = self.views.get(int(r["view"]))
        if window is None:
            return
        op = chr(r["op"])
        if op == "S":
            if r["j"] < 0:
                window.set_message(None)
            else:
                off = int(r["i"])
                window.set_message(
                    text[off:off + int(r["j"])].decode("latin-1"))
        elif op == "N":
            window.notify(int(r["i"]), int(r["obj"]) or None, int(r["j"]))
        elif op == "F":
            window.flush()
        elif op == "U":
            window.unconfigured()
