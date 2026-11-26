"""What the Field line section does: one field line at a time, picked in
the 2D plot (a click on the B2.5 grid) or in the 3D view (a click on a
cut face, its point in the poloidal plane there), the line of both views
(picked in 2D, it starts in 3D on the cut face at the start of the
sector), traced anticlockwise in the 2D plot (one poloidal turn on a
closed flux surface), drawn while the section is open; the section shows
its connection lengths, the
profile of the quantity measured (as the chords: the plasma quantity,
else the vector one, its magnitude) along it with its integral and
average, the colour bar of the line."""

import json
import math

import numpy as np

from ...b2plot import labels
from ...qt import QtWidgets, Qt
from ..model import split_unit
from ..plot import magnetic
from . import fieldlines as fl, measure
from .fieldsection import XLABELS, FieldLineSection

NO_FIELD = "No magnetic field in b2fgmtry (cvEb, or bb with crx and cry)"


def _end(line, k, way):
    if not line.hits[k]:
        return "%s: more than %.0f m" % (way, line.lengths[k])
    name = line.names[k]
    return "%s: %.2f m to %s (%.2f toroidal turns)" % (
        way, line.lengths[k], "the %s target" % name if name else
        "the edge of the grid", line.turns(k))


def connection(line, phi=None):
    """Rich text of where the line starts and its connection lengths."""
    head = "From R = %.3f m, Z = %.3f m" % line.start
    if phi is not None:
        head += ", toroidal angle %.1f°" % math.degrees(phi)
    if line.closed:
        n = max(line.turns(0), line.turns(1))
        return "<br>".join((head, "Closed field line, one poloidal turn: "
                            "%.2f m, %.2f toroidal turns (q = %.2f)" % (
                                max(line.lengths), n, n)))
    return "<br>".join((head, "Connection length: %.2f m" % sum(
        line.lengths), _end(line, 0, "against B"), _end(line, 1,
                                                        "along B")))


class FieldLineTool:
    """The Field line section of Tools (tools.tab its Tab2D)."""

    def __init__(self, tools):
        self.tools, self.tab = tools, tools.tab
        self.section = FieldLineSection(self, self.tab.settings)
        try:
            self.section.restore(json.loads(
                self.tab.settings.value("fieldline", "") or "{}"))
        except (ValueError, TypeError):
            pass
        self.section.hide()
        self.line = None
        self.phi3d = None               # toroidal angle of the 3D start
        #                                 (None: the start of the sector)
        self.artists, self.mappable = [], None
        self.open = False
        self.shown_view = None

    # ------------------------------------------------------------ state
    def view(self):
        return "3d" if self.tab.mode3d.on() else "2d"

    def reset(self):
        """A new run: no lines."""
        self.line, self.phi3d = None, None
        self.artists = []           # the axes were cleared
        if self.open:
            self.show()

    def set_open(self, on):
        """The section opened (the start picked at once) or closed."""
        self.open = on
        self.section.setVisible(on)
        self.shown_view = self.view() if on else None
        self.arm(on)
        self.draw()
        if on:
            self.show()

    def switched(self):
        """The 2D plot or the 3D view shown now: picking there, the
        section for its line."""
        if not self.open or self.view() == self.shown_view:
            return
        self.shown_view = self.view()
        self.arm(self.section.pick.isChecked())
        self.show()

    def arm(self, on):
        """Pick the start with the next clicks (on), or not."""
        bar, mode3d = self.tools.bar, self.tab.mode3d
        nav = getattr(mode3d.view, "navigator", None)
        three = self.view() == "3d"
        if on and not three:
            bar.set_mode("fieldline")
        elif bar.mode == "fieldline":
            bar.set_mode(None)
        if nav is not None:
            if on and three:
                nav.start_pick(self.picked3d, faces=True)
                self.tab.status.emit("Click a point on a cut face of the "
                                     "3D view")
            elif nav.pick == self.picked3d:
                nav.start_pick(None)
        self.section.set_armed(on)

    def modes(self):
        """The mouse mode of the 2D plot changed."""
        if self.view() == "2d":
            self.section.set_armed(self.tools.bar.mode == "fieldline")

    def restyled(self):
        self.tab.settings.setValue("fieldline", json.dumps(
            self.section.settings()))
        self.draw()
        self.show()

    # ---------------------------------------------------------- tracing
    def _field(self):
        run = self.tab.run
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            bf = fl.field_of(run, self.tab.plot)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        if bf is None:
            self.tab.status.emit(NO_FIELD)
        return bf

    def _trace(self, r, z):
        run = self.tab.run
        bf = None if run is None else self._field()
        if bf is None:
            return None
        line = fl.trace(bf, r, z, fl.directions(run)["bpol_clockwise"], run)
        if line is None:
            self.tab.status.emit("Outside the B2.5 grid")
        return line

    def picked2d(self, r, z):
        line = self._trace(r, z)
        if line is not None:
            self.line, self.phi3d = line, None
            self.draw()
            self.show()

    def picked3d(self, point):
        if point is None:
            self.tab.status.emit("Click on a cut face of the 3D view")
            return
        line = self._trace(float(np.hypot(point[0], point[1])),
                           float(point[2]))
        if line is not None:
            self.line = line
            self.phi3d = float(np.arctan2(point[1], point[0]))
            self.draw()
            self.show()

    def clear(self):
        """No field line (in both views)."""
        self.line = None
        self.draw()
        self.show()

    # ------------------------------------------------------------ drawing
    def by(self):
        return self.section.by.currentData()

    def draw(self):
        """The 2D line on the plot while the section is open."""
        for a in self.artists:
            if a.axes is not None:
                a.remove()
        self.artists, self.mappable = [], None
        line = self.line
        if self.open and line is not None and self.tab.run is not None:
            self.artists, self.mappable = magnetic.fieldline_artists(
                self.tab.plot.ax, line, self.section.look(), self.by())
        self.tab.canvas.draw_idle()
        self.tab.mode3d.follow()

    def for_3d(self):
        """(line, start angle, look, colouring) of the 3D view, or
        None."""
        if not self.open or self.line is None:
            return None
        return self.line, self._phi(), self.section.look(), self.by()

    def _phi(self):
        """Toroidal angle of the start in 3D: where it was picked there,
        else the cut face at the start of the sector."""
        return self.phi3d if self.phi3d is not None else \
            self.tab.mode3d.sector()[0]

    # ------------------------------------------------------------ section
    def show(self):
        """The section for the field line (its start angle in 3D)."""
        if not self.open:
            return
        sec, line = self.section, self.line
        if line is None:
            sec.conn.setText(
                "Click a point on a cut face of the 3D view" if
                self.view() == "3d" else "Click a point of the B2.5 grid "
                "on the plot")
            sec.profile.hide()
            sec.bar.hide()
            return
        sec.conn.setText(connection(line, self._phi() if self.view() ==
                                    "3d" else None))
        by = self.by()
        sec.bar.setVisible(by is not None)
        if by is not None:
            _, norm, cmap = magnetic.colour_scale(line, by,
                                                  sec.look()[3])
            sec.bar.show_scale(norm, cmap, XLABELS[by])
        self._profile(line)

    def _profile(self, line):
        sec, tab = self.section, self.tab
        m = self.tools._measured()
        if m is not None:
            vector = hasattr(m[0], "vr")
            mask = tab.plot.vector_mask if vector else tab.plot.mask
            if m[0].location == "cells" and mask is None:
                m = None                # not drawn yet: shown once drawn
        sec.profile.setVisible(m is not None)
        if m is None:
            return
        data, q, col, _, sent = m
        pts, k0 = line.anticlockwise()
        xs = fl.along(pts)
        key = sec.xaxis.currentData()
        x = xs[key]
        v = measure.at_points(tab.plot, data, pts[:, 0], pts[:, 1], col)
        _, total, mean, _ = measure.line_sums(x, pts[:, 0], v, None)
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        html = measure.html_unit
        per = "the toroidal turns" if key == "turns" else "the field line"
        sec.text.setText("<br>".join((
            "Integral along %s: %.5g %s" % (
                per, total, html(unit if key == "turns" else
                                 measure.times_m(unit, 1))),
            "Average along %s: %.5g %s" % (per, mean, html(unit)))))
        name = self.tools._name(q, sent)
        start = x[k0]

        def draw(ax, options):
            ax.set_title(name, fontsize="medium")
            ax.plot(x, v)
            if not line.closed:         # where the line was picked
                ax.axvline(start, color="0.5", linestyle=":",
                           linewidth=0.8, label="Start")
            if len(x) > 1 and x[-1] > x[0]:
                ax.set_xlim(x[0], x[-1])
            ax.set_xlabel(XLABELS[key])
            ax.set_ylabel(measure.math_unit(unit))
        header = [XLABELS["parallel"], XLABELS["poloidal"],
                  XLABELS["turns"], "R (m)", "Z (m)",
                  "value (%s)" % unit]
        rows = zip(xs["parallel"], xs["poloidal"], xs["turns"], pts[:, 0],
                   pts[:, 1], v)
        sec.view.set_figure(draw, header, [list(r) for r in rows],
                            kind="line", name="fieldline_" + q.name,
                            space=True)

    def apply_theme(self):
        self.draw()
        self.section.bar.apply_theme()
        if self.section.view.draw is not None:
            self.section.view.apply_theme()
