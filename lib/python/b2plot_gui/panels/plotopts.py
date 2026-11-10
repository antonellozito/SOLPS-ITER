"""Option groups of the plot: colour scale, contour lines, arrows and
streamlines; each gives its part of the PlotStyle (style_fields)."""

from ..plot.shapes import SEEDS
from ..plot.vector import NUM_ARROWS
from ...qt import QtGui, QtWidgets, Qt, Signal
from .layers import ColorButton, spin, style_combo

CMAPS = ["turbo", "viridis", "plasma", "inferno", "magma", "cividis",
         "jet", "hot", "coolwarm", "RdBu_r", "seismic", "bwr", "Spectral_r",
         "gray", "pwn"]


def _number(text, default):
    try:
        return float(text)
    except ValueError:
        return default


class _Box(QtWidgets.QGroupBox):
    """A group whose widgets all emit changed."""

    changed = Signal()

    def _watch(self, combos=(), checks=(), values=(), colours=()):
        for w in combos:
            w.currentIndexChanged.connect(self._emit)
        for w in checks:
            w.toggled.connect(self._emit)
        for w in values:
            w.valueChanged.connect(self._emit)
        for w in colours:
            w.changed.connect(self._emit)

    def _emit(self, *_):
        self.changed.emit()


class ColourBox(_Box):
    """Colormap, scale, range, factor, colour bar and cell edges."""

    def __init__(self, parent=None):
        super().__init__("Colour scale", parent)
        cf = QtWidgets.QFormLayout(self)
        row = QtWidgets.QHBoxLayout()
        self.cmap = QtWidgets.QComboBox()
        self.cmap.addItems(CMAPS)
        self.cmap.setItemData(len(CMAPS) - 1, "Red positive, white zero, "
                              "blue negative (MATLAB colorbarpwn)",
                              Qt.ToolTipRole)
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
            w.editingFinished.connect(self._emit)
        row.addWidget(self.auto)
        row.addWidget(self.vmin, 1)
        row.addWidget(self.vmax, 1)
        cf.addRow("Range", row)
        row = QtWidgets.QHBoxLayout()
        self.factor = QtWidgets.QLineEdit("1")
        self.factor.setValidator(QtGui.QDoubleValidator())
        self.factor.setToolTip("Values multiplied by this factor (b2plot "
                               "rm*, rem*)")
        self.factor.editingFinished.connect(self._emit)
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
        row = QtWidgets.QHBoxLayout()
        self.bw = QtWidgets.QCheckBox("black and white")
        self.bw.setToolTip("Grey patches, hatched filled contours, black "
                           "lines (b2plot bw)")
        self.cell_values = QtWidgets.QCheckBox("values in cells")
        self.cell_values.setToolTip("Values written in the cells when at "
                                    "most 400 are in the view")
        row.addWidget(self.bw)
        row.addWidget(self.cell_values)
        cf.addRow(row)
        self._watch((self.cmap, self.scale), (self.reverse, self.colorbar,
                                              self.edges, self.bw,
                                              self.cell_values),
                    (self.decades,))
        self.auto.toggled.connect(self._auto_toggled)

    def _auto_toggled(self, on):
        self.vmin.setEnabled(not on)
        self.vmax.setEnabled(not on)
        self._emit()

    def factor_value(self):
        return _number(self.factor.text(), 1.0)

    def set_range(self, lo, hi):
        """Show the automatic range in the min and max boxes."""
        if self.auto.isChecked():
            self.vmin.setText("%.4g" % lo)
            self.vmax.setText("%.4g" % hi)

    def style_fields(self):
        return dict(cmap=self.cmap.currentText(),
                    reverse=self.reverse.isChecked(),
                    scale=self.scale.currentText(), auto=self.auto.isChecked(),
                    vmin=_number(self.vmin.text(), 0.0),
                    vmax=_number(self.vmax.text(), 1.0),
                    colorbar=self.colorbar.isChecked(),
                    edges=self.edges.isChecked(),
                    decades=self.decades.value(), bw=self.bw.isChecked(),
                    cell_values=self.cell_values.isChecked())


class LinesBox(_Box):
    """Contour lines: over the fill, one colour, width, style, labels."""

    def __init__(self, parent=None):
        super().__init__("Contour lines", parent)
        lf = QtWidgets.QFormLayout(self)
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
        self._watch((self.line_style,), (self.fill_lines, self.mono,
                                         self.line_labels),
                    (self.line_width,), (self.line_color,))

    def style_fields(self):
        return dict(fill_lines=self.fill_lines.isChecked(),
                    line_mono=self.mono.isChecked(),
                    line_color=self.line_color.color(),
                    line_width=self.line_width.value(),
                    line_style=self.line_style.currentData(),
                    line_labels=self.line_labels.isChecked())


class ArrowsBox(_Box):
    """Arrow length, width, spacing and colour."""

    def __init__(self, parent=None):
        super().__init__("Arrows", parent)
        af = QtWidgets.QFormLayout(self)
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
        self._watch((), (self.normalize, self.by_magnitude),
                    (self.every, self.arrow_length, self.arrow_width),
                    (self.arrow_color,))

    def style_fields(self):
        return dict(normalize=self.normalize.isChecked(),
                    arrow_length=self.arrow_length.value(),
                    arrow_width=self.arrow_width.value(),
                    every=self.every.value(),
                    color_by_magnitude=self.by_magnitude.isChecked(),
                    arrow_color=self.arrow_color.color())


class StreamBox(_Box):
    """Streamline density, line, arrows and seed points (a line drawn on
    the plot or a preset of the run geometry)."""

    seed_line = Signal(bool)        # wait for the clicks of the line, or not
    seed_preset = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Streamlines", parent)
        sf = QtWidgets.QFormLayout(self)
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
        self.num_arrows = QtWidgets.QSpinBox()
        self.num_arrows.setRange(1, 20)
        self.num_arrows.setEnabled(NUM_ARROWS)
        self.num_arrows.setToolTip("Arrows along each streamline" + (
            "" if NUM_ARROWS else " (needs matplotlib 3.10)"))
        sf.addRow("Arrows per line", self.num_arrows)
        row = QtWidgets.QHBoxLayout()
        self.seed_kind = QtWidgets.QComboBox()
        for text, key in SEEDS:
            self.seed_kind.addItem(text, key)
        self.seed_kind.setToolTip("Where the streamlines start")
        self.seed_kind.activated.connect(lambda *_: self._seed_kind())
        self.nseeds = QtWidgets.QSpinBox()
        self.nseeds.setRange(2, 500)
        self.nseeds.setValue(30)
        self.nseeds.setToolTip("Seeds along the line")
        self.nseeds.valueChanged.connect(lambda *_: self._seed_kind(False))
        row.addWidget(self.seed_kind, 1)
        row.addWidget(self.nseeds)
        sf.addRow("Seeds", row)
        row = QtWidgets.QHBoxLayout()
        self.seed_button = QtWidgets.QPushButton("Draw seed line")
        self.seed_button.setToolTip("Then click the two ends of the line on "
                                    "the plot (click again to cancel)")
        self.seed_button.setCheckable(True)
        self.seed_button.clicked.connect(
            lambda on: self.seed_line.emit(bool(on)))
        self.clear_seeds = QtWidgets.QPushButton("Clear")
        self.clear_seeds.clicked.connect(lambda *_: self.set_seeds([]))
        self.markers = QtWidgets.QCheckBox("markers")
        self.markers.setToolTip("Red circles at the seeds")
        row.addWidget(self.seed_button)
        row.addWidget(self.clear_seeds)
        row.addWidget(self.markers)
        row.addStretch(1)
        sf.addRow(row)
        self.seeds = []
        self._watch((self.stream_style,), (self.markers,),
                    (self.density, self.stream_width, self.num_arrows),
                    (self.stream_color,))

    def _seed_kind(self, line=True):
        """A preset gives its seeds at once (and with each new number);
        the drawn line waits for the clicks of Draw seed line."""
        key = self.seed_kind.currentData()
        self.seed_button.setEnabled(key == "line")
        if key != "line":
            self.seed_preset.emit(key)
        elif line:
            self.seed_line.emit(True)

    def waiting(self, on):
        """Draw seed line shows whether the plot waits for its clicks."""
        self.seed_button.blockSignals(True)
        self.seed_button.setChecked(on)
        self.seed_button.blockSignals(False)

    def set_seeds(self, seeds):
        self.seeds = list(seeds)
        self._emit()

    def style_fields(self):
        return dict(density=self.density.value(),
                    stream_width=self.stream_width.value(),
                    stream_color=self.stream_color.color(),
                    stream_style=self.stream_style.currentData(),
                    seeds=self.seeds, num_arrows=self.num_arrows.value(),
                    seed_markers=self.markers.isChecked())
