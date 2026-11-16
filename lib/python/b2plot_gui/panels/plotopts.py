"""Option groups of the plot: colour scale, contour lines, arrows and
streamlines; each gives its part of the PlotStyle (style_fields)."""

from ..plot.shapes import SEEDS
from ..plot.vector import NUM_ARROWS
from ..scaling import Number
from ...qt import QtWidgets, Signal
from .glyphs import CmapChooser, WidthChooser
from .layers import ColorButton, spin, style_combo


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
    """Colormap (reversed or not), scale and range."""

    def __init__(self, parent=None):
        super().__init__("Colour scale", parent)
        lay = QtWidgets.QVBoxLayout(self)
        row = QtWidgets.QHBoxLayout()   # colormap, reversed, scale
        self.cmap = CmapChooser("turbo")
        self.cmap.setToolTip("Colour map")
        self.reverse = QtWidgets.QCheckBox("reversed")
        self.scale = QtWidgets.QComboBox()
        self.scale.addItems(["linear", "log", "symlog"])
        self.scale.setToolTip("Scale: linear, logarithmic or symmetric "
                              "logarithmic")
        row.addWidget(self.cmap, 1)
        row.addWidget(self.reverse)
        row.addWidget(self.scale)
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()   # range
        self.auto = QtWidgets.QCheckBox("auto")
        self.auto.setChecked(True)
        self.vmin = QtWidgets.QLineEdit()
        self.vmax = QtWidgets.QLineEdit()
        for w, tip in ((self.vmin, "minimum"), (self.vmax, "maximum")):
            w.setPlaceholderText(tip)
            w.setValidator(Number())
            w.setEnabled(False)
            w.editingFinished.connect(self._emit)
        row.addWidget(QtWidgets.QLabel("Range"))
        row.addWidget(self.auto)
        row.addWidget(self.vmin, 1)
        row.addWidget(self.vmax, 1)
        lay.addLayout(row)
        self._watch((self.cmap, self.scale), (self.reverse,))
        self.auto.toggled.connect(self._auto_toggled)

    def _auto_toggled(self, on):
        self.vmin.setEnabled(not on)
        self.vmax.setEnabled(not on)
        self._emit()

    def set_range(self, lo, hi):
        """Show the automatic range in the min and max boxes."""
        if self.auto.isChecked():
            self.vmin.setText("%.4g" % lo)
            self.vmax.setText("%.4g" % hi)

    def style_fields(self):
        return dict(cmap=self.cmap.name(),
                    reverse=self.reverse.isChecked(),
                    scale=self.scale.currentText(), auto=self.auto.isChecked(),
                    vmin=_number(self.vmin.text(), 0.0),
                    vmax=_number(self.vmax.text(), 1.0))


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
        self.line_width = WidthChooser(0.8)
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
        grid = QtWidgets.QGridLayout(self)
        self.normalize = QtWidgets.QCheckBox("same length")
        self.normalize.setToolTip("The same length for all arrows")
        self.arrow_length = spin(0.0, 10.0, 0.005, 0.0, 3,
                                 "Arrow length in m (0: automatic) for the "
                                 "98th percentile of the magnitudes; longer "
                                 "arrows are capped at 1.5 times")
        self.arrow_width = spin(0.1, 10.0, 0.1, 1.0, tip="Relative width")
        self.every = QtWidgets.QSpinBox()
        self.every.setRange(0, 1000)
        self.every.setSpecialValueText("auto")
        self.every.setKeyboardTracking(False)
        self.every.setToolTip("One arrow every so many cells (auto: as "
                              "many as fit the view)")
        self.by_magnitude = QtWidgets.QCheckBox("colour by magnitude")
        self.by_magnitude.setChecked(True)
        self.arrow_color = ColorButton("#000000")
        length = QtWidgets.QLabel("Length")
        length.setToolTip("Arrow length in m (0: automatic)")
        for c, w in enumerate((length, self.arrow_length,
                               QtWidgets.QLabel("Width"), self.arrow_width)):
            grid.addWidget(w, 0, c)
        grid.addWidget(QtWidgets.QLabel("Every"), 1, 0)
        grid.addWidget(self.every, 1, 1)
        grid.addWidget(self.normalize, 1, 2, 1, 2)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.by_magnitude)
        row.addWidget(self.arrow_color)
        row.addStretch(1)
        grid.addLayout(row, 2, 0, 1, 4)
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
        self.num_arrows = QtWidgets.QSpinBox()
        self.num_arrows.setRange(1, 20)
        self.num_arrows.setEnabled(NUM_ARROWS)
        self.num_arrows.setToolTip("Arrows along each streamline" + (
            "" if NUM_ARROWS else " (needs matplotlib 3.10)"))
        row = QtWidgets.QHBoxLayout()   # density, arrows per line
        row.addWidget(self.density)
        arrows = QtWidgets.QLabel("Arrows")
        arrows.setToolTip(self.num_arrows.toolTip())
        row.addWidget(arrows)
        row.addWidget(self.num_arrows)
        row.addStretch(1)
        sf.addRow("Density", row)
        row = QtWidgets.QHBoxLayout()
        self.stream_width = WidthChooser(0.8)
        self.stream_style = style_combo("-")
        self.stream_color = ColorButton("#1f77b4")
        self.markers = QtWidgets.QCheckBox("markers")
        self.markers.setToolTip("Red circles at the seeds")
        row.addWidget(self.stream_width)
        row.addWidget(self.stream_style)
        row.addWidget(self.stream_color)
        sf.addRow("Line", row)
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
        row.addWidget(self.markers)
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
        row.addWidget(self.seed_button)
        row.addWidget(self.clear_seeds)
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


class MaskBox(_Box):
    """Integer argument and colour of a mask quantity (a label with an
    integer argument, as ixeq, or of cells set to 1, as bdcl): its cells
    not zero in the colour, the others not drawn, no colour bar."""

    argument_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Mask", parent)
        form = QtWidgets.QFormLayout(self)
        self.argument = QtWidgets.QSpinBox()
        self.argument.setRange(-99999, 99999)
        self.argument.setValue(1)
        self.argument.setKeyboardTracking(False)
        self.argument.setToolTip("Integer argument of the quantity (b2plot "
                                 "pushes it before the label: 1 ixeq)")
        self.argument.valueChanged.connect(self.argument_changed)
        self.colour = ColorButton("#d62728")
        self.colour.setToolTip("Colour of the cells where the quantity is "
                               "not zero")
        self.argument_label = QtWidgets.QLabel("Argument")
        form.addRow(self.argument_label, self.argument)
        form.addRow("Colour", self.colour)
        self._watch(colours=(self.colour,))

    def show_argument(self, on):
        """The argument row only for the labels that take one."""
        self.argument_label.setVisible(on)
        self.argument.setVisible(on)

    def set_argument(self, value):
        self.argument.blockSignals(True)
        self.argument.setValue(value)
        self.argument.blockSignals(False)

    def style_fields(self):
        return dict(mask=self.colour.color())
