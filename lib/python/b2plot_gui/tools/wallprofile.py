"""The wall quantity plotted in the final state as a function of the
distance along the wall, on the B2.5 wall elements (an EIRENE wall
quantity on those of its elements), with its integral and average over
their area above it: the last section of the quantity column, under the
chords, overlay and statistics sections; its figure has the options of a
line profile, Save plot and Export."""

import numpy as np

from ...b2plot import labels
from ...qt import QtWidgets
from .. import catalog
from ..model import split_unit
from ..plot.overlays import wall_segments, wall_values
from ..scaling import squeezable
from . import measure
from .figure import FigureView
from .sections import _button, _text

XLABEL = "distance along the wall (m)"
AREA = catalog.Quantity("wallarea", "Wall area (m^{2})", "Geometry", "wall")


def along(seg):
    """Distance along the wall of the middle of each element [(n, 4)
    r1, z1, r2, z2] (as walldist of b2plot: the gaps between elements
    counted) and where an element does not start at the end of the one
    before it."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    length = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    gap = np.hypot(seg[1:, 0] - seg[:-1, 2], seg[1:, 1] - seg[:-1, 3])
    step = 0.5 * (length[1:] + length[:-1]) + gap
    dist = 0.5 * length[:1].sum() + np.concatenate(([0.0], np.cumsum(step)))
    return dist[:len(seg)], np.concatenate(([False], gap > 1e-4 * max(
        float(length.max(initial=0.0)), 1e-12)))[:len(seg)]


def toroidal_area(seg):
    """Area of each element turned around the axis (m^2)."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    return np.pi * (seg[:, 0] + seg[:, 2]) * np.hypot(
        seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])


class WallProfile(QtWidgets.QGroupBox):
    """The section: the integral and average with Save plot and Export at
    their right, the figure under them."""

    def __init__(self, settings, parent=None):
        super().__init__("Wall profile", parent)
        self.text = _text()
        self.view = FigureView(settings)
        self.view.options.xaxes = False     # the distance along the wall
        self.key = None
        self.asked = None               # the run asked for the areas
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.text, 1)
        row.addWidget(_button("Save plot", "The wall profile as an image or "
                              "vector file", lambda: self.view.save()))
        row.addWidget(_button("Export…", "The wall profile as a CSV file",
                              lambda: self.view.export()))
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addLayout(row)
        lay.addWidget(self.view)
        squeezable(self)

    def follow(self, tab):
        """Shown with the wall quantity plotted in the final state (the
        areas of the B2.5 wall elements asked for once per run; those of
        a field with its own segments turned around the axis)."""
        w, q, run = tab.wall_data, tab.wall_wanted, tab.run
        show = run is not None and w is not None and q is not None and \
            tab.time_box.source.currentIndex() == 0    # Final state
        if show and getattr(w, "segments", None) is None:
            d = run.cache.get(("wfield", AREA.name, (), None))
            if d is None and self.asked is not run:
                self.asked = run
                tab.request.emit(("tools", AREA, (), None))
            area = None if d is None else np.ravel(np.asarray(d.values,
                                                              float)[0])
        elif show:
            area = toroidal_area(w.segments)
        show = show and area is not None and len(area) > 0
        self.setVisible(bool(show))
        if not show:
            return
        cols = tab._wall_pair()[1].columns
        unit = labels.any_to_plain(split_unit(q.description)[1] or
                                   getattr(w, "unit", "") or "")
        name = tab._name_of(q, w)
        self.show_profile((id(run), id(w), name, len(area)), name, unit,
                          wall_values(w, cols), wall_segments(run, w), area,
                          q.name)

    def show_profile(self, key, name, unit, values, seg, area, what):
        """values (plain unit) on the elements seg with their areas (the
        first len(area) elements of the quantity), name its title, what
        its label (file name); nothing done again for the same key."""
        if key == self.key:
            return
        self.key = key
        n = min(len(area), len(seg), len(values))
        v = np.asarray(values, float)[:n]
        seg = np.asarray(seg, float)[:n]
        area = np.asarray(area, float)[:n]
        x, gaps = along(seg)
        ok = np.isfinite(v) & np.isfinite(area)
        total = float(np.sum(v[ok] * area[ok]))
        a = float(np.sum(area[ok]))
        html = measure.html_unit
        self.text.setText("<br>".join((
            "Integral over the B2.5 wall: %.5g %s" % (
                total, html(measure.times_m(unit, 2))),
            "Average over the B2.5 wall: %.5g %s" % (
                total / a if a > 0 else np.nan, html(unit)))))
        cut = np.flatnonzero(gaps)      # the pieces of the wall apart
        xs, ys = np.insert(x, cut, np.nan), np.insert(v, cut, np.nan)

        def draw(ax, options):
            ax.set_title(name, fontsize="medium")
            ax.plot(xs, ys)
            if n > 1:
                ax.set_xlim(x[0], x[-1])
            ax.set_xlabel(XLABEL)
            ax.set_ylabel(measure.math_unit(unit))
        r, z = 0.5 * (seg[:, 0] + seg[:, 2]), 0.5 * (seg[:, 1] + seg[:, 3])
        self.view.set_figure(
            draw, [XLABEL, "R (m)", "Z (m)", "area (m^2)",
                   "value (%s)" % unit],
            [list(row) for row in zip(x, r, z, area, v)], kind="line",
            name="wall_" + what)

    def clear(self):
        self.key = None
