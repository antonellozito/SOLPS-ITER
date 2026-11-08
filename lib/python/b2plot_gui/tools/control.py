"""What the mouse tools of a 2D tab do with the shapes drawn: the cell
inspector, the line cut and the statistics in the results panel, the
seed line of the streamlines."""

import numpy as np

from ...b2plot import labels
from ..model import split_unit
from . import inspect, measure
from .base import MouseTools
from .results import ResultsPanel

VOLUMES = {"cells": ("field", "vol"), "triangles": ("efield", "triavol")}
WHERE = {"shown": "the cells shown", "box": "the box",
         "polygon": "the polygon"}


class Tools:
    """Mouse bar and results panel of a Tab2D (its run, data, plot)."""

    def __init__(self, tab):
        self.tab = tab
        self.bar = MouseTools(tab.canvas, tab.plot, tab.toolbar)
        self.panel = ResultsPanel(tab.settings)
        self.bar.done.connect(self._done)
        self.bar.shown.connect(lambda: self._done("shown", None))
        self.bar.hint.connect(tab.status)
        for key in ("inspect", "box", "polygon"):
            self.bar.buttons[key].toggled.connect(
                lambda on: on and self._load())
        self.last, self.waiting = None, False

    def _load(self):
        """Ask b2plot for the default quantities of the inspector and the
        volumes (kept in the cache once loaded)."""
        tab = self.tab
        for name in inspect.DEFAULTS:
            q = next((q for q in tab.final_quantities if q.name == name),
                     None)
            if q is not None:
                tab.request.emit(("tools", q, (), None))

    def deliver(self, data):
        """A quantity the tools asked for arrived (None: b2plot failed):
        the result again."""
        if data is None:
            self.waiting = False
        elif self.last is not None and (self.waiting or
                                        self.panel.isVisible()):
            self._done(*self.last)

    def _done(self, mode, pts):
        tab = self.tab
        if mode == "seeds":
            (x0, y0), (x1, y1) = pts
            t = np.linspace(0.0, 1.0, tab.quantity.streams.nseeds.value())
            tab.quantity.set_seeds(list(zip(x0 + t * (x1 - x0),
                                            y0 + t * (y1 - y0))))
            tab.status.emit("Seed line set")
            return
        if tab.run is None or (mode != "inspect" and not tab._current()):
            tab.status.emit("No plot to measure")
            return
        self.last = (mode, pts)
        if mode == "inspect":
            names = {q.name: q.label for q in tab.final_quantities
                     + tab.movie_quantities}
            x, y = pts[0]
            self.panel.show_table(
                "Cell at R %.4f m, Z %.4f m" % (x, y), inspect.HEADER,
                inspect.rows(tab.run, tab.plot, x, y, names,
                             tab._species()))
        elif mode == "line":
            self._line(pts)
        else:
            self._statistics(mode, pts)

    def _what(self):
        """Name of the quantity shown, with its species."""
        tab = self.tab
        text = tab.wanted.label
        if tab.quantity.species.count() > 1:
            text += " [%s]" % tab.quantity.species.currentText()
        return text

    def _line(self, pts):
        tab = self.tab
        data = tab.data
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        s, r, z, v, vn = measure.profile(tab.plot, data, pts[0], pts[1])
        inside, total, mean, flux = measure.line_sums(s, r, v, vn)
        text = ("Inside the cells shown: %.4g m of %.4g m.  Integral %.5g %s,"
                "  average %.5g %s" % (inside, s[-1], total, plain(
                    measure.times_m(unit, 1)), mean, plain(unit)))
        if vn is not None and measure.PER_M.search(unit) and \
                measure.PER_M.search(unit).group(1) == "2":
            text += (".  Flux through the surface the line sweeps around "
                     "the axis (2πR v·n, n to the right of the "
                     "line): %.5g %s" % (flux, plain(measure.times_m(
                         unit, 2))))
        elif vn is not None:
            text += ".  No flux: the unit is not a flux density (m^-2)"

        def draw(ax):
            ax.plot(s, v, label="|v|" if vn is not None else None)
            if vn is not None:
                ax.plot(s, vn, label="v·n")
                ax.legend(fontsize="small")
            ax.set_xlabel("distance along the line (m)")
            ax.set_ylabel(plain(unit))
            ax.grid(alpha=0.3)
        (x0, y0), (x1, y1) = pts
        header = ["s (m)", "R (m)", "Z (m)", "value (%s)" % plain(unit)] + (
            ["normal component (%s)" % plain(unit)] if vn is not None else [])
        rows = [list(row) for row in zip(s, r, z, v)] if vn is None else \
            [list(row) for row in zip(s, r, z, v, vn)]
        self.panel.show_figure(
            "Line from (%.4f, %.4f) to (%.4f, %.4f) m: %s" % (
                x0, y0, x1, y1, self._what()), text, draw, header, rows)

    def _statistics(self, mode, pts):
        tab = self.tab
        data, plot, g = tab.data, tab.plot, tab.run.geometry
        kind, name = VOLUMES[data.location]
        vol = tab.run.cache.get((kind, name, (), None))
        if vol is None:
            q = next((q for q in tab.final_quantities if q.name == name),
                     None)
            if q is None:
                tab.status.emit("Statistics need the volumes (b2plot %s)"
                                % name)
            elif not self.waiting:
                self.waiting = True
                tab.status.emit("Loading the volumes (b2plot %s)…"
                                % name)
                tab.request.emit(("tools", q, (), None))
            return
        self.waiting = False
        idx = measure.chosen(plot, data, pts)
        cells = data.location == "cells"
        i = g.cells[idx] - 1 if cells else idx
        values = measure.values_at(plot, data, idx)
        volumes = np.asarray(vol.values[0], float)[i]
        st = measure.statistics(values, volumes)
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        text = ("%d %s, volume %.5g m^3.  Volume integral %.5g %s,  volume "
                "average %.5g %s,  minimum %.5g,  maximum %.5g" % (
                    st["n"], "cells" if cells else "triangles", st["volume"],
                    st["integral"], plain(measure.times_m(unit, 3)),
                    st["average"], plain(unit), st["min"], st["max"]))
        ok = np.isfinite(values)

        def draw(ax):
            v = values[ok]
            if not v.size:
                return
            log = plot.style.scale == "log" and v.min() > 0
            bins = np.geomspace(v.min(), v.max(), 31) if log and \
                v.max() > v.min() else 30
            ax.hist(v, bins=bins, color="#4c72b0")
            if log:
                ax.set_xscale("log")
            ax.set_xlabel(plain(unit))
            ax.set_ylabel("cells" if cells else "triangles")
        centres = g.centres[idx] if cells else plot.ecentres[idx]
        rows = [[int(n), c[0], c[1], w, x] for n, c, w, x in zip(
            g.cells[idx] if cells else idx + 1, centres, volumes, values)]
        self.panel.show_figure(
            "Statistics over %s: %s" % (WHERE[mode], self._what()), text,
            draw, ["cell" if cells else "triangle", "R (m)", "Z (m)",
                   "volume (m^3)", "value (%s)" % plain(unit)], rows)
