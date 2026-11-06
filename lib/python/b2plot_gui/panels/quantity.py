"""Quantity panel of the 2D tab: what to plot and how."""

from ...b2plot import labels
from ..plot.styles import KINDS_SCALAR, KINDS_VECTOR, PlotStyle
from ...qt import QtWidgets, Qt, Signal
from .options import CellsBox, LabelsBox, LevelsBox, OverlayBox
from .plotopts import ArrowsBox, ColourBox, LinesBox, StreamBox
from .timebox import TimeBox

KIND_TEXT = {"patch": "Patch", "contourf": "Filled contour",
             "contour": "Contour lines", "quiver": "Quiver",
             "stream": "Streamlines", "quiverstream": "Quiver + streamlines"}
SUM = "Sum over species"


def real_token(x):
    """A b2plot real: short (b2plot reads tokens of limited length) and
    with a point or an exponent, so that it is not read as an integer."""
    t = "%.6g" % x
    return t if ("." in t or "e" in t or "n" in t) else t + ".0"


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
        self.time_box = TimeBox()
        lay.addWidget(self.time_box)

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

        self.colour = ColourBox()
        self.levels_box = LevelsBox()
        self.lines = LinesBox()
        self.arrows = ArrowsBox()
        self.streams = StreamBox()
        self.streams.seed_line.connect(self.seed_line)
        for box in (self.colour, self.levels_box, self.lines, self.arrows,
                    self.streams):
            box.changed.connect(self._changed)
            lay.addWidget(box)
        self.overlay_box = OverlayBox()
        self.overlay_box.changed.connect(self._changed)
        lay.addWidget(self.overlay_box)
        self.cells_box = CellsBox()
        self.cells_box.changed.connect(self._changed)
        lay.addWidget(self.cells_box)
        self.labels_box = LabelsBox()
        self.labels_box.changed.connect(self._changed)
        lay.addWidget(self.labels_box)
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
        self.colour.edges.setEnabled(not vector)
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
        return self.colour.factor_value()

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

    def value_ops(self, q, all_species=False):
        """b2plot operations for writing the values of q as plotted: sum
        or species shown (unless all_species), and the scale factor."""
        eirene = q.source in ("eirene", "evector")
        ops = []
        if self.summed():
            ops.append("0 -1 esumz" if eirene else "0 -1 sumz")
        elif not all_species and self.species.count() > 1:
            ops.append("%d %s" % (max(self.species.currentIndex(), 0),
                                  "ezsel" if eirene else "zsel"))
        f = self.factor_value()
        if f != 1.0:
            ops.append("%s %s" % (real_token(f), "rem*" if eirene else "rm*"))
        return tuple(ops)

    def kind(self):
        b = self.kind_buttons.checkedButton()
        return b.property("kind") if b else "patch"

    def _kind_changed(self, emit=True):
        kind = self.kind()
        source = self.current.source if self.current is not None else ""
        self.lines.setVisible(kind in ("contour", "contourf"))
        self.lines.fill_lines.setVisible(kind == "contourf")
        self.arrows.setVisible(kind in ("quiver", "quiverstream"))
        self.streams.setVisible(kind in ("stream", "quiverstream"))
        self.levels_box.setVisible(kind in ("contourf", "contour"))
        self.overlay_box.setVisible(kind in KINDS_SCALAR)
        self.cells_box.setVisible(source in ("matrix", "vector"))
        if emit:
            self._changed()

    def set_range(self, lo, hi):
        self.colour.set_range(lo, hi)

    def set_seeds(self, seeds):
        self.streams.set_seeds(seeds)

    def set_run_choices(self, vectors, scalars, geometry):
        """Overlay quantities and cell groups of a new run."""
        self.overlay_box.set_choices(vectors, scalars)
        self.cells_box.set_geometry(geometry)

    def style(self):
        fields = {}
        for box in (self.colour, self.levels_box, self.lines, self.arrows,
                    self.streams, self.cells_box):
            fields.update(box.style_fields())
        return PlotStyle(kind=self.kind(), column=0 if self.reduced()
                         else max(self.species.currentIndex(), 0), **fields)

    def _changed(self, *_):
        self.style_changed.emit()

