"""What the mouse tools of a 2D tab do with the shapes drawn: the cell
inspector in its window, the chords and the statistics in their sections
of the quantity column (both follow the quantity, species or frame
plotted: the chords the plasma or the vector quantity, the statistics the
plasma quantity; the statistics of the cells shown follow the view), the
seed line of the streamlines, the field line (its section). The
chords stay in memory when their section is closed; they are drawn on
the plot (a dot at the start, an arrow at the end, the number) while it
is open. With the movies, Show all draws the
profiles and sums of every frame (loaded in the background, two requests
at a time, only the profiles and sums kept)."""

import numpy as np

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Qt
from ..model import split_unit
from ..scaling import squeezable
from . import chordplots, inspect, measure
from .base import MouseTools
from .cameratool import CameraTool
from .fieldtool import FieldLineTool
from .figure import frame_lines
from .results import ResultsPanel
from ..catalog import CHORD_POINTS
from .sections import LOOK, ChordsSection, StatisticsSection
from .spectrum import Spectrum

VOLUMES = {"cells": ("field", "vol"), "triangles": ("efield", "triavol")}
WHERE = {"shown": "the cells shown in the view", "box": "the box",
         "polygon": "the polygon"}
CHORDS = ("chords", "spectrum")  # the sections of the chords
XLABELS = {"R": "R (m)", "Z": "Z (m)", "rhop": r"$\rho_p$",
           "dssep": "distance from the separatrix along the line (m)"}


class _Frames:
    """The frames of the slider positions loaded for the chords of one
    quantity: their results by source, the key they are for, those to ask
    for and those asked, the quantity."""

    def __init__(self):
        self.results, self.key, self.queue, self.flight = {}, None, [], set()
        self.q = None


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
        self.fieldline = FieldLineTool(self)
        self.camera = CameraTool(self)
        self.spectrum = Spectrum(self)
        self.chords_section.per_sr.toggled.connect(
            lambda *_: self._chords_all())
        for w in (self.chords_section.shapes, self.chords_section.continua):
            w.toggled.connect(
                lambda *_: self.section == "spectrum" and self._chords_all())
        self.chords_section.instrument.valueChanged.connect(
            lambda *_: self.section == "spectrum" and self._chords_all())
        self.chords_section.which.currentIndexChanged.connect(
            lambda *_: self.section == "spectrum" and self._chords_all())
        self.bar.done.connect(self._done)
        self.bar.hint.connect(tab.status)
        self.bar.changed.connect(self._modes)
        self.bar.buttons["inspect"].toggled.connect(
            lambda on: on and self._load())
        self.last, self.waiting = None, False   # the inspector
        self.shown = None               # the data and column measured
        self.section = None             # "chords", "spectrum", "stats",
        #                                 "fieldline", "camera" or None
        self.source = "drawn"           # or "run": the *.chords files
        self.run_labels = []
        self.drawn, self.results, self.artists = [], [], []
        self.looks = {"drawn": [], "run": []}   # of each chord on the plot
        self.all_frames = None          # (shown, others) with Show all
        self.stats_last = None          # (mode, points) of the statistics
        self.show_all = False           # movies: the frames all drawn
        self.fs = (_Frames(), _Frames())    # plasma (or vector), vector
        self.pumping = False
        self.other, self.other_m, self.other_frames = [], None, None
        self.full = {}                  # (name, source) -> every species
        self.full_asked = set()         # asked for, not yet here
        self.each = None                # [(species, column)]: a curve each
        self._frames_again = QtCore.QTimer(tab)
        self._frames_again.setSingleShot(True)
        self._frames_again.setInterval(400)
        self._frames_again.timeout.connect(self._frames_arrived)
        self._again = QtCore.QTimer(tab)
        self._again.setSingleShot(True)
        self._again.setInterval(150)
        self._again.timeout.connect(self._stats_again)
        self.chords_section.tabs.currentChanged.connect(self._chord_tab)

    # the frames of the quantity measured first (self.fs[0])
    frame_results = property(lambda self: self.fs[0].results,
                             lambda self, v: setattr(self.fs[0], "results",
                                                     v))
    frames_key = property(lambda self: self.fs[0].key,
                          lambda self, v: setattr(self.fs[0], "key", v))
    queue = property(lambda self: self.fs[0].queue,
                     lambda self, v: setattr(self.fs[0], "queue", v))
    flight = property(lambda self: self.fs[0].flight)

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
        """The chords, the field line, the overlay, the statistics or none
        in the quantity column."""
        self.section = which
        self.chords_section.set_spectrum(which == "spectrum")
        self.chords_section.setVisible(which in CHORDS)
        self.stats_section.setVisible(which == "stats")
        if self.fieldline.open != (which == "fieldline"):
            self.fieldline.set_open(which == "fieldline")
        if self.camera.open != (which == "camera"):
            self.camera.set_open(which == "camera")
        q = self.tab.quantity
        q.overlay_section.setVisible(which == "overlay")
        for b, key in ((q.chords_button, "chords"), (q.stats_button,
                                                     "stats"),
                       (q.overlay_button, "overlay"),
                       (q.field_button, "fieldline"),
                       (q.spectrum_button, "spectrum"),
                       (q.camera_button, "camera")):
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
        elif which in CHORDS:
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
        self.fieldline.modes()
        self.camera.modes()
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
        q = tab.quantity
        key = (id(tab.data), tab.plot.style.column,
               q.plasma_species.text())     # its sum or a curve each
        for data, menu in ((tab.vector_data if tab.vector_wanted else None,
                            q.vector_species),
                           (tab.wall_data if tab.wall_wanted else None,
                            q.wall_species)):
            key += (id(data), None if data is None else
                    tab._columns(data, menu))
        if self.section == "fieldline":    # also once the plot is drawn
            self.fieldline.show()
        if key == self.shown:
            return
        self.shown = key
        self._refresh()

    def _refresh(self):
        if self.section in CHORDS:
            self._chords_all()
        elif self.section == "stats" and self.stats_last is not None:
            self._statistics(*self.stats_last)
        if self.last is not None and self.panel.isVisible():
            self._done(*self.last)

    # ------------------------------------------------- frames of a movie
    def _shown_widgets(self):
        """The figures and texts of the open section."""
        if self.section in CHORDS:
            sec = self.chords_section
            return ([t.view for t in sec.chords] + [
                t.view_v for t in sec.chords if t.second.isVisible()] +
                [sec.sums, sec.trace] + [
                    v for v in (sec.board.sums_v, sec.board.trace_v)
                    if v.isVisible()], [t.text for t in sec.chords] + [
                    t.text_v for t in sec.chords if t.second.isVisible()],
                sec)
        if self.section == "stats":
            sec = self.stats_section
            return [sec.view], [sec.heading, sec.text], sec
        if self.section == "fieldline":
            sec = self.fieldline.section
            return [sec.view], [sec.conn, sec.text], sec
        return [], [], None

    def snapshot(self):
        """What the open section shows (for an image of the movie), and the
        camera image of the frame while Export frames draws them."""
        views, texts, _ = self._shown_widgets()
        return (self.section,
                [(v, v.draw, v.header, v.rows, getattr(v, "kind",
                                                       v.options.kind),
                  v.name) for v in views if v.draw is not None],
                [(t, t.text()) for t in texts], self.camera.snapshot())

    def show_snapshot(self, snap):
        """The open section as it was for an image of the movie (the
        figures shown: a chord tab chosen meanwhile at the next image)."""
        section, views, texts, _ = snap
        if section != self.section or section is None:
            return
        for v, draw, header, rows, kind, name in views:
            if v.isVisible():
                v.set_figure(draw, header, rows, kind=kind, name=name)
        for t, text in texts:
            t.setText(text)

    def hold(self, on):
        """The open section not painted (on) while a frame of the movie is
        drawn into an image, or painted again."""
        for sec in (self.chords_section, self.stats_section,
                    self.fieldline.section):
            sec.setUpdatesEnabled(not on)

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
        self.fieldline.apply_theme()
        self.camera.apply_theme()
        self._chord_artists()
        for view in [t.view for t in self.chords_section.chords] + [
                self.chords_section.sums, self.chords_section.trace,
                self.stats_section.view]:
            if view.draw is not None:
                view.apply_theme()

    def _done(self, mode, pts):
        tab = self.tab
        if mode == "polygon" and tab.balance.neutrals.take(pts):
            return                      # Draw region of the Neutrals balance
        if mode == "seeds":             # the ends of the seed line
            tab.quantity.set_seeds([tuple(p) for p in pts])
            tab.status.emit("Seed line set")
            return
        if mode == "fieldline":
            self.bar._draw([])
            self.fieldline.picked2d(*pts[0])
            return
        if mode == "camera":
            self.camera.picked(pts)
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
        chords measure: the plasma quantity plotted, else the vector one
        (with both, the vector one is the other one, _other), or None."""
        tab = self.tab
        if tab.run is None:
            return None
        plasma = tab._current()
        if tab._vector_args() is not None and not plasma:
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
        spectrum = self.section == "spectrum"
        m = self._measured() if self.section in CHORDS else None
        if spectrum and m is not None and m[0] is not self.tab.data:
            m = None                    # the plasma quantity only
        if spectrum:
            self.spectrum.lines()
        sec.target.hide()               # both measured with both plotted
        self.each = self._species_curves(m)
        if self.each is not None:       # every species of the field, then
            full = self._full(m)        # a curve each (meanwhile their sum)
            self.each = self.each if full is not None else None
        self.results = [self._chord(c, m) if self.each is None else
                        self._chord_species(c, m, full) for c in
                        self.chords] if m else []
        mo = None if spectrum else self._other(m)   # both plotted: the
        #                                             vector one too
        other = [self._chord(c, mo) for c in self.chords] if mo else []
        sec.show_all.setVisible(tab.time_box.movie() and not spectrum)
        multi = self._species_curves(m) is not None
        if multi and self.show_all:     # Show all: one curve per chord only
            self.show_all = False
            sec.show_all.blockSignals(True)
            sec.show_all.setChecked(False)
            sec.show_all.blockSignals(False)
        sec.show_all.setEnabled(not multi)
        frames = bool(m) and self._movie(m)
        self.all_frames = self._frames(m) if frames else None
        self.other_frames = self._frames(mo, other, self.fs[1]) if \
            frames and mo else None
        for fs, got in zip(self.fs, (self.all_frames, self.other_frames)):
            if got is None:
                fs.queue = []
        self._attach(self.results, self.all_frames, self.fs[0])
        self._attach(other, self.other_frames, self.fs[1])
        self.other, self.other_m = other, mo
        sec.set_count(len(self.chords), trace=frames, second=bool(other))
        run = self.source == "run"
        for k, (t, c, look) in enumerate(zip(sec.chords, self.chords,
                                             self._looks())):
            t.set_look(look)
            t.ends.set(c, lambda new, t=t: sec.moved(t, new))
            sec.tabs.setTabToolTip(sec.tabs.indexOf(t), self.run_labels[k]
                                   if run and k < len(self.run_labels)
                                   else "")
            t.second.setVisible(bool(other))
            if k < len(self.results) and spectrum:
                self.spectrum.show(t, k, c, m, sec.per_sr.isChecked(),
                                   sec.which.currentData() == "average")
            elif k < len(self.results):     # the plasma quantity first
                self._show_chord(t.view, t.text, self.results[k], k)
                if other:
                    self._show_chord(t.view_v, t.text_v, other[k], k)
        if self.results:
            self.show_sums(m)
        self._chord_artists()

    def _attach(self, results, all_frames, fs):
        """With Show all, the frames loaded to the results of each chord
        (its profile figure then only moves the frame shown)."""
        if all_frames is None or not self.show_all:
            return
        now, others = all_frames
        for k, res in enumerate(results):
            res["frames"] = (now, [(t, p, fr[k]) for t, p, fr in others])
            ys = [np.ravel(fr[k][c]) for _, _, fr in others
                  for c in ("v", "vn") if fr[k][c] is not None]
            res["draw"].key = (fs.key, k, tuple(p for _, p, _ in others),
                               hash(np.concatenate(ys).tobytes()) if ys
                               else 0)
            res["draw"].current = res["current"]

    def _show_chord(self, view, text, res, k):
        """The text and the profile of chord k (its result res)."""
        text.setText(res["text"])
        view.options.allow(res["xs"])
        header, rows = res["header"], res["rows"]
        if res.get("frames"):           # the values of every frame too
            header, rows = self._frame_rows(res)
        view.set_figure(res["draw"], header, rows, space=True,
                        kind="frames" if
                        res.get("frames") else "line",
                        name="chord_%d_%s" % (k + 1, res["what"]))

    def _other(self, m):
        """With a plasma and a vector quantity plotted, the vector one (as
        _measured gives it; m: the plasma one), else None."""
        tab = self.tab
        if not m or not tab._current() or tab._vector_args() is None:
            return None
        v, col = tab.summed_vector(tab.vector_data)
        return v, tab.vector_wanted, col, (), tab.vector_data

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
            for c, k in enumerate(("v", "vn") if others else ()):
                frame_lines(ax, x, [fr[k] for _, _, fr in others],
                            [t for t, _, _ in others], c)  # all, under it
            for c, (y, label) in enumerate(((v, "|v|" if vn is not None
                                             else None), (vn, "v·n"))):
                if y is not None:
                    ln, = ax.plot(x, y, label=label)
                    ln.frame, ln.curve = (1.0 if now is None else now,
                                          True), c
                    ln.moves = bool(others)     # over all frames: moved
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
        def current(options):
            x = xs.get(options.xaxis.currentData(), s)
            return [(x, y) for y in (v, vn) if y is not None]
        out.update(r=r, z=z, xs=xs, draw=draw, header=header, current=current,
                   rows=[list(row) for row in zip(*cols)],
                   text="<br>".join(lines), integral=total, average=mean,
                   units=(plain(measure.times_m(unit, 1)), plain(unit)),
                   what=q.label, v=v, vn=vn, unit=plain(unit))
        return out

    # ------------------------------------------------- all the movie frames
    def set_show_all(self, on):
        self.show_all = on
        self._chords_all()

    def _movie(self, m):
        """A movie quantity measured (m) in the movie tab: every frame
        loaded (the sums in time; with Show all also drawn)."""
        return self.tab.time_box.movie() and bool(getattr(m[1], "movie", 0))

    def _frames(self, m, results=None, fs=None):
        """(position of the frame shown along the frames from 0 to 1,
        [(position, frame, results of the chords)] of the frames loaded)
        of what the chords measure (m, its results of the frame shown;
        fs: its frames, default those of the first quantity); asks b2plot
        for the frames not loaded yet."""
        tb = self.tab.time_box
        fs = fs or self.fs[0]
        results = self.results if results is None else results
        data, q, col, ops, _ = m
        if fs is self.fs[0] and self.each is not None:  # every species:
            ops, col = (), tuple(c for _, c in self.each)   # unsummed
        key = (q.name, ops, col, tuple(tuple(c) for c in self.chords),
               self.source)
        if key != fs.key:
            fs.results, fs.key = {}, key
        fs.q = q
        positions = tb.positions()
        sources = [tb.source_of(q, p) for p in positions]
        shown = data.source
        fs.results[shown] = [dict(v=r["v"], vn=r["vn"],
                                  integral=r["integral"],
                                  average=r["average"]) for r in results]
        fs.queue = [x for x in sources if x not in fs.results and
                    x not in fs.flight]
        self._pump()
        lo, hi = positions[0], positions[-1]

        def along(p):
            return (p - lo) / float(hi - lo) if hi > lo else 1.0
        others = [(along(p), p, fs.results[x])    # with the one shown
                  for p, x in zip(positions, sources)
                  if fs.results.get(x) is not None]
        return along(tb.position()), others

    def _pump(self):
        """The next frames asked for, two at a time (the requests of the
        plot never wait long behind them)."""
        if self.pumping:
            return
        self.pumping = True
        try:
            while sum(len(f.flight) for f in self.fs) < 2:
                fs = next((f for f in self.fs if f.queue), None)
                if fs is None:
                    break
                x = fs.queue.pop(0)
                if x in fs.results or fs.q is None:
                    continue
                fs.flight.add(x)
                self.tab.request.emit(("frames", fs.q, fs.key[1], x))
        finally:
            self.pumping = False

    def frame_delivered(self, want, data):
        """A frame of Show all: the profiles and sums of the chords kept
        (None: b2plot failed, not asked again)."""
        _, q, ops, x = want
        fs = next((f for f in self.fs if f.key is not None and x in
                   f.flight and (q.name, tuple(ops)) == f.key[:2]), None)
        for f in self.fs if fs is None else (fs,):
            f.flight.discard(x)
        if fs is not None:
            each = fs.key[2] if isinstance(fs.key[2], tuple) else None
            fs.results[x] = None if data is None else [
                self._profile(c, data) if each is None else
                self._profile_species(c, data, each) for c in self.chords]
            n = len(self.tab.time_box.positions()) * sum(
                1 for f in self.fs if f.key is not None and f.q is not None)
            got = sum(1 for f in self.fs for v in f.results.values()
                      if v is not None)
            busy = any(f.queue or f.flight for f in self.fs)
            self.tab.status.emit("Chords: %d of %d frames" % (min(got, n), n)
                                 if busy else "Chords: all frames loaded")
            if not self._frames_again.isActive():
                self._frames_again.start()
        self._pump()

    def _frames_arrived(self):
        m = self._measured()
        if self.section == "chords" and m and self._movie(m):
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

    def _profile_species(self, coords, data, cols):
        """Profiles and sums along a chord of each species column of cols
        of the field of another frame (lists in the order of cols)."""
        r0, z0, f0, r1, z1, f1 = coords
        out = dict(v=[], vn=None, integral=[], average=[])
        for c in cols:
            s, r, _, _, v, vn, l = measure.profile(
                self.tab.plot, data, (r0, z0), (r1, z1), phi=(f0, f1), col=c)
            _, total, mean, _ = measure.line_sums(s, r, v, vn, l)
            out["v"].append(v)
            out["integral"].append(total)
            out["average"].append(mean)
        return out

    # ------------------------------------------------ a curve per species
    def _species_curves(self, m):
        """[(species, column)] when the plasma quantity measured has a
        choice of a curve per species (All, X (all)), else None."""
        tab = self.tab
        if not m or m[1] is not tab.wanted or m[0] is not tab.data:
            return None
        menu = tab.quantity.plasma_species
        return menu.curves() if menu.is_multi() else None

    def _full(self, m):
        """The field of every species of what is plotted (b2plot sums them
        for the plot), or None while b2plot is asked for it."""
        q, source = m[1], m[4].source
        key = (q.name, source)
        if key in self.full:
            return self.full[key]
        if key not in self.full_asked:
            self.full_asked.add(key)
            self.tab.request.emit(("allspecies", q, (), source))
        return None

    def species_delivered(self, want, data):
        """The field of every species: the chords with a curve each."""
        _, q, _, source = want
        key = (q.name, source)
        self.full_asked.discard(key)
        if data is None:
            return
        if len(self.full) > 8:          # the latest only
            self.full = {}
        self.full[key] = data
        if self.section in CHORDS:
            self._chords_all()

    def _chord_tab(self, *_):
        """Another chord tab: with a curve per species, its sums in
        time."""
        if self.each is not None and self.results:
            self.show_sums()

    def _chord_species(self, coords, m, full):
        """As _chord, a curve per species (self.each) of the field full of
        every species: the profiles, the line integrals and averages."""
        tab = self.tab
        data, q, _, _, sent = m
        plain = labels.any_to_plain
        unit = plain(split_unit(sent.label)[1])
        r0, z0, f0, r1, z1, f1 = coords
        got = self._profile_species(coords, full, [c for _, c in self.each])
        s, r, z, ph, _, _, _ = measure.profile(tab.plot, data, (r0, z0),
                                               (r1, z1), phi=(f0, f1))
        names = [n for n, _ in self.each]
        psimap = tab.run.psimap
        rho = psimap.rhop(r, z) if psimap is not None else None
        dsep = measure.separatrix_distance(s, rho) if rho is not None \
            else None
        first = got["v"][0] if got["v"] else s
        xs = {"s": s, "R": r, "Z": z}
        if rho is not None and measure.single_valued(rho, first):
            xs["rhop"] = rho
            if dsep is not None and measure.single_valued(dsep, first):
                xs["dssep"] = dsep
        title = labels.any_to_mathtext(split_unit(q.description)[0] + (
            " [%s]" % tab.quantity.plasma_species.text()))

        def draw(ax, options):
            key = options.xaxis.currentData()
            x = xs.get(key, s)
            ax.set_title(title, fontsize="medium")
            known = np.zeros(len(x), bool)
            for n, y in zip(names, got["v"]):
                ax.plot(x, y, label=n)
                known |= np.isfinite(x) & np.isfinite(y)
            if known.any() and np.ptp(x[known]) > 0:
                ax.set_xlim(x[known].min(), x[known].max())
            ax.legend(fontsize="small")
            ax.set_xlabel(XLABELS.get(key, "distance along the line (m)"))
            ax.set_ylabel(measure.math_unit(unit))
        units = (plain(measure.times_m(unit, 1)), plain(unit))
        header = ["s (m)", "R (m)", "Z (m)"] + [
            "%s (%s)" % (n, plain(unit)) for n in names] + ["phi (deg)"]
        cols = (s, r, z) + tuple(got["v"]) + (ph,)
        return dict(r=r, z=z, xs=xs, draw=draw, header=header,
                    rows=[list(row) for row in zip(*cols)],
                    text=chordplots.two_rows(
                        list(zip(names, got["integral"])),
                        list(zip(names, got["average"])), units),
                    integral=got["integral"], average=got["average"],
                    units=units, what=q.label, v=got["v"], vn=None,
                    unit=plain(unit), current=lambda options: [],
                    species=names, title=title)

    def _frame_rows(self, res):
        """Header and rows of a profile with the values of the other
        frames in more columns."""
        prefix = self.tab.time_box.pos.prefix().strip() or "frame"
        header, rows = list(res["header"]), [list(r) for r in res["rows"]]
        shown = self.tab.time_box.position()
        for _, p, fr in res["frames"][1]:
            if p == shown:              # its values: the columns before
                continue
            for name, y in (("value", fr["v"]), ("normal component",
                                                 fr["vn"])):
                if y is not None:
                    header.append("%s (%s), %s %d" % (name, res["unit"],
                                                      prefix, p))
                    for row, val in zip(rows, y):
                        row.append(val)
        return header, rows

    def show_sums(self, m=None):
        """Under the chord tabs, the line integrals or averages (as chosen)
        of what the chords measure (m): against the chord number with two
        or more chords, in time with a movie quantity (the frames loaded so
        far, a curve per chord); Export writes both sums."""
        sec = self.chords_section
        m = m or self._measured()
        if not self.results or m is None:
            return
        self._sums(m, self.results, self.all_frames, sec.sums, sec.trace)
        if self.other and self.other_m is not None:     # the vector one
            self._sums(self.other_m, self.other, self.other_frames,
                       sec.sums_v, sec.trace_v)

    def _sums(self, m, results, all_frames, view, trace):
        """The sums of the results of the chords of what m measures,
        against the chord number in view, in time (all_frames) in trace."""
        sec = self.chords_section
        name = self._name(m[1], m[4])
        units = results[0]["units"]
        key = sec.board.key()
        unit = units[key == "average"]
        what = results[0]["what"]
        frames = all_frames if self.show_all else None
        names = results[0].get("species")
        if names:                       # a curve per species
            name = results[0]["title"]
            if len(results) >= 2:
                chordplots.fresh_limits(view, key)
                view.set_figure(
                    chordplots.sums_draw(name, [(n, [res[key][i] for res in
                                                     results])
                                                for i, n in enumerate(names)],
                                         key, unit),
                    ["chord"] + ["%s %s (%s)" % (n, w, u) for n in names
                                 for w, u in zip(("integral", "average"),
                                                 units)],
                    [[k] + [x for i in range(len(names))
                            for x in (res["integral"][i], res["average"][i])]
                     for k, res in enumerate(results, 1)],
                    kind="sums", name="chords_%s_%s" % (key, what))
            if all_frames is not None:
                self._show_trace(m, name, key, units, what, names, results,
                                 all_frames, trace)
            return
        if len(results) >= 2:
            n = np.arange(1, len(results) + 1)
            rows = [[k, res["integral"], res["average"]]
                    for k, res in zip(n, results)]
            header = ["chord", "integral (%s)" % units[0],
                      "average (%s)" % units[1]]
            others, now = (), 1.0
            if frames is not None:      # every frame: chord, frame, sums
                prefix = self.tab.time_box.pos.prefix().strip() or "frame"
                p_now = self.tab.time_box.position()
                header = ["chord", prefix] + header[1:]
                rows = [[k, p_now] + row[1:] for k, row in zip(n, rows)] + [
                    [k, p, fr[k - 1]["integral"], fr[k - 1]["average"]]
                    for _, p, fr in frames[1] for k in n]
                others = [(t, [f[key] for f in fr]) for t, _, fr in frames[1]]
                now = frames[0]
            chordplots.fresh_limits(view, key)
            view.set_figure(
                chordplots.sums_draw(name, [res[key] for res in results],
                                     key, unit, others, now),
                header, rows, kind="sums" if frames is None else "sumframes",
                name="chords_%s_%s" % (key, what))
        if all_frames is not None:
            self._show_trace(m, name, key, units, what, None, results,
                             all_frames, trace)

    def _show_trace(self, m, name, key, units, what, names, results,
                    all_frames, view):
        """The sums of the chords in time: every frame loaded so far (the
        frames of the slider positions), a curve per chord (names: a curve
        per species of the chord of the tab shown)."""
        tb, sec, q = self.tab.time_box, self.chords_section, m[1]
        per = {tb.position(): [dict(integral=r["integral"],
                                     average=r["average"])
                                for r in results]}
        for _, p, fr in all_frames[1]:
            per[p] = fr
        ps = sorted(per)
        times = tb.times.get(q.movie, [])

        def t_of(p):
            return tb.time_at(p, q.movie) if times else float(p)
        t = [t_of(p) for p in ps]
        tname = "time (s)" if times else (tb.pos.prefix().strip() or "frame")
        if names:
            j = min(max(sec.tabs.currentIndex(), 0), len(results) - 1)
            ps = [p for p in ps if isinstance(per[p][j]["integral"], list)]
            t = [t_of(p) for p in ps]
            sums = [(np.array([per[p][j]["integral"][i] for p in ps], float),
                     np.array([per[p][j]["average"][i] for p in ps], float))
                    for i in range(len(names))]
            curves = [(n, s_[key == "average"]) for n, s_ in zip(names, sums)]
            name = "%s, chord %d" % (name, j + 1)
            header, rows = chordplots.traces_rows(t, sums, units, tname,
                                                  names=names)
        else:
            sums = [(np.array([per[p][k]["integral"] for p in ps], float),
                     np.array([per[p][k]["average"] for p in ps], float))
                    for k in range(len(results))]
            curves = [("Chord %d" % (k + 1), s[key == "average"])
                      for k, s in enumerate(sums)]
            header, rows = chordplots.traces_rows(t, sums, units, tname)
        chordplots.fresh_limits(view, key)
        view.set_figure(
            chordplots.traces_draw(name, t, curves, t_of(tb.position()),
                                   key, units[key == "average"], tname),
            header, rows, kind="line",
            name="chords_%s_in_time_%s" % (key, what))

    def _chord_artists(self):
        """The chords on the plot while their section is open: a dot at the
        start, an arrow at the end and the number beyond it."""
        for a in self.artists:
            if a.axes is not None:
                a.remove()
        self.artists = []
        self.tab.mode3d.follow()        # the chords in 3D too
        if self.section not in CHORDS:
            self.tab.canvas.draw_idle()
            return
        ax = self.tab.plot.ax
        for k, (res, look) in enumerate(zip(self.results, self._looks()), 1):
            self.artists += chordplots.draw_chord(
                ax, k, [np.column_stack((res["r"], res["z"]))], look)
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
