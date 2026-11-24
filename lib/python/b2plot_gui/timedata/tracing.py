"""The Run tracing tab of a 2D tab: the tracing files of the latest run in
the run directory (each tab of the page only with its files), the plots of
the quantity chosen in each tab (the profiles and chords at the position
of the slider), and its place glowing on the 2D plot; the time traces and
the profiles and the tallies (b2tallies.nc: volume and face regions) of
the place clicked on the plot."""

import numpy as np

from ...b2plot import labels
from ...qt import QtWidgets, Qt
from ..panels.species import chosen_columns, column_names
from ..tools import chordplots, inspect, measure
from ..tools.sections import LOOK
from . import b2time, plots, traces
from .b2time import AREA_TEXT, B2Time
from .chords import AMU, GROUPS as CHORD_GROUPS, TRIANGLES, ChordFile, \
    line_sums, ordered
from .files import B2TIME, TALLIES, latest, netcdf4
from .marks import Marks, hit
from .page import TracingPage
from .tallies import SURFACE, VOLUME, WHOLE, Tallies

ERRORS = (OSError, RuntimeError, KeyError, ValueError, IndexError)
NEED = {"trace": "No b2time.nc of the latest run in the run directory",
        "chord": "No b2chords.nc or eirenechords.nc of the latest run in "
                 "the run directory (b2mn writes them for the *.chords "
                 "files of the run directory)"}
NEED["profile"] = NEED["trace"]
NEED["vtally"] = NEED["stally"] = "No b2tallies.nc of the latest run in " \
    "the run directory"
TALLY = {"vtally": "v", "stally": "f"}  # the tabs of the tallies: regions
CHORD_TABLE = [g for g, _ in CHORD_GROUPS] + [TRIANGLES]  # always shown
WHOLE_LINK = "<a href='%s'>the whole plasma</a>" % WHOLE
EIRENE = {"natm": "a", "nmol": "m"}     # EIRENE species names of the tab
CLICK = 4.0                         # pixels: a press and release, no pan


class RunTracing:
    """The Run tracing tab of a Tab2D: its page in the quantity column and
    the marks on its plot."""

    def __init__(self, tab):
        self.tab = tab
        self.page = TracingPage(tab.settings)
        self.marks = Marks(tab)
        self.b2time, self.chords = None, {}     # B2Time, name -> ChordFile
        self.looks = {}                 # (file, set) -> how its chords look
        self.chords_drawn = None        # (file, set, chords) on the plot
        self.why, self.shown = "no run", False
        self.marked = None              # what the marks show
        self.place, self.hover = None, None     # of the time traces
        self.shapes = None              # the places on the plot
        self.anchors = (None, {})       # where their names go
        self.profile_place = None       # of the profiles
        self.profile_shapes = None      # their places on the plot
        self.tallies = None             # Tallies
        self.tally_place = {"vtally": None, "stally": None}
        self.chord = None               # the chord clicked (1 ...)
        self._pressed = None            # where the mouse was pressed
        self._pointing = False          # the cursor over a place
        page = self.page
        page.changed.connect(self.redraw)
        page.frames.frames_changed.connect(self.redraw)
        page.show_all.toggled.connect(lambda *_: self.redraw())
        for part in page.parts.values():
            part.chosen.connect(self._chosen)
            part.species.changed.connect(self.redraw)
            part.area.currentIndexChanged.connect(lambda *_: self.redraw())
        chord = page.parts["chord"]
        chord.set_menu.currentIndexChanged.connect(self._set_chosen)
        chord.sums_changed.connect(lambda: self.redraw())
        chord.restyled.connect(self._restyle)
        chord.tabs.currentChanged.connect(self._chord_tab)
        page.parts["vtally"].where.linkActivated.connect(
            lambda place: self.choose_tally_place("vtally", place))
        page.trace_box.changed.connect(self.redraw)
        tab.species_known.connect(self.redraw)
        for name, slot in (("button_press_event", self._press),
                           ("button_release_event", self._release),
                           ("motion_notify_event", self._motion)):
            tab.canvas.mpl_connect(name, slot)

    def ok(self):
        return self.b2time is not None or bool(self.chords) or \
            self.tallies is not None

    def close(self):
        for f in [self.b2time, self.tallies] + list(self.chords.values()):
            if f is not None:
                f.close()
        self.b2time, self.chords, self.tallies = None, {}, None

    # ----------------------------------------------------------------- run
    def set_run(self, run):
        """The tracing files of the latest run of the run: the tabs with
        theirs, their quantities, their frames."""
        self.close()
        self.marks.clear()
        self.marked = self.shapes = self.hover = None
        self.profile_shapes = None
        self.anchors = (None, {})
        self.place = self.profile_place = self.chord = None
        page = self.page
        page.frames.play.setChecked(False)
        if netcdf4() is None:
            paths, notes = {}, ["The run tracing needs the Python module "
                                "netCDF4"]
        else:
            paths, notes = latest(run.rundir, run.state[0])
        for name, path in paths.items():
            try:
                if name == B2TIME:
                    self.b2time = B2Time(path)
                    self.b2time.set_geometry(run.geometry)
                    continue
                if name == TALLIES:
                    self.tallies = Tallies(path)
                    self.tallies.set_geometry(run, inspect.files(run)[0])
                    continue
                f = ChordFile(path)
                f.masses = self._eirene_masses
                if f.sets:
                    self.chords[name] = f
                else:
                    f.close()
                    notes.append("No chords in %s" % name)
            except ERRORS as err:
                notes.append("Cannot read %s: %s" % (name, err))
        b = self.b2time
        page.parts["trace"].set_items(traces.items(b, self.place) if b
                                      else [], always=traces.GROUPS)
        page.parts["profile"].set_items(b.items(self.profile_place) if b
                                        else [], always=b2time.GROUPS)
        tl = self.tallies
        faces = tl.regions("f") if tl else []
        self.tally_place = {"vtally": None, "stally": None}
        for key, groups in (("vtally", VOLUME), ("stally", SURFACE)):
            place = self.tally_place[key]
            page.parts[key].set_items(tl.items(place) if tl and place
                                      else [], always=[g for g, _ in
                                                       groups])
        page.trace_box.set_frames(max(len(b.times) if b else 1,
                                      len(tl.times) if tl else 1))
        page.parts["chord"].set_items([], always=CHORD_TABLE)   # a click
        times = {B2TIME: b.times} if b else {}
        times.update((n, f.times) for n, f in self.chords.items())
        page.frames.set_times(times, B2TIME)
        self._fill_sets()
        have = {"trace": b is not None, "profile": b is not None,
                "chord": bool(self.chords), "vtally": tl is not None,
                "stally": bool(faces)}
        self.why = "\n".join(["no b2time.nc, b2chords.nc, eirenechords.nc "
                              "or b2tallies.nc of the latest run in the run "
                              "directory"] +
                             notes)
        page.set_tabs({k: "" if have[k] else "\n".join([NEED[k]] + notes)
                       for k in have})
        page.fit()

    def set_shown(self, on):
        """The Run tracing tab shown or not (the marks with it)."""
        self.shown = on
        if not on:
            self.page.frames.play.setChecked(False)
        self.marks.set_shown(on)
        if on:
            self.page.fit()
            self.redraw()

    def apply_theme(self):
        for part in self.page.parts.values():
            part.apply_theme()
        self.marked = None
        self.redraw()

    def _fill_sets(self):
        """The sets of chords of the chord files in their menu."""
        menu = self.page.parts["chord"].set_menu
        sets = {}
        for f in self.chords.values():
            sets.update(f.sets)
        menu.blockSignals(True)
        menu.clear()
        for name, label in sets.items():
            menu.addItem(label, name)
        menu.blockSignals(False)
        self._set_chosen(redraw=False)

    def _set_chosen(self, *_, redraw=True):
        """Another set of chords: its tabs and plots, no chord clicked (the
        table grey)."""
        if self.chord is not None:
            self.chord = None
            self.page.parts["chord"].set_items([], always=CHORD_TABLE)
        if redraw:
            self.redraw()

    def _chosen(self, item):
        self.redraw()
        if item is None or item.kind != "profile" or self.b2time is None:
            return
        where = self.b2time.place_text(item)
        self.tab.status.emit("%s: %s" % (item.title(), "at %s, glowing on "
                                          "the plot" % where if where else
                                          "no single place on the plot"))

    # ------------------------------------------------------------ drawing
    def redraw(self, *_):
        """The plot of the tab shown at the position of the slider, the
        marks on the 2D plot."""
        if not self.shown or not self.ok():
            return
        part, key = self.page.part(), self.page.key()
        item = part.current
        if key not in ("trace", "vtally", "stally"):
            self._file(item.file if item is not None else B2TIME if
                       key != "chord" else next(iter(self.chords), None))
        try:
            if key == "trace":
                self._trace(part, item)
            elif key in TALLY:
                self._tally(part, item, key)
            elif key == "chord":
                self._chord(part, item)
            elif self.b2time is not None:
                self._profiles(part, item)
            else:
                self._mark(None)
                part.clear()
        except ERRORS as err:
            part.show_plot(False, "Cannot read %s: %s" % (
                item.name if item is not None else "the file", err))

    def _mark(self, key, places=False, **what):
        """The marks of what (Marks.show, with places Marks.places), again
        only when key changed."""
        if key != self.marked or key is None:
            self.marked = key
            (self.marks.places if places else self.marks.show)(**what)

    def _eirene_masses(self):
        """{a, m: [mass (kg) of each EIRENE atom, molecule]} from the species
        of the run (b2plot massa, massm), for the chord quantities."""
        out = {}
        for n in getattr(self.tab.species, "neutrals", []):
            out.setdefault(n.stack, {})[n.column] = n.mass * AMU
        return {k: [v.get(i, np.nan) for i in range(max(v) + 1)]
                for k, v in out.items()}

    def _species(self, part, item, n):
        """(columns summed, species text, [(species, (column,))] of a choice
        of a curve per species or None) of the item, as chosen in the
        species menu of its table (grey without species)."""
        if not item.dim:
            part.species.set_columns([""])
            return (0,), "", None
        tab = self.tab
        names = [labels.species_text(s) for s in (tab._species() or [])] \
            if item.dim == "ns" else list(tab.eirene_names.get(
                EIRENE.get(item.dim), []))
        names = [names[i] if i < len(names) and names[i] else
                 "species %d" % (i + 1) for i in range(n)]
        menu = part.species
        menu.set_columns(names)
        text = menu.text()
        curves = [(name, (c,)) for name, c in menu.curves()] if \
            menu.is_multi() else None
        return chosen_columns(column_names(names), text), text, curves

    def _show_all(self, ok):
        """Show all only with one curve (a curve per species: off, grey)."""
        box = self.page.show_all
        if not ok and box.isChecked():
            box.blockSignals(True)
            box.setChecked(False)
            box.blockSignals(False)
        box.setEnabled(ok)

    def _chord_tab(self, *_):
        """Another chord tab: its chord glowing (once one was clicked);
        with a curve per species, its sums in time."""
        part = self.page.parts["chord"]
        if self.page.key() != "chord":
            return
        k = part.tabs.currentIndex() + 1
        if self.chord is not None and k >= 1 and k != self.chord:
            self.chord = k
            self.redraw_marks()
        if part.current is not None and part.species.is_multi():
            self.redraw()

    def _file(self, f):
        """The frames of file f, the time shown kept (one frame)."""
        box = self.page.frames
        if f == box.file or f not in box.times:
            return
        t = box.time_value()
        box.set_file(f)
        if t is not None and box.key() == "frame":
            box.jump(int(np.argmin(np.abs(np.asarray(box.times[f]) - t)))
                     + 1, silent=False)

    def _rhop(self, r, z, values):
        """rho poloidal at the points where the values are a function of
        it, or None."""
        psimap = self.tab.run.psimap if self.tab.run is not None else None
        if psimap is None:
            return None
        rho = psimap.rhop(r, z)
        return rho if measure.single_valued(rho, values) else None

    @staticmethod
    def _x_axes(view, xs):
        """The x axes of a profile offered (rho_p shown first, else the
        distance from the separatrix: FigureView.allow)."""
        view.options.allow(set(xs))

    # -------------------------------------------------------- time traces
    def _trace(self, part, item):
        """The places on the plot (the one chosen glowing), the time trace
        chosen at the place (separatrix and maximum of a state variable at
        a target) with what is shown with it."""
        b, box = self.b2time, self.page.trace_box
        self.redraw_marks()
        name = traces.PLACES.get(self.place)
        part.where.setText("<b>%s</b>: click another place on the plot for "
                           "its time traces" % b.side_text(name) if name
                           else "Click a place on the plot for its time "
                           "traces")
        part.where.show()
        if item is None:
            part.clear()
            return
        n = len(b.nc.dimensions[item.dim]) if item.dim else 1
        cols, species, each = self._species(part, item, n)
        curves = traces.curves(b, item, cols) if each is None else [
            ("%s, %s" % (name, label.lower()) if label else name, y)
            for name, c in each for label, y in traces.curves(b, item, c)]
        draw, header, rows, text = plots.time_trace(
            b.times, curves, box.key(), box.window.value(),
            item.title(species), item.unit)
        part.view.set_figure(draw, header, rows, name=item.label)
        part.show_plot(True, text)

    def _shapes(self):
        """The places of the time traces on the plot (once per run: the
        faces from the geometry file of the run)."""
        if self.shapes is None:
            QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                geo = inspect.files(self.tab.run)[0]
                self.shapes = traces.shapes(self.b2time,
                                            self.tab.run.geometry, geo)
                self.anchors = traces.anchors(self.shapes)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
        return self.shapes

    def _picking(self, event):
        """The time traces or the profiles shown, the mouse on the plot
        with no tool."""
        tab = self.tab
        key = self.page.key()
        return self.shown and (key in ("trace", "profile") and
                               self.b2time is not None or key in TALLY and
                               self.tallies is not None or key == "chord"
                               and self.chords_drawn is not None) and \
            event.inaxes is tab.plot.ax and \
            event.xdata is not None and tab.tools.bar.mode is None and \
            not str(tab.toolbar.mode)

    def _at(self, event):
        """The place under the mouse: its name, the separatrix point, a
        target, a boundary, else the plasma (anywhere else in the grid), or
        None; with the profiles a line of their cells or its name."""
        x, y = event.xdata, event.ydata
        key = self.page.key()
        if key == "chord":
            shapes = self._chord_shapes()
            return hit(self.tab.plot.ax, shapes, list(shapes), x, y)
        if key in TALLY:
            tl, ax = self.tallies, self.tab.plot.ax
            named = self.marks.name_at(event.x, event.y)
            if named is not None or key == "stally":
                return named or hit(ax, tl.shapes, tl.regions("f"), x, y)
            finder = self.tab.plot.finder
            tri = int(finder(x, y)) if finder is not None else -1
            return tl.region_at(int(self.tab.run.geometry.tri_cell[tri])) \
                if tri >= 0 else None
        shapes = self._shapes()
        if key == "profile":
            return self.marks.name_at(event.x, event.y) or hit(
                self.tab.plot.ax, self._profile_shapes(), b2time.SHOWN, x, y)
        place = self.marks.name_at(event.x, event.y) or hit(
            self.tab.plot.ax, shapes, traces.SHOWN, x, y)
        finder = self.tab.plot.finder
        if place is None and finder is not None and int(finder(x, y)) >= 0:
            place = "plasma"
        return place

    def _motion(self, event):
        """The place under the mouse brighter, a pointing hand over it."""
        tab = self.tab
        if tab._pan is not None and tab._pan[3]:
            return
        place = self._at(event) if self._picking(event) else None
        if place is not None:           # again after each draw (matplotlib
            tab.canvas.setCursor(Qt.PointingHandCursor)     # sets its own)
        elif self._pointing:
            tab.canvas.unsetCursor()
        self._pointing = place is not None
        hover = place if place != self._place_now() else None
        if hover != self.hover:
            self.hover = hover
            self.redraw_marks()

    def _press(self, event):
        self._pressed = (event.x, event.y) if event.button == 1 and \
            self._picking(event) else None

    def _release(self, event):
        pressed, self._pressed = self._pressed, None
        if pressed is None or not self._picking(event) or np.hypot(
                event.x - pressed[0], event.y - pressed[1]) > CLICK:
            return
        place = self._at(event)
        if place is not None and self.page.key() == "chord":
            self.choose_chord(int(place[1:]))
        elif place is not None and self.page.key() in TALLY:
            self.choose_tally_place(self.page.key(), place)
        elif place is not None and self.page.key() == "profile":
            self.choose_profile_place(place)
        elif place is not None:
            self.choose_place(place)

    def choose_place(self, place):
        """The time traces of a place of the plot in the table, the same
        quantity chosen there if it has it."""
        part = self.page.parts["trace"]
        old = part.current
        self.place, self.hover = place, None
        items = traces.items(self.b2time, place)
        part.set_items(items, keep=True, always=traces.GROUPS)
        same = next((q for q in items if old is not None and
                     traces.key(q) == traces.key(old)), None)
        if same is not None:
            part.select(same)
        self.redraw()
        name = traces.PLACES.get(place)
        self.tab.status.emit("%s: its time traces in the table" %
                             self.b2time.side_text(name) if name else
                             "The integrated quantities of the plasma in "
                             "the table")

    def _place_now(self):
        """The place chosen in the tab shown."""
        key = self.page.key()
        if key == "chord":
            return None if self.chord is None else "c%d" % self.chord
        return self.tally_place.get(key) if key in TALLY else \
            self.profile_place if key == "profile" else self.place

    def _chord_shapes(self):
        """{"c1" ...: ("lines", segments)} of the chords on the plot."""
        if self.chords_drawn is None:
            return {}
        _, _, chords = self.chords_drawn
        out = {}
        for k, c in enumerate(chords, 1):
            xy = np.column_stack((c.r, c.z))
            seg = [np.stack((xy[a:b][:-1], xy[a:b][1:]), axis=1)
                   for a, b in c.parts() if b - a > 1]
            if seg:
                out["c%d" % k] = ("lines", np.concatenate(seg))
        return out

    def choose_chord(self, k):
        """Chord k clicked on the plot: the quantities of the chord files in
        the table (the same one chosen again), its tab shown."""
        part = self.page.parts["chord"]
        old, first = part.current, self.chord is None
        self.chord = k
        if first:
            items = ordered([i for f in self.chords.values()
                             for i in f.items()])
            part.set_items(items, always=CHORD_TABLE)
            same = next((q for q in items if old is not None and
                         q.name == old.name), None)
            if same is not None:
                part.select(same)
        part.tabs.setCurrentIndex(k - 1)
        self.redraw()
        self.tab.status.emit("Chord %d: the quantities along the chords in "
                             "the table" % k)

    def choose_tally_place(self, key, place):
        """The tallies of a region of the plot in the table of the tab key,
        the same quantity chosen there if it has it."""
        part = self.page.parts[key]
        old = part.current
        self.tally_place[key], self.hover = place, None
        items = self.tallies.items(place)
        part.set_items(items, keep=True, always=[
            g for g, _ in (VOLUME if key == "vtally" else SURFACE)])
        same = next((q for q in items if old is not None and
                     q.name == old.name), None)
        if same is not None:
            part.select(same)
        self.redraw()
        self.tab.status.emit("%s: its tallies in the table" %
                             self.tallies.names.get(place, place))

    def _tally(self, part, item, key):
        """The regions on the plot (the one chosen glowing), the time trace
        of the tally chosen there."""
        tl, box = self.tallies, self.page.trace_box
        self.redraw_marks()
        place = self.tally_place.get(key)
        what = "region" if key == "vtally" else "face region"
        text = ("<b>%s</b>: click another %s on the plot for its tallies" %
                (tl.names.get(place, place), what) if place else
                "Click a %s on the plot for its tallies" % what)
        if key == "vtally":
            text += ", or " + WHOLE_LINK if place != WHOLE else ""
        part.where.setText(text)
        part.where.show()
        if item is None:
            part.clear()
            return
        cols, species, each = self._species(part, item,
                                            tl.species_count(item))
        curves = tl.curves(item, cols) if each is None else [
            (name, tl.curves(item, c)[0][1]) for name, c in each]
        draw, header, rows, text = plots.time_trace(
            tl.times, curves, box.key(), box.window.value(),
            item.title(species), item.unit)
        part.view.set_figure(draw, header, rows, name=item.label + "_" +
                             item.place)
        part.show_plot(True, text)

    def choose_profile_place(self, place):
        """The profiles of a place of the plot in the table, the same
        quantity chosen there if it has it."""
        part = self.page.parts["profile"]
        old = part.current
        self.profile_place, self.hover = place, None
        items = self.b2time.items(place)
        part.set_items(items, keep=True, always=b2time.GROUPS)
        same = next((q for q in items if old is not None and
                     q.name.split("3d")[0] == old.name.split("3d")[0]),
                    None)
        if same is not None:
            part.select(same)
        self.redraw()
        self.tab.status.emit("%s: its profiles in the table" %
                             self.b2time.side_text(b2time.NAMES[place]))

    def _profile_shapes(self):
        """The places of the profiles on the plot: the lines of their cell
        centres, the targets on their faces (as the time traces)."""
        if self.profile_shapes is None:
            shapes = self.b2time.shapes()
            faces = self._shapes()
            for k in ("target_w", "target_e"):
                if k in shapes and k in faces:
                    shapes[k] = faces[k]
            self.profile_shapes = shapes
        return self.profile_shapes

    def redraw_marks(self):
        """The places again with their names (the one under the mouse,
        the name of the one clicked bold), not the plot."""
        part = self.page.parts["trace"]
        key = self.page.key()
        if self.shown and key == "chord" and self.chords_drawn is not None:
            f, name, chords = self.chords_drawn
            self._chord_marks(f, name, chords,
                              self._looks(f, name, len(chords)))
        if self.shown and key in TALLY and self.tallies is not None:
            tl = self.tallies
            place = self.tally_place.get(key)
            keys = tl.regions(TALLY[key])
            shown = [k for k in keys if k in tl.shapes]
            chosen = (place,) + ((("a" + place),) if key == "vtally" and
                                 place != WHOLE else ()) if place else ()
            if place == WHOLE:          # the whole plasma: every region
                chosen = tuple("a" + k for k in shown)
            names = []                  # the regions without their names
            hover = self.hover
            if key == "vtally" and hover and "a" + hover in tl.shapes:
                hover = (hover, "a" + hover)    # its cells shown lightly
            self._mark((key, chosen, self.hover), places=True,
                       shapes=tl.shapes, shown=shown, chosen=chosen,
                       hover=hover, names=names, centre=tl.centre)
        if self.shown and self.page.key() == "profile" and \
                self.b2time is not None:
            shapes = self._profile_shapes()
            centre = self.anchors[0] if self.shapes is not None else None
            at = self.b2time.anchors(shapes, centre)
            chosen = (self.profile_place,)
            names = [(k, self.b2time.side_text(b2time.NAMES[k])) + at[k] +
                     (k == self.profile_place,) for k in b2time.SHOWN
                     if k in at]
            self._mark(("profile", chosen, self.hover), places=True,
                       shapes=shapes, shown=b2time.SHOWN, chosen=chosen,
                       hover=self.hover, names=names, centre=centre)
        if self.shown and self.page.key() == "trace":
            item = part.current
            chosen = traces.mark(item) if item is not None else \
                (self.place,)
            shapes = self._shapes()
            centre, at = self.anchors
            names = [(k, self.b2time.side_text(traces.PLACES[k])) + at[k] +
                     (k == self.place,) for k in traces.SHOWN if k in at]
            self._mark(("trace", chosen, self.hover, self.place),
                       places=True, shapes=shapes, shown=traces.SHOWN,
                       chosen=chosen, hover=self.hover, names=names,
                       centre=centre)

    def _profiles(self, part, item):
        """The places of the profiles on the plot (the one chosen glowing),
        the profile chosen there."""
        self._shapes()                  # the centre of the grid
        self.redraw_marks()
        name = b2time.NAMES.get(self.profile_place)
        part.where.setText("<b>%s</b>: click another place on the plot for "
                           "its profiles" % self.b2time.side_text(name)
                           if name else "Click a place on the plot for its "
                           "profiles")
        part.where.show()
        if item is None:
            part.area.hide()
            part.clear()
            return
        self._profile(part, item)

    def _profile(self, part, item):
        box, b = self.page.frames, self.b2time
        cols, species, each = self._species(part, item,
                                            b.species_count(item))
        self._show_all(each is None)
        areas = b.areas(item)
        part.area.setVisible(len(areas) > 1)
        area = part.area.currentData() if len(areas) > 1 else "target"
        a = b.series(item, cols if each is None else each[0][1], area)
        xs = {"dssep": b.distance(item)}
        line = b.lines.get(item.place)
        if line is not None:
            xs.update(R=line[:, 0], Z=line[:, 1],
                      rhop=self._rhop(line[:, 0], line[:, 1], a[-1]))
        xs = {k: v for k, v in xs.items() if v is not None and
              len(v) == a.shape[1]}
        self._x_axes(part.view, xs)
        draw, header, rows, kind = plots.profile(
            xs, a if each is None else [(name, b.series(item, c, area))
                                        for name, c in each],
            box, self.page.show_all.isChecked(), item.title(species) + (
                ", " + AREA_TEXT[area] if areas else ""), item.unit)
        part.view.set_figure(draw, header, rows, kind=kind, name=item.label,
                             space=True)
        part.show_plot(True, box.time_text())

    def _looks(self, f, name, n):
        """How the n chords of the set are drawn on the plot (each as its
        tab says, at first red, dashed, numbered)."""
        looks = self.looks.setdefault((f.name if f else "", name), [])
        looks += [LOOK] * (n - len(looks))
        return looks

    def _restyle(self):
        """A chord drawn as its tab says now."""
        part = self.page.parts["chord"]
        if self.chords_drawn is None:
            return
        f, name, chords = self.chords_drawn
        looks = self._looks(f, name, len(chords))
        for k, tab in enumerate(part.chords[:len(chords)]):
            looks[k] = tab.look()
        self._chord_marks(f, name, chords, looks)

    def _chord_marks(self, f, name, chords, looks):
        """The chords of the set on the plot, the one clicked glowing (the
        one under the mouse lighter)."""
        self.chords_drawn = (f, name, chords)
        hover = int(self.hover[1:]) if self.page.key() == "chord" and \
            self.hover and self.hover.startswith("c") else None
        self._mark(("chord", f.name if f else "", name, tuple(looks),
                    self.chord, hover),
                   chords=[(k, [np.column_stack((c.r, c.z))[a:b]
                                for a, b in c.parts()], look)
                           for k, (c, look) in enumerate(zip(chords, looks),
                                                         1)],
                   chosen=self.chord, hover=hover)

    def _chord(self, part, item):
        """The chords of the set on the plot (each as its tab says), a tab
        per chord (its ends, its line integral and average at the position,
        its profile) and the line integrals or averages against the chord
        number and in time, as in the Chords section of the plots."""
        name = part.set_menu.currentData()
        f = self.chords.get(item.file) if item is not None else next(
            iter(self.chords.values()), None)
        chords = f.chords.get(name, []) if f is not None else []
        looks = self._looks(f, name, len(chords))
        part.set_count(len(chords))
        for k, (tab, c) in enumerate(zip(part.chords, chords)):
            tab.set_look(looks[k])
            tab.ends.set((c.r[0], c.z[0], c.phi[0], c.r[-1], c.z[-1],
                          c.phi[-1]) if len(c.r) else (0.0,) * 6,
                         lambda *_: None)
            part.tabs.setTabToolTip(k, "Chord %d of %s" % (
                c.number, part.set_menu.currentText()))
        self._chord_marks(f, name, chords, looks)
        part.where.setText("<b>Chord %d</b>: click another chord on the "
                           "plot to show its tab" % self.chord if self.chord
                           else "Click a chord on the plot for the "
                           "quantities along the chords")
        part.where.show()
        if item is None:
            part.clear()
            return
        if not chords:
            part.show_plot(False, "No chord of this set crosses the grid "
                           "of %s" % f.name)
            return
        box = self.page.frames
        cols, species, each = self._species(part, item,
                                            f.species_count(item))
        self._show_all(each is None)
        if each is not None:
            return self._chord_species(part, item, f, chords, each, species)
        title = item.title(species)
        units = (measure.times_m(item.unit, 1), item.unit)
        sums, values = [], []
        for k, (tab, chord) in enumerate(zip(part.chords, chords), 1):
            a = f.profile(item, chord, cols)
            if a is None:               # not along this chord
                nan = np.full(len(f.times), np.nan)
                sums.append((nan, nan))
                values.append((np.nan, np.nan))
                tab.text.setText("%s is not along this chord" % title)
                tab.view.hide()
                continue
            tab.view.show()
            integral, average = line_sums(chord, a)
            self._chord_profile(tab.view, chord, a, box, title, k, item)
            ys = [plots.minus_reference(y, box) for y in (integral, average)]
            v = [float(plots.at_position(y, box)) for y in ys]
            sums.append(tuple(ys))
            values.append(tuple(v))
            tab.text.setText(chordplots.two_rows(v[0], v[1], units))
        key = part.board.key()
        kk = key == "average"
        if len(chords) >= 2:
            chordplots.fresh_limits(part.sums, key)
            part.sums.set_figure(
                chordplots.sums_draw(title, [v[kk] for v in values], key,
                                     units[kk]),
                ["chord", "integral (%s)" % units[0],
                 "average (%s)" % units[1]],
                [[k, v[0], v[1]] for k, v in enumerate(values, 1)],
                kind="sums", name="%s_chords_%s" % (item.name, key))
        t = np.asarray(f.times, float)
        t_now = box.time_value() if len(t) else None
        header, rows = chordplots.traces_rows(t, sums, units)
        chordplots.fresh_limits(part.trace, key)
        part.trace.set_figure(
            chordplots.traces_draw(
                "Line %s, %s" % (key, title[:1].lower() + title[1:]), t,
                [("Chord %d" % k, s[kk]) for k, s in enumerate(sums, 1)],
                t_now, key, units[kk]),
            header, rows, kind="line",
            name="%s_chords_%s_in_time" % (item.name, key))
        part.show_plot(True, box.time_text())

    def _chord_species(self, part, item, f, chords, each, species):
        """The chords with a curve per species (each [(species, columns)]):
        in each tab the profiles of the species, against the chord number
        markers of each species, in time the species of the chord of the
        tab shown."""
        box = self.page.frames
        title = item.title(species)
        units = (measure.times_m(item.unit, 1), item.unit)
        names = [name for name, _ in each]
        nan = np.full(len(f.times), np.nan)
        sums = []                       # per chord [(integrals, averages)]
        for k, (tab, chord) in enumerate(zip(part.chords, chords), 1):
            a = [(name, f.profile(item, chord, c)) for name, c in each]
            if any(y is None for _, y in a):
                sums.append([(nan, nan)] * len(each))
                tab.text.setText("%s is not along this chord" % title)
                tab.view.hide()
                continue
            tab.view.show()
            got = [tuple(plots.minus_reference(y, box) for y in
                         line_sums(chord, v)) for _, v in a]
            sums.append(got)
            self._chord_profile(tab.view, chord, a, box, title, k, item)
            now = [[float(plots.at_position(y, box)) for y in g]
                   for g in got]
            tab.text.setText(chordplots.two_rows(
                [(n, v[0]) for n, v in zip(names, now)],
                [(n, v[1]) for n, v in zip(names, now)], units))
        key = part.board.key()
        kk = key == "average"
        if len(chords) >= 2:
            values = [[[float(plots.at_position(y, box)) for y in g]
                       for g in per] for per in sums]
            chordplots.fresh_limits(part.sums, key)
            part.sums.set_figure(
                chordplots.sums_draw(title, [(n, [v[s][kk] for v in values])
                                             for s, n in enumerate(names)],
                                     key, units[kk]),
                ["chord"] + ["%s %s (%s)" % (n, w, u) for n in names
                             for w, u in zip(("integral", "average"),
                                             units)],
                [[k] + [x for v in per for x in v]
                 for k, per in enumerate(values, 1)],
                kind="sums", name="%s_chords_%s" % (item.name, key))
        j = min(max(part.tabs.currentIndex(), 0), len(sums) - 1)
        t = np.asarray(f.times, float)
        t_now = box.time_value() if len(t) else None
        header, rows = chordplots.traces_rows(t, sums[j], units,
                                              names=names)
        chordplots.fresh_limits(part.trace, key)
        part.trace.set_figure(
            chordplots.traces_draw(
                "Line %s, chord %d, %s" % (key, j + 1, title[:1].lower() +
                                           title[1:]), t,
                [(n, s[kk]) for n, s in zip(names, sums[j])],
                t_now, key, units[kk]),
            header, rows, kind="line",
            name="%s_chord_%d_%s_in_time" % (item.name, j + 1, key))
        part.show_plot(True, box.time_text())

    def _chord_profile(self, view, chord, a, box, title, k, item):
        """The profile of chord k (a: nt, npt; or [(species, (nt, npt))])
        in its tab."""
        cut = [b for _, b in chord.parts()[:-1]]

        def gaps(v):                    # no line over the parts left out
            return np.insert(np.asarray(v, float), cut, np.nan, axis=-1)
        each = a if isinstance(a, list) else None
        a = a[0][1] if each else a
        xs = {"s": chord.ds, "R": chord.r, "Z": chord.z}
        rho = self._rhop(chord.r, chord.z, a[-1])
        if rho is not None:
            xs["rhop"] = rho
            dsep = measure.separatrix_distance(chord.ds, rho)
            if dsep is not None and measure.single_valued(dsep, a[-1]):
                xs["dssep"] = dsep
        xs = {key: gaps(v) for key, v in xs.items()}
        self._x_axes(view, xs)
        draw, header, rows, kind = plots.profile(
            xs, gaps(a) if each is None else [(n, gaps(y)) for n, y in each],
            box, self.page.show_all.isChecked(),
            "%s, chord %d" % (title, k), item.unit,
            extra={"phi": gaps(chord.phi)})
        view.set_figure(draw, header, rows, kind=kind, space=True,
                        name="%s_chord_%d" % (item.name, k))
