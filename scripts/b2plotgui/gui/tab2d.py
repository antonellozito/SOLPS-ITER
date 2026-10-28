"""2D tab: quantity panel, one fixed plot, layers panel."""

import json
import os
import socket
from dataclasses import replace

import numpy as np
from matplotlib.figure import Figure

from .. import catalog, page, plot2d
from ..data import split_unit
from ..qt import (FigureCanvasQTAgg, NavigationToolbar2QT, QtCore, QtGui,
                  QtWidgets, Qt, Signal)
from .export import FigureDialog, ValuesDialog
from .layers import LayersPanel, from_dict
from .quantity import QuantityPanel


def _scrolled(widget, width):
    area = QtWidgets.QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setMinimumWidth(width)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    return area


class Tab2D(QtWidgets.QWidget):
    """The 2D plots tab; data requests go through the main window."""

    request = Signal(object)        # (role, Quantity, operations, source)
    export = Signal(object)         # (Quantity, names, paths, ops, table,
                                    #  source)
    add_to_page = Signal(object)    # plot2d.Snapshot
    status = Signal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.run = None
        self.data = None
        self.wanted = None
        self.odata = {}                 # overlay role -> Field or Vector
        self._seed_points = None
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(420, 420)
        self.plot = plot2d.Plot2D(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.quantity = QuantityPanel()
        self.quantity.quantity_chosen.connect(self._chosen)
        self.quantity.style_changed.connect(self._options_changed)
        self.quantity.seed_line.connect(self._start_seed_line)
        self.time_box = self.quantity.time_box
        self.time_box.source_changed.connect(self._source_changed)
        self.time_box.frames_changed.connect(self._fetch)
        self.time_box.export_frames.connect(lambda: self.export_frames())
        self.time_box.ready = self._shown
        self._frames_job = None
        self.final_quantities, self.movie_quantities = [], []
        self.layers = LayersPanel(self._saved_layers())
        self.layers.changed.connect(self._layer_changed)
        for key, st in self.layers.styles().items():
            self.plot.layer_styles[key] = st

        self.views = QtWidgets.QComboBox()
        self.views.setToolTip("View presets and saved views")
        self.views.activated.connect(self._view_chosen)
        save = QtWidgets.QToolButton()
        save.setText("Save view")
        save.clicked.connect(lambda *_: self._save_view())
        add = QtWidgets.QToolButton()
        add.setText("Add to page")
        add.setToolTip("Add this plot with all its settings to the page "
                       "composer")
        add.clicked.connect(lambda *_: self._add_to_page())
        self.box = []
        for tip in ("R min (m)", "R max (m)", "Z min (m)", "Z max (m)"):
            e = QtWidgets.QLineEdit()
            e.setValidator(QtGui.QDoubleValidator())
            e.setToolTip(tip + "; the box is widened to the equal aspect")
            e.setMaximumWidth(64)
            e.editingFinished.connect(self._box_edited)
            self.box.append(e)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.toolbar, 1)
        second = QtWidgets.QHBoxLayout()
        second.addWidget(QtWidgets.QLabel("View"))
        second.addWidget(self.views)
        second.addWidget(save)
        second.addSpacing(12)
        second.addWidget(QtWidgets.QLabel("R"))
        second.addWidget(self.box[0])
        second.addWidget(self.box[1])
        second.addWidget(QtWidgets.QLabel("Z"))
        second.addWidget(self.box[2])
        second.addWidget(self.box[3])
        second.addStretch(1)
        second.addWidget(add)
        self.hover = QtWidgets.QLabel(" ")
        self.hover.setTextInteractionFlags(Qt.TextSelectableByMouse)
        centre = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(centre)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addLayout(top)
        cl.addLayout(second)
        cl.addWidget(self.canvas, 1)
        cl.addWidget(self.hover)

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
        self.canvas.mpl_connect("button_press_event", self._click)
        self.setEnabled(False)

    # ----------------------------------------------------------- settings
    def _saved_layers(self):
        raw = self.settings.value("layers2d", "")
        try:
            saved = json.loads(raw) if raw else {}
        except ValueError:
            saved = {}
        return {k: from_dict(saved.get(k, {}), default)
                for k, (_, default) in plot2d.LAYERS.items()}

    def _layer_changed(self, key, style):
        self.plot.set_layer(key, style)
        self.settings.setValue("layers2d", json.dumps(
            {k: dict(s.__dict__) for k, s in self.layers.styles().items()}))
        self.canvas.draw_idle()

    # ---------------------------------------------------------------- run
    def set_run(self, run):
        self.run, self.data, self.wanted, self.odata = run, None, None, {}
        self.plot.set_run(run)
        for signal in ("xlim_changed", "ylim_changed"):
            self.plot.ax.callbacks.connect(signal, self._view_moved)
        self._view_moved()
        available = {"structure", "device", "separatrices", "boundary"}
        available = (available & set(k for k, v in run.layers.items()
                                     if len(v))) | {"grid"}
        if run.trimesh is not None:
            available.add("eirene")
        if len(run.geometry.xpoints):
            available.add("xpoints")
        if run.psimap is not None:
            available.add("flux")
        self.layers.set_available(available)
        self.final_quantities = catalog.quantities(run.catalog)
        self.movie_quantities = catalog.movie_quantities(run.movies)
        self.time_box.set_movies(run.movies)
        quantities = self.final_quantities
        self.quantity.set_quantities(quantities)
        self.quantity.set_run_choices(
            [q for q in quantities if q.source in ("vector", "evector")],
            [q for q in quantities if q.source in ("matrix", "eirene")],
            run.geometry)
        self._fill_views()
        self.setEnabled(True)
        self.toolbar.update()
        self.canvas.draw_idle()
        last = self.settings.value("quantity2d", "te")
        if not self.quantity.select(last):
            self.quantity.select("te")

    def _source_changed(self):
        """Final state or movie frames: the quantities of that source,
        the same quantity again where it exists."""
        movie = self.time_box.movie()
        quantities = self.movie_quantities if movie else \
            self.final_quantities
        name = self.wanted.name if self.wanted else "te"
        self.quantity.set_quantities(quantities)
        self.quantity.overlay_box.set_choices(
            [q for q in quantities if q.source in ("vector", "evector")],
            [q for q in quantities if q.source in ("matrix", "eirene")])
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
        if self.quantity.kind() not in plot2d.KINDS_SCALAR:
            return []
        return self.quantity.overlay_box.wanted()

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
                src = (q.movie,) + self.time_box.frames_at(p, q.movie)
                self.request.emit(("prefetch", q, ops, src))

    def _options_changed(self):
        self._fetch()

    def deliver(self, want, data, error=""):
        """Result of a request (data None and an error text on failure)."""
        role, q, ops, source = want
        if role == "export":
            self.status.emit("Values of %s written to %s" % (
                q.name, ", ".join(data)) if data is not None else
                "b2plot did not write the values of %s. %s" % (q.name,
                                                                error))
            return
        if data is None:
            self.status.emit("b2plot returned no data for %s. %s"
                             % (q.name, error))
            return
        if role != "main":
            if (role, q) in self._overlays_needed() and \
                    source == self._source(q):
                self.odata[role] = data
                self.redraw()
            return
        if q is not self.wanted or ops != self.quantity.ops(q) or \
                source != self._source(q):
            return
        self.data = data
        if not self.quantity.reduced():
            species = (self.run.info or {}).get("species")
            self.quantity.set_columns(data.columns, species)
        self.redraw()

    def _unit(self):
        unit = split_unit(self.wanted.description)[1] if self.wanted else None
        factor = self.quantity.factor_value()
        if factor != 1.0:
            unit = "%s  (\u00d7 %g)" % (unit or "", factor)
        return unit or None

    def _overlay_data(self):
        ostyle = self.quantity.overlay_box.style()
        overlays = {}
        for role, q in self._overlays_needed():
            if self._loaded(role, q):
                overlays[role] = (self.odata[role], ostyle)
        return overlays

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
            if self._frames_job is not None:
                QtCore.QTimer.singleShot(0, self._frame_ready)
        if self.plot.mappable is not None:
            norm = self.plot.mappable.norm
            self.quantity.set_range(norm.vmin, norm.vmax)
        self.canvas.draw_idle()

    # ------------------------------------------------------------- export
    def snapshot(self):
        """The plot shown with all its settings, or None."""
        if self.run is None or not self._current():
            return None
        return plot2d.Snapshot(
            run=self.run, data=self.data, style=self.quantity.style(),
            unit=self._unit(), overlays=self._overlay_data(),
            layers={k: replace(s) for k, s in self.layers.styles().items()},
            view=self.plot.get_view(),
            labels=self.quantity.labels_box.style(), title=self._title(),
            values=self.label_values())

    def _add_to_page(self):
        snap = self.snapshot()
        if snap is None:
            self.status.emit("No plot to add to the page")
            return
        self.add_to_page.emit(snap)

    def export_figure(self, path=None, shape="shown", dpi=150):
        """Write the plot (dialog unless path is given); returns files."""
        snap = self.snapshot()
        if snap is None:
            self.status.emit("No plot to export")
            return []
        if path is None:
            dlg = FigureDialog(self.settings, self.wanted.name.replace(
                " ", "_") + ".pdf", parent=self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return []
            path, dpi = dlg.path(), dlg.dpi.value()
            shape = dlg.shape.currentData()
        size = page.SHAPES[shape][1]
        try:
            if size is None:            # as shown: the figure of the tab
                self.figure.savefig(path, dpi=dpi)
                files = [path]
            else:
                files = page.save(path, [snap], size, dpi, own=True)
        except Exception as err:
            self.status.emit("Cannot export the figure: %s" % err)
            return []
        self.status.emit("Figure written to %s" % ", ".join(files))
        return files

    def export_values(self, paths=None, table=False, all_species=False):
        """Ask b2plot to write the values of the quantity shown (dialog
        unless paths are given)."""
        q = self.wanted
        if self.run is None or q is None:
            return
        if paths is None:
            dlg = ValuesDialog(self.settings, q,
                               self.quantity.species.currentText(), self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            paths, table = dlg.paths(), dlg.table()
            all_species = dlg.all_species()
        names = [q.poloidal, q.radial] if q.source in ("vector", "evector") \
            else [q.name]
        self.export.emit((q, names, list(paths),
                          self.quantity.value_ops(q, all_species), table,
                          self._source(q)))

    def export_frames(self, path=None, shape="shown", dpi=150):
        """Every slider position of the movie as numbered image files
        (name_0001.png, ...) or as the pages of one PDF (dialog unless
        path is given); the frames are drawn one after the other."""
        if self.run is None or self.wanted is None or \
                not self._source(self.wanted):
            self.status.emit("Export frames needs movie frames: Time > "
                             "Movie frames")
            return
        if path is None:
            dlg = FigureDialog(self.settings, self.wanted.name.replace(
                " ", "_") + "_frames.png", parent=self)
            dlg.setWindowTitle("Export frames")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            path, dpi = dlg.path(), dlg.dpi.value()
            shape = dlg.shape.currentData()
        self.time_box.play.setChecked(False)
        self._frames_job = dict(path=path, shape=shape, dpi=dpi,
                                todo=self.time_box.positions(), snaps=[],
                                files=[], start=self.time_box.pos.value())
        self._next_frame()

    def _next_frame(self):
        job = self._frames_job
        if not job["todo"]:
            self._finish_frames()
            return
        p = job["todo"][0]
        if p == self.time_box.pos.value() and self._shown():
            QtCore.QTimer.singleShot(0, self._frame_ready)
        else:
            self.time_box.set_position(p)

    def _frame_ready(self):
        """Save the frame drawn (PNG, SVG) or keep it for the PDF."""
        job = self._frames_job
        if job is None or not job["todo"] or not self._shown() or \
                self.time_box.pos.value() != job["todo"][0]:
            return
        p = job["todo"].pop(0)
        stem, ext = os.path.splitext(job["path"])
        size = page.SHAPES[job["shape"]][1]
        try:
            if ext.lower() == ".pdf":
                snap = self.snapshot()
                if size is None:
                    size = tuple(self.figure.get_size_inches())
                job["size"] = size
                job["snaps"].append(snap)
            else:
                name = "%s_%04d%s" % (stem, p, ext)
                if size is None:
                    self.figure.savefig(name, dpi=job["dpi"])
                else:
                    page.save(name, [self.snapshot()], size, job["dpi"],
                              own=True)
                job["files"].append(name)
        except Exception as err:
            self._frames_job = None
            self.status.emit("Cannot export the frames: %s" % err)
            return
        self.status.emit("Exporting frames: %d left" % len(job["todo"]))
        self._next_frame()

    def _finish_frames(self):
        job, self._frames_job = self._frames_job, None
        if job["snaps"]:
            try:
                job["files"] = page.save(job["path"], job["snaps"],
                                         job["size"], job["dpi"], own=True)
            except Exception as err:
                self.status.emit("Cannot export the frames: %s" % err)
                return
        self.time_box.set_position(job["start"])
        n = len(job["snaps"]) or len(job["files"])
        self.status.emit("%d frames written to %s" % (
            n, job["files"][0] if len(job["files"]) == 1 else
            "%s ... %s" % (job["files"][0], job["files"][-1])))

    # -------------------------------------------------------------- views
    def _fill_views(self):
        self.views.clear()
        for name, box in self.plot.views().items():
            self.views.addItem(name, box)
        saved = self._saved_views()
        if saved:
            self.views.insertSeparator(self.views.count())
            for name, box in saved.items():
                self.views.addItem(name, tuple(box))

    def _saved_views(self):
        try:
            return json.loads(self.settings.value("views2d", "") or "{}")
        except ValueError:
            return {}

    def _view_chosen(self, index):
        box = self.views.itemData(index)
        if box:
            self.plot.set_view(box)
            self.toolbar.push_current()
            self.canvas.draw_idle()

    def _save_view(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save view",
                                                  "Name of this view")
        if ok and name.strip():
            saved = self._saved_views()
            saved[name.strip()] = list(self.plot.get_view())
            self.settings.setValue("views2d", json.dumps(saved))
            self._fill_views()

    def _view_moved(self, *_):
        for e, v in zip(self.box, self.plot.get_view()):
            e.setText("%.4g" % v)
        vectors = self.data is not None and hasattr(self.data, "vr")
        if vectors or "arrows" in self.odata:
            self._vector_timer.start()

    def _box_edited(self):
        try:
            box = [float(e.text()) for e in self.box]
        except ValueError:
            return
        if box[1] > box[0] and box[3] > box[2]:
            self.plot.set_view(box)
            self.toolbar.push_current()
            self.canvas.draw_idle()

    def _redraw_vectors(self):
        self.redraw()

    # -------------------------------------------------------------- mouse
    def _motion(self, event):
        if event.inaxes is self.plot.ax and event.xdata is not None:
            self.hover.setText(self.plot.lookup(event.xdata, event.ydata))
        else:
            self.hover.setText(" ")

    def _start_seed_line(self):
        self._seed_points = []
        self.status.emit("Click the start and the end of the seed line")

    def _click(self, event):
        if self._seed_points is None or event.inaxes is not self.plot.ax:
            return
        self._seed_points.append((event.xdata, event.ydata))
        if len(self._seed_points) == 2:
            (x0, y0), (x1, y1) = self._seed_points
            n = self.quantity.nseeds.value()
            t = np.linspace(0.0, 1.0, n)
            self._seed_points = None
            self.status.emit("Seed line set")
            self.quantity.set_seeds(list(zip(x0 + t * (x1 - x0),
                                             y0 + t * (y1 - y0))))

