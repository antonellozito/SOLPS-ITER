"""What the mouse tools of a 2D tab do with the shapes drawn: the cell
inspector, the line cut and the statistics in the results panel (those of
the cells shown follow the view), the seed line of the streamlines."""

import numpy as np

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Qt
from ..model import split_unit
from . import inspect, measure
from .base import MouseTools
from .results import ResultsPanel

VOLUMES = {"cells": ("field", "vol"), "triangles": ("efield", "triavol")}
WHERE = {"shown": "the cells shown in the view", "box": "the box",
         "polygon": "the polygon"}


class Tools:
    """Mouse bar and results panel of a Tab2D (its run, data, plot)."""

    def __init__(self, tab):
        self.tab = tab
        self.bar = MouseTools(tab.canvas, tab.plot, tab.toolbar)
        self.panel = ResultsPanel(tab.settings, tab)
        self.bar.done.connect(self._done)
        self.bar.shown.connect(lambda: self._done("shown", None))
        self.bar.hint.connect(tab.status)
        for key in ("inspect", "box", "polygon"):
            self.bar.buttons[key].toggled.connect(
                lambda on: on and self._load())
        self.last, self.waiting = None, False
        self._again = QtCore.QTimer(tab)
        self._again.setSingleShot(True)
        self._again.setInterval(150)
        self._again.timeout.connect(lambda: self.last is not None and
                                    self._done(*self.last))

    def _load(self):
        """Ask b2plot for the triangle areas and volumes and the cell
        volumes (kept in the cache once loaded); the inspector reads the
        geometry files of the run once."""
        tab = self.tab
        if tab.run is None:
            return
        for name in inspect.REQUESTS + ("vol",):
            q = next((q for q in tab.final_quantities if q.name == name),
                     None)
            if q is not None:
                tab.request.emit(("tools", q, (), None))
        if self.bar.mode == "inspect":
            QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                inspect.files(tab.run)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()

    def view_changed(self):
        """The statistics of the cells shown again for a new view (once
        the view stops moving)."""
        if self.last is not None and self.last[0] == "shown" and \
                self.panel.isVisible():
            self._again.start()

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
            x, y = pts[0]
            found = inspect.groups(tab, x, y)
            if not found:               # outside every cell and triangle
                self.last = None
                return
            title = []
            for t, _ in found:
                t = t.split(":")[0]
                if t != "Quantity shown" and t not in title:
                    title.append(t)
            self.panel.show_groups(", ".join(title), inspect.HEADER, found)
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
        lines = ["Length inside the cells shown: %.4g m of %.4g m" % (
                     inside, s[-1]),
                 "Integral along the line: %.5g %s" % (
                     total, plain(measure.times_m(unit, 1))),
                 "Average along the line: %.5g %s" % (mean, plain(unit))]
        if vn is not None and measure.PER_M.search(unit) and \
                measure.PER_M.search(unit).group(1) == "2":
            lines.append("Flux through the surface the line sweeps around "
                         "the axis (2πR v·n, n to the right of the line): "
                         "%.5g %s" % (flux, plain(measure.times_m(unit, 2))))
        elif vn is not None:
            lines.append("No flux: the unit is not a flux density (m^-2)")
        text = "\n".join(lines)
        ok = np.isfinite(v)

        def draw(ax):
            ax.plot(s, v, label="|v|" if vn is not None else None)
            if vn is not None:
                ax.plot(s, vn, label="v·n")
                ax.legend(fontsize="small")
            if ok.any():                # the profile from end to end
                ax.set_xlim(s[ok].min(), s[ok].max())
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
        if mode == "shown":             # the cells shown in the view
            x0, x1, y0, y1 = plot.get_view()
            pts = np.array([(x0, y0), (x1, y1)])
        idx = measure.chosen(plot, data, pts)
        cells = data.location == "cells"
        i = g.cells[idx] - 1 if cells else idx
        values = measure.values_at(plot, data, idx)
        volumes = np.asarray(vol.values[0], float)[i]
        st = measure.statistics(values, volumes)
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        text = "\n".join((
            "%s: %d" % ("Cells" if cells else "Triangles", st["n"]),
            "Volume: %.5g m^3" % st["volume"],
            "Volume integral: %.5g %s" % (st["integral"], plain(
                measure.times_m(unit, 3))),
            "Volume average: %.5g %s" % (st["average"], plain(unit)),
            "Minimum: %.5g %s" % (st["min"], plain(unit)),
            "Maximum: %.5g %s" % (st["max"], plain(unit))))
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
