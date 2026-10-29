"""Option groups of the 2D quantity panel: contour levels, overlays on the
plot, the cells shown and the labels."""

import numpy as np

from ..plot2d import LabelStyle, OverlayStyle
from ..qt import QtGui, QtWidgets, Qt, Signal
from .layers import ColorButton, spin, style_combo

LEVEL_MODES = [("Number of levels", "number"), ("Step", "step"),
               ("List of values", "list"),
               ("Proportion (b2plot clvp)", "proportion")]
STANDARD_LABEL = "${HOST} ${RUN} `date` T=${TIME}"     # b2plot stdl


def _row(*widgets, stretch=True):
    box = QtWidgets.QHBoxLayout()
    for w in widgets:
        box.addWidget(w)
    if stretch:
        box.addStretch(1)
    return box


class LevelsBox(QtWidgets.QGroupBox):
    """How the contour levels are chosen."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Contour levels", parent)
        self.form = QtWidgets.QFormLayout(self)
        self.mode = QtWidgets.QComboBox()
        for text, key in LEVEL_MODES:
            self.mode.addItem(text, key)
        self.mode.setToolTip("Proportion: b2plot clvp, equal integral of "
                             "the absolute value between neighbouring "
                             "levels")
        self.number = QtWidgets.QSpinBox()
        self.number.setRange(2, 200)
        self.number.setValue(20)
        self.number.setKeyboardTracking(False)
        self.step = QtWidgets.QLineEdit()
        self.step.setValidator(QtGui.QDoubleValidator())
        self.step.setPlaceholderText("step from the minimum")
        self.values = QtWidgets.QLineEdit()
        self.values.setPlaceholderText("values separated by blanks")
        self.positive = QtWidgets.QSpinBox()
        self.positive.setRange(1, 200)
        self.positive.setValue(10)
        self.positive.setToolTip("Intervals of the positive values (all "
                                 "values if the negative count is -1)")
        self.negative = QtWidgets.QSpinBox()
        self.negative.setRange(-1, 200)
        self.negative.setValue(-1)
        self.negative.setToolTip("Intervals of the negative values; -1 "
                                 "treats all values together")
        self.form.addRow("Levels", self.mode)
        self.form.addRow("Number", self.number)
        self.form.addRow("Step", self.step)
        self.form.addRow("Values", self.values)
        self.form.addRow("Intervals", _row(self.positive, self.negative))
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.number.valueChanged.connect(lambda *_: self.changed.emit())
        self.positive.valueChanged.connect(lambda *_: self.changed.emit())
        self.negative.valueChanged.connect(lambda *_: self.changed.emit())
        self.step.editingFinished.connect(lambda: self.changed.emit())
        self.values.editingFinished.connect(lambda: self.changed.emit())
        self._mode_changed(emit=False)

    def key(self):
        return self.mode.currentData()

    def _mode_changed(self, *_, emit=True):
        key = self.key()
        for row, on in ((1, key == "number"), (2, key == "step"),
                        (3, key == "list"), (4, key == "proportion")):
            self.form.setRowVisible(row, on)
        if emit:
            self.changed.emit()

    def proportion(self):
        """(positive, negative) intervals of clvp, or None."""
        if self.key() != "proportion":
            return None
        return self.positive.value(), self.negative.value()

    def style_fields(self):
        try:
            step = float(self.step.text())
        except ValueError:
            step = 0.0
        return dict(level_mode=self.key(), levels=self.number.value(),
                    level_step=step, level_list=self.values.text())


class OverlayBox(QtWidgets.QGroupBox):
    """Arrows of a vector quantity and contour lines of a second quantity
    over a scalar plot (b2plot arow and same)."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Overlay on the plot", parent)
        form = QtWidgets.QFormLayout(self)
        self.arrows = QtWidgets.QCheckBox("Arrows of")
        self.vector = QtWidgets.QComboBox()
        self.vector.setToolTip("Vector quantity drawn as arrows, for the "
                               "species of the plot where it exists")
        self.arrow_length = spin(0.0, 10.0, 0.005, 0.0, 3,
                                 "Arrow length in m (0: automatic)")
        self.arrow_width = spin(0.1, 10.0, 0.1, 1.0, tip="Relative width")
        self.arrow_color = ColorButton("#000000")
        form.addRow(self.arrows, self.vector)
        form.addRow("   length, width",
                    _row(self.arrow_length, self.arrow_width,
                         self.arrow_color))
        self.lines = QtWidgets.QCheckBox("Contours of")
        self.scalar = QtWidgets.QComboBox()
        self.scalar.setEditable(True)
        self.scalar.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.scalar.setToolTip("Second quantity drawn as contour lines")
        self.line_levels = QtWidgets.QSpinBox()
        self.line_levels.setRange(2, 100)
        self.line_levels.setValue(10)
        self.line_log = QtWidgets.QCheckBox("log")
        self.line_color = ColorButton("#ffffff")
        self.line_width = spin(0.1, 10.0, 0.1, 0.6, tip="Line width")
        self.line_style = style_combo("-")
        self.line_labels = QtWidgets.QCheckBox("labels")
        form.addRow(self.lines, self.scalar)
        form.addRow("   levels", _row(self.line_levels, self.line_log,
                                      self.line_labels))
        form.addRow("   line", _row(self.line_width, self.line_style,
                                    self.line_color))
        for w in (self.arrows, self.lines, self.line_log, self.line_labels):
            w.toggled.connect(lambda *_: self.changed.emit())
        for w in (self.vector, self.line_style):
            w.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.scalar.activated.connect(lambda *_: self.changed.emit())
        for w in (self.arrow_length, self.arrow_width, self.line_width,
                  self.line_levels):
            w.valueChanged.connect(lambda *_: self.changed.emit())
        for w in (self.arrow_color, self.line_color):
            w.changed.connect(lambda *_: self.changed.emit())

    def set_choices(self, vectors, scalars, default_vector="up vv"):
        """Quantities offered (final state or movie), keeping the names
        chosen where they exist."""
        old = (self.vector.currentText() or default_vector,
               self.scalar.currentText())
        for combo, items in ((self.vector, vectors), (self.scalar, scalars)):
            combo.blockSignals(True)
            combo.clear()
            for q in items:
                combo.addItem(q.name, q)
                combo.setItemData(combo.count() - 1, q.text, Qt.ToolTipRole)
            combo.blockSignals(False)
        for combo, name in zip((self.vector, self.scalar), old):
            i = combo.findText(name)
            if i >= 0:
                combo.blockSignals(True)
                combo.setCurrentIndex(i)
                combo.blockSignals(False)
        if self.vector.findText(old[0]) < 0:
            i = self.vector.findText(default_vector)
            if i >= 0:
                self.vector.setCurrentIndex(i)
        completer = QtWidgets.QCompleter([q.name for q in scalars], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.scalar.setCompleter(completer)

    def wanted(self):
        """[(role, Quantity)] of the active overlays."""
        out = []
        if self.arrows.isChecked() and self.vector.currentData() is not None:
            out.append(("arrows", self.vector.currentData()))
        if self.lines.isChecked():
            i = self.scalar.findText(self.scalar.currentText())
            if i >= 0:
                out.append(("lines", self.scalar.itemData(i)))
        return out

    def style(self):
        return OverlayStyle(
            arrow_length=self.arrow_length.value(),
            arrow_width=self.arrow_width.value(),
            arrow_color=self.arrow_color.color(),
            line_levels=self.line_levels.value(),
            line_log=self.line_log.isChecked(),
            line_color=self.line_color.color(),
            line_width=self.line_width.value(),
            line_style=self.line_style.currentData(),
            line_labels=self.line_labels.isChecked())


class CellsBox(QtWidgets.QGroupBox):
    """B2.5 cells shown: index intervals on classical grids and regions."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Cells shown", parent)
        self.form = QtWidgets.QFormLayout(self)
        self.spins = []
        for _ in range(4):
            s = QtWidgets.QSpinBox()
            s.setKeyboardTracking(False)
            s.valueChanged.connect(lambda *_: self.changed.emit())
            self.spins.append(s)
        self.form.addRow("ix from, to", _row(*self.spins[:2]))
        self.form.addRow("iy from, to", _row(*self.spins[2:]))
        self.regions = QtWidgets.QWidget()
        self.region_layout = QtWidgets.QHBoxLayout(self.regions)
        self.region_layout.setContentsMargins(0, 0, 0, 0)
        self.form.addRow("Regions", self.regions)
        self.checks = []
        self.full = None

    def set_geometry(self, g):
        """Index ranges and regions of the run, all shown."""
        for c in self.checks:
            c.deleteLater()
        self.checks = []
        for reg, n in zip(*np.unique(g.region[g.visible],
                                     return_counts=True)):
            c = QtWidgets.QCheckBox(str(int(reg)))
            c.setToolTip("Region %d: %d cells" % (reg, n))
            c.setChecked(True)
            c.toggled.connect(lambda *_: self.changed.emit())
            self.region_layout.addWidget(c)
            self.checks.append(c)
        self.region_layout.addStretch(1)
        classical = bool(g.classical and (g.ix >= 0).any())
        self.form.setRowVisible(0, classical)
        self.form.setRowVisible(1, classical)
        self.full = None
        if classical:
            ix, iy = g.ix[g.visible], g.iy[g.visible]
            self.full = (int(ix.min()), int(ix.max()), int(iy.min()),
                         int(iy.max()))
            for s, (lo, hi), v in zip(self.spins,
                                      [self.full[:2]] * 2 + [self.full[2:]]
                                      * 2, self.full):
                s.blockSignals(True)
                s.setRange(lo, hi)
                s.setValue(v)
                s.blockSignals(False)

    def style_fields(self):
        """ix_range, iy_range and regions, None where nothing is hidden."""
        out = dict(ix_range=None, iy_range=None, regions=None)
        if self.full is not None:
            v = tuple(s.value() for s in self.spins)
            if v[:2] != self.full[:2]:
                out["ix_range"] = (min(v[:2]), max(v[:2]))
            if v[2:] != self.full[2:]:
                out["iy_range"] = (min(v[2:]), max(v[2:]))
        if self.checks and not all(c.isChecked() for c in self.checks):
            out["regions"] = tuple(int(c.text()) for c in self.checks
                                   if c.isChecked())
        return out


class LabelsBox(QtWidgets.QGroupBox):
    """Texts of the plot (b2plot extl, xlab, ylab, glob, lbsz, bold, noax
    and xcol); ${NAME} and `date` are expanded as in b2plot."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Labels", parent)
        form = QtWidgets.QFormLayout(self)
        self.title = QtWidgets.QLineEdit()
        self.extra = QtWidgets.QLineEdit()
        self.extra.setPlaceholderText("extra label over the plot")
        self.standard = QtWidgets.QToolButton()
        self.standard.setText("Standard")
        self.standard.setToolTip("Host, run directory, date and time of the "
                                 "run (b2plot stdl)")
        self.standard.clicked.connect(lambda *_: self._standard())
        self.xlabel = QtWidgets.QLineEdit()
        self.xlabel.setPlaceholderText("R (m)")
        self.ylabel = QtWidgets.QLineEdit()
        self.ylabel.setPlaceholderText("Z (m)")
        self.header = QtWidgets.QLineEdit()
        self.header.setPlaceholderText("global header over the figure")
        for w in (self.title, self.extra, self.xlabel, self.ylabel,
                  self.header):
            w.setToolTip("${NAME}: environment, RUN, HOST or TIME; `date`; "
                         "^{...} and _{...} for super- and subscripts")
            w.setClearButtonEnabled(True)
            w.editingFinished.connect(lambda: self.changed.emit())
        self.size = spin(0.5, 3.0, 0.1, 1.0, 1, "Label size (b2plot lbsz)")
        self.bold = QtWidgets.QCheckBox("bold")
        self.axes = QtWidgets.QCheckBox("axes")
        self.axes.setChecked(True)
        self.axes.setToolTip("Axes, ticks and axis labels (b2plot noax)")
        self.color = ColorButton("#000000")
        form.addRow("Title", self.title)
        form.addRow("Extra", _row(self.extra, self.standard,
                                  stretch=False))
        form.addRow("x label", self.xlabel)
        form.addRow("y label", self.ylabel)
        form.addRow("Header", self.header)
        form.addRow("Size", _row(self.size, self.bold, self.axes,
                                 self.color))
        self.size.valueChanged.connect(lambda *_: self.changed.emit())
        for w in (self.bold, self.axes):
            w.toggled.connect(lambda *_: self.changed.emit())
        self.color.changed.connect(lambda *_: self.changed.emit())

    def _standard(self):
        self.extra.setText(STANDARD_LABEL)
        self.changed.emit()

    def set_title_hint(self, text):
        self.title.setPlaceholderText(text)

    def style(self):
        return LabelStyle(
            title=self.title.text(), extra=self.extra.text(),
            xlabel=self.xlabel.text(), ylabel=self.ylabel.text(),
            header=self.header.text(), size=self.size.value(),
            bold=self.bold.isChecked(), axes=self.axes.isChecked(),
            color=self.color.color())
