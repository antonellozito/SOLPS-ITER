"""Quantity panel of the 2D tab: what to plot and how."""

from .. import labels
from ..plot2d import KINDS_SCALAR, KINDS_VECTOR, PlotStyle
from ..qt import QtGui, QtWidgets, Qt, Signal
from .layers import ColorButton, spin, style_combo
from .options2d import CellsBox, LevelsBox, OverlayBox

KIND_TEXT = {"patch": "Patch", "contourf": "Filled contour",
             "contour": "Contour lines", "quiver": "Quiver",
             "stream": "Streamlines", "quiverstream": "Quiver + streamlines"}
SUM = "Sum over species"
CMAPS = ["turbo", "viridis", "plasma", "inferno", "magma", "cividis",
         "jet", "hot", "coolwarm", "RdBu_r", "seismic", "bwr", "Spectral_r",
         "gray"]


def real_token(x):
    """A b2plot real: short (b2plot reads tokens of limited length) and
    with a point or an exponent, so that it is not read as an integer."""
    t = "%.6g" % x
    return t if ("." in t or "e" in t or "n" in t) else t + ".0"


def _number(text, default):
    try:
        return float(text)
    except ValueError:
        return default


class QuantityPanel(QtWidgets.QWidget):
    """Quantity tree, species, plot type and the plot options."""

    quantity_chosen = Signal(object)
    style_changed = Signal()
    seed_line = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = None
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search quantities (te, flux, ...)")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Quantity", "Description"])
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setMinimumHeight(220)
        self.tree.itemActivated.connect(self._activated)
        self.tree.itemClicked.connect(self._activated)
        lay.addWidget(self.search)
        lay.addWidget(self.tree, 1)

        form = QtWidgets.QFormLayout()
        self.species = QtWidgets.QComboBox()
        self.species.currentIndexChanged.connect(self._changed)
        form.addRow("Species", self.species)
        lay.addLayout(form)

        kinds = QtWidgets.QGroupBox("Plot type")
        kgrid = QtWidgets.QGridLayout(kinds)
        self.kind_buttons = QtWidgets.QButtonGroup(self)
        for i, kind in enumerate(KINDS_SCALAR + KINDS_VECTOR):
            b = QtWidgets.QRadioButton(KIND_TEXT[kind])
            b.setProperty("kind", kind)
            self.kind_buttons.addButton(b, i)
            kgrid.addWidget(b, i % 3, i // 3)
        self.kind_buttons.button(0).setChecked(True)
        self.kind_buttons.idToggled.connect(
            lambda i, on: on and self._kind_changed())
        lay.addWidget(kinds)

        # colour scale (fields and colour by magnitude)
        col = QtWidgets.QGroupBox("Colour scale")
        cf = QtWidgets.QFormLayout(col)
        row = QtWidgets.QHBoxLayout()
        self.cmap = QtWidgets.QComboBox()
        self.cmap.addItems(CMAPS)
        self.reverse = QtWidgets.QCheckBox("reversed")
        row.addWidget(self.cmap, 1)
        row.addWidget(self.reverse)
        cf.addRow("Colormap", row)
        self.scale = QtWidgets.QComboBox()
        self.scale.addItems(["linear", "log", "symlog"])
        cf.addRow("Scale", self.scale)
        row = QtWidgets.QHBoxLayout()
        self.auto = QtWidgets.QCheckBox("auto")
        self.auto.setChecked(True)
        self.vmin = QtWidgets.QLineEdit()
        self.vmax = QtWidgets.QLineEdit()
        for w, tip in ((self.vmin, "minimum"), (self.vmax, "maximum")):
            w.setPlaceholderText(tip)
            w.setValidator(QtGui.QDoubleValidator())
            w.setEnabled(False)
            w.editingFinished.connect(self._changed)
        row.addWidget(self.auto)
        row.addWidget(self.vmin, 1)
        row.addWidget(self.vmax, 1)
        cf.addRow("Range", row)
        row = QtWidgets.QHBoxLayout()
        self.factor = QtWidgets.QLineEdit("1")
        self.factor.setValidator(QtGui.QDoubleValidator())
        self.factor.setToolTip("Values multiplied by this factor (b2plot "
                               "rm*, rem*)")
        self.factor.editingFinished.connect(self._changed)
        self.decades = QtWidgets.QSpinBox()
        self.decades.setRange(0, 30)
        self.decades.setSpecialValueText("all")
        self.decades.setToolTip("Log scale: decades shown below the "
                                "maximum")
        self.decades.setKeyboardTracking(False)
        row.addWidget(self.factor, 1)
        row.addWidget(QtWidgets.QLabel("decades"))
        row.addWidget(self.decades)
        cf.addRow("Factor", row)
        row = QtWidgets.QHBoxLayout()
        self.colorbar = QtWidgets.QCheckBox("colour bar")
        self.colorbar.setChecked(True)
        self.edges = QtWidgets.QCheckBox("cell edges")
        row.addWidget(self.colorbar)
        row.addWidget(self.edges)
        cf.addRow(row)
        lay.addWidget(col)
        self.levels_box = LevelsBox()
        self.levels_box.changed.connect(self._changed)
        lay.addWidget(self.levels_box)

        # contour lines
        self.lines_box = QtWidgets.QGroupBox("Contour lines")
        lf = QtWidgets.QFormLayout(self.lines_box)
        row = QtWidgets.QHBoxLayout()
        self.fill_lines = QtWidgets.QCheckBox("over the fill")
        self.fill_lines.setToolTip("Lines on the filled contours, as "
                                   "b2plot cont")
        self.mono = QtWidgets.QCheckBox("one colour")
        self.line_color = ColorButton("#000000")
        row.addWidget(self.fill_lines)
        row.addWidget(self.mono)
        row.addWidget(self.line_color)
        row.addStretch(1)
        lf.addRow(row)
        row = QtWidgets.QHBoxLayout()
        self.line_width = spin(0.1, 10.0, 0.1, 0.8, tip="Line width (pt)")
        self.line_style = style_combo("-")
        self.line_labels = QtWidgets.QCheckBox("labels")
        row.addWidget(self.line_width)
        row.addWidget(self.line_style)
        row.addWidget(self.line_labels)
        lf.addRow(row)
        lay.addWidget(self.lines_box)

        # arrows
        self.arrow_box = QtWidgets.QGroupBox("Arrows")
        af = QtWidgets.QFormLayout(self.arrow_box)
        self.normalize = QtWidgets.QCheckBox("same length for all")
        af.addRow(self.normalize)
        self.arrow_length = spin(0.0, 10.0, 0.005, 0.0, 3,
                                 "Arrow length in m (0: automatic) for the "
                                 "98th percentile of the magnitudes; longer "
                                 "arrows are capped at 1.5 times")
        af.addRow("Length (m)", self.arrow_length)
        self.arrow_width = spin(0.1, 10.0, 0.1, 1.0, tip="Relative width")
        af.addRow("Width", self.arrow_width)
        self.every = QtWidgets.QSpinBox()
        self.every.setRange(0, 1000)
        self.every.setSpecialValueText("auto")
        self.every.setKeyboardTracking(False)
        af.addRow("One arrow every", self.every)
        row = QtWidgets.QHBoxLayout()
        self.by_magnitude = QtWidgets.QCheckBox("colour by magnitude")
        self.by_magnitude.setChecked(True)
        self.arrow_color = ColorButton("#000000")
        row.addWidget(self.by_magnitude)
        row.addWidget(self.arrow_color)
        row.addStretch(1)
        af.addRow(row)
        lay.addWidget(self.arrow_box)

        # streamlines
        self.stream_box = QtWidgets.QGroupBox("Streamlines")
        sf = QtWidgets.QFormLayout(self.stream_box)
        self.density = spin(0.2, 10.0, 0.1, 1.5, tip="Density")
        sf.addRow("Density", self.density)
        row = QtWidgets.QHBoxLayout()
        self.stream_width = spin(0.1, 10.0, 0.1, 0.8, tip="Line width")
        self.stream_style = style_combo("-")
        self.stream_color = ColorButton("#1f77b4")
        row.addWidget(self.stream_width)
        row.addWidget(self.stream_style)
        row.addWidget(self.stream_color)
        sf.addRow("Line", row)
        row = QtWidgets.QHBoxLayout()
        self.seed_button = QtWidgets.QPushButton("Draw seed line")
        self.seed_button.setToolTip("Click two points on the plot")
        self.seed_button.clicked.connect(lambda *_: self.seed_line.emit())
        self.nseeds = QtWidgets.QSpinBox()
        self.nseeds.setRange(2, 500)
        self.nseeds.setValue(30)
        self.nseeds.setToolTip("Seeds along the line")
        self.clear_seeds = QtWidgets.QPushButton("Clear")
        row.addWidget(self.seed_button)
        row.addWidget(self.nseeds)
        row.addWidget(self.clear_seeds)
        sf.addRow(row)
        lay.addWidget(self.stream_box)
        self.overlay_box = OverlayBox()
        self.overlay_box.changed.connect(self._changed)
        lay.addWidget(self.overlay_box)
        self.cells_box = CellsBox()
        self.cells_box.changed.connect(self._changed)
        lay.addWidget(self.cells_box)
        self.seeds = []
        self.clear_seeds.clicked.connect(lambda *_: self.set_seeds([]))

        for w in (self.cmap, self.scale, self.line_style, self.stream_style):
            w.currentIndexChanged.connect(self._changed)
        for w in (self.reverse, self.colorbar, self.edges, self.mono,
                  self.line_labels, self.normalize, self.by_magnitude,
                  self.fill_lines):
            w.toggled.connect(self._changed)
        for w in (self.decades, self.every, self.line_width,
                  self.arrow_length, self.arrow_width, self.density,
                  self.stream_width):
            w.valueChanged.connect(self._changed)
        for w in (self.line_color, self.arrow_color, self.stream_color):
            w.changed.connect(self._changed)
        self.auto.toggled.connect(self._auto_toggled)
        self._kind_changed(emit=False)

    # ---------------------------------------------------------- quantities
    def set_quantities(self, quantities):
        self.tree.clear()
        groups = {}
        for q in quantities:
            top = groups.get(q.group)
            if top is None:
                top = QtWidgets.QTreeWidgetItem([q.group])
                top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
                groups[q.group] = top
                self.tree.addTopLevelItem(top)
            item = QtWidgets.QTreeWidgetItem([q.name, q.text])
            item.setToolTip(0, q.text)
            item.setToolTip(1, q.text)
            item.setData(0, Qt.UserRole, q)
            top.addChild(item)
        self.tree.resizeColumnToContents(0)
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            shown = 0
            for j in range(top.childCount()):
                item = top.child(j)
                q = item.data(0, Qt.UserRole)
                hit = (not text or text in q.name.lower()
                       or text in q.text.lower())
                item.setHidden(not hit)
                shown += hit
            top.setHidden(shown == 0)
            top.setExpanded(bool(text) and shown > 0)

    def _activated(self, item, *_):
        q = item.data(0, Qt.UserRole)
        if q is None or q is self.current:
            return
        self.current = q
        vector = q.source in ("vector", "evector")
        for b in self.kind_buttons.buttons():
            b.setEnabled((b.property("kind") in KINDS_VECTOR) == vector)
        kind = self.kind()
        if (kind in KINDS_VECTOR) != vector:
            self.kind_buttons.button(3 if vector else 0).setChecked(True)
        self.edges.setEnabled(not vector)
        self._kind_changed(emit=False)
        self.quantity_chosen.emit(q)

    def select(self, name):
        """Select the quantity with this name, if listed."""
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            for j in range(top.childCount()):
                item = top.child(j)
                if item.data(0, Qt.UserRole).name == name:
                    self.tree.setCurrentItem(item)
                    self._activated(item)
                    return True
        return False

    def set_columns(self, columns, species=None):
        """Species names of the field columns (keeps the choice if it can)."""
        names = [labels.species_text(c) or (
            labels.species_text(species[i]) if species and i < len(species)
            else "") for i, c in enumerate(columns)]
        names = [n or "column %d" % (i + 1) for i, n in enumerate(names)]
        if len(columns) == 1 and not columns[0].strip():
            names = ["\u2014"]
        if len(names) > 1:
            names.append(SUM)
        old = self.species.currentText()
        self.species.blockSignals(True)
        self.species.clear()
        self.species.addItems(names)
        if old in names:
            self.species.setCurrentIndex(names.index(old))
        self.species.setEnabled(len(names) > 1)
        self.species.blockSignals(False)

    # -------------------------------------------------------------- style
    def summed(self):
        return self.species.currentText() == SUM

    def factor_value(self):
        try:
            return float(self.factor.text())
        except ValueError:
            return 1.0

    def proportion(self):
        """clvp intervals when b2plot computes the contour levels."""
        if self.kind() not in ("contourf", "contour"):
            return None
        return self.levels_box.proportion()

    def reduced(self):
        """True if b2plot sends one column (sum or clvp on one species)."""
        return self.summed() or (self.proportion() is not None
                                 and self.current is not None
                                 and self.current.source in ("matrix",
                                                             "eirene"))

    def ops(self, q):
        """b2plot operations applied after the label of quantity q: species
        sum or selection, scale factor, clvp contour levels."""
        eirene = q.source in ("eirene", "evector")
        ops = []
        prop = self.proportion() if q.source in ("matrix", "eirene") \
            else None
        if self.summed():
            ops.append("0 -1 esumz" if eirene else "0 -1 sumz")
        elif prop is not None:
            col = max(self.species.currentIndex(), 0)
            ops.append("%d %s" % (col, "ezsel" if eirene else "zsel"))
        f = self.factor_value()
        if f != 1.0:
            ops.append("%s %s" % (real_token(f), "rem*" if eirene else "rm*"))
        if prop is not None:
            npos, nneg = prop
            if eirene:
                ops += ["%d %d eclvp" % (nneg, npos), "guieclv", "0 eclvs"]
            else:
                ops += ["%d %d clvp" % (nneg, npos), "guiclv", "0 clvs"]
        return tuple(ops)

    def kind(self):
        b = self.kind_buttons.checkedButton()
        return b.property("kind") if b else "patch"

    def _kind_changed(self, emit=True):
        kind = self.kind()
        source = self.current.source if self.current is not None else ""
        self.lines_box.setVisible(kind in ("contour", "contourf"))
        self.fill_lines.setVisible(kind == "contourf")
        self.arrow_box.setVisible(kind in ("quiver", "quiverstream"))
        self.stream_box.setVisible(kind in ("stream", "quiverstream"))
        self.levels_box.setVisible(kind in ("contourf", "contour"))
        self.overlay_box.setVisible(kind in KINDS_SCALAR)
        self.cells_box.setVisible(source in ("matrix", "vector"))
        if emit:
            self._changed()

    def _auto_toggled(self, on):
        self.vmin.setEnabled(not on)
        self.vmax.setEnabled(not on)
        self._changed()

    def set_range(self, lo, hi):
        """Show the automatic range in the min and max boxes."""
        if self.auto.isChecked():
            self.vmin.setText("%.4g" % lo)
            self.vmax.setText("%.4g" % hi)

    def set_seeds(self, seeds):
        self.seeds = list(seeds)
        self._changed()

    def set_run_choices(self, vectors, scalars, geometry):
        """Overlay quantities and cell groups of a new run."""
        self.overlay_box.set_choices(vectors, scalars)
        self.cells_box.set_geometry(geometry)

    def style(self):
        return PlotStyle(
            **self.levels_box.style_fields(), **self.cells_box.style_fields(),
            decades=self.decades.value(),
            fill_lines=self.fill_lines.isChecked(),
            kind=self.kind(),
            column=0 if self.reduced()
            else max(self.species.currentIndex(), 0),
            cmap=self.cmap.currentText(), reverse=self.reverse.isChecked(),
            scale=self.scale.currentText(), auto=self.auto.isChecked(),
            vmin=_number(self.vmin.text(), 0.0),
            vmax=_number(self.vmax.text(), 1.0),
            colorbar=self.colorbar.isChecked(),
            edges=self.edges.isChecked(), line_mono=self.mono.isChecked(),
            line_color=self.line_color.color(),
            line_width=self.line_width.value(),
            line_style=self.line_style.currentData(),
            line_labels=self.line_labels.isChecked(),
            normalize=self.normalize.isChecked(),
            arrow_length=self.arrow_length.value(),
            arrow_width=self.arrow_width.value(), every=self.every.value(),
            color_by_magnitude=self.by_magnitude.isChecked(),
            arrow_color=self.arrow_color.color(),
            density=self.density.value(),
            stream_width=self.stream_width.value(),
            stream_color=self.stream_color.color(),
            stream_style=self.stream_style.currentData(), seeds=self.seeds)

    def _changed(self, *_):
        self.style_changed.emit()

