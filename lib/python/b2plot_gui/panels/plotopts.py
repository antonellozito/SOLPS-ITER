"""Option groups of the plot: colour scales (of the plasma and of the
vector plot, with their plot types), contour lines, arrows and
streamlines, each giving its part of the PlotStyle (style_fields); the
options of the wall plot (WallStyle)."""

from ..plot.styles import WallStyle
from ..plot.vector import NUM_ARROWS
from ..scaling import Number
from ..tools import births
from ...qt import QtCore, QtGui, QtWidgets, Signal
from .glyphs import CmapChooser, LineStyleChooser, WidthChooser
from .layers import ColorButton, left_form, spin, style_combo


def _number(text, default):
    try:
        return float(text)
    except ValueError:
        return default


class _Watched:
    """_watch: the widgets given emit changed."""

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


class _Box(_Watched, QtWidgets.QGroupBox):
    """A group whose widgets all emit changed."""

    changed = Signal()


class _Part(_Watched, QtWidgets.QWidget):
    """A part of a group (no frame) whose widgets all emit changed."""

    changed = Signal()


class ColourBox(_Box):
    """Colormap (reversed or not), scale and range."""

    def __init__(self, title="Colour scale", cmap="turbo",
                 scales=("linear", "log", "symlog"), parent=None):
        super().__init__(title, parent)
        lay = QtWidgets.QVBoxLayout(self)
        row = QtWidgets.QHBoxLayout()   # colormap, reversed, scale
        self.cmap = CmapChooser(cmap)  # its name in its tooltip
        self.reverse = QtWidgets.QCheckBox("reversed")
        self.scale = QtWidgets.QComboBox()
        self.scale.addItems(list(scales))
        self.scale.setToolTip("Scale: " + ", ".join(
            {"linear": "linear", "log": "logarithmic",
             "symlog": "symmetric logarithmic"}[s] for s in scales))
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


STRIP_WIDTHS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30)     # points


class WallBox(ColourBox):
    """Options of the wall plot: the width and style of its strip, its
    colour map (reversed or not), linear or logarithmic, its range."""

    def __init__(self, parent=None):
        super().__init__("Wall plot options", "viridis", ("linear", "log"),
                         parent)
        self.strip_width = WidthChooser(6.0, STRIP_WIDTHS, "Width of the "
                                        "strip along the wall (pt)")
        self.strip_style = LineStyleChooser("-")
        self.strip_style.setToolTip("Line style of the strip")
        row = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Line")
        row.addWidget(label)
        row.addWidget(self.strip_width, 1)
        row.addWidget(self.strip_style, 1)
        self.layout().insertLayout(0, row)
        self.line_row = [label, self.strip_width, self.strip_style]
        self._watch((self.strip_width, self.strip_style))

    def wall_style(self, columns):
        """The WallStyle of the options, summing the columns given."""
        f = self.style_fields()
        return WallStyle(columns=tuple(columns),
                         width=self.strip_width.value(),
                         style=self.strip_style.currentData(),
                         cmap=f["cmap"], reverse=f["reverse"],
                         scale=f["scale"],
                         auto=f["auto"], vmin=f["vmin"], vmax=f["vmax"])


class LinesBox(_Part):
    """Contour lines (under the levels in the Contours section): over the
    fill (filled contours), one colour (contour lines), colour, width,
    style, labels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lf = left_form(self)
        lf.setContentsMargins(0, 0, 0, 0)
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
    """Streamline density, line, arrows and where they start (tools.births:
    in proportion to the magnitude, at random, at random along a line of
    the run or the line drawn on the plot), how many."""

    seed_line = Signal(bool)        # wait for the clicks of the line, or not

    def __init__(self, parent=None):
        super().__init__("Streamlines", parent)
        sf = left_form(self)
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
        for text, key in births.KINDS:
            self.seed_kind.addItem(text, key)
        self.seed_kind.setToolTip("Where the streamlines start")
        self.seed_kind.activated.connect(lambda *_: self._seed_kind())
        self.nseeds = QtWidgets.QSpinBox()
        self.nseeds.setRange(2, 500)
        self.nseeds.setValue(40)
        self.nseeds.setKeyboardTracking(False)
        self.nseeds.setToolTip("Streamlines started along the line (over "
                               "the view the density sets them)")
        self.nseeds.setEnabled(False)
        row.addWidget(self.seed_kind, 1)
        row.addWidget(self.nseeds)
        row.addWidget(self.markers)
        sf.addRow("Seeds", row)
        row = QtWidgets.QHBoxLayout()
        self.seed_button = QtWidgets.QPushButton("Draw seed line")
        self.seed_button.setToolTip("Then click the two ends of the line on "
                                    "the plot (click again to cancel); "
                                    "also where the tracers of the 3D view "
                                    "can be born")
        self.seed_button.setEnabled(False)
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
                    (self.density, self.stream_width, self.num_arrows,
                     self.nseeds), (self.stream_color,))

    def _seed_kind(self):
        """Streamlines from the new places; the drawn line, if none is
        drawn yet, waits for the clicks of Draw seed line."""
        key = self.seed_kind.currentData()
        self.seed_button.setEnabled(key == "line")
        self.nseeds.setEnabled(key in births.LINES)
        if key == "line" and len(self.seeds) < 2:
            self.seed_line.emit(True)
        self._emit()

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
                    seed_markers=self.markers.isChecked(),
                    seed_kind=self.seed_kind.currentData(),
                    seed_count=self.nseeds.value())


class TextureBox(_Box):
    """Flow texture: the noise smeared along the flow lines (line
    integral convolution), its detail, streaks, contrast, opacity and
    colours."""

    def __init__(self, parent=None):
        super().__init__("Texture", parent)
        sf = left_form(self)

        def ispin(lo, hi, step, value, tip):
            w = QtWidgets.QSpinBox()
            w.setRange(lo, hi)
            w.setSingleStep(step)
            w.setValue(value)
            w.setKeyboardTracking(False)
            w.setToolTip(tip)
            return w
        self.detail = ispin(100, 2000, 50, 500, "Pixels of the texture "
                            "along the longer side of the view")
        self.length = ispin(2, 200, 2, 20, "Length of the streaks, in "
                            "pixels each way along the flow")
        self.grain = ispin(1, 8, 1, 1, "Size of the grains of the noise, "
                           "in pixels (coarser streaks)")
        self.contrast = spin(0.2, 5.0, 0.1, 1.0, tip="Contrast of the "
                             "streaks")
        self.alpha = spin(0.05, 1.0, 0.05, 1.0, tip="Opacity over the "
                          "plasma plot")
        self.magnitude = QtWidgets.QCheckBox("colour by magnitude")
        self.magnitude.setChecked(True)
        self.magnitude.setToolTip("Coloured by the magnitude of the vector "
                                  "(its colour scale), else grey")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.detail)
        row.addWidget(QtWidgets.QLabel("Grain"))
        row.addWidget(self.grain)
        row.addStretch(1)
        sf.addRow("Detail", row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.length)
        row.addWidget(QtWidgets.QLabel("Contrast"))
        row.addWidget(self.contrast)
        row.addStretch(1)
        sf.addRow("Streaks", row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.alpha)
        row.addWidget(self.magnitude)
        row.addStretch(1)
        sf.addRow("Opacity", row)
        self._watch((), (self.magnitude,),
                    (self.detail, self.length, self.grain, self.contrast,
                     self.alpha), ())

    def style_fields(self):
        return dict(tex_detail=self.detail.value(),
                    tex_length=self.length.value(),
                    tex_grain=self.grain.value(),
                    tex_contrast=self.contrast.value(),
                    tex_alpha=self.alpha.value(),
                    tex_magnitude=self.magnitude.isChecked())


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


def _narrow_text(w):
    """A check box that never widens its column (its text cut where the
    column is narrow, whole in its tooltip)."""
    w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                    QtWidgets.QSizePolicy.Fixed)
    w.setMinimumWidth(40)
    if not w.toolTip():
        w.setToolTip(w.text())


class SplitBox(_Part):
    """A vector drawn as its components, one split at a time (arrows
    only): its physical components (the parts b2plot gives, for the total
    fluxes; each shown or not, a check box in the colour of its arrows)
    or its poloidal and radial components (horizontal and vertical for
    the EIRENE vectors)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 2)
        lay.setSpacing(8)               # the two splits well apart
        self.on = QtWidgets.QCheckBox("Split into physical components")
        self.on.setToolTip("Arrows of each physical component of the total "
                           "flux (the parts b2plot gives), in colours of "
                           "their own, on the length scale of the total; "
                           "the rest (total minus the components) too when "
                           "they do not add up to it")
        self.geo = QtWidgets.QCheckBox("Split into poloidal/radial "
                                       "components")
        self.geo.setToolTip("Arrows of the poloidal and the radial "
                            "component, on the length scale of the vector")
        for w in (self.on, self.geo):    # a row each
            w.setMinimumHeight(w.sizeHint().height())
            _narrow_text(w)
            lay.addWidget(w)
        self.list = QtWidgets.QWidget()     # a check box per component
        self.rows = QtWidgets.QVBoxLayout(self.list)
        self.rows.setContentsMargins(18, 0, 0, 0)
        self.rows.setSpacing(5)
        lay.addWidget(self.list)
        self.list.hide()
        self.on.toggled.connect(lambda on: self._exclusive(self.geo, on))
        self.geo.toggled.connect(lambda on: self._exclusive(self.on, on))
        self.names, self.boxes = [], []

    def _exclusive(self, other, on):
        if on and other.isChecked():
            other.blockSignals(True)
            other.setChecked(False)
            other.blockSignals(False)
        self._shown()
        self._emit()

    def _shown(self, *_):
        self.list.setVisible(self.on.isChecked() and bool(self.names))

    def set_cartesian(self, on):
        """Horizontal and vertical components (EIRENE vectors) instead of
        poloidal and radial ones."""
        self.geo.setText("Split into horizontal/vertical components" if on
                         else "Split into poloidal/radial components")
        self.geo.setToolTip(self.geo.text())

    def set_parts(self, parts):
        """[(name, text, colour, zero)] of the physical components (the
        ticks of those listed before kept); [] or None: none offered."""
        off = set(self.split_off())
        names = [n for n, _, _, _ in parts or ()]
        if parts and names == self.names:
            for b, (_, text, _, zero) in zip(self.boxes, parts):
                b.setText(text + (" (zero)" if zero else ""))
                if zero:
                    b.blockSignals(True)
                    b.setChecked(False)
                    b.blockSignals(False)
                b.setEnabled(not zero)
            return
        for b in self.boxes:
            b.deleteLater()
        self.boxes, self.names = [], names
        for name, text, colour, zero in parts or ():
            b = QtWidgets.QCheckBox(text + (" (zero)" if zero else ""))
            _narrow_text(b)
            pix = QtGui.QPixmap(12, 12)
            pix.fill(QtGui.QColor(colour))
            b.setIcon(QtGui.QIcon(pix))
            b.setChecked(name not in off and not zero)
            b.setEnabled(not zero)
            b.name = name
            b.toggled.connect(self._emit)
            self.rows.addWidget(b)
            self.boxes.append(b)
        self.on.setVisible(bool(self.names))
        if not self.names and self.on.isChecked():
            self.on.setChecked(False)
        self._shown()

    def split_off(self):
        return [b.name for b in self.boxes if not b.isChecked()]

    def mode(self):
        """"physical", "geometric" or "" (no split)."""
        return "physical" if self.on.isChecked() and self.names else \
            "geometric" if self.geo.isChecked() else ""

    def allow(self, on):
        """The splits offered (quiver) or not (unticked, greyed out)."""
        for w in (self.on, self.geo):
            if not on and w.isChecked():
                w.blockSignals(True)
                w.setChecked(False)
                w.blockSignals(False)
            w.setEnabled(on)
        self._shown()

    def style_fields(self):
        return dict(split=self.mode(), split_off=tuple(self.split_off()))
