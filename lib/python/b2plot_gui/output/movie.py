"""Smooth movies of the 2D tab: on Play, every position of the slider is
drawn once (its frames read by b2plot, the plot drawn as for one frame)
and kept as an image of the canvas; the movie then shows these images at
the frame rate. They are kept while nothing that changes the plot
changes (quantities, options, view, layers, window size, run)."""

import json
import re
import subprocess

import numpy as np

from ...qt import QtCore, QtWidgets, Qt
from . import moviefile, state

SHARE = 0.5                     # of the memory available, for the images


def available():
    """Bytes of memory available now (Linux: MemAvailable; macOS: the
    free, inactive, speculative and purgeable pages of vm_stat), or None
    where it is not known."""
    try:
        with open("/proc/meminfo") as f:
            m = re.search(r"MemAvailable:\s+(\d+) kB", f.read())
        if m:
            return int(m.group(1)) * 1024
    except OSError:
        pass
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True,
                             timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    page = re.search(r"page size of (\d+) bytes", out)
    pages = [re.search(r"Pages %s:\s+(\d+)" % k, out) for k in (
        "free", "inactive", "speculative", "purgeable")]
    if not page or not all(pages):
        return None
    return int(page.group(1)) * sum(int(p.group(1)) for p in pages)


def budget():
    """Bytes of images at most, else the movie is played live: SHARE of
    the memory available when Play is pressed (2 GB if not known)."""
    free = available()
    return int(SHARE * free) if free else 2 * 2 ** 30
LIVE = ("time_box.pos", "time_box.play", "time_box.fps", "time_box.loop")


class MovieFrames:
    """The images of the positions of a Tab2D, drawn before playing."""

    def __init__(self, tab):
        self.tab = tab
        self.images, self.key = {}, None
        self.todo, self.back = [], None
        self.done = None                # after the images: write a file
        self._poll = QtCore.QTimer(tab)
        self._poll.setSingleShot(True)
        self._poll.setInterval(5)
        self._poll.timeout.connect(self._step)

    def _key(self):
        """What the images depend on: the plot settings without the
        position, the playing options and the automatic ranges, the masks,
        the canvas size and resolution, the run."""
        tab = self.tab
        st = state.capture(tab)
        panel = st["panel"]
        st["panel"] = {k: v for k, v in panel.items()
                       if not k.startswith(LIVE) and not (
                           k.endswith((".vmin", ".vmax")) and panel.get(
                               k.rsplit(".", 1)[0] + ".auto"))}
        #   automatic ranges show the frame on the screen: left out
        canvas = tab.canvas
        return (json.dumps(st, sort_keys=True, default=str),
                tuple(tab.mask_keys), canvas.get_width_height(physical=True),
                id(tab.run))

    def prepare(self, done=None):
        """Play pressed: True if the images are there (play them), False
        if they would take too much memory (play live), None while they
        are drawn (then start() of the time box, or done())."""
        self.done = done
        tab, tb = self.tab, self.tab.time_box
        key = self._key()
        if key != self.key:
            self.images, self.key = {}, key
        positions = tb.positions()
        w, h = tab.canvas.get_width_height(physical=True)
        size, cap = len(positions) * w * h * 4, budget()
        if size > cap:
            tab.status.emit("Too many frames to draw beforehand (%.1f GB, "
                            "%.1f GB of memory free for them): the movie "
                            "is played as the frames are read"
                            % (size / 2 ** 30, cap / 2 ** 30))
            return False
        self.todo = [p for p in positions if p not in self.images]
        if not self.todo:
            return True
        self.back = tb.pos.value()
        tab.canvas.hold(True)           # nothing shown while drawn
        tab.ask_frames(self.todo)       # b2plot reads them all at once
        self._next()
        return None

    def cancel(self):
        """Pause while the images are drawn."""
        if self.todo:
            self.todo = []
            self._poll.stop()
            self.tab.canvas.hold(False)
            self.tab.canvas.draw_idle()     # the position it stopped at

    def _next(self):
        tb = self.tab.time_box
        if not self.todo:
            self.tab.status.emit("Movie ready: %d frames" % len(
                self.images))
            self.tab.canvas.hold(False)
            if self.back is not None and self.show(self.back):
                tb.jump(self.back)      # from where Play was pressed
            if self.done is not None:
                done, self.done = self.done, None
                tb.rest()               # the plot drawn again soon
                done()
            else:
                tb.start()
            return
        tb.set_position(self.todo[0])   # read and drawn as usual
        self._poll.start()

    def _step(self):
        """The position drawn: its image kept, then the next one."""
        tab, tb = self.tab, self.tab.time_box
        if not self.todo:
            return
        p = self.todo[0]
        if tb.pos.value() != p or not tab._shown():
            self._poll.start()          # still read or drawn
            return
        tab.plot.fast_draw(blit=False)      # only what changes, not shown
        self.images[p] = tab.canvas.copy_from_bbox(tab.figure.bbox)
        self.todo.pop(0)
        n = len(tb.positions())
        tab.status.emit("Preparing the movie: %d of %d frames drawn, then "
                        "played at %d fps" % (len(self.images), n,
                                              tb.fps.value()))
        self._next()

    def save(self, path=None):
        """Save movie: the file (and its format) asked unless path is
        given, the images drawn first where missing, then written at the
        frame rate. Returns the path or None."""
        tab, tb = self.tab, self.tab.time_box
        exts = [e for e, _ in moviefile.formats()]
        if path is None:
            q = tab._plotted()
            name = re.sub(r"[^A-Za-z0-9_.+-]+", "_", q.label if q else
                          "movie") + exts[0]
            path = tab._file("Save movie", name, moviefile.filters())
            if path is None:
                return None
        if "." + path.rsplit(".", 1)[-1].lower() not in exts:
            path += exts[0]
        tb.play.setChecked(False)
        self.path = path
        ready = self.prepare(done=self._write)
        if ready is True:
            self._write()
        elif ready is False:
            return None
        return path

    def _write(self):
        """The images of all positions written to the movie file."""
        tab, tb = self.tab, self.tab.time_box
        frames = [np.asarray(memoryview(self.images[p]))
                  for p in tb.positions() if p in self.images]
        if not frames:
            return
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            moviefile.write(self.path, frames, tb.fps.value())
        except (OSError, ValueError) as err:
            tab.status.emit("Cannot write the movie: %s" % err)
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        tab.status.emit("Movie written to %s (%d frames, %d fps)"
                        % (self.path, len(frames), tb.fps.value()))

    def show(self, p, check=False):
        """The image of position p on the canvas; False if there is none
        (a change of the plot stops the movie first: Tab2D) or, with
        check, if the plot changed since it was drawn (the slider moved by
        hand)."""
        region = self.images.get(p)
        if region is None or check and self._key() != self.key:
            return False
        self.tab.canvas.restore_region(region)
        self.tab.canvas.blit(self.tab.figure.bbox)
        return True
