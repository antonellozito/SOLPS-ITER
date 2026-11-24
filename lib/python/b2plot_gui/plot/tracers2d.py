"""Tracers of the 2D plot (vector plot type Tracers): points moving with
the poloidal flow of the vector quantity (its R and Z components, gridded
over the data), each with a tail of its last positions fading towards
the background, the heads coloured by the magnitude; the tracers, options
and defaults of the 3D view (tools/tracers). Drawn by blitting over the
rest of the plot (kept from its last full draw), about 30 frames a second
while the plot is shown and not paused, and drawn with the rest in the
files saved; on a plot of a figure not on the screen (export, page
composer) drawn once where they are. The speed is relative to the view
(the fastest cross a quarter of it in a second)."""

import numpy as np
from matplotlib import colors as mcolors
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm, Normalize

from .. import theme
from ..tools import births, vector3d as v3
from ..tools.tracers import FADE, FRAME, Field, Tracers, colour_range
from ...qt import QtCore

FRAME_MS = round(1000 * FRAME)
ZORDER = 5.1                    # over the plasma plot, under the layers


def _on_screen(artist):
    """get_animated of an artist moved by blitting: True but while its
    figure is saved to a file (then drawn with the rest)."""
    def animated():
        fig = artist.figure
        return not (fig is not None and fig.canvas.is_saving())
    return animated


class Tracers2D:
    """The tracers of one vector field and style on a Plot2D; valid
    False when there is nothing to move (zero field, no line to be born
    on)."""

    def __init__(self, plot, key, tri, nu, nw, st, box, cmap):
        self.plot, self.key, self.st = plot, key, st
        self.paused, self.bg, self.cid = False, None, None
        xs, ys, f = v3.resample(tri, (nu, nw, np.zeros_like(nu)), box)
        field = Field(xs, ys, f)
        born = st.tr_born
        lines = births.lines(plot.run, born, st.seeds) \
            if born in births.LINES else None
        self.valid = field.valid and np.isfinite(field.v98) and \
            field.v98 > 0 and not (born in births.LINES and not lines)
        self.artists, self.heads = [], None
        if not self.valid:
            return
        log = bool(st.tr_log)
        self.tr = Tracers(field, int(st.tr_n), int(st.tr_tail), 0.0, 0.0,
                          np.random.default_rng(7), (None, None),
                          births.weight(born), FADE if st.tr_fade else 0.0,
                          lines, self.vref(), log,
                          0.0 if st.auto else max(float(st.vmin), 0.0))
        self.tr.warm_up(self.vref(), log)
        clog = st.scale == "log"        # the colour scale of the options
        lo, hi = colour_range(field, None if st.auto else
                              (st.vmin, st.vmax), clog)
        self.norm = LogNorm(lo, hi) if clog else Normalize(lo, hi)
        self.cmap = cmap
        size = float(st.tr_size)
        self.tails = LineCollection(self._segments(),
                                    linewidths=0.6 * size,
                                    capstyle="round", animated=True,
                                    zorder=ZORDER)
        self.heads = plot.ax.scatter(
            self.tr.hist[0, :, 0], self.tr.hist[0, :, 2],
            s=(1.6 * size) ** 2, c=np.maximum(self.tr.mag, 1e-300),
            cmap=cmap, norm=self.norm, linewidths=0.0, animated=True,
            zorder=ZORDER + 0.01)
        self.heads.remove()             # added by attach
        self._colour()
        self.artists = [self.tails, self.heads]
        canvas = plot.ax.figure.canvas
        self.live = hasattr(canvas, "isVisible")    # on the screen
        for a in self.artists:          # left to the blits, but saved
            a.set_animated(self.live)
            if self.live:
                a.get_animated = _on_screen(a)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(FRAME_MS)
        self.timer.timeout.connect(self._tick)

    def vref(self):
        """Reference speed (m/s): a quarter of the view a second."""
        x0, x1, y0, y1 = self.plot.get_view()
        return float(self.st.tr_speed) * max(x1 - x0, y1 - y0) / 4.0

    def _segments(self):
        h = self.tr.hist                    # (tail, n, 3): newest first
        p = np.stack((h[:, :, 0], h[:, :, 2]), axis=-1)
        return np.stack((p[:-1], p[1:]), axis=2).reshape(-1, 2, 2)

    def _colour(self):
        """Heads by the magnitude, tails fading towards the background."""
        m = np.maximum(np.nan_to_num(self.tr.mag), 1e-300)
        base = np.asarray(self.cmap(self.norm(m)))[:, :3]
        bg = mcolors.to_rgb(theme.axes_bg())
        c = self.tr.colors(base, bg)[:(self.tr.tail - 1) * self.tr.n]
        self.tails.set_color(np.clip(c, 0.0, 1.0))
        self.heads.set_array(m)

    # ---------------------------------------------------------- drawing
    def attach(self):
        """The artists on the axes and the animation running."""
        if not self.valid:
            return []
        ax = self.plot.ax
        for a in self.artists:
            ax.add_collection(a, autolim=False)
        if not self.live:
            return list(self.artists)
        canvas = ax.figure.canvas
        if self.cid is None:
            self.cid = canvas.mpl_connect("draw_event", self._drawn)
        self.bg = None
        self.timer.start()
        return list(self.artists)

    def detach(self):
        """The animation stopped (the artists are removed by the plot)."""
        if not self.valid or not self.live:
            return
        self.timer.stop()
        if self.cid is not None:
            self.plot.ax.figure.canvas.mpl_disconnect(self.cid)
            self.cid = None
        self.bg = None

    def _drawn(self, event):
        """After a full draw (the tracers left out): the background kept,
        the tracers drawn over it once the draw is over (not from inside
        the paint of the canvas)."""
        canvas = self.plot.ax.figure.canvas
        self.bg = canvas.copy_from_bbox(self.plot.ax.bbox)
        QtCore.QTimer.singleShot(0, self._blit)

    def _blit(self):
        ax = self.plot.ax
        if self.bg is None or self.tails.axes is None:
            return
        canvas = ax.figure.canvas
        canvas.restore_region(self.bg)
        ax.draw_artist(self.tails)
        ax.draw_artist(self.heads)
        canvas.blit(ax.bbox)

    def _tick(self):
        canvas = self.plot.ax.figure.canvas
        if self.paused or self.bg is None or not canvas.isVisible() or \
                getattr(canvas, "held", False):
            return
        self.tr.step(FRAME, self.vref(), bool(self.st.tr_log))
        self.tails.set_segments(self._segments())
        self.heads.set_offsets(np.column_stack((self.tr.hist[0, :, 0],
                                                self.tr.hist[0, :, 2])))
        self._colour()
        self._blit()

    def set_paused(self, on):
        self.paused = bool(on)
