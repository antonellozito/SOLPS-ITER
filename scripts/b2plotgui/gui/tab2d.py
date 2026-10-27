"""2D tab: quantity panel, one fixed plot, layers panel."""

import json

import numpy as np
from matplotlib.figure import Figure

from .. import catalog, plot2d
from ..qt import (FigureCanvasQTAgg, NavigationToolbar2QT, QtWidgets, Qt,
                  Signal)
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

    request = Signal(object)        # catalog.Quantity
    status = Signal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.run = None
        self.data = None
        self.wanted = None
        self._seed_points = None
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(420, 420)
        self.plot = plot2d.Plot2D(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.quantity = QuantityPanel()
        self.quantity.quantity_chosen.connect(self._chosen)
        self.quantity.style_changed.connect(self.redraw)
        self.quantity.seed_line.connect(self._start_seed_line)
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
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.toolbar, 1)
        top.addWidget(QtWidgets.QLabel("View"))
        top.addWidget(self.views)
        top.addWidget(save)
        self.hover = QtWidgets.QLabel(" ")
        self.hover.setTextInteractionFlags(Qt.TextSelectableByMouse)
        centre = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(centre)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addLayout(top)
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
        self.run, self.data, self.wanted = run, None, None
        self.plot.set_run(run)
        available = {"structure", "separatrices", "boundary", "grid"}
        available &= set(run.layers) | {"grid"}
        if run.trimesh is not None:
            available.add("eirene")
        if len(run.geometry.xpoints):
            available.add("xpoints")
        if run.geometry.psin is not None:
            available.add("flux")
        self.layers.set_available(available)
        self.quantity.set_quantities(catalog.quantities(run.catalog))
        self._fill_views()
        self.setEnabled(True)
        self.toolbar.update()
        self.canvas.draw_idle()
        last = self.settings.value("quantity2d", "te")
        if not self.quantity.select(last):
            self.quantity.select("te")

    def _chosen(self, q):
        self.wanted = q
        self.settings.setValue("quantity2d", q.name)
        self.request.emit(q)

    def deliver(self, q, data, error=""):
        """Result of a request (data None and an error text on failure)."""
        if q is not self.wanted:
            return
        if data is None:
            self.status.emit("b2plot returned no data for %s. %s"
                             % (q.name, error))
            return
        self.data = data
        species = (self.run.info or {}).get("species")
        self.quantity.set_columns(data.columns, species)
        self.redraw()

    def redraw(self):
        if self.run is None or self.data is None:
            return
        if self.wanted is not None and self.data.name != self.wanted.name:
            return
        style = self.quantity.style()
        try:
            self.plot.show(self.data, style)
        except Exception as err:     # a bad option must not end the GUI
            self.status.emit("Cannot draw %s: %s" % (self.data.name, err))
            return
        q = self.wanted
        species = self.quantity.species.currentText()
        title = q.description if q is not None else self.data.label
        if self.quantity.species.count() > 1:
            title += "  [%s]" % species
        self.plot.title(title)
        if self.plot.mappable is not None:
            norm = self.plot.mappable.norm
            self.quantity.set_range(norm.vmin, norm.vmax)
        self.canvas.draw_idle()

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

