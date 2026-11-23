"""2D view: quantity panel, one plot with its commands at its right, how
the plot looks (plot type, colour scale, contours, arrows, streamlines,
layers, masks, volume regions, labels), in columns of fixed width (28, 50,
5 and, after 1 % of space, 16 % of the window)."""

import json
import os
import socket
from dataclasses import replace

import numpy as np
from matplotlib.figure import Figure

from . import catalog, presets, runstate, scaling, theme
from .plot import shapes
from .plot.canvas import Plot2D
from .plot.styles import LAYERS
from .model import split_unit
from ..qt import NavigationToolbar2QT, QtCore, QtWidgets, Qt, Signal
from .panels.layers import (CELL_MASKS, MASKS, LayersPanel, MasksPanel,
                            from_dict)
from .panels.plotarea import (READOUT, Columns, PlotCommands, Readout,
                              ScaledCanvas)
from .panels.calculator import CalculatorDialog
from .panels.quantity import QuantityPanel
from .panels.species import ALL, SUM, chosen_columns, column_names
from .panels.timebox import BALANCES, PAGES, TRACING
from .output.actions import TabOutput
from .output.movie import MovieFrames
from .tools import cellfiles, equilibrium, inspect, regions
from .tools.control import Tools
from .balances.picker import BalanceTool
from .timedata.tracing import RunTracing

MASSES = {"massa": "a", "massm": "m", "massi": "i"}   # EIRENE species
WARNINGS = ("no data found", "not found", "no adas file", "faulty",
            "not recognized", "error")      # in what b2plot prints
COLUMNS = (0.28, 0.5, 0.05, 0.16)    # quantities, plot, commands, layers
SPACE = (0.0, 0.0, 0.0, 0.01)        # before each column


def _scrolled(widget):
    area = QtWidgets.QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    return area


def movies_of_state(run):
    """Only the movie files of the latest run in run.movies (runstate:
    with a final state those written with it, as balance.nc; else those
    written since the start of the run); why the others are left out."""
    files = runstate.movies(run.rundir, run.state[0])
    run.movies = {f: m for f, m in run.movies.items()
                  if not files.get(os.path.basename(m.path), ("", ""))[1]}
    return [why for _, why in files.values() if why]


class Tab2D(TabOutput, QtWidgets.QWidget):
    """The 2D view; data requests go through the main window."""

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
        self.odata = {}                 # overlay role ("lines") -> Field
        self.overlay_wanted = None      # the quantity overlaid
        self.vector_wanted = None       # the vector quantity plotted
        self.vector_data = None
        self.wall_wanted = None         # the wall quantity plotted
        self.wall_data = None
        self.eirene_names = {}          # a, m, i -> EIRENE species names
        self.figure = Figure()
        self.canvas = ScaledCanvas(self.figure, self._keep_view)
        self.plot = Plot2D(self.figure, fixed=True)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.hide()             # PlotCommands does its work

        self.quantity = QuantityPanel()
        self.quantity.quantity_chosen.connect(self._chosen)
        self.quantity.vector_chosen.connect(self._vector_chosen)
        self.quantity.wall_chosen.connect(self._wall_chosen)
        self.quantity.overlay_chosen.connect(self._overlay_chosen)
        self.quantity.style_changed.connect(self._options_changed)
        self.quantity.seed_line.connect(
            lambda on: self.tools.bar.set_mode("seeds" if on else None))
        self.quantity.streams.seed_preset.connect(self._seed_preset)
        self.quantity.calculator.connect(self.open_calculator)
        self.time_box = self.quantity.time_box
        self.time_box.source_changed.connect(self._source_changed)
        self.time_box.frames_changed.connect(self._frames_moved)
        self._moving = False            # only the frames changed
        self.time_box.ready = self._shown
        self.movie = MovieFrames(self)      # drawn before playing
        self.time_box.prepare = self.movie.prepare
        self.time_box.show_frame = self.movie.show
        self.time_box.cancel = self.movie.cancel
        self.time_box.save_movie.connect(lambda: self.movie.save())
        self.final_quantities, self.movie_quantities = [], []
        self._tab, self._tab_plot = 0, {}   # the tab open, what each plots
        self.layers = LayersPanel(self._saved_layers())
        self.layers.changed.connect(self._layer_changed)
        for key, st in self.layers.styles().items():
            self.plot.layer_styles[key] = st

        self.tools = Tools(self)
        self.tools.bar.changed.connect(lambda: self.quantity.streams.waiting(
            self.tools.bar.mode == "seeds"))
        self.quantity.sections.addWidget(self.tools.chords_section)
        self.quantity.sections.addWidget(self.tools.stats_section)
        self.quantity.chords_button.toggled.connect(
            lambda on: self.tools.open_section("chords" if on else None))
        self.quantity.stats_button.toggled.connect(
            lambda on: self.tools.open_section("stats" if on else None))
        self.quantity.overlay_button.toggled.connect(
            lambda on: self.tools.open_section("overlay" if on else None))
        self.balance = BalanceTool(self)
        self.tracing = RunTracing(self)
        self.tools.bar.changed.connect(
            lambda: self.tools.bar.mode is not None and self.balance.cancel())
        self.commands = PlotCommands(self)
        self.hover = Readout(parent=self.canvas)    # under the plot box
        centre = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(centre)
        cl.setContentsMargins(4, 0, 6, 0)
        cl.addWidget(self.canvas, 1)
        self.masks = MasksPanel()
        self.mask_keys = []             # the masks drawn
        self.masks.changed.connect(self._masks_changed)
        right = QtWidgets.QWidget()     # how the plot looks
        rl = QtWidgets.QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        for w in self.quantity.style_boxes + (self.layers, self.masks) + \
                self.quantity.lower_boxes:
            rl.addWidget(w)
        rl.addStretch(1)
        left = QtWidgets.QWidget()      # the tabs stay over the scrolling
        ll = QtWidgets.QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 0)
        ll.setSpacing(6)                # the panel scrolls apart from them
        ll.addWidget(self.time_box.source)
        fixed = QtWidgets.QWidget()     # over the scrolling too: the rows of
        fl = QtWidgets.QVBoxLayout(fixed)   # the movies, the tabs and rows
        fl.setContentsMargins(0, 0, 6, 0)   # of the Run tracing page
        fl.setSpacing(0)
        self.quantity.layout().removeWidget(self.time_box)
        fl.addWidget(self.time_box)
        fl.addWidget(self.tracing.page.header)
        ll.addWidget(fixed)
        self.left_column = left         # the balance extensions start right
        self.quantity_area = _scrolled(self.quantity)   # of it
        self.quantity_area.setVerticalScrollBarPolicy(  # its width never
            Qt.ScrollBarAlwaysOn)   # changes: no scroll bar coming and
        #                             going as the plots follow the width
        ll.addWidget(self.quantity_area, 1)
        self.quantity.page_slot.addWidget(self.tracing.page)
        self.quantity.page_slot.addWidget(self.balance.page)
        self.quantity.show_page(None)
        self.columns = Columns((left, centre, self.commands,
                                _scrolled(right)), COLUMNS, SPACE)
        for column in (self.quantity, right):  # never scrolled sideways
            scaling.squeezable(column)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.columns)

        self._pan = None            # (pixel, view, data per pixel)
        self.canvas.mpl_connect("button_press_event", self._pan_start)
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self.canvas.mpl_connect("button_release_event", self._nav_done)
        self.canvas.mpl_connect("scroll_event", self._scroll)
        for name in ("axes_leave_event", "figure_leave_event"):
            self.canvas.mpl_connect(        # off the plot: no readout
                name, lambda e: self.hover.setText(READOUT))
        self.canvas.mpl_connect("draw_event", self._align_commands)
        self._lims = QtCore.QTimer(self)
        self._lims.setSingleShot(True)
        self._lims.timeout.connect(self._view_changed)
        self._vector_timer = QtCore.QTimer(self)
        self._vector_timer.setSingleShot(True)
        self._vector_timer.setInterval(150)
        self._vector_timer.timeout.connect(self._draw_vectors)
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
        self.vector_wanted = self.vector_data = None
        self.wall_wanted = self.wall_data = self.overlay_wanted = None
        for kind in ("vector", "wall", "overlay"):
            self.quantity.unselect_extra(kind)
        self.mask_keys = []
        run.layers["midplanes"] = self._midplanes(run)
        self.plot.set_run(run)
        self._show_empty()
        self.tools.panel.hide()
        self.tools.last = None
        self.balance.set_run(run)
        self.quantity.unselect()
        self._species_menus()
        for signal in ("xlim_changed", "ylim_changed"):   # after set_run
            self.plot.ax.callbacks.connect(signal, self._lims_changed)
        self._set_available()
        self.translate = catalog.translator(run.catalog)
        stale = movies_of_state(run)
        kind, why = run.state
        self.time_box.set_movies(run.movies, stale,
                                 kind in ("finished", "crashed"), why)
        self.time_box.set_balances(self.balance.path is not None,
                                   self.balance.why)
        self.tracing.set_run(run)
        self.time_box.set_tracing(self.tracing.ok(), self.tracing.why)
        self._tab = self.time_box.source.currentIndex()
        self._tab_plot = {}             # tab -> the quantity plotted there
        self.show_page()
        for menu in (self.quantity.plasma_regions,
                     self.quantity.vector_regions):
            menu.set_geometry(run.geometry)
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
        finder = g.finder

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
            catalog.Quantity(*equilibrium.WALL, "Geometry", "eqwall")]
            if geometry else [])
        self.final_quantities = derived + catalog.quantities(
            self.run.catalog, maps)
        self.movie_quantities = catalog.movie_quantities(
            self.run.movies, derived, self.translate)
        quantities = self.movie_quantities if self.time_box.movie() else \
            self.final_quantities if self.time_box.final() else []
        vectors = [q for q in quantities if q.source in ("vector", "evector")]
        self.quantity.set_quantities([q for q in quantities
                                      if q not in vectors])
        self.quantity.set_vector_quantities(vectors)
        self.quantity.set_wall_quantities(sorted(   # none in the movies
            walls, key=lambda q: [w.group for w in walls].index(q.group))
            if not self.time_box.movie() else [])
        self.quantity.set_overlay_quantities([q for q in quantities
                                              if q not in vectors])

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

    def show_page(self):
        """The Run tracing and Balances tabs: their page in the column
        instead of the quantities, their marks or volume drawn (and picked)
        only there; the chords and statistics drawn on the plot go (their
        results are kept)."""
        page = self.time_box.page()
        if page is not None and self.tools.section is not None:
            self.tools.open_section(None)
        self.quantity.show_page({TRACING: self.tracing.page,
                                 BALANCES: self.balance.page}.get(page))
        self.balance.set_shown(page == BALANCES)
        self.tracing.set_shown(page == TRACING)

    def _source_changed(self):
        """Another tab: what the tab left plotted goes, the plot of the
        tab opened comes back (Final state, Run movies: the quantity last
        plotted there, the layers alone if none; Run tracing: its marks;
        Balances: its volume), with the quantities of its source."""
        old, new = self._tab, self.time_box.source.currentIndex()
        self._tab = new
        if old not in PAGES:
            self._tab_plot[old] = tuple(q.name if q else None for q in (
                self.wanted, self.vector_wanted, self.wall_wanted,
                self.overlay_wanted))
        self.show_page()
        self._set_quantities()
        self.odata = {}
        name, *extra = (None,) * 4 if new in PAGES else \
            self._tab_plot.get(new, (None,) * 4)
        for kind, other in zip(("vector", "wall", "overlay"), extra):
            if other is None or not self.quantity.select_extra(kind, other):
                self.quantity.unselect_extra(kind)
                if getattr(self, kind + "_wanted") is not None:
                    getattr(self, "_%s_chosen" % kind)(None)
        if name is not None and self.quantity.select(name):
            return
        self.quantity.unselect()
        if self.wanted is not None:
            self._chosen(None)

    def _chosen(self, q):
        """A plasma quantity chosen in the tree, None: no plasma plot (the
        vector and wall plots stay)."""
        self.wanted = q
        self._set_plotted()
        if q is None:
            self.data, self.odata = None, {}
            self._species_menus()
            self.redraw()
            return
        if q.movie:
            self.time_box.set_file(q.movie)
        self._fetch()

    def _set_plotted(self):
        self.quantity.set_plotted(self.wanted is not None,
                                  self.vector_wanted is not None,
                                  self.wall_wanted is not None,
                                  bool(self._overlays_needed()))

    def _overlay_chosen(self, q):
        """A quantity chosen in the Overlay section, None: no overlay."""
        self.overlay_wanted = q
        if q is None:
            self.odata = {}
        self._set_plotted()
        self._species_menus()
        self._fetch()

    def _overlay_allowed(self):
        """An overlay over a plasma plot that is not contour lines."""
        return self.wanted is not None and self.quantity.kind() != "contour"

    def _vector_chosen(self, q):
        """A vector quantity chosen in its tree, None: no vector plot (the
        plasma and wall plots stay)."""
        self.vector_wanted = q
        if q is None or not self._vector_loaded():
            self.vector_data = None
        if q is not None and q.movie and self.wanted is None:
            self.time_box.set_file(q.movie)
        self._set_plotted()
        self._species_menus()
        self._fetch_vector()
        self.redraw()

    def _vector_loaded(self):
        """The vector data of the quantity and frames chosen are here (or
        no vector quantity is chosen)."""
        q, v = self.vector_wanted, self.vector_data
        # the data is named by its two components (b2plot tokens)
        return q is None or v is not None and (v.name, v.source) == (
            q.poloidal + " " + q.radial, self._source(q))

    def _fetch_vector(self):
        """Ask for the vector quantity if it is not loaded (all species:
        those chosen are summed here)."""
        q = self.vector_wanted
        if q is not None and not self._vector_loaded():
            self.request.emit(("vector", q, (), self._source(q)))

    def _vector_args(self):
        """(vector data, PlotStyle, unit) of the vector plot shown, the
        species chosen summed, or None."""
        if self.vector_wanted is None or self.vector_data is None or \
                not self._vector_loaded():
            return None
        v, col = self.summed_vector(self.vector_data)
        return (v, self.quantity.vector_style(col),
                self._bar_label(self.vector_wanted, self.vector_data))

    def summed_vector(self, v):
        """(vector data v with the species chosen summed, its column);
        the frames of the chords too."""
        menu = self.quantity.vector_species
        cols = self._columns(v, menu)
        if len(cols) == 1:
            return v, cols[0]
        return replace(v, columns=[menu.text()],
                       **{k: np.asarray(getattr(v, k))[list(cols)].sum(
                           0, keepdims=True) for k in ("vr", "vz", "vxr",
                                                       "vxz")
                          if getattr(v, k) is not None}), 0

    def _draw_vectors(self):
        """The vector plot (or none), over the plasma plot or alone; while
        new frames are asked for, the old ones stay. True if drawn."""
        args = self._vector_args()
        if self.run is None or args is None and self.vector_wanted:
            return False
        try:
            self.plot.set_vectors(*args or (None, None))
        except Exception as err:     # a bad option must not end the GUI
            self.status.emit("Cannot draw %s: %s" % (args[0].name, err))
            return False
        m = self.plot.vector_mappable
        if m is not None:
            self.quantity.set_vector_range(m.norm.vmin, m.norm.vmax)
        self.tools.data_changed()       # the chords and the inspector
        self.canvas.draw_idle()
        return args is not None

    def _wall_chosen(self, q):
        """A wall quantity chosen in its tree, None: no wall plot (the
        plasma and vector plots stay)."""
        self.wall_wanted = q
        if self.wall_data is not None and (q is None or
                                           self.wall_data.name != q.name):
            self.wall_data = None
        self._set_plotted()
        self._species_menus()
        self._fetch_wall()
        self.redraw()           # the other bars and the title too

    def _fetch_wall(self):
        """Ask for the wall quantity if it is not loaded (computed here for
        the equilibrium one)."""
        q = self.wall_wanted
        if q is None or self.wall_data is not None:
            return
        if q.source == "eqwall":
            geo = inspect.files(self.run)[0]
            if geo is not None:
                self.deliver(("wall", q, (), None),
                             equilibrium.wall_field(geo))
            return
        self.request.emit(("wall", q, (), self._source(q)))

    def _columns(self, data, menu):
        """Columns of vector or wall data summed: the species chosen in
        its menu, all of them (sum of the species), those of the element
        (sum of an element), else the first."""
        return chosen_columns(column_names(data.columns, self._species()),
                              menu.text())

    def _species_menus(self):
        """Each species menu with the species of its data: the plasma one
        kept while the plasma data are asked for or b2plot sends one
        column of them (sum, proportion), the vector one while the vector
        data are asked for; grey without a quantity."""
        q = self.quantity
        d = self.data if self._current() else None
        if self.wanted is None:
            q.plasma_species.set_columns([""])
        elif d is not None and not q.reduced():
            q.plasma_species.set_columns(d.columns, self._species())
        v = self.vector_data if self._vector_loaded() else None
        for menu, wanted, data in ((q.vector_species, self.vector_wanted, v),
                                   (q.wall_species, self.wall_wanted,
                                    self.wall_data)):
            if wanted is None:
                menu.set_columns([""])
            elif data is not None:
                menu.set_columns(data.columns, self._species())
        o = self.odata.get("lines")     # the overlay: as the plasma one
        if self.overlay_wanted is None:
            q.overlay_species.set_columns([""])
        elif o is not None and self._loaded("lines", self.overlay_wanted) \
                and not q.overlay_reduced():
            q.overlay_species.set_columns(o.columns, self._species())

    def _wall_pair(self):
        """(wall data, WallStyle, colour-bar label) of the wall plot
        shown, or None."""
        if self.wall_wanted is None or self.wall_data is None:
            return None
        return (self.wall_data, self.quantity.wall_box.wall_style(
            self._columns(self.wall_data, self.quantity.wall_species)),
            self._bar_label(self.wall_wanted, self.wall_data))

    def _draw_wall(self):
        """The wall plot (or none), apart from the plasma plot."""
        w = self.wall_data
        if self.run is None:
            return
        if w is None or self.wall_wanted is None:
            self.plot.set_wall(None, None)
        else:
            self.plot.set_wall(*self._wall_pair())
            m = self.plot.wall_mappable
            if m is not None:
                self.quantity.set_wall_range(m.norm.vmin, m.norm.vmax)
        self.tools.data_changed()       # the inspector
        self.canvas.draw_idle()

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
        """The overlay data of q are here (its b2plot operations, its
        frames)."""
        d = self.odata.get(role)
        return d is not None and (d.name, tuple(d.ops), d.source) == (
            q.name, self.quantity.ops(q, overlay=True), self._source(q))

    def _shown(self):
        """The plot of the current frames is drawn: the plasma quantity
        with its overlays, the vector quantity."""
        if self.wanted is None and self.vector_wanted is None:
            return False
        return self._vector_loaded() and (self.wanted is None or (
            self._current() and all(self._loaded(r, q) for r, q in
                                    self._overlays_needed())))

    def _overlays_needed(self):
        """[(role, Quantity)] of the overlay drawn: the quantity of the
        Overlay section over a plasma plot that is not contour lines."""
        return [("lines", self.overlay_wanted)] if \
            self.overlay_wanted is not None and self._overlay_allowed() \
            else []

    def _fetch(self):
        """Ask for the chosen quantity (with the current b2plot operations)
        and for the active overlays that are not loaded yet; the vector
        and wall quantities too."""
        self._fetch_wall()
        self._fetch_vector()
        if self.wanted is None:
            self.redraw()
            return
        for role, q in self._overlays_needed():
            ops = self.quantity.ops(q, overlay=True)
            if self._loaded(role, q):
                continue
            if q.source == "equilibrium":   # computed here, as the maps
                geo = inspect.files(self.run)[0]
                try:
                    data = equilibrium.field(self.run, geo, q.name, ops)
                except Exception as err:    # e.g. midplanes not asked
                    data = None
                    self.status.emit("Overlay of %s: %s" % (q.name, err))
                if data is not None:
                    self.deliver((role, q, ops, None), data)
            else:
                self.request.emit((role, q, ops, self._source(q)))
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
        self.ask_frames([p])

    def ask_frames(self, positions):
        """Ask b2plot for the frames of the quantities plotted at these
        slider positions (kept in the cache)."""
        wants = [("main", self.wanted, self.quantity.ops(self.wanted))] + [
            (r, q, self.quantity.ops(q, overlay=True))
            for r, q in self._overlays_needed()] if \
            self.wanted is not None else []
        wants += [("vector", self.vector_wanted, ())]
        for p in positions:
            for role, q, ops in wants:
                if q is not None and q.movie:
                    self.request.emit(("prefetch", q, ops,
                                       self.time_box.source_of(q, p)))

    def _options_changed(self):
        if self.time_box.playing_images():  # the images are of the old
            self.time_box.play.setChecked(False)    # plot
        self._fetch()

    def deliver(self, want, data, console=""):
        """Result of a request (data None on failure) and what b2plot
        printed for it (warnings go to the status bar)."""
        role, q, ops, source = want
        lines = [x.strip() for x in console.splitlines() if x.strip()]
        tail = " ".join(lines[-3:])
        if role == "tools":
            self.tools.deliver(data)
            return
        if role == "frames":            # all the frames of the chords
            self.tools.frame_delivered(want, data)
            return
        if role == "allspecies":        # the chords, a curve per species
            self.tools.species_delivered(want, data)
            return
        if role == "balance":
            self.balance.deliver_rc(data)
            return
        if role == "vector":
            if data is not None and q is self.vector_wanted and \
                    source == self._source(q):
                self.vector_data = data
                self._species_menus()
                self.redraw()
            elif data is None:
                self.status.emit("b2plot returned no data for %s. %s"
                                 % (q.name, tail))
            return
        if role == "wall":
            if data is not None and q is self.wall_wanted:
                self.wall_data = data
                self._species_menus()
                self.redraw()
            elif data is None:
                self.status.emit("b2plot returned no data for %s. %s"
                                 % (q.name, tail))
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
                    source == self._source(q) and tuple(ops) == \
                    self.quantity.ops(q, overlay=True):
                self.odata[role] = data
                self._species_menus()
                self.redraw()
            return
        if q is not self.wanted or ops != self.quantity.ops(q) or \
                source != self._source(q):
            return
        self.data = data
        self._species_menus()
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
        """The label of the colour bar of the plasma quantity."""
        return self._bar_label(self.wanted, self.data) if self.wanted \
            else None

    def _shown_pairs(self):
        """[(Quantity, data as sent)] of the plots drawn: plasma, vector,
        wall."""
        return [(q, d) for q, d, on in (
            (self.wanted, self.data, self.run is not None and
             self._current()),
            (self.vector_wanted, self.vector_data, self.vector_wanted and
             self.vector_data is not None and self._vector_loaded()),
            (self.wall_wanted, self.wall_data, self.wall_wanted and
             self.wall_data is not None)) if on]

    def _name_of(self, q, data):
        """The description of quantity q (data as sent) without its unit,
        with its species."""
        species = self.species_text(data)
        return split_unit(q.description)[0] + (
            " [%s]" % species if species else "")

    def _bar_label(self, q, data):
        """Label of the colour bar of quantity q (data as sent): its unit
        when it is the only plot (its name is the title), else its name
        and the unit in parentheses (no title)."""
        unit = split_unit(q.description)[1] or (data.unit if data else "")
        if len(self._shown_pairs()) <= 1:
            return unit or None
        return self._name_of(q, data) + (" (%s)" % unit if unit else "")

    def _overlay_data(self):
        """{"lines": (data, PlotStyle, label of its colour bar)} of the
        overlay drawn (loaded), or {}."""
        return {role: (self.odata[role], self.quantity.overlay_style(),
                       self._overlay_label(q, self.odata[role]))
                for role, q in self._overlays_needed()
                if self._loaded(role, q)}

    def _overlay_label(self, q, data):
        """Name of the overlay quantity, its species and its unit in
        parentheses: always on its colour bar."""
        unit = split_unit(q.description)[1] or data.unit
        return self._name_of(q, data) + (" (%s)" % unit if unit else "")

    def _seed_preset(self, key):
        """Streamline seeds along a curve of the run (plot.shapes.SEEDS)."""
        if self.run is None:
            return
        n = self.quantity.streams.nseeds.value()
        pts = shapes.seed_points(self.run, key, n, lambda p: np.asarray(
            self.run.geometry.finder(p[:, 0], p[:, 1])) >= 0)
        text = dict((k, t) for t, k in shapes.SEEDS)[key]
        self.status.emit("%d seeds along the %s" % (len(pts), text)
                         if len(pts) else "No %s in this run" % text)
        self.quantity.set_seeds([tuple(p) for p in pts])

    def species_text(self, data):
        """The species chosen, for the name of the plasma, vector or wall
        data: '' unless data has several species (or b2plot reduced the
        plasma data to the species chosen)."""
        q = self.quantity
        overlay = data is not None and data is self.odata.get("lines")
        menu = q.plasma_species if data is self.data else \
            q.vector_species if data is self.vector_data else \
            q.overlay_species if overlay else q.wall_species
        if data is None or menu.combo.count() <= 1 or not (
                len(data.columns) > 1 or data is self.data and q.reduced()
                or overlay and q.overlay_reduced()):
            return ""
        text = menu.text()      # several curves (the chords): their sum
        return SUM if text == ALL else text.replace(" (all)", " (sum)")

    def _title(self):
        """The automatic title: the name of the quantity plotted when it is
        the only plot (its unit in the colour bar), else none (the names
        in the colour bars); the frames of a movie shown; the masks."""
        shown = self._shown_pairs()
        title = self._name_of(*shown[0]) if len(shown) == 1 else ""
        movie = next((q for q, _ in shown if self._source(q)), None)
        if movie is not None:
            title = (title + "  \u2014  " if title else "") + \
                self.time_box.time_text(movie.movie)
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

    def _frames_moved(self):
        """Another position of the movie: once its frames are here, only
        what changes is drawn again (Plot2D.fast_draw)."""
        self._moving = True
        self._fetch()

    def redraw(self):
        """The plots again; after a move of the slider, by repainting only
        what changes (no full draw of the canvas)."""
        canvas = self.canvas
        if not (self._moving and self._shown()) or canvas.held:
            self._redraw()
            return
        self._moving = False
        canvas.held = True              # the draws asked for: skipped
        try:
            self._redraw()
        finally:
            canvas.held = False
        if not self.plot.fast_draw():
            canvas.draw_idle()

    def _redraw(self):
        self._draw_wall()
        if self.wanted is None:     # the vector or the wall plot alone, both
            self._show_empty()
            self._draw_vectors()
            if self._shown_pairs():
                self._labels_and_prefetch()
            return
        if self.run is None or self.data is None or not self._current():
            return
        try:
            self.plot.show(self.data, self.quantity.style(), self._unit(),
                           self._overlay_data())
        except Exception as err:     # a bad option must not end the GUI
            self.status.emit("Cannot draw %s: %s" % (self.data.name, err))
            return
        self._draw_vectors()
        self.balance.restyle()
        self.tools.data_changed()       # the results window follows
        if self.plot.drawn == 0:
            self.status.emit("%s: zero in every cell shown" % self.data.name)
        self._labels_and_prefetch()
        if self.plot.mappable is not None:
            norm = self.plot.mappable.norm
            self.quantity.set_range(norm.vmin, norm.vmax)
        if self.plot.overlay_mappable is not None:
            norm = self.plot.overlay_mappable.norm
            self.quantity.set_overlay_range(norm.vmin, norm.vmax)
        self._measures()
        self.canvas.draw_idle()

    def _labels_and_prefetch(self):
        """The title of the plot drawn, then the next frames asked for
        (playing)."""
        title = self._title()
        self.quantity.labels_box.set_title_hint(title)
        self.plot.set_labels(self.quantity.labels_box.style(), title,
                             self.label_values())
        if self._shown():
            self._prefetch()

    def _measures(self):
        """Chords with a plasma or a vector quantity plotted, Statistics
        with a plasma quantity, Overlay with a plasma quantity that is not
        contour lines (Inspect cell also on the grid alone); a section
        open closes without its quantity."""
        plasma = self.run is not None and self.data is not None and \
            self.wanted is not None
        chords = plasma or self.run is not None and \
            self._vector_args() is not None
        overlay = plasma and self._overlay_allowed()
        self.quantity.chords_button.setEnabled(chords)
        self.quantity.stats_button.setEnabled(plasma)
        self.quantity.overlay_button.setEnabled(overlay)
        self._set_plotted()             # the overlay options or not
        section = self.tools.section
        if section == "chords" and not chords or \
                section == "stats" and not plasma or \
                section == "overlay" and not overlay:
            self.tools.open_section(None)

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
        """Arrows and streamlines follow zoom and pan."""
        if self.vector_wanted is not None and self.vector_data is not None:
            self._vector_timer.start()

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
                self.balance.grabs(event):
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
        self.tools.apply_theme()
        self.quantity.mark_groups()
        self.balance.apply_theme()
        self.tracing.apply_theme()
        self.canvas.draw_idle()

    def _show_empty(self):
        """Nothing plotted: the layers, the colour-bar placeholder and the
        axis labels."""
        self.plot.show_empty()
        self.balance.restyle()
        self.plot.set_labels(self.quantity.labels_box.style(),
                             self._mask_title(""), self.label_values())
        self._measures()
        self.canvas.draw_idle()

    def _align_commands(self, *_):
        """The first command at the height of the top of the plot box, the
        last one at the height of its bottom; the readout under the box,
        from its left edge, at the bottom of the canvas."""
        y = self.canvas.mapTo(self, QtCore.QPoint(0, 0)).y() - \
            self.commands.mapTo(self, QtCore.QPoint(0, 0)).y()
        box = self.plot.ax.get_position()
        h = self.canvas.height()
        self.commands.set_top(y + round((1.0 - box.y1) * h))
        self.commands.set_bottom(self.commands.height() - y -
                                 round((1.0 - box.y0) * h))
        self.hover.move(round(box.x0 * self.canvas.width()),
                        h - self.hover.height())

    def ask_label(self, name):
        """Ask b2plot for a label quantity for the parallel balance."""
        q = next((q for q in self.final_quantities if q.name == name), None)
        if q is not None:
            self.request.emit(("balance", q, (), None))

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
