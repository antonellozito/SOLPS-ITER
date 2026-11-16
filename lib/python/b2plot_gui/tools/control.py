"""What the mouse tools of a 2D tab do with the shapes drawn: the cell
inspector in its window, the chords and the statistics in their sections
of the quantity column (both follow the quantity, species or frame
plotted: the chords the plasma or the vector quantity, the statistics the
plasma quantity; the statistics of the cells shown follow the view), the
seed
line of the streamlines. The chords stay in memory when their section is
closed; they are drawn on the plot (a dot at the start, an arrow at the
end, the number) while it is open. With the movies, Show all draws the
profiles and sums of every frame (loaded in the background, two requests
at a time, only the profiles and sums kept)."""

import numpy as np
from matplotlib.ticker import FixedLocator, FormatStrFormatter, \
    MaxNLocator

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Qt
from .. import theme
from ..model import split_unit
from ..scaling import squeezable
from . import inspect, measure
from .base import MouseTools
from .results import ResultsPanel
from ..catalog import CHORD_POINTS
from .sections import LOOK, ChordsSection, StatisticsSection

VOLUMES = {"cells": ("field", "vol"), "triangles": ("efield", "triavol")}
WHERE = {"shown": "the cells shown in the view", "box": "the box",
         "polygon": "the polygon"}
XLABELS = {"R": "R (m)", "Z": "Z (m)", "rhop": r"$\rho_p$",
           "dssep": "distance from the separatrix along the line (m)"}


class Tools:
    """Mouse bar and results panel of a Tab2D (its run, data, plot)."""

    def __init__(self, tab):
        self.tab = tab
        self.bar = MouseTools(tab.canvas, tab.plot, tab.toolbar)
        self.panel = ResultsPanel(tab.settings, tab)    # the inspector
        self.chords_section = ChordsSection(self, tab.settings)
        self.stats_section = StatisticsSection(self, tab.settings)
        for w in (self.chords_section, self.stats_section):
            w.hide()
            squeezable(w)
        self.bar.done.connect(self._done)
        self.bar.hint.connect(tab.status)
        self.bar.changed.connect(self._modes)
        self.bar.buttons["inspect"].toggled.connect(
            lambda on: on and self._load())
        self.last, self.waiting = None, False   # the inspector
        self.shown = None               # the data and column measured
        self.section = None             # "chords", "stats" or None
        self.source = "drawn"           # or "run": the *.chords files
        self.run_labels = []
        self.drawn, self.results, self.artists = [], [], []
        self.looks = {"drawn": [], "run": []}   # of each chord on the plot
        self.all_frames = None          # (shown, others) with Show all
        self.stats_last = None          # (mode, points) of the statistics
        self.show_all = False           # movies: the frames all drawn
        self.frame_results, self.frames_key = {}, None  # source -> chords
        self.queue, self.flight, self.pumping = [], set(), False
        self._frames_again = QtCore.QTimer(tab)
        self._frames_again.setSingleShot(True)
        self._frames_again.setInterval(400)
        self._frames_again.timeout.connect(self._frames_arrived)
        self._again = QtCore.QTimer(tab)
        self._again.setSingleShot(True)
        self._again.setInterval(150)
        self._again.timeout.connect(self._stats_again)

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

    # ------------------------------------------------------------ sections
    def open_section(self, which):
        """The chords, the overlay, the statistics or none in the quantity
        column."""
        self.section = which
        self.chords_section.setVisible(which == "chords")
        self.stats_section.setVisible(which == "stats")
        q = self.tab.quantity
        q.overlay_section.setVisible(which == "overlay")
        for b, key in ((q.chords_button, "chords"), (q.stats_button,
                                                     "stats"),
                       (q.overlay_button, "overlay")):
            b.blockSignals(True)
            b.setChecked(which == key)
            b.blockSignals(False)
        if self.bar.mode in ("line", "box", "polygon"):
            self.bar.set_mode(None)
        self.bar._draw([])
        if which == "stats":
            self._load()
            if self.stats_last is None:
                self.stats_last = ("shown", None)
            self._statistics(*self.stats_last)
        elif which == "chords":
            item = self.chords_section.source.model().item(1)
            item.setEnabled(bool(self.run_chords()))    # with chord files
            self._chords_all()
        self._chord_artists()

    def _modes(self):
        """The drawing buttons of the sections show the mouse mode; the
        box or polygon of the statistics stays drawn."""
        for b, mode in ((self.chords_section.draw, "line"),
                        (self.stats_section.box, "box"),
                        (self.stats_section.polygon, "polygon")):
            b.blockSignals(True)
            b.setChecked(self.bar.mode == mode)
            b.blockSignals(False)
        last = self.stats_last
        if self.section == "stats" and last is not None and \
                last[0] != "shown" and not self.bar.points:
            self.bar.show_shape(*last)

    def draw_chords(self, on):
        self.bar.set_mode("line" if on else None)

    def draw_statistics(self, mode, on):
        self.bar.set_mode(mode if on else None)

    def statistics_of(self, mode):
        self.bar.set_mode(None)
        self.stats_last = (mode, None)
        self._statistics(mode, None)

    def data_changed(self):
        """A new quantity, species or frame plotted (plasma, vector or
        wall): the open section and the inspector again for it (the same
        chords, box, polygon, view or cell)."""
        tab = self.tab
        key = (id(tab.data), tab.plot.style.column)
        q = tab.quantity
        for data, menu in ((tab.vector_data if tab.vector_wanted else None,
                            q.vector_species),
                           (tab.wall_data if tab.wall_wanted else None,
                            q.wall_species)):
            key += (id(data), None if data is None else
                    tab._columns(data, menu))
        if key == self.shown:
            return
        self.shown = key
        self._refresh()

    def _refresh(self):
        if self.section == "chords":
            self._chords_all()
        elif self.section == "stats" and self.stats_last is not None:
            self._statistics(*self.stats_last)
        if self.last is not None and self.panel.isVisible():
            self._done(*self.last)

    def view_changed(self):
        """The statistics of the cells shown again for a new view (once
        the view stops moving)."""
        if self.section == "stats" and self.stats_last is not None and \
                self.stats_last[0] == "shown":
            self._again.start()

    def _stats_again(self):
        if self.section == "stats" and self.stats_last is not None:
            self._statistics(*self.stats_last)

    def deliver(self, data):
        """A quantity the tools asked for arrived (None: b2plot failed):
        the results again."""
        if data is None:
            self.waiting = False
        else:
            self._refresh()

    def apply_theme(self):
        """The chords on the plot and the figures in the theme."""
        self.bar.apply_theme()
        self._chord_artists()
        for view in [t.view for t in self.chords_section.chords] + [
                self.chords_section.sums, self.stats_section.view]:
            if view.draw is not None:
                view.apply_theme()

    def _done(self, mode, pts):
        tab = self.tab
        if mode == "seeds":
            (x0, y0), (x1, y1) = pts
            t = np.linspace(0.0, 1.0, tab.quantity.streams.nseeds.value())
            tab.quantity.set_seeds(list(zip(x0 + t * (x1 - x0),
                                            y0 + t * (y1 - y0))))
            tab.status.emit("Seed line set")
            return
        if tab.run is None or mode == "line" and self._measured() is None \
                or mode in ("box", "polygon") and not tab._current():
            tab.status.emit("No plot to measure")
            return
        if mode == "inspect":
            self.last = (mode, pts)
            x, y = pts[0]
            found = inspect.groups(tab, x, y)
            if not found:               # outside every cell and triangle
                self.last = None
                return
            title = []
            for t, _ in found:
                t = t.split(":")[0]
                if not t.endswith("quantity shown") and t not in title:
                    title.append(t)
            self.panel.show_groups(", ".join(title), inspect.HEADER, found)
        elif mode == "line":            # a new chord
            (x0, y0), (x1, y1) = pts
            if self.source != "drawn":
                return
            self.drawn.append((x0, y0, 0.0, x1, y1, 0.0))
            self.looks["drawn"].append(LOOK)
            self.bar._draw([])
            self._chords_all()
            self.chords_section.show_chord(len(self.chords) - 1)
        else:
            self.stats_last = (mode, pts)
            self._statistics(mode, pts)

    def _what(self, q, data):
        """Name of quantity q shown (data), with its species."""
        species = self.tab.species_text(data)
        return q.label + (" [%s]" % species if species else "")

    def _name(self, q, data):
        """The description of quantity q shown (data), as the title of the
        2D plot (without its unit), with its species."""
        species = self.tab.species_text(data)
        return labels.any_to_mathtext(split_unit(q.description)[0] + (
            " [%s]" % species if species else ""))

    def _measured(self):
        """(data, Quantity, column, b2plot operations, data as sent) the
        chords measure: the plasma or the vector quantity plotted (with
        both, the one chosen in their section), or None."""
        tab = self.tab
        if tab.run is None:
            return None
        plasma = tab._current()
        if tab._vector_args() is not None and (
                not plasma or self.chords_section.target.currentData()
                == "vector"):
            v, col = tab.summed_vector(tab.vector_data)
            return v, tab.vector_wanted, col, (), tab.vector_data
        if plasma:
            return (tab.data, tab.wanted, tab.plot._column(
                tab.data, tab.plot.style), tuple(tab.quantity.ops(
                    tab.wanted)), tab.data)
        return None

    def set_target(self, *_):
        """The chords for the plasma or the vector quantity."""
        self._chords_all()

    # -------------------------------------------------------------- chords
    @property
    def chords(self):
        """Ends (R, Z, phi) of the chords of the source chosen."""
        return self.drawn if self.source == "drawn" else self.run_chords()

    @chords.setter
    def chords(self, value):
        self.drawn = list(value)

    def run_chords(self):
        """The chords of the *.chords files of the run (from the points
        b2plot sends), with the set and number of each."""
        run = self.tab.run
        if run is None:
            return []
        cache = run.__dict__.setdefault("chord_ends", None)
        if cache is None:
            cache, self.run_labels = [], []
            for key in [k for k in run.layers if k.startswith("chords: ")]:
                seg = run.layers[key].reshape(-1, CHORD_POINTS - 1, 4)
                for j, c in enumerate(seg, 1):
                    r = np.concatenate((c[:, 0], c[-1:, 2]))
                    z = np.concatenate((c[:, 1], c[-1:, 3]))
                    cache.append(measure.chord_ends(r, z))
                    self.run_labels.append("%s, chord %d" % (key[8:], j))
            run.chord_ends = cache
        return run.chord_ends

    def set_source(self, source):
        """Chords drawn or typed, or those of the run (kept apart)."""
        self.source = source
        if self.bar.mode == "line":
            self.bar.set_mode(None)
        self.chords_section.set_editable(source == "drawn")
        self._chords_all()

    def _looks(self):
        """How each chord of the source chosen is drawn on the plot."""
        looks = self.looks[self.source]
        looks += [LOOK] * (len(self.chords) - len(looks))
        return looks

    def restyle(self, k):
        """Chord k drawn on the plot as its tab says now."""
        looks = self._looks()
        if k < len(looks) and k < len(self.chords_section.chords):
            looks[k] = self.chords_section.chords[k].look()
            self._chord_artists()

    def add_chord(self):
        """A new chord to type: the ends of the chord shown, or across the
        middle of the view."""
        w = self.chords_section.tabs.currentWidget()
        tabs = self.chords_section.chords
        if w in tabs:
            new = self.chords[tabs.index(w)]
        else:
            x0, x1, y0, y1 = self.tab.plot.get_view()
            y = 0.5 * (y0 + y1)
            new = (x0 + 0.25 * (x1 - x0), y, 0.0, x0 + 0.75 * (x1 - x0), y,
                   0.0)
        if self.source != "drawn":
            return
        self.drawn.append(tuple(new))
        self.looks["drawn"].append(LOOK)
        self._chords_all()
        self.chords_section.show_chord(len(self.chords) - 1)

    def remove_chord(self, k):
        if self.source == "drawn":
            del self._looks()[k]
            del self.drawn[k]
            self._chords_all()

    def clear_chords(self):
        if self.source == "drawn":
            self.drawn = []
            self.looks["drawn"] = []
            self._chords_all()

    def move_chord(self, k, coords):
        """New ends (R, Z, phi) typed for a drawn chord k."""
        if self.source != "drawn":
            return
        self.drawn[k] = tuple(coords)
        self._chords_all()
        self.chords_section.show_chord(k)

    def _chords_all(self):
        """Every chord computed for the plot shown, its tab, the sums and
        the chords on the plot (with Show all, every frame loaded)."""
        sec = self.chords_section
        tab = self.tab
        m = self._measured() if self.section == "chords" else None
        sec.target.setVisible(tab.run is not None and tab._current() and
                              tab._vector_args() is not None)
        self.results = [self._chord(c, m) for c in self.chords] if m else []
        sec.show_all.setVisible(tab.time_box.movie())
        self.all_frames = self._frames(m) if m and self._every_frame(m) \
            else None
        if self.all_frames is None:
            self.queue = []
        for k, res in enumerate(self.results):
            if self.all_frames is not None:
                now, others = self.all_frames
                res["frames"] = (now, [(t, p, fr[k]) for t, p, fr in others])
        sec.set_count(len(self.chords))
        run = self.source == "run"
        for k, (t, c, look) in enumerate(zip(sec.chords, self.chords,
                                             self._looks())):
            t.set_look(look)
            t.ends.set(c, lambda new, t=t: sec.moved(t, new))
            sec.tabs.setTabToolTip(sec.tabs.indexOf(t), self.run_labels[k]
                                   if run and k < len(self.run_labels)
                                   else "")
            if k < len(self.results):
                res = self.results[k]
                t.text.setText(res["text"])
                t.view.options.allow(res["xs"])
                header, rows = res["header"], res["rows"]
                if res.get("frames"):   # the values of every frame too
                    header, rows = self._frame_rows(res)
                t.view.set_figure(res["draw"], header, rows,
                                  kind="frames" if res.get("frames") else
                                  "line",
                                  name="chord_%d_%s" % (k + 1, res["what"]))
        if len(self.results) >= 2:
            self.show_sums(m)
        self._chord_artists()

    def _chord(self, coords, m):
        """The profile along a chord (R, Z, phi of its two ends) of what
        the chords measure (m, as _measured gives it) and its sums, the
        figure and the rows of its tab."""
        tab = self.tab
        data, q, col, _, sent = m
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        r0, z0, f0, r1, z1, f1 = coords
        s, r, z, ph, v, vn, l = measure.profile(tab.plot, data, (r0, z0),
                                                (r1, z1), phi=(f0, f1),
                                                col=col)
        _, total, mean, flux = measure.line_sums(s, r, v, vn, l)
        psimap = tab.run.psimap
        rho = psimap.rhop(r, z) if psimap is not None else None
        dsep = measure.separatrix_distance(s, rho) if rho is not None \
            else None
        xs = {"s": s, "R": r, "Z": z}       # x axes this chord offers
        if rho is not None and measure.single_valued(rho, v):
            xs["rhop"] = rho
            if dsep is not None and measure.single_valued(dsep, v):
                xs["dssep"] = dsep
        html = measure.html_unit
        lines = ["Integral along the line: %.5g %s" % (
                     total, html(measure.times_m(unit, 1))),
                 "Average along the line: %.5g %s" % (mean, html(unit))]
        if vn is not None and measure.PER_M.search(unit) and \
                measure.PER_M.search(unit).group(1) == "2":
            lines.append("Flux through the surface the line (its projection "
                         "on the poloidal plane) sweeps around the axis "
                         "(2πR v·n, n to the right of the line): %.5g %s" % (
                             flux, html(measure.times_m(unit, 2))))
        elif vn is not None:
            lines.append("No flux: the unit is not a flux density (%s)"
                         % html("m^-2"))
        ok = np.isfinite(v)
        name = self._name(q, sent)
        out = {}

        def draw(ax, options):
            key = options.xaxis.currentData()
            x = xs.get(key, s)
            ax.set_title(name, fontsize="medium")
            now, others = out.get("frames") or (None, [])
            for t, _, fr in others:     # the other frames first, thin
                for c, y in enumerate((fr["v"], fr["vn"])):
                    if y is not None:
                        ln, = ax.plot(x, y, label="_frame")
                        ln.frame, ln.curve = (t, False), c
            for c, (y, label) in enumerate(((v, "|v|" if vn is not None
                                             else None), (vn, "v·n"))):
                if y is not None:
                    ln, = ax.plot(x, y, label=label)
                    ln.frame, ln.curve = (1.0 if now is None else now,
                                          True), c
            if vn is not None:
                ax.legend(fontsize="small")
            known = ok & np.isfinite(x)
            if known.any() and np.ptp(x[known]) > 0:    # from end to end
                ax.set_xlim(x[known].min(), x[known].max())
            ax.set_xlabel(XLABELS.get(key, "distance along the line (m)"))
            ax.set_ylabel(measure.math_unit(unit))
        header = ["s (m)", "R (m)", "Z (m)", "value (%s)" % plain(unit)] + (
            ["normal component (%s)" % plain(unit)] if vn is not None
            else []) + ["phi (deg)"]
        cols = (s, r, z, v) + ((vn,) if vn is not None else ()) + (ph,)
        out.update(r=r, z=z, xs=xs, draw=draw, header=header,
                   rows=[list(row) for row in zip(*cols)],
                   text="<br>".join(lines), integral=total, average=mean,
                   units=(plain(measure.times_m(unit, 1)), plain(unit)),
                   what=q.label, v=v, vn=vn, unit=plain(unit))
        return out

    # ------------------------------------------------- all the movie frames
    def set_show_all(self, on):
        self.show_all = on
        self._chords_all()

    def _every_frame(self, m):
        """Show all on, with a movie quantity measured (m) in the movie
        tab."""
        return self.show_all and self.tab.time_box.movie() and \
            bool(getattr(m[1], "movie", 0))

    def _frames(self, m):
        """(position of the frame shown along the frames from 0 to 1,
        [(position, frame, results of the chords)] of the other frames
        loaded) of what the chords measure (m); asks b2plot for the frames
        not loaded yet."""
        tb = self.tab.time_box
        data, q, col, ops, _ = m
        key = (q.name, ops, col, tuple(tuple(c) for c in self.chords),
               self.source)
        if key != self.frames_key:
            self.frame_results, self.frames_key = {}, key
        positions = tb.positions()
        sources = [tb.source_of(q, p) for p in positions]
        shown = data.source
        self.frame_results[shown] = [dict(v=r["v"], vn=r["vn"],
                                          integral=r["integral"],
                                          average=r["average"])
                                     for r in self.results]
        self.queue = [x for x in sources if x not in self.frame_results and
                      x not in self.flight]
        self._pump()
        lo, hi = positions[0], positions[-1]

        def along(p):
            return (p - lo) / float(hi - lo) if hi > lo else 1.0
        others = [(along(p), p, self.frame_results[x])
                  for p, x in zip(positions, sources) if x != shown and
                  self.frame_results.get(x) is not None]
        return along(tb.pos.value()), others

    def _pump(self):
        """The next frames asked for, two at a time (the requests of the
        plot never wait long behind them)."""
        if self.pumping:
            return
        self.pumping = True
        try:
            while self.queue and len(self.flight) < 2:
                x = self.queue.pop(0)
                if x in self.frame_results:
                    continue
                self.flight.add(x)
                m = self._measured()
                if m is not None:
                    self.tab.request.emit(("frames", m[1],
                                           self.frames_key[1], x))
        finally:
            self.pumping = False

    def frame_delivered(self, want, data):
        """A frame of Show all: the profiles and sums of the chords kept
        (None: b2plot failed, not asked again)."""
        _, q, ops, x = want
        self.flight.discard(x)
        key = self.frames_key
        if key is not None and (q.name, tuple(ops)) == key[:2]:
            self.frame_results[x] = None if data is None else [
                self._profile(c, data) for c in self.chords]
            n = len(self.tab.time_box.positions())
            got = sum(1 for v in self.frame_results.values()
                      if v is not None)
            self.tab.status.emit("Chords: %d of %d frames" % (min(got, n), n)
                                 if self.queue or self.flight else
                                 "Chords: all %d frames" % n)
            if not self._frames_again.isActive():
                self._frames_again.start()
        self._pump()

    def _frames_arrived(self):
        m = self._measured()
        if self.section == "chords" and m and self._every_frame(m):
            self._chords_all()

    def _profile(self, coords, data):
        """Profile and sums along a chord for the field or the vector of
        another frame (its species summed as plotted)."""
        col = None
        if hasattr(data, "vr"):
            data, col = self.tab.summed_vector(data)
        r0, z0, f0, r1, z1, f1 = coords
        s, r, _, _, v, vn, l = measure.profile(self.tab.plot, data, (r0, z0),
                                               (r1, z1), phi=(f0, f1),
                                               col=col)
        _, total, mean, _ = measure.line_sums(s, r, v, vn, l)
        return dict(v=v, vn=vn, integral=total, average=mean)

    def _frame_rows(self, res):
        """Header and rows of a profile with the values of the other
        frames in more columns."""
        prefix = self.tab.time_box.pos.prefix().strip() or "frame"
        header, rows = list(res["header"]), [list(r) for r in res["rows"]]
        for _, p, fr in res["frames"][1]:
            for name, y in (("value", fr["v"]), ("normal component",
                                                 fr["vn"])):
                if y is not None:
                    header.append("%s (%s), %s %d" % (name, res["unit"],
                                                      prefix, p))
                    for row, val in zip(rows, y):
                        row.append(val)
        return header, rows

    def show_sums(self, m=None):
        """The line integrals or averages (as chosen) against the chord
        number of what the chords measure (m); Export writes both."""
        sec = self.chords_section
        m = m or self._measured()
        if len(self.results) < 2 or m is None:
            return
        n = np.arange(1, len(self.results) + 1)
        name = self._name(m[1], m[4])
        units = self.results[0]["units"]
        rows = [[k, res["integral"], res["average"]]
                for k, res in zip(n, self.results)]
        header = ["chord", "integral (%s)" % units[0],
                  "average (%s)" % units[1]]
        key = sec.which.currentData()
        unit = units[key == "average"]
        y = [res[key] for res in self.results]
        frames = self.all_frames
        if frames is not None:          # every frame: chord, frame, sums
            prefix = self.tab.time_box.pos.prefix().strip() or "frame"
            p_now = self.tab.time_box.pos.value()
            header = ["chord", prefix] + header[1:]
            rows = [[k, p_now] + row[1:] for k, row in zip(n, rows)] + [
                [k, p, fr[k - 1]["integral"], fr[k - 1]["average"]]
                for _, p, fr in frames[1] for k in n]
        if key != getattr(sec.sums, "shown", key):  # its own y limits
            for e in sec.sums.options.limits[2:]:
                e.clear()
        sec.sums.shown = key

        def draw(ax, options):
            ax.set_title(name, fontsize="medium")
            if frames is not None:      # the other frames first, small
                for t, _, fr in frames[1]:
                    ln, = ax.plot(n, [f[key] for f in fr], linestyle="None",
                                  marker="o", label="_frame")
                    ln.frame = (t, False)
            ln, = ax.plot(n, y, linestyle="None", marker="o")
            ln.frame = (1.0 if frames is None else frames[0], True)
            ax.xaxis.set_major_locator(FixedLocator(n) if len(n) <= 20
                                       else MaxNLocator(integer=True))
            ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
            ax.set_xlim(0.5, len(n) + 0.5)
            ax.set_xlabel("chord")
            ax.set_ylabel("line %s (%s)" % (key, measure.math_unit(unit)))
        sec.sums.set_figure(draw, header, rows, kind="sums" if frames is
                            None else "sumframes",
                            name="chords_%s_%s" % (
                                key, self.results[0]["what"]))

    def _chord_artists(self):
        """The chords on the plot while their section is open: a dot at the
        start, an arrow at the end and the number beyond it."""
        for a in self.artists:
            if a.axes is not None:
                a.remove()
        self.artists = []
        if self.section != "chords":
            self.tab.canvas.draw_idle()
            return
        ax = self.tab.plot.ax
        for k, (res, look) in enumerate(zip(self.results, self._looks()), 1):
            colour, width, style, number = look
            colour = theme.rgb(colour)
            r, z = res["r"], res["z"]
            line, = ax.plot(r, z, color=colour, linestyle=style,
                            linewidth=width, zorder=6.5)
            start, = ax.plot(r[:1], z[:1], color=colour, linestyle="None",
                             marker="o", markersize=3.0 + 1.5 * width,
                             zorder=6.6)
            self.artists += [line, start]
            if len(r) < 2:
                continue
            d = np.array([r[-1] - r[-2], z[-1] - z[-2]])
            if not np.hypot(*d) > 0:
                continue
            d = d / np.hypot(*d)
            self.artists.append(ax.annotate(
                "", xy=(r[-1], z[-1]), xytext=(r[-1] - 1e-6 * d[0],
                                               z[-1] - 1e-6 * d[1]),
                arrowprops=dict(arrowstyle="-|>", color=colour, lw=width,
                                shrinkA=0, shrinkB=0,
                                mutation_scale=8.0 + 2.0 * width),
                zorder=6.6))
            if number:
                self.artists.append(ax.annotate(
                    "%d" % k, xy=(r[-1], z[-1]), xytext=tuple(
                        (9.0 + width) * d), textcoords="offset points",
                    color=colour, fontsize=9, fontweight="bold",
                    ha="center", va="center", zorder=6.6,
                    annotation_clip=True))
        self.tab.canvas.draw_idle()

    # ---------------------------------------------------------- statistics
    def _statistics(self, mode, pts):
        tab = self.tab
        sec = self.stats_section
        if tab.run is None or not tab._current():
            return
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
            self.bar._draw([])
        else:                           # the shape stays drawn
            self.bar.show_shape(mode, pts)
        idx = measure.chosen(plot, data, pts)
        cells = data.location == "cells"
        i = g.cells[idx] - 1 if cells else idx
        values = measure.values_at(plot, data, idx)
        volumes = np.asarray(vol.values[0], float)[i]
        st = measure.statistics(values, volumes)
        plain = labels.any_to_plain
        unit = plain(split_unit(data.label)[1])
        sec.heading.setText("Statistics over %s: %s" % (
            WHERE[mode], self._what(tab.wanted, data)))
        html = measure.html_unit
        sec.text.setText("<br>".join((
            "%s: %d" % ("Cells" if cells else "Triangles", st["n"]),
            "Volume: %.5g %s" % (st["volume"], html("m^3")),
            "Volume integral: %.5g %s" % (st["integral"], html(
                measure.times_m(unit, 3))),
            "Volume average: %.5g %s" % (st["average"], html(unit)),
            "Minimum: %.5g %s" % (st["min"], html(unit)),
            "Maximum: %.5g %s" % (st["max"], html(unit)))))
        ok = np.isfinite(values)
        title = self._name(tab.wanted, data)

        def draw(ax, options):
            v = values[ok]
            ax.set_title(title, fontsize="medium")
            if not v.size:
                return
            n = options.bins.value()
            log = options.logx.isChecked() and v.min() > 0
            ax.hist(v, bins=np.geomspace(v.min(), v.max(), n + 1) if log and
                    v.max() > v.min() else n)
            ax.set_xlabel(measure.math_unit(unit))
            ax.set_ylabel("cells" if cells else "triangles")
        centres = g.centres[idx] if cells else plot.ecentres[idx]
        rows = [[int(n), c[0], c[1], w, x] for n, c, w, x in zip(
            g.cells[idx] if cells else idx + 1, centres, volumes, values)]
        sec.view.set_figure(
            draw, ["cell" if cells else "triangle", "R (m)", "Z (m)",
                   "volume (m^3)", "value (%s)" % plain(unit)], rows,
            kind="hist", logx=plot.style.scale == "log",
            name="statistics_%s" % tab.wanted.label)
