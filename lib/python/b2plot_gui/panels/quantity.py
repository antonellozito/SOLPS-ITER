"""Quantity panel of the 2D tab: what to plot and how."""

import re
import time

from ...b2plot import labels
from ..catalog import INTEGER
from ..expression import real_token
from ..plot.styles import (KINDS_FLAT, KINDS_SCALAR, KINDS_VECTOR,
                           PlotStyle)
from ...qt import QtWidgets, Qt, Signal
from .options import CellsBox, LabelsBox, LevelsBox
from .overlays import OverlayBox
from .trajectories import TrajBox
from .plotopts import ArrowsBox, ColourBox, LinesBox, StreamBox
from .timebox import TimeBox

KIND_TEXT = {"patch": "Patch", "contourf": "Filled contour",
             "contour": "Contour lines", "surface": "3D surface",
             "quiver": "Quiver",
             "stream": "Streamlines", "quiverstream": "Quiver + streamlines"}
SUM = "Sum over species"


def column_names(columns, species=None):
    """Species names of the field columns (the run species where b2plot
    sends no name)."""
    names = [labels.species_text(c) or (
        labels.species_text(species[i]) if species and i < len(species)
        else "") for i, c in enumerate(columns)]
    return [n or "column %d" % (i + 1) for i, n in enumerate(names)]


class QuantityPanel(QtWidgets.QWidget):
    """Quantity tree, species, plot type and the plot options."""

    quantity_chosen = Signal(object)
    style_changed = Signal()
    seed_line = Signal()
    calculator = Signal(str)        # open the calculator with this text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = None
        self.wanted_species = None      # species name to choose next
        self._last_click = (None, 0.0)  # item, time (double clicks)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.time_box = TimeBox()
        lay.addWidget(self.time_box)

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search quantities (te, flux, ...)")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        calc = QtWidgets.QToolButton()
        calc.setText("Calculator\u2026")
        calc.setToolTip("Derived quantities: expressions of b2plot "
                        "quantities, presets")
        calc.clicked.connect(lambda *_: self.calculator.emit(""))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.search, 1)
        row.addWidget(calc)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Quantity", "Name"])
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setMinimumHeight(220)
        head = self.tree.header()
        head.setStretchLastSection(False)
        head.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        head.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setToolTip("Click a quantity to plot it, click it again "
                             "to clear the plot")
        self.tree.itemActivated.connect(self._clicked)
        self.tree.itemClicked.connect(self._clicked)
        lay.addLayout(row)
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
            vector = kind in KINDS_VECTOR
            kgrid.addWidget(b, i - len(KINDS_SCALAR) * vector, int(vector))
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
        self.traj_box = TrajBox()
        lay.addWidget(self.traj_box)
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
            item = QtWidgets.QTreeWidgetItem([q.text, q.label])
            item.setToolTip(0, q.text)
            item.setToolTip(1, q.label)
            item.setData(0, Qt.UserRole, q)
            top.addChild(item)
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            shown = 0
            for j in range(top.childCount()):
                item = top.child(j)
                q = item.data(0, Qt.UserRole)
                hit = (not text or text in q.label.lower()
                       or text in q.text.lower())
                item.setHidden(not hit)
                shown += hit
            top.setHidden(shown == 0)
            top.setExpanded(bool(text) and shown > 0)

    def _clicked(self, item, *_):
        """A click (or Return) on a quantity: plot it, or clear the plot
        if it is the one plotted; the second click of a double click is
        no new click."""
        last, when = self._last_click
        now = time.monotonic()
        self._last_click = (item, now)
        if item is last and now - when < \
                QtWidgets.QApplication.doubleClickInterval() / 1000.0:
            return
        q = item.data(0, Qt.UserRole)
        if q is not None and q is self.current:
            self.unselect()
            self.quantity_chosen.emit(None)
            return
        self._activated(item)

    def unselect(self):
        """No quantity chosen (the state at the start)."""
        self.current = None
        self.tree.clearSelection()
        self.tree.setCurrentItem(None)

    def _activated(self, item, *_):
        q = item.data(0, Qt.UserRole)
        if q is None or q is self.current:
            return
        if INTEGER.fullmatch(q.name):           # needs an integer argument
            self.calculator.emit("%s(1)" % q.name)
            return
        self.current = q
        vector = q.source in ("vector", "evector")
        for b in self.kind_buttons.buttons():
            b.setEnabled((b.property("kind") in KINDS_VECTOR) == vector)
        kind = self.kind()
        if (kind in KINDS_VECTOR) != vector:
            self.kind_buttons.button(len(KINDS_SCALAR) if vector else 0
                                     ).setChecked(True)
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
        names = column_names(columns, species)
        if len(columns) == 1 and not columns[0].strip():
            names = ["\u2014"]
        self.partial = {}
        if len(names) > 1:
            names.append(SUM)
            elements = [re.match(r"[A-Za-z]*", n).group(0) for n in names]
            for e in dict.fromkeys(elements[:-1]):
                cols = [i for i, x in enumerate(elements[:-1]) if x == e]
                if e and 1 < len(cols) < len(names) - 1:
                    names.append("Sum %s" % e)
                    self.partial[names[-1]] = (cols[0], cols[-1])
        old = self.wanted_species or self.species.currentText()
        self.wanted_species = None
        self.species.blockSignals(True)
        self.species.clear()
        self.species.addItems(names)
        if old in names:
            self.species.setCurrentIndex(names.index(old))
        self.species.setEnabled(len(names) > 1)
        self.species.blockSignals(False)

    # -------------------------------------------------------------- style
    def summed(self):
        """True for the sum over all species or over one element."""
        return self.species.currentText() == SUM or self._partial()

    def _partial(self):
        return getattr(self, "partial", {}).get(self.species.currentText())

    def _sum_op(self, eirene):
        lo, hi = self._partial() or (0, -1)
        return "%d %d %s" % (lo, hi, "esumz" if eirene else "sumz")

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
            ops.append(self._sum_op(eirene))
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
            ops.append(self._sum_op(eirene))
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
        self.overlay_box.setVisible(kind in KINDS_FLAT)
        self.cells_box.setVisible(source in ("matrix", "vector"))
        if emit:
            self._changed()

    def set_range(self, lo, hi):
        self.colour.set_range(lo, hi)

    def set_seeds(self, seeds):
        self.streams.set_seeds(seeds)

    def style(self):
        fields = {}
        for box in (self.colour, self.levels_box, self.lines, self.arrows,
                    self.streams, self.cells_box):
            fields.update(box.style_fields())
        return PlotStyle(kind=self.kind(), column=0 if self.reduced()
                         else max(self.species.currentIndex(), 0), **fields)

    def _changed(self, *_):
        self.style_changed.emit()

