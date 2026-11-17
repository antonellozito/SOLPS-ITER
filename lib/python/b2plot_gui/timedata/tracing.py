"""The Run tracing tab of a 2D tab: the tracing files of the latest run in
the run directory (each tab of the page only with its files), the plots of
the quantity chosen in each tab (the profiles and chords at the position
of the slider), and its place glowing on the 2D plot; the time traces of
the place clicked on the plot."""

import numpy as np

from ...b2plot import labels
from ...qt import QtWidgets, Qt
from ..panels.species import chosen_columns, column_names
from ..tools import inspect, measure
from . import plots, traces
from .b2time import B2Time
from .chords import ChordFile, line_sums
from .files import B2TIME, latest, netcdf4
from .marks import Marks, hit
from .page import TracingPage

ERRORS = (OSError, RuntimeError, KeyError, ValueError, IndexError)
NEED = {"trace": "No b2time.nc of the latest run in the run directory",
        "chord": "No b2chords.nc or eirenechords.nc of the latest run in "
                 "the run directory (b2mn writes them for the *.chords "
                 "files of the run directory)"}
NEED["profile"] = NEED["trace"]
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
        self.why, self.shown = "no run", False
        self.marked = None              # what the marks show
        self.place, self.hover = "omp", None    # of the time traces
        self.shapes = None              # the places on the plot
        self.anchors = (None, {})       # where their names go
        self._pressed = None            # where the mouse was pressed
        self._pointing = False          # the cursor over a place
        page = self.page
        page.changed.connect(self.redraw)
        page.frames.frames_changed.connect(self.redraw)
        page.show_all.toggled.connect(lambda *_: self.redraw())
        for part in page.parts.values():
            part.chosen.connect(self._chosen)
            part.species.changed.connect(self.redraw)
        chord = page.parts["chord"]
        chord.set_menu.currentIndexChanged.connect(self._set_chosen)
        chord.chord_menu.currentIndexChanged.connect(
            lambda *_: self.redraw())
        chord.which.currentIndexChanged.connect(lambda *_: self.redraw())
        page.trace_box.changed.connect(self.redraw)
        tab.species_known.connect(self.redraw)
        for name, slot in (("button_press_event", self._press),
                           ("button_release_event", self._release),
                           ("motion_notify_event", self._motion)):
            tab.canvas.mpl_connect(name, slot)

    def ok(self):
        return self.b2time is not None or bool(self.chords)

    def close(self):
        for f in [self.b2time] + list(self.chords.values()):
            if f is not None:
                f.close()
        self.b2time, self.chords = None, {}

    # ----------------------------------------------------------------- run
    def set_run(self, run):
        """The tracing files of the latest run of the run: the tabs with
        theirs, their quantities, their frames."""
        self.close()
        self.marks.clear()
        self.marked = self.shapes = self.hover = None
        self.anchors = (None, {})
        self.place = "omp"
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
                f = ChordFile(path)
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
        page.parts["profile"].set_items(b.items() if b else [])
        page.trace_box.set_frames(len(b.times) if b else 1)
        page.parts["chord"].set_items([i for f in self.chords.values()
                                       for i in f.items()])
        times = {B2TIME: b.times} if b else {}
        times.update((n, f.times) for n, f in self.chords.items())
        page.frames.set_times(times, B2TIME)
        self._fill_sets()
        have = {"trace": b is not None, "profile": b is not None,
                "chord": bool(self.chords)}
        self.why = "\n".join(["no b2time.nc, b2chords.nc or eirenechords.nc "
                              "of the latest run in the run directory"] +
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
        """A set of chords: its chords in the chord menu (the same number
        kept)."""
        part = self.page.parts["chord"]
        name = part.set_menu.currentData()
        numbers = sorted({c.number for f in self.chords.values()
                          for c in f.chords.get(name, [])})
        menu = part.chord_menu
        old = menu.currentData()
        menu.blockSignals(True)
        menu.clear()
        for n in numbers:
            menu.addItem("%d" % n, n)
        if old in numbers:
            menu.setCurrentIndex(numbers.index(old))
        menu.blockSignals(False)
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
        if key != "trace":
            self._file(item.file if item is not None else B2TIME if
                       key != "chord" else next(iter(self.chords), None))
        try:
            if key == "trace":
                self._trace(part, item)
            elif key == "chord":
                self._chord(part, item)
            elif item is not None and self.b2time is not None:
                self._mark((key, item.name, item.index),
                           place=self.b2time.place(item),
                           label=self._label(item))
                self._profile(part, item)
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

    def _label(self, item):
        where = self.b2time.place_text(item).replace("the ", "", 1)
        return where[:1].upper() + where[1:]

    def _species(self, part, item, n):
        """(columns summed, species text) of the item, as chosen in the
        species menu of its table (grey without species)."""
        if not item.dim:
            part.species.set_columns([""])
            return (0,), ""
        tab = self.tab
        names = [labels.species_text(s) for s in (tab._species() or [])] \
            if item.dim == "ns" else list(tab.eirene_names.get(
                EIRENE.get(item.dim), []))
        names = [names[i] if i < len(names) and names[i] else
                 "species %d" % (i + 1) for i in range(n)]
        part.species.set_columns(names)
        text = part.species.text()
        return chosen_columns(column_names(names), text), text

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
        """The x axes of a profile offered (the first one if the one chosen
        is not)."""
        axis = view.options.xaxis
        if axis.currentData() not in xs:
            axis.blockSignals(True)
            axis.setCurrentIndex(max(axis.findData(next(iter(xs))), 0))
            axis.blockSignals(False)
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
        cols, species = self._species(part, item, n)
        draw, header, rows, text = plots.time_trace(
            b.times, traces.curves(b, item, cols), box.key(),
            box.window.value(), item.title(species), item.unit)
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
        """The time traces shown, the mouse on the plot with no tool."""
        tab = self.tab
        return self.shown and self.page.key() == "trace" and \
            self.b2time is not None and event.inaxes is tab.plot.ax and \
            event.xdata is not None and tab.tools.bar.mode is None and \
            not str(tab.toolbar.mode)

    def _at(self, event):
        """The place under the mouse: its name, the separatrix point, a
        target, a boundary, else the plasma (anywhere else in the grid), or
        None."""
        shapes = self._shapes()
        x, y = event.xdata, event.ydata
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
        hover = place if place != self.place else None
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
        if place is not None:
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

    def redraw_marks(self):
        """The places again with their names (the one under the mouse,
        the name of the one clicked bold), not the plot."""
        part = self.page.parts["trace"]
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

    def _profile(self, part, item):
        box, b = self.page.frames, self.b2time
        cols, species = self._species(part, item, b.species_count(item))
        a = b.series(item, cols)
        xs = {"dssep": b.distance(item)}
        line = b.lines.get(item.place)
        if line is not None:
            xs.update(R=line[:, 0], Z=line[:, 1],
                      rhop=self._rhop(line[:, 0], line[:, 1], a[-1]))
        xs = {k: v for k, v in xs.items() if v is not None and
              len(v) == a.shape[1]}
        self._x_axes(part.view, xs)
        draw, header, rows, kind = plots.profile(
            xs, a, box, self.page.show_all.isChecked(), item.title(species),
            item.unit)
        part.view.set_figure(draw, header, rows, kind=kind, name=item.label)
        part.show_plot(True, box.time_text())

    def _chord(self, part, item):
        """The chords of the set on the plot (the one chosen glowing), its
        profile and its line integrals or averages in time."""
        name = part.set_menu.currentData()
        number = part.chord_menu.currentData()
        f = self.chords.get(item.file) if item is not None else next(
            iter(self.chords.values()), None)
        chords = f.chords.get(name, []) if f is not None else []
        self._mark(("chord", f.name if f else "", name, number),
                   chords=[(c.number, [np.column_stack((c.r, c.z))[a:b]
                                       for a, b in c.parts()])
                           for c in chords], current=number)
        if item is None:
            part.clear()
            return
        chord = f.chord(name, number)
        if chord is None:
            part.show_plot(False, "Chord %s is not in %s: it does not cross "
                           "its grid" % (number, f.name))
            return
        box = self.page.frames
        cols, species = self._species(part, item, f.species_count(item))
        a = f.profile(item, chord, cols)
        integral, average = line_sums(chord, a)
        cut = [b for _, b in chord.parts()[:-1]]

        def gaps(v):                    # no line over the parts left out
            return np.insert(np.asarray(v, float), cut, np.nan, axis=-1)
        xs = {"s": chord.ds, "R": chord.r, "Z": chord.z}
        rho = self._rhop(chord.r, chord.z, a[-1])
        if rho is not None:
            xs["rhop"] = rho
            dsep = measure.separatrix_distance(chord.ds, rho)
            if dsep is not None and measure.single_valued(dsep, a[-1]):
                xs["dssep"] = dsep
        xs = {k: gaps(v) for k, v in xs.items()}
        self._x_axes(part.view, xs)
        title = "%s, chord %d" % (item.title(species), number)
        draw, header, rows, kind = plots.profile(
            xs, gaps(a), box, self.page.show_all.isChecked(), title,
            item.unit, extra={"phi": gaps(chord.phi)})
        part.view.set_figure(draw, header, rows, kind=kind,
                             name="%s_chord_%d" % (item.name, number))
        units = (measure.times_m(item.unit, 1), item.unit)
        values = [float(plots.at_position(plots.minus_reference(y, box),
                                          box)) for y in (integral, average)]
        which = part.which.currentData()
        k = which == "average"
        draw, header, rows, _ = plots.trace(
            f.times, average if k else integral, box,
            "Line %s, %s" % (which, title[:1].lower() + title[1:]), units[k])
        part.sums.set_figure(draw, header, rows, name="%s_chord_%d_%s" % (
            item.name, number, which))
        html = measure.html_unit
        part.show_plot(True, "%s: line integral %.5g %s, line average "
                       "%.5g %s" % (box.time_text(), values[0],
                                    html(units[0]), values[1],
                                    html(units[1])))
