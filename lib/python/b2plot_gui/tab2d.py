"""2D tab: quantity panel, one fixed plot, layers panel."""

import json
import re
import socket
from dataclasses import replace

import numpy as np
from matplotlib.figure import Figure

from . import catalog, presets
from .plot import shapes
from .plot.canvas import Plot2D
from .plot.styles import KINDS_FLAT, LAYERS
from .model import split_unit
from ..qt import (FigureCanvasQTAgg, NavigationToolbar2QT, QtCore,
                  QtWidgets, Qt, Signal)
from .panels.layers import LayersPanel, from_dict
from .panels.calculator import CalculatorDialog
from .panels.quantity import QuantityPanel, column_names
from .panels.views import ViewBar
from .output import state
from .output.actions import TabOutput
from .output.frames import FrameExport
from .tools.control import Tools

MASSES = {"massa": "a", "massm": "m"}   # b2plot label: Eirene stack
MARKS = {"iimp": ("IMP", np.argmin), "iomp": ("OMP", np.argmax)}
WARNINGS = ("no data found", "not found", "no adas file", "faulty",
            "not recognized", "error")      # in what b2plot prints


def _scrolled(widget, width):
    area = QtWidgets.QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setMinimumWidth(width)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    return area


class Tab2D(TabOutput, QtWidgets.QWidget):
    """The 2D plots tab; data requests go through the main window."""

    request = Signal(object)        # (role, Quantity, operations, source)
    export = Signal(object)         # (Quantity, names, paths, ops, table,
                                    #  source)
    add_to_page = Signal(object)    # Snapshot
    status = Signal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.run = None
        self.data = None
        self.wanted = None
        self.odata = {}                 # overlay role -> Field or Vector
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(420, 420)
        self.plot = Plot2D(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.quantity = QuantityPanel()
        self.quantity.quantity_chosen.connect(self._chosen)
        self.quantity.style_changed.connect(self._options_changed)
        self.quantity.seed_line.connect(
            lambda: self.tools.bar.set_mode("seeds"))
        self.quantity.streams.seed_preset.connect(self._seed_preset)
        self.quantity.traj_box.draw.connect(self._draw_trajectories)
        self.quantity.traj_box.clear.connect(self._clear_trajectories)
        self.quantity.calculator.connect(self.open_calculator)
        self.time_box = self.quantity.time_box
        self.time_box.source_changed.connect(self._source_changed)
        self.time_box.frames_changed.connect(self._fetch)
        self.frames = FrameExport(self)
        self.maps = state.MapsJob(self)
        self.time_box.export_frames.connect(lambda: self.frames.start())
        self.time_box.ready = self._shown
        self.final_quantities, self.movie_quantities = [], []
        self.layers = LayersPanel(self._saved_layers())
        self.layers.changed.connect(self._layer_changed)
        for key, st in self.layers.styles().items():
            self.plot.layer_styles[key] = st

        self.viewbar = ViewBar(self.plot, self.toolbar, settings)
        self.viewbar.moved.connect(self._view_moved)
        add = QtWidgets.QToolButton()
        add.setText("Add to page")
        add.setToolTip("Add this plot with all its settings to the page "
                       "composer")
        add.clicked.connect(lambda *_: self._add_to_page())
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.toolbar, 1)
        second = QtWidgets.QHBoxLayout()
        second.addWidget(self.viewbar, 1)
        second.addWidget(add)
        self.tools = Tools(self)
        self.hover = QtWidgets.QLabel(" ")
        self.hover.setTextInteractionFlags(Qt.TextSelectableByMouse)
        centre = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(centre)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addLayout(top)
        cl.addLayout(second)
        cl.addWidget(self.tools.bar)
        cl.addWidget(self.canvas, 1)
        cl.addWidget(self.hover)
        cl.addWidget(self.tools.panel)

        split = QtWidgets.QSplitter(Qt.Horizontal)
        split.addWidget(_scrolled(self.quantity, 300))
        split.addWidget(centre)
        split.addWidget(_scrolled(self.layers, 330))
        split.setStretchFactor(1, 1)
        split.setCollapsible(1, False)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(split)

        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self._vector_timer = QtCore.QTimer(self)
        self._vector_timer.setSingleShot(True)
        self._vector_timer.setInterval(150)
        self._vector_timer.timeout.connect(self._redraw_vectors)
        self.setEnabled(False)

    # ----------------------------------------------------------- settings
    def _saved_layers(self):
        raw = self.settings.value("layers2d", "")
        try:
            saved = json.loads(raw) if raw else {}
        except ValueError:
            saved = {}
        return {k: from_dict(saved.get(k, {}), default)
                for k, (_, default) in LAYERS.items()}

    def _layer_changed(self, key, style):
        self.plot.set_layer(key, style)
        self.settings.setValue("layers2d", json.dumps(
            {k: dict(s.__dict__) for k, s in self.layers.styles().items()}))
        self.canvas.draw_idle()

    # ---------------------------------------------------------------- run
    def set_run(self, run):
        self.run, self.data, self.wanted, self.odata = run, None, None, {}
        self.plot.set_run(run)
        self.tools.panel.hide()
        self.tools.last = None
        self.quantity.traj_box.set_species(column_names(
            self._species() or []))
        self.viewbar.set_run()
        self._set_available()
        self.translate = catalog.translator(run.catalog)
        self.time_box.set_movies(run.movies)
        self.quantity.cells_box.set_geometry(run.geometry)
        self._set_quantities()
        self._ask_species(run)
        self.setEnabled(True)
        self.toolbar.update()
        self.canvas.draw_idle()
        last = self.settings.value("quantity2d", "te")
        if not self.quantity.select(last):
            self.quantity.select("te")

    def _ask_species(self, run):
        """Species of the run for the calculator: B2.5 ones from the run
        information, EIRENE atoms and molecules with their masses from
        b2plot (massa, massm)."""
        self.species = presets.Species((run.info or {}).get("species", []))
        self.mp = next((float(v) for n, v, _ in dict(run.catalog).get(
            "Constants", []) if n.strip() == "mp"), 1.6726219e-27)
        for q in self.final_quantities:
            if q.name in MASSES:
                self.request.emit(("species", q, (), None))
            elif q.name in MARKS:
                self.request.emit(("marks", q, (), None))

    def _set_quantities(self):
        """Quantities of the run (derived ones first), of the source shown
        (final state or movie frames), in the panel lists."""
        derived, errors = catalog.derived(self._derived_specs(),
                                          self.translate)
        for text in errors:
            self.status.emit("Derived quantity not available: " + text)
        self.final_quantities = derived + catalog.quantities(
            self.run.catalog) + catalog.chord_quantities(
            self.run.layers, self.run.trimesh is not None)
        self.movie_quantities = catalog.movie_quantities(self.run.movies,
                                                         derived)
        quantities = self.movie_quantities if self.time_box.movie() else \
            self.final_quantities
        self.quantity.set_quantities(quantities)
        self.quantity.overlay_box.set_choices(
            [q for q in quantities if q.source in ("vector", "evector")],
            [q for q in quantities if q.source in ("matrix", "eirene")],
            walls=catalog.wall_quantities(self.run.catalog))
        self.quantity.cells_box.set_conditions(
            [q for q in quantities if q.expr and q.source == "matrix"])

    def _derived_specs(self):
        try:
            return json.loads(self.settings.value("derived2d", "") or "[]")
        except ValueError:
            return []

    def open_calculator(self, text=""):
        """The calculator dialog; the saved derived quantities after it."""
        if self.run is None:
            return
        specs = self._derived_specs()
        names = [q.name for q in self.final_quantities if not q.expr]
        CalculatorDialog(specs, self.translate, names, self.species, text,
                         self).exec()
        self.settings.setValue("derived2d", json.dumps(specs))
        self._source_changed()

    def _source_changed(self):
        """Final state or movie frames: the quantities of that source,
        the same quantity again where it exists."""
        movie = self.time_box.movie()
        name = self.wanted.name if self.wanted else "te"
        self._set_quantities()
        self.odata = {}
        if not self.quantity.select(name) and not self.quantity.select("te"):
            self.status.emit("No %s in the %s" % (name, "movie files" if
                                                  movie else "final state"))

    def _chosen(self, q):
        self.wanted = q
        if q.movie:
            self.time_box.set_file(q.movie)
        else:
            self.settings.setValue("quantity2d", q.name)
        self._fetch()

    def _source(self, q):
        return self.time_box.source_of(q)

    def _current(self):
        """True if the data shown belong to the chosen quantity, ops and
        frames."""
        return (self.data is not None and self.wanted is not None
                and (self.data.name, self.data.ops, self.data.source)
                == (self.wanted.name, self.quantity.ops(self.wanted),
                    self._source(self.wanted)))

    def _loaded(self, role, q):
        d = self.odata.get(role)
        return d is not None and (d.name, d.source) == (q.name,
                                                        self._source(q))

    def _shown(self):
        """The plot of the current frames is drawn, overlays included."""
        return self._current() and all(self._loaded(r, q) for r, q in
                                       self._overlays_needed())

    def _overlays_needed(self):
        """[(role, Quantity)] of the active overlays (scalar plots only)."""
        cells = self.quantity.cells_box.wanted() if self.wanted is not None \
            and self.wanted.source in ("matrix", "vector") else []
        if self.quantity.kind() not in KINDS_FLAT:
            return cells
        return self.quantity.overlay_box.wanted() + cells

    def _fetch(self):
        """Ask for the chosen quantity (with the current b2plot operations)
        and for the active overlays that are not loaded yet."""
        if self.wanted is None:
            return
        for role, q in self._overlays_needed():
            if not self._loaded(role, q):
                self.request.emit((role, q, (), self._source(q)))
        if self._current():
            self.redraw()
        else:
            self.request.emit(("main", self.wanted,
                               self.quantity.ops(self.wanted),
                               self._source(self.wanted)))

    def _prefetch(self):
        """While playing, ask for the frames of the next position."""
        p = self.time_box.next_position()
        if p is None or not self.time_box.play.isChecked():
            return
        wants = [("main", self.wanted, self.quantity.ops(self.wanted))] + [
            (r, q, ()) for r, q in self._overlays_needed()]
        for role, q, ops in wants:
            if q.movie:
                self.request.emit(("prefetch", q, ops,
                                   self.time_box.source_of(q, p)))

    def _options_changed(self):
        self._fetch()

    def deliver(self, want, data, console=""):
        """Result of a request (data None on failure) and what b2plot
        printed for it (warnings go to the status bar)."""
        role, q, ops, source = want
        lines = [x.strip() for x in console.splitlines() if x.strip()]
        tail = " ".join(lines[-3:])
        if role == "export":
            self.status.emit("Values of %s written to %s" % (
                q.name, ", ".join(data)) if data is not None else
                "b2plot did not write the values of %s. %s" % (q.name, tail))
            return
        if role == "traj":
            self._show_trajectories(data)
            return
        if role == "tools":
            self.tools.deliver(data)
            return
        if data is None:
            self.status.emit("b2plot returned no data for %s. %s"
                             % (q.name, tail))
            return
        if role == "species":
            self.species.set_neutrals(MASSES[q.name], data.columns,
                                      data.values[:, 0] / self.mp)
            return
        if role == "marks":
            self._mark(q.name, data)
            return
        warn = [x for x in lines if any(w in x.lower() for w in WARNINGS)]
        if warn and role != "prefetch":
            self.status.emit("b2plot: " + warn[-1])
        if role != "main":
            if (role, q) in self._overlays_needed() and \
                    source == self._source(q):
                self.odata[role] = data
                box = self.quantity.overlay_box
                if role in box.ROLES:
                    box.vectors[box.ROLES.index(role)].set_species(
                        column_names(data.columns, self._species()))
                elif role == "wall":
                    box.set_wall_species(column_names(data.columns))
                self.redraw()
            return
        if q is not self.wanted or ops != self.quantity.ops(q) or \
                source != self._source(q):
            return
        self.data = data
        if not self.quantity.reduced():
            self.quantity.set_columns(data.columns, self._species())
        self.redraw()

    def _set_available(self):
        """Layers the run has (those built, flux surfaces with a psi map)."""
        available = {k for k, a in self.plot.layer_artists.items()
                     if a is not None and (not isinstance(a, list) or a)}
        if self.run.psimap is not None:
            available.add("flux")
        self.layers.set_available(available)

    def _species(self):
        return (self.run.info or {}).get("species")

    def _unit(self):
        unit = split_unit(self.wanted.description)[1] if self.wanted else None
        factor = self.quantity.factor_value()
        if factor != 1.0:
            unit = "%s  (\u00d7 %g)" % (unit or "", factor)
        return unit or None

    def _overlay_data(self):
        box = self.quantity.overlay_box
        overlays = {}
        for role, q in self._overlays_needed():
            if self._loaded(role, q):
                d, o = self.odata[role], box.style(role)
                if role in box.ROLES:
                    o = replace(o, column=self._arrow_column(o.column, d))
                overlays[role] = (d, o)
        return overlays

    def _arrow_column(self, chosen, vec):
        """Species column of a vector overlay: the one chosen, else the
        species of the plot, else the first ion (of the element summed)."""
        names = column_names(vec.columns, self._species())
        if 0 <= chosen < len(names):
            return chosen
        plot = self.quantity.species.currentText()
        if plot in names:
            return names.index(plot)
        element = re.sub(r"^Sum ", "", plot)
        ions = [i for i, n in enumerate(names) if "+" in n]
        same = [i for i in ions
                if re.match(r"[A-Za-z]*", names[i]).group(0) == element]
        return (same + ions + [0])[0]

    def _mark(self, name, data):
        """Label position of a midplane (b2plot iimp, iomp): its cell of
        smallest R (inner) or largest R (outer)."""
        g = self.run.geometry
        rows = np.flatnonzero(np.asarray(data.values[0], float)[
            g.cells - 1] > 0)
        if rows.size:
            text, pick = MARKS[name]
            self.run.marks[text] = tuple(g.centres[rows[pick(
                g.centres[rows, 0])]])
            self.plot._build_layer("labels")
            self.canvas.draw_idle()

    def _draw_trajectories(self):
        """b2plot traj with the settings of the box: weighting by the
        quantity shown (matrix ones), start cells from the Only where
        mask."""
        box = self.quantity.traj_box
        if self.run is None or not box.chosen():
            self.status.emit("Trajectories: choose at least one species")
            return
        q = self.wanted
        weight = self.run._head(q.name, None) if q is not None and \
            q.source == "matrix" else ""
        mask = self.quantity.cells_box.where.currentData()
        self.status.emit("Computing trajectories\u2026")
        self.request.emit(("traj", q, (box.words(weight, self.run._head(
            mask.name, None) if mask is not None else ""),), None))

    def _show_trajectories(self, seg):
        if seg is None or not len(seg):
            self.status.emit("b2plot drew no trajectories")
            return
        self.plot._build_layer("trajectories")
        self._set_available()
        self.layers.rows["trajectories"]["check"].setChecked(True)
        self.status.emit("%d trajectory segments" % len(seg))
        self.canvas.draw_idle()

    def _clear_trajectories(self):
        if self.run is not None:
            self.run.layers.pop("trajectories", None)
            self.plot._build_layer("trajectories")
            self.layers.rows["trajectories"]["check"].setChecked(False)
            self._set_available()
            self.canvas.draw_idle()

    def _seed_preset(self, key):
        """Streamline seeds along a curve of the run (plot.shapes.SEEDS)."""
        if self.run is None:
            return
        n = self.quantity.streams.nseeds.value()
        pts = shapes.seed_points(self.run, key, n, lambda p: np.asarray(
            self.plot.tri.get_trifinder()(p[:, 0], p[:, 1])) >= 0)
        text = dict((k, t) for t, k in shapes.SEEDS)[key]
        self.status.emit("%d seeds along the %s" % (len(pts), text)
                         if len(pts) else "No %s in this run" % text)
        self.quantity.set_seeds([tuple(p) for p in pts])

    def _title(self):
        q = self.wanted
        title = q.description if q is not None else self.data.label
        if self.quantity.species.count() > 1:
            title += "  [%s]" % self.quantity.species.currentText()
        if q is not None and self._source(q):
            title += "  \u2014  " + self.time_box.time_text(q.movie)
        return title

    def label_values(self):
        """${NAME} of the label texts: RUN, HOST and TIME (of the run, or
        of the movie frames shown)."""
        info = (self.run.info or {}) if self.run is not None else {}
        t = info.get("time", 0.0)
        if self.wanted is not None and self._source(self.wanted):
            t = self.time_box.time_value(self.wanted.movie)
        return {"RUN": self.run.rundir if self.run is not None else "",
                "HOST": socket.gethostname().split(".")[0],
                "TIME": "%.6g" % t}

    def redraw(self):
        if self.run is None or self.data is None or not self._current():
            return
        try:
            self.plot.show(self.data, self.quantity.style(), self._unit(),
                           self._overlay_data())
        except Exception as err:     # a bad option must not end the GUI
            self.status.emit("Cannot draw %s: %s" % (self.data.name, err))
            return
        title = self._title()
        self.quantity.labels_box.set_title_hint(title)
        self.plot.set_labels(self.quantity.labels_box.style(), title,
                             self.label_values())
        if self._shown():
            self._prefetch()
            for job in (self.frames, self.maps):
                if job.job is not None:
                    QtCore.QTimer.singleShot(0, job.ready)
        if self.plot.mappable is not None:
            norm = self.plot.mappable.norm
            self.quantity.set_range(norm.vmin, norm.vmax)
        self.canvas.draw_idle()

    # -------------------------------------------------------------- views
    def _view_moved(self):
        """Arrows, streamlines and cell values follow zoom and pan."""
        if (self.data is not None and hasattr(self.data, "vr")) or any(
                r.startswith("arrows") for r in self.odata) or \
                self.quantity.colour.cell_values.isChecked():
            self._vector_timer.start()

    def _redraw_vectors(self):
        self.redraw()

    # -------------------------------------------------------------- mouse
    def _motion(self, event):
        if event.inaxes is self.plot.ax and event.xdata is not None:
            self.hover.setText(self.plot.lookup(event.xdata, event.ydata))
        else:
            self.hover.setText(" ")
