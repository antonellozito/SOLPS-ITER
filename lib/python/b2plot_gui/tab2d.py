"""2D tab: quantity panel, one plot with its commands, layers panel, in
columns of fixed width (30, 50 and 20 % of the window)."""

import json
import re
import socket
from dataclasses import replace

import numpy as np
import matplotlib.tri as mtri
from matplotlib.figure import Figure

from . import catalog, presets, theme
from .plot import shapes
from .plot.canvas import Plot2D
from .plot.styles import KINDS_FLAT, LAYERS
from .model import split_unit
from ..qt import NavigationToolbar2QT, QtCore, QtWidgets, Qt, Signal
from .panels.layers import (CELL_MASKS, MASKS, LayersPanel, MasksPanel,
                            from_dict)
from .panels.plotarea import READOUT, Columns, PlotCommands, ScaledCanvas
from .panels.calculator import CalculatorDialog
from .panels.quantity import QuantityPanel, column_names
from .output.actions import TabOutput
from .output.frames import FrameExport
from .tools import cellfiles, equilibrium, inspect, regions
from .tools.control import Tools

MASSES = {"massa": "a", "massm": "m", "massi": "i"}   # EIRENE species
WARNINGS = ("no data found", "not found", "no adas file", "faulty",
            "not recognized", "error")      # in what b2plot prints
COLUMNS = (0.3, 0.5, 0.2)       # quantity panel, plot, layers


def _scrolled(widget):
    area = QtWidgets.QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    return area


class Tab2D(TabOutput, QtWidgets.QWidget):
    """The 2D plots tab; data requests go through the main window."""

    request = Signal(object)        # (role, Quantity, operations, source)
    add_to_page = Signal(object)    # Snapshot
    composer = Signal()             # show the page composer
    status = Signal(str)
    species_known = Signal()        # EIRENE species names arrived

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.run = None
        self.data = None
        self.wanted = None
        self.odata = {}                 # overlay role -> Field or Vector
        self.eirene_names = {}          # a, m, i -> EIRENE species names
        self.figure = Figure()
        self.canvas = ScaledCanvas(self.figure, self._keep_view)
        self.plot = Plot2D(self.figure, fixed=True)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.hide()             # PlotCommands does its work

        self.quantity = QuantityPanel()
        self.quantity.quantity_chosen.connect(self._chosen)
        self.quantity.style_changed.connect(self._options_changed)
        self.quantity.seed_line.connect(
            lambda on: self.tools.bar.set_mode("seeds" if on else None))
        self.quantity.streams.seed_preset.connect(self._seed_preset)
        self.quantity.traj_box.draw.connect(self._draw_trajectories)
        self.quantity.traj_box.clear.connect(self._clear_trajectories)
        self.quantity.calculator.connect(self.open_calculator)
        self.time_box = self.quantity.time_box
        self.time_box.source_changed.connect(self._source_changed)
        self.time_box.frames_changed.connect(self._fetch)
        self.frames = FrameExport(self)
        self.time_box.export_frames.connect(lambda: self.frames.start())
        self.time_box.ready = self._shown
        self.final_quantities, self.movie_quantities = [], []
        self.layers = LayersPanel(self._saved_layers())
        self.layers.changed.connect(self._layer_changed)
        for key, st in self.layers.styles().items():
            self.plot.layer_styles[key] = st

        self.tools = Tools(self)
        self.tools.bar.changed.connect(lambda: self.quantity.streams.waiting(
            self.tools.bar.mode == "seeds"))
        self.commands = PlotCommands(self)
        self.hover = self.commands.readout
        centre = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(centre)
        cl.setContentsMargins(6, 0, 6, 0)
        cl.setSpacing(2)
        cl.addWidget(self.commands)
        cl.addWidget(self.canvas, 1)
        self.masks = MasksPanel()
        self.mask_keys = []             # the masks drawn
        self.masks.changed.connect(self._masks_changed)
        right = QtWidgets.QWidget()
        rl = QtWidgets.QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.layers)
        rl.addWidget(self.masks)
        rl.addStretch(1)
        self.columns = Columns((_scrolled(self.quantity), centre,
                                _scrolled(right)), COLUMNS)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.columns)

        self._pan = None            # (pixel, view, data per pixel)
        self.canvas.mpl_connect("button_press_event", self._pan_start)
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self.canvas.mpl_connect("button_release_event", self._nav_done)
        self.canvas.mpl_connect("scroll_event", self._scroll)
        self._lims = QtCore.QTimer(self)
        self._lims.setSingleShot(True)
        self._lims.timeout.connect(self._view_changed)
        self._vector_timer = QtCore.QTimer(self)
        self._vector_timer.setSingleShot(True)
        self._vector_timer.setInterval(150)
        self._vector_timer.timeout.connect(self._redraw_vectors)
        self._show_empty()
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
        self.mask_keys = []
        run.layers["midplanes"] = self._midplanes(run)
        self.plot.set_run(run)
        self._show_empty()
        self.tools.panel.hide()
        self.tools.last = None
        self.quantity.unselect()
        self.quantity.traj_box.set_species(column_names(
            self._species() or []))
        for signal in ("xlim_changed", "ylim_changed"):   # after set_run
            self.plot.ax.callbacks.connect(signal, self._lims_changed)
        self._set_available()
        self.translate = catalog.translator(run.catalog)
        self.time_box.set_movies(run.movies)
        self.quantity.cells_box.set_geometry(run.geometry)
        self._set_quantities()
        self._ask_species(run)
        geometry = any(cellfiles.find(run.rundir, n)
                       for n in cellfiles.GEOMETRY)
        self.masks.set_available(
            [k for k in ("volume", "face", "topological", "labels")
             if geometry] + (["strata"] if geometry and
                             regions.recycling_strata(run) else []))
        self._masks_changed()
        self.setEnabled(True)
        self.toolbar.update()
        self.canvas.draw_idle()

    @staticmethod
    def _midplanes(run):
        """Segments of the midplanes of b2.user.parameters (rzimp, rzomp)
        where they cross the cells of the B2.5 grid."""
        g = run.geometry
        tri = mtri.Triangulation(g.vx[:, 0], g.vx[:, 1], g.triangles)
        finder = tri.get_trifinder()

        def inside(p):
            it = finder(p[:, 0], p[:, 1])
            return (it >= 0) & g.visible[g.tri_cell[np.maximum(it, 0)]]
        segs = [cellfiles.inside_segments(a, b, inside) for a, b in
                cellfiles.midplane_points(run.rundir).values()]
        return np.vstack([np.zeros((0, 4))] + segs)

    def _masks_changed(self):
        """The masks checked, computed once per run from the files of the
        run (tools.regions), over the plot."""
        if self.run is None:
            return
        out, cache = [], self.run.__dict__.setdefault("mask_cache", {})
        want = self.masks.wanted()
        geo = inspect.files(self.run)[0] if want else None
        for key in want:
            if key not in cache:
                try:
                    cache[key] = regions.cell_mask(self.run, geo, key) if \
                        key in CELL_MASKS else regions.face_mask(
                            self.run, geo, key)
                except (TypeError, ValueError, IndexError, AttributeError,
                        OSError):
                    cache[key] = None
            if cache[key] is None or not len(cache[key][1]):
                self.status.emit("No %s in this run" % dict(MASKS)[
                    key].lower())
            else:
                out.append(cache[key])
        self.plot.set_masks(out)
        self.mask_keys = [k for k in want if cache.get(k) is not None and
                          len(cache[k][1])]
        self.redraw()           # title, colour bar under a cell mask
        self.canvas.draw_idle()

    def _ask_species(self, run):
        """Species of the run for the calculator: B2.5 ones from the run
        information, EIRENE atoms and molecules with their masses from
        b2plot (massa, massm)."""
        self.species = presets.Species((run.info or {}).get("species", []))
        self.eirene_names = {}
        self.mp = next((float(v) for n, v, _ in dict(run.catalog).get(
            "Constants", []) if n.strip() == "mp"), 1.6726219e-27)
        for q in self.final_quantities:
            if q.name in MASSES:
                self.request.emit(("species", q, (), None))

    def _set_quantities(self):
        """Quantities of the run (derived ones first), of the source shown
        (final state or movie frames), in the panel lists."""
        derived, errors = catalog.derived(self._derived_specs(),
                                          self.translate)
        for text in errors:
            self.status.emit("Derived quantity not available: " + text)
        geometry = any(cellfiles.find(self.run.rundir, n)
                       for n in cellfiles.GEOMETRY)
        maps = equilibrium.MAPS if geometry else ()
        walls = catalog.wall_quantities(self.run.catalog) + ([
            catalog.Quantity(*equilibrium.WALL, "Wall", "eqwall")]
            if geometry else [])
        self.final_quantities = derived + catalog.quantities(
            self.run.catalog, maps) + catalog.chord_quantities(
            self.run.layers, self.run.trimesh is not None)
        self.movie_quantities = catalog.movie_quantities(self.run.movies,
                                                         derived)
        quantities = self.movie_quantities if self.time_box.movie() else \
            self.final_quantities
        self.quantity.set_quantities(quantities)
        self.quantity.overlay_box.set_choices(
            [q for q in quantities if q.source in ("vector", "evector")],
            [q for q in quantities if q.source in ("matrix", "eirene")],
            walls=walls)
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
        the same quantity again where it exists (nothing if nothing was
        plotted)."""
        movie = self.time_box.movie()
        self._set_quantities()
        self.odata = {}
        if self.wanted is None:
            return
        name = self.wanted.name
        if not self.quantity.select(name):
            self.quantity.unselect()
            self.status.emit("No %s in the %s" % (name, "movie files" if
                                                  movie else "final state"))

    def _chosen(self, q):
        """A quantity chosen in the tree, None: nothing plotted (as at the
        start)."""
        self.wanted = q
        if q is None:
            self.data, self.odata = None, {}
            self.quantity.set_columns([""])
            self._show_empty()
            return
        if q.movie:
            self.time_box.set_file(q.movie)
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
            and self.wanted.source in ("matrix", "vector",
                                       "equilibrium") else []
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
                if q.source == "eqwall":    # computed here, as the maps
                    geo = inspect.files(self.run)[0]
                    if geo is not None:
                        self.deliver((role, q, (), None),
                                     equilibrium.wall_field(geo))
                else:
                    self.request.emit((role, q, (), self._source(q)))
        if self._current():
            self.redraw()
        elif self.wanted.source == "equilibrium":
            self._equilibrium()
        else:
            self.request.emit(("main", self.wanted,
                               self.quantity.ops(self.wanted),
                               self._source(self.wanted)))

    def _equilibrium(self):
        """A map of the derived equilibrium, computed here from the
        geometry files (the midplane cells of the flux expansion asked of
        b2plot first)."""
        q, ops = self.wanted, self.quantity.ops(self.wanted)
        geo = inspect.files(self.run)[0]
        if geo is None:
            self.status.emit("%s needs the unstructured geometry of "
                             "b2fgmtry" % q.description)
            return
        missing = [m for m in equilibrium.MIDPLANES if ("field", m, (), None)
                   not in self.run.cache]
        if q.name == "fexp" and missing:
            for m in missing:
                mq = next((x for x in self.final_quantities if x.name == m),
                          None)
                if mq is not None:
                    self.request.emit(("eqdata", mq, (), None))
            self.status.emit("Asking b2plot for the midplane cells\u2026")
            return
        self.deliver(("main", q, ops, None), equilibrium.field(
            self.run, geo, q.name, ops))

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
        if role == "traj":
            self._show_trajectories(data)
            return
        if role == "tools":
            self.tools.deliver(data)
            return
        if role == "eqdata":           # midplane cells: the map again
            if data is not None and self.wanted is not None and \
                    self.wanted.source == "equilibrium":
                self._fetch()
            return
        if data is None:
            self.status.emit("b2plot returned no data for %s. %s"
                             % (q.name, tail))
            return
        if role == "species":
            kind = MASSES[q.name]
            self.eirene_names[kind] = [c.strip() for c in data.columns
                                       if c.strip()]
            if kind != "i":         # test ions: not in the calculator
                self.species.set_neutrals(kind, data.columns,
                                          data.values[:, 0] / self.mp)
            self.species_known.emit()
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
        return self._mask_title(title)

    def _mask_title(self, title):
        """The title with the masks shown: a cell mask covers the
        quantity, a face mask is named after it."""
        keys = sorted(self.mask_keys, key=lambda k: k not in CELL_MASKS)
        names = [dict(MASKS)[k] for k in keys]
        if keys and keys[0] in CELL_MASKS or not title:
            return ", ".join(names)
        return ", ".join([title] + names)

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
        if self.wanted is None:
            self._show_empty()
        if self.run is None or self.data is None or not self._current():
            return
        try:
            self.plot.show(self.data, self.quantity.style(), self._unit(),
                           self._overlay_data())
        except Exception as err:     # a bad option must not end the GUI
            self.status.emit("Cannot draw %s: %s" % (self.data.name, err))
            return
        if self.plot.drawn == 0:
            self.status.emit("%s: zero in every cell shown" % self.data.name)
        title = self._title()
        self.quantity.labels_box.set_title_hint(title)
        self.plot.set_labels(self.quantity.labels_box.style(), title,
                             self.label_values())
        if self._shown():
            self._prefetch()
            if self.frames.job is not None:
                QtCore.QTimer.singleShot(0, self.frames.ready)
        if self.plot.mappable is not None:
            norm = self.plot.mappable.norm
            self.quantity.set_range(norm.vmin, norm.vmax)
        self.canvas.draw_idle()

    # -------------------------------------------------------------- views
    def _lims_changed(self, *_):
        self._lims.start(0)         # once both limits are set

    def _view_changed(self):
        """A new view (zoom, pan, unzoom, scroll): inside the limits of the
        run, then arrows and cell values for it."""
        if self.plot.clamp():
            self.canvas.draw_idle()
        self._view_moved()
        self.tools.view_changed()

    def _scroll(self, event):
        """The mouse wheel zooms around the cursor, 10 % a wheel step (a
        touch pad in smaller steps)."""
        if event.inaxes is self.plot.ax and event.xdata is not None and \
                self.run is not None:
            gui = event.guiEvent
            steps = gui.angleDelta().y() / 120.0 if hasattr(
                gui, "angleDelta") else event.step   # not pixels (macOS)
            if steps:
                self._history()
                self.plot.zoom_at(event.xdata, event.ydata,
                                  0.9 ** float(np.clip(steps, -3.0, 3.0)))
                self.toolbar.push_current()
                self.canvas.draw_idle()

    def restore(self):
        """The full view of the run (its limits)."""
        if self.run is not None:
            self._history()
            self.plot.set_view(self.plot.full_box())
            self.toolbar.push_current()
            self.canvas.draw_idle()

    def _history(self):
        """Before a view change of the wheel, Restore or a pan: the view
        on the stack of Unzoom (the new one is pushed after it)."""
        if self.toolbar._nav_stack() is None:
            self.toolbar.push_current()

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
        if self._pan is not None:
            self._pan_move(event)
        if event.inaxes is self.plot.ax and event.xdata is not None:
            self.hover.setText(self.plot.lookup(event.xdata, event.ydata))
        else:
            self.hover.setText(READOUT)

    def _pan_start(self, event):
        """A left press on the plot, with no tool and no Zoom on, starts a
        pan: the view follows the mouse and never leaves the limits."""
        if event.button != 1 or event.inaxes is not self.plot.ax or \
                self.run is None or str(self.toolbar.mode) or \
                self.tools.bar.mode is not None or event.dblclick or \
                self.plot.ax3d is not None:
            return
        box = self.plot.ax.get_window_extent()
        x0, x1, y0, y1 = self.plot.get_view()
        self._pan = ((event.x, event.y), (x0, x1, y0, y1),
                     ((x1 - x0) / box.width, (y1 - y0) / box.height), False)
        self.canvas.setCursor(Qt.ClosedHandCursor)

    def _pan_move(self, event):
        (px, py), (x0, x1, y0, y1), (sx, sy), moved = self._pan
        dx, dy = (event.x - px) * sx, (event.y - py) * sy
        if not moved:
            self._history()
            self._pan = self._pan[:3] + (True,)
        self.plot.pan_to((x0 - dx, x1 - dx, y0 - dy, y1 - dy))
        self.canvas.draw_idle()

    # -------------------------------------------------------------- theme
    def apply_theme(self):
        """The plot and the tool results in the colours of the theme."""
        self.canvas.setStyleSheet("background-color: %s;"
                                  % theme.figure_bg())
        self.plot.apply_theme()
        if self.wanted is None:
            self._show_empty()
        else:
            self.redraw()
        panel = self.tools.panel
        if panel.isVisible() and panel.canvas.isVisible():
            panel.apply_theme()
        self.canvas.draw_idle()

    def _show_empty(self):
        """Nothing plotted: the layers, the colour-bar placeholder and the
        axis labels."""
        self.plot.show_empty()
        self.plot.set_labels(self.quantity.labels_box.style(),
                             self._mask_title(""), self.label_values())
        self.canvas.draw_idle()

    def _keep_view(self):
        """After a resize the view asked for, not the one matplotlib
        widened to the new shape of the axes."""
        if self.run is not None and self.plot.requested is not None:
            self.plot.set_view(self.plot.requested)

    def _nav_done(self, event):
        """A zoom or pan with the mouse: that view is the one kept."""
        if self._pan is not None:
            moved, self._pan = self._pan[3], None
            self.canvas.unsetCursor()
            if moved:
                self.plot.requested = self.plot.get_view()
                self.toolbar.push_current()
        elif str(self.toolbar.mode):
            self.plot.requested = self.plot.get_view()

    def freeze_scale(self):
        """The present size of the plot is its reference: it scales with
        the window from now on."""
        self.canvas.freeze()
        self.plot.freeze()
