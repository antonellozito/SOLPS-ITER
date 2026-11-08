"""Overlays of the 2D quantity panel: two vector quantities (arrows or
streamlines), the contour lines of a second quantity and a wall quantity
as a strip along the wall."""

from dataclasses import replace

from ..plot.styles import OverlayStyle, VectorStyle, WallStyle
from ...qt import QtWidgets, Qt, Signal
from .layers import ColorButton, spin, style_combo
from .options import _row
from .plotopts import CMAPS

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
        self._wall_rows(form)

    def _wall_rows(self, form):
        """Wall strip: a wall quantity, or a plasma quantity at the wall
        (b2plot stow), per ne or per area (pwne, pswa)."""
        self.wall = QtWidgets.QCheckBox("Wall strip")
        self.wall_from = QtWidgets.QComboBox()
        self.wall_from.addItems(["wall quantity", "plasma at the wall"])
        self.wall_from.setToolTip("Plasma at the wall: the values of the "
                                  "boundary cells next to each wall element "
                                  "(b2plot stow)")
        self.wall_q = QtWidgets.QComboBox()
        self.wall_species = QtWidgets.QComboBox()
        self.wall_per = QtWidgets.QComboBox()
        for text, op in (("", ""), ("per ne", "pwne"),
                         ("per area", "pswa")):
            self.wall_per.addItem(text, op)
        self.wall_cmap = QtWidgets.QComboBox()
        self.wall_cmap.addItems([c for c in CMAPS if c != "pwn"])
        self.wall_cmap.setCurrentText("viridis")
        self.wall_log = QtWidgets.QCheckBox("log")
        self.wall_width = spin(1.0, 30.0, 1.0, 6.0, 1, "Strip width (pt)")
        self.wall_bar = QtWidgets.QCheckBox("colour bar")
        self.wall_bar.setChecked(True)
        form.addRow(self.wall, self.wall_from)
        form.addRow("   quantity", self.wall_q)
        form.addRow("   species", _row(self.wall_species, self.wall_per))
        form.addRow("   colours", _row(self.wall_cmap, self.wall_log,
                                       self.wall_width, self.wall_bar))
        self.walls, self.plasma = [], []
        self.wall_from.currentIndexChanged.connect(
            lambda *_: self._fill_wall())
        for w in (self.wall, self.wall_log, self.wall_bar):
            w.toggled.connect(lambda *_: self.changed.emit())
        for w in (self.wall_q, self.wall_species, self.wall_per,
                  self.wall_cmap):
            w.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.wall_width.valueChanged.connect(lambda *_: self.changed.emit())

    def _fill_wall(self):
        old = self.wall_q.currentText()
        self.wall_q.blockSignals(True)
        self.wall_q.clear()
        for q in self.walls if self.wall_from.currentIndex() == 0 else \
                self.plasma:
            self.wall_q.addItem(q.label, q)
            self.wall_q.setItemData(self.wall_q.count() - 1, q.text,
                                    Qt.ToolTipRole)
        self.wall_q.setCurrentIndex(max(self.wall_q.findText(old), 0))
        self.wall_q.blockSignals(False)
        self.changed.emit()

    def set_wall_species(self, names):
        old = self.wall_species.currentText()
        self.wall_species.blockSignals(True)
        self.wall_species.clear()
        for i, n in enumerate(names):
            self.wall_species.addItem(n, i)
        self.wall_species.setCurrentIndex(
            max(self.wall_species.findText(old), 0))
        self.wall_species.blockSignals(False)

    def wall_quantity(self):
        """The wall strip as a quantity of the wall stack: the label or the
        plasma quantity with stow, then pwne or pswa."""
        q = self.wall_q.currentData()
        if q is None:
            return None
        ops = (["stow"] if self.wall_from.currentIndex() else []) + [
            op for op in [self.wall_per.currentData()] if op]
        return replace(q, name=" ".join([q.name] + ops), source="wall",
                       movie=0)

    def set_choices(self, vectors, scalars, default_vector="up vv",
                    walls=()):
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
        self.walls = list(walls)
        self.plasma = [q for q in scalars if q.source == "matrix"]
        self._fill_wall()

    def wanted(self):
        """[(role, Quantity)] of the active overlays."""
        out = [(role, v.vector.currentData()) for role, v in
               zip(self.ROLES, self.vectors) if v.check.isChecked()
               and v.vector.currentData() is not None]
        if self.lines.isChecked():
            i = self.scalar.findText(self.scalar.currentText())
            if i >= 0:
                out.append(("lines", self.scalar.itemData(i)))
        wall = self.wall_quantity() if self.wall.isChecked() else None
        if wall is not None:
            out.append(("wall", wall))
        return out

    def style(self, role="lines"):
        if role in self.ROLES:
            return self.vectors[self.ROLES.index(role)].style()
        if role == "wall":
            return WallStyle(column=max(self.wall_species.currentIndex(), 0),
                             cmap=self.wall_cmap.currentText(),
                             log=self.wall_log.isChecked(),
                             width=self.wall_width.value(),
                             colorbar=self.wall_bar.isChecked())
        return OverlayStyle(
            line_levels=self.line_levels.value(),
            line_log=self.line_log.isChecked(),
            line_color=self.line_color.color(),
            line_width=self.line_width.value(),
            line_style=self.line_style.currentData(),
            line_labels=self.line_labels.isChecked())
