"""Overlays of the 2D quantity panel: two vector quantities (arrows or
streamlines) and the contour lines of a second quantity over the plot."""

from ..plot.styles import OverlayStyle, VectorStyle
from ...qt import QtWidgets, Qt, Signal
from .layers import ColorButton, spin, style_combo
from .options import _row

AS_PLOT = "as the plot"


class VectorRow:
    """Widgets of one vector overlay: quantity, species, arrows or
    streamlines, same length, length, width, colour."""

    def __init__(self, form, title, changed):
        self.check = QtWidgets.QCheckBox(title)
        self.vector = QtWidgets.QComboBox()
        self.vector.setToolTip("Vector quantity drawn over the plot")
        self.species = QtWidgets.QComboBox()
        self.species.addItem(AS_PLOT, -1)
        self.species.setToolTip("Species of the vector; as the plot: the "
                                "species shown, else the first ion (of the "
                                "element summed)")
        self.stream = QtWidgets.QComboBox()
        self.stream.addItems(["arrows", "streamlines"])
        self.same = QtWidgets.QCheckBox("same length")
        self.same.setToolTip("All arrows equally long: the direction only")
        self.length = spin(0.0, 10.0, 0.005, 0.0, 3,
                           "Arrow length in m (0: automatic)")
        self.width = spin(0.1, 10.0, 0.1, 1.0, tip="Relative width")
        self.color = ColorButton("#000000")
        form.addRow(self.check, self.vector)
        form.addRow("   species", _row(self.species, self.stream))
        form.addRow("   length, width", _row(self.same, self.length,
                                             self.width, self.color))
        for w in (self.check, self.same):
            w.toggled.connect(lambda *_: changed.emit())
        for w in (self.vector, self.species, self.stream):
            w.currentIndexChanged.connect(lambda *_: changed.emit())
        for w in (self.length, self.width):
            w.valueChanged.connect(lambda *_: changed.emit())
        self.color.changed.connect(lambda *_: changed.emit())

    def set_species(self, names):
        """Species columns of the vector (keeps the choice if it can)."""
        old = self.species.currentText()
        self.species.blockSignals(True)
        self.species.clear()
        self.species.addItem(AS_PLOT, -1)
        for i, n in enumerate(names):
            self.species.addItem(n, i)
        self.species.setCurrentIndex(max(self.species.findText(old), 0))
        self.species.blockSignals(False)

    def style(self):
        return VectorStyle(length=self.length.value(),
                           width=self.width.value(), color=self.color.color(),
                           column=self.species.currentData(),
                           same=self.same.isChecked(),
                           stream=self.stream.currentIndex() == 1)


class OverlayBox(QtWidgets.QGroupBox):
    """Two vector quantities (arrows or streamlines, b2plot arow) and the
    contour lines of a second quantity (b2plot same) over a scalar
    plot."""

    changed = Signal()
    ROLES = ("arrows", "arrows2")

    def __init__(self, parent=None):
        super().__init__("Overlay on the plot", parent)
        form = QtWidgets.QFormLayout(self)
        self.vectors = [VectorRow(form, "Vector", self.changed),
                        VectorRow(form, "2nd vector", self.changed)]
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
        for w in (self.lines, self.line_log, self.line_labels):
            w.toggled.connect(lambda *_: self.changed.emit())
        self.line_style.currentIndexChanged.connect(
            lambda *_: self.changed.emit())
        self.scalar.activated.connect(lambda *_: self.changed.emit())
        for w in (self.line_width, self.line_levels):
            w.valueChanged.connect(lambda *_: self.changed.emit())
        self.line_color.changed.connect(lambda *_: self.changed.emit())

    def set_choices(self, vectors, scalars, default_vector="up vv"):
        """Quantities offered (final state or movie), keeping the names
        chosen where they exist."""
        combos = [v.vector for v in self.vectors] + [self.scalar]
        old = [c.currentText() for c in combos]
        old[0] = old[0] or default_vector
        for combo, items in zip(combos, [vectors] * len(self.vectors)
                                + [scalars]):
            combo.blockSignals(True)
            combo.clear()
            for q in items:
                combo.addItem(q.label, q)
                combo.setItemData(combo.count() - 1, q.text, Qt.ToolTipRole)
            i = combo.findText(old[combos.index(combo)])
            if i >= 0:
                combo.setCurrentIndex(i)
            combo.blockSignals(False)
        first = self.vectors[0].vector
        if first.findText(old[0]) < 0 and first.findText(default_vector) >= 0:
            first.setCurrentIndex(first.findText(default_vector))
        completer = QtWidgets.QCompleter([q.label for q in scalars], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.scalar.setCompleter(completer)

    def wanted(self):
        """[(role, Quantity)] of the active overlays."""
        out = [(role, v.vector.currentData()) for role, v in
               zip(self.ROLES, self.vectors) if v.check.isChecked()
               and v.vector.currentData() is not None]
        if self.lines.isChecked():
            i = self.scalar.findText(self.scalar.currentText())
            if i >= 0:
                out.append(("lines", self.scalar.itemData(i)))
        return out

    def style(self, role="lines"):
        if role in self.ROLES:
            return self.vectors[self.ROLES.index(role)].style()
        return OverlayStyle(
            line_levels=self.line_levels.value(),
            line_log=self.line_log.isChecked(),
            line_color=self.line_color.color(),
            line_width=self.line_width.value(),
            line_style=self.line_style.currentData(),
            line_labels=self.line_labels.isChecked())
