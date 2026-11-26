"""The places of the run tracing on the 2D plot, glowing over everything
else: the places of the time traces (all of them always there with their
names, placed where they cover least; the one under the mouse brighter,
the one chosen glowing, the name of the one clicked bold; points, faces,
the cells of the plasma) and which one a click is on, the line of a
profile (a dot where each value is), the chords of a set (each as its tab
says, as in the Chords section of the plots)."""

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection

from .. import theme
from ..balances.style import glow
from ..tools.chordplots import draw_chord

COLOUR = "#ff2a6d"                  # the places
WIDTH = 3.0                         # of a line (points)
ZORDER = 8.0                        # over the layers and the balances
# line width, opacity and point size of a place: faint, under the mouse,
# chosen
LOOKS = {"faint": (1.8, 0.7, 8.0), "hover": (2.4, 0.9, 9.0),
         "on": (WIDTH, 1.0, 11.0)}
AREA = {"hover": 0.1, "on": 0.22}   # opacity of the cells of the plasma
REACH = 8.0                         # pixels: a click on a place
GAP = 10.0                          # points from a place to its name


def hit(ax, shapes, keys, x, y):
    """The place of keys (shapes: Marks.places) within REACH pixels of the
    point (x, y) of the plot, the nearest; None if there is none."""
    p = ax.transData.transform([(x, y)])[0]
    best, near = None, REACH
    for k in keys:
        kind, data = shapes.get(k, (None, None))
        if kind == "point":
            d = np.hypot(*(ax.transData.transform(data)[0] - p))
        elif kind == "lines" and len(data):
            a = ax.transData.transform(data[:, 0])
            b = ax.transData.transform(data[:, 1])
            ab = b - a
            t = np.clip(np.einsum("ij,ij->i", p - a, ab) / np.maximum(
                np.einsum("ij,ij->i", ab, ab), 1e-12), 0.0, 1.0)
            d = np.min(np.hypot(*(a + t[:, None] * ab - p).T))
        else:
            continue
        if d < near:
            best, near = k, d
    return best


def _around(d):
    """The direction d (unit vector) and those around it by 45 degrees,
    the nearest first."""
    a = np.arctan2(d[1], d[0])
    return [np.array((np.cos(a + s * np.pi / 4), np.sin(a + s * np.pi / 4)))
            for s in (0, 1, -1, 2, -2, 3, -3, 4)]


def _spot(ann, u):
    """The name ann GAP points from its place in the direction u."""
    ann.xyann = (GAP * u[0], GAP * u[1])
    ann.set_ha("left" if u[0] > 0.38 else "right" if u[0] < -0.38 else
               "center")
    ann.set_va("bottom" if u[1] > 0.38 else "top" if u[1] < -0.38 else
               "center")


class Marks:
    """The marks of the run tracing on the plot of a Tab2D."""

    def __init__(self, tab):
        self.tab = tab
        self.artists = []
        self.shown = False
        self.names = []                 # [(annotation, point, away, key)]
        self.centre = None              # of the grid (the names around it)
        self.keep_off = np.empty((0, 2))   # points the names do not cover
        self.spots = {}                 # (text, point) -> direction
        self.view = None                # the view of the spots
        tab.canvas.mpl_connect("draw_event", self._drawn)

    def clear(self):
        for a in self.artists:
            try:
                a.remove()
            except (ValueError, NotImplementedError):   # axes cleared
                pass
        self.artists = []
        self.names = []

    def set_shown(self, on):
        self.shown = on
        for a in self.artists:
            a.set_visible(on)
        self.tab.canvas.draw_idle()

    def _add(self, artist):
        artist.set_visible(self.shown)
        self.artists.append(artist)

    def show(self, place=None, label="", chords=(), chosen=None,
             hover=None):
        """place: ("point", (1, 2)) or ("line", (n, 2)) with its label, or
        chords: [(number, [(n, 2) parts], look)], each drawn as its tab
        says (chordplots.draw_chord), the one numbered chosen glowing in
        its colour, the one hover lighter."""
        self.clear()
        ax = self.tab.plot.ax
        colour = theme.rgb(COLOUR)
        if place is not None:
            kind, xy = place
            ok = np.isfinite(xy).all(axis=1)
            xy = xy[ok]
            if not len(xy):
                return self._done()
            if kind == "line":
                line, = ax.plot(xy[:, 0], xy[:, 1], color=colour,
                                linewidth=WIDTH, solid_capstyle="round",
                                zorder=ZORDER)
                line.set_path_effects(glow(WIDTH, COLOUR, on_map=True))
                dots, = ax.plot(xy[:, 0], xy[:, 1], linestyle="none",
                                marker="o", markersize=1.8, color="white",
                                zorder=ZORDER + 0.1)
                self._add(line)
                self._add(dots)
                at = xy[np.argmax(xy[:, 1])]    # the label at the top end
            else:
                dot, = ax.plot(xy[:, 0], xy[:, 1], linestyle="none",
                               marker="o", markersize=11, color=colour,
                               markeredgecolor="white", markeredgewidth=1.5,
                               zorder=ZORDER + 0.2)
                dot.set_path_effects(glow(5.5, COLOUR, strong=True,
                                          on_map=True))
                self._add(dot)
                at = xy[0]
            if label:
                self._label(ax, label, at, colour)
        for number, parts, look in chords:
            lit = number == chosen or number == hover
            for xy in parts if lit else ():     # the glow under it, solid
                halo, = ax.plot(xy[:, 0], xy[:, 1], color=theme.rgb(
                    look[0]), linestyle="-", linewidth=look[1],
                    solid_capstyle="round", zorder=ZORDER + 0.4)
                halo.set_path_effects(glow(look[1], look[0], strong=number
                                           == chosen, on_map=True)[:-1])
                self._add(halo)         # (its strokes only: the chord over
            drawn = draw_chord(ax, number, parts, look,     # it as it is)
                               zorder=ZORDER + (0.5 if lit else 0.0))
            if lit:                     # its first dot
                drawn[len(parts)].set_path_effects(glow(
                    look[1], look[0], strong=number == chosen,
                    on_map=True))
            for a in drawn:
                self._add(a)
        return self._done()

    def _label(self, ax, label, at, colour, bold=True):
        """The label of a place at the point at, on the side with more
        room."""
        left = at[0] > np.mean(ax.get_xlim())
        ann = ax.annotate(
            label, xy=at, xytext=(-12 if left else 12, 10),
            textcoords="offset points", ha="right" if left else "left",
            color=colour, fontsize=9,
            fontweight="bold" if bold else "normal",
            zorder=ZORDER + 0.3, annotation_clip=True,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=colour,
                      lw=1.2 if bold else 0.6, alpha=0.85))
        self._add(ann)
        return ann

    def places(self, shapes, shown, chosen=(), hover=None, names=(),
               centre=None):
        """shapes: {key: ("point", (1, 2)), ("lines", (n, 2, 2) segments)
        or ("area", [polygons])}; those of shown faint, hover brighter,
        those of chosen glowing; names: [(key, text, point, away, bold)] of
        the places, away from the centre of the grid or toward it where
        they cover least (bold: the place clicked); hover a key or a tuple
        of keys (a region: its outline and its cells)."""
        self.clear()
        ax = self.tab.plot.ax
        colour = theme.rgb(COLOUR)
        hovers = [k for k in (hover if isinstance(hover, tuple) else
                              (hover,)) if k is not None and k not in chosen]
        looks = [(k, "faint") for k in shown if k not in chosen and
                 k not in hovers] + [(k, "hover") for k in hovers] + [
            (k, "on") for k in chosen]
        for k, how in looks:
            if k in shapes:
                self._shape(ax, shapes[k], how, colour)
        self.centre = centre
        keep = [np.asarray(d, float).reshape(-1, 2) for k, (kind, d) in
                shapes.items() if kind != "area"] + \
            [np.asarray(d, float).mean(axis=1) for kind, d in
             shapes.values() if kind == "lines" and len(d)]
        self.keep_off = np.concatenate(keep) if keep else np.empty((0, 2))
        for key, text, at, away, bold in names:
            self.names.append((self._label(ax, text, at, colour, bold), at,
                               away, key))
        known = [self.spots.get(self._key(n)) for n in self.names]
        if self.view == self._view() and all(u is not None for u in known):
            for (ann, *_), u in zip(self.names, known):
                _spot(ann, u)
        else:
            self._place()
        return self._done()

    @staticmethod
    def _key(name):
        ann, at = name[:2]
        return ann.get_text(), float(at[0]), float(at[1])

    def _view(self):
        ax = self.tab.plot.ax
        return (tuple(ax.get_xlim()), tuple(ax.get_ylim()),
                tuple(np.round(ax.bbox.bounds, 1)))

    def _place(self, renderer=None):
        """The names where they cover least: inside the plot, off each
        other, off the places, on the side wanted (away from the centre or
        toward it) or the nearest one; for the view of now."""
        ax = self.tab.plot.ax
        self.view, self.spots = self._view(), {}
        if not self.names or self.centre is None:
            return
        try:
            renderer = renderer or self.tab.canvas.get_renderer()
        except AttributeError:          # no renderer: the side wanted
            renderer = None
        box = ax.get_window_extent(renderer)
        pts = ax.transData.transform(self.keep_off) if \
            len(self.keep_off) else np.empty((0, 2))
        c = ax.transData.transform([self.centre])[0]
        taken = []
        for name in self.names:
            ann, at, away, _ = name
            d = (ax.transData.transform([at])[0] - c) * (1 if away else -1)
            n = np.hypot(*d)
            d = d / n if n > 0 else np.array((1.0, 0.0))
            if renderer is None:
                _spot(ann, d)
                continue
            shown, weight = ann.get_visible(), ann.get_fontweight()
            ann.set_visible(True)
            ann.set_fontweight("bold")  # the widest
            best = None
            for k, u in enumerate(_around(d)):
                _spot(ann, u)
                bb = ann.get_window_extent(renderer).padded(4)
                out = bb.x0 < box.x0 or bb.x1 > box.x1 or \
                    bb.y0 < box.y0 or bb.y1 > box.y1
                cover = np.count_nonzero(
                    (pts[:, 0] > bb.x0) & (pts[:, 0] < bb.x1) &
                    (pts[:, 1] > bb.y0) & (pts[:, 1] < bb.y1))
                cost = 1000 * out + 100 * sum(bb.overlaps(t) for t in
                                              taken) + 2 * cover + k
                if best is None or cost < best[0]:
                    best = (cost, u, bb)
            _spot(ann, best[1])
            ann.set_visible(shown)
            ann.set_fontweight(weight)
            taken.append(best[2])
            self.spots[self._key(name)] = best[1]

    def name_at(self, x, y):
        """The key of the name of a place at the pixel (x, y) of the plot
        (its box), or None."""
        if not self.shown:
            return None
        try:
            renderer = self.tab.canvas.get_renderer()
        except AttributeError:
            return None
        for ann, _, _, key in self.names:
            bb = ann.get_window_extent(renderer).padded(3)  # its box
            if bb.width > 8 and bb.contains(x, y):      # not hidden
                return key
        return None

    def _drawn(self, event):
        """After a draw in another view (zoom, pan, size): the names placed
        again for it."""
        if self.names and self.shown and self._view() != self.view:
            self._place(event.renderer)
            self.tab.canvas.draw_idle()

    def _shape(self, ax, shape, how, colour):
        kind, data = shape
        width, alpha, size = LOOKS[how]
        if kind == "point":
            a, = ax.plot(data[:, 0], data[:, 1], linestyle="none",
                         marker="o", markersize=size, color=colour,
                         markeredgecolor="white", alpha=alpha,
                         markeredgewidth=0.8 if how == "faint" else 1.5,
                         zorder=ZORDER + 0.2)
            if how != "faint":
                a.set_path_effects(glow(0.5 * size, COLOUR, strong=how ==
                                        "on", on_map=True))
        elif kind == "lines":
            a = LineCollection(data, colors=[colour], linewidths=width,
                               alpha=alpha, capstyle="round", zorder=ZORDER)
            if how != "faint":
                a.set_path_effects(glow(width, COLOUR, strong=how == "on",
                                        on_map=True))
            ax.add_collection(a, autolim=False)
        elif how != "faint":
            a = PolyCollection(data, facecolors=[colour], edgecolors="none",
                               alpha=AREA[how], zorder=ZORDER - 1.0)
            ax.add_collection(a, autolim=False)
        else:
            return
        self._add(a)

    def _done(self):
        self.tab.canvas.draw_idle()
