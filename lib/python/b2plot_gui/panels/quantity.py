"""Quantity panel of the 2D tab: what to plot and how."""

import re
import time
from dataclasses import replace

from ...b2plot import labels
from .. import theme
from ..catalog import FLAGS, GUARD, INTEGER
from ..plot.styles import KINDS_FLAT, KINDS_VECTOR, PlotStyle
from ...qt import QtCore, QtGui, QtWidgets, Qt, Signal
from .options import CellsBox, LabelsBox, LevelsBox
from .overlays import OverlayBox
from .trajectories import TrajBox
from .plotopts import ArrowsBox, ColourBox, LinesBox, MaskBox, StreamBox
from .timebox import TimeBox

KIND_TEXT = {"patch": "Patch", "contourf": "Filled contour",
             "contour": "Contour lines", "quiver": "Quiver",
             "stream": "Streamlines", "quiverstream": "Quiver + streamlines"}
SUM = "Sum over species"
TREE_ROWS = 14                      # rows of the quantity tree
ARGUMENT = re.compile(r"(-?\d+) (\S+)")     # "1 ixeq": a mask and its argument
CHARGE = re.compile(r"([A-Za-z]*)\s*\+?(\d*)")     # D0, D+, N+7, N7+


def default_species(names):
    """Index of the highest charge state of the first species in names
    (D+ of D0, D+, N0, ...)."""
    def parse(n):
        m = CHARGE.match(n)
        charge = int(m.group(2)) if m.group(2) else 1 if "+" in n else 0
        return m.group(1), charge
    first = parse(names[0])[0] if names else ""
    same = [(parse(n)[1], -i) for i, n in enumerate(names)
            if parse(n)[0] == first]
    return -max(same)[1] if same else 0


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
    seed_line = Signal(bool)
    calculator = Signal(str)        # open the calculator with this text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = None
        self.wanted_species = None      # species name to choose next
        self.chosen_species = None      # the species last chosen by hand
        self._last_click = (None, 0.0)  # item, time (double clicks)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 6)   # the tabs: 6 px over it
        self.time_box = TimeBox()
        lay.addWidget(self.time_box)
        self.page_slot = QtWidgets.QVBoxLayout()    # the Balances tab
        self.page_slot.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self.page_slot)
        self.main_part = QtWidgets.QWidget()        # the other tabs
        column, lay = lay, QtWidgets.QVBoxLayout(self.main_part)
        lay.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.main_part)

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search quantities (te, flux, ...)")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        calc = QtWidgets.QToolButton()
        calc.setText("Calculator\u2026")
        calc.setProperty("bold", True)
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
        head = self.tree.header()
        head.setStretchLastSection(False)
        head.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        head.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setToolTip("Click a group to open or close it, a quantity "
                             "to plot it, click it again to clear the plot")
        self.tree.itemActivated.connect(self._clicked)
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemExpanded.connect(self._group_marked)
        self.tree.itemCollapsed.connect(self._group_marked)
        lay.addLayout(row)
        lay.addWidget(self.tree)        # fixed height (_tree_height)

        row = QtWidgets.QHBoxLayout()   # species, then the two sections
        self.species = QtWidgets.QComboBox()
        self.species.currentIndexChanged.connect(self._species_chosen)
        label = QtWidgets.QLabel("Species")
        label.setProperty("bold", True)
        row.addWidget(label)
        row.addWidget(self.species, 5)
        self.chords_button = QtWidgets.QPushButton("Chords")
        self.chords_button.setToolTip("Profiles of the quantity shown along "
                                      "chords drawn on the plot or typed, "
                                      "their integrals and averages")
        self.stats_button = QtWidgets.QPushButton("Statistics")
        self.stats_button.setToolTip("Volume integral, average, minimum, "
                                     "maximum and histogram of the quantity "
                                     "shown over the cells shown, a box or "
                                     "a polygon")
        for b in (self.chords_button, self.stats_button):
            b.setCheckable(True)
            b.setProperty("bold", True)
            row.addWidget(b, 2)
        lay.addLayout(row)
        self.sections = QtWidgets.QVBoxLayout()  # the open one (tab)
        self.sections.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self.sections)
        self.mask_box = MaskBox()
        self.mask_box.argument_changed.connect(self._argument)
        self.mask_box.changed.connect(self._changed)
        lay.addWidget(self.mask_box)

        kinds = QtWidgets.QGroupBox("Plot type")    # a menu of the kinds
        form = QtWidgets.QFormLayout(kinds)     # as the other groups
        self.kind_combo = QtWidgets.QComboBox()
        self.kind_combo.setToolTip("Cell data: patch, filled contour, "
                                   "contour lines; face data (vectors): "
                                   "quiver, streamlines or both")
        form.addRow(self.kind_combo)
        self._vector = None             # the kinds listed: of vectors?
        self._fill_kinds(False, False)
        self.kind_combo.currentIndexChanged.connect(self._kind_chosen)

        self.colour = ColourBox()
        self.levels_box = LevelsBox()
        self.lines = LinesBox()
        self.arrows = ArrowsBox()
        self.streams = StreamBox()
        self.streams.seed_line.connect(self.seed_line)
        for box in (self.colour, self.levels_box, self.lines, self.arrows,
                    self.streams):
            box.changed.connect(self._changed)
        self.overlay_box = OverlayBox()
        self.overlay_box.changed.connect(self._changed)
        lay.addWidget(self.overlay_box)
        self.cells_box = CellsBox()
        self.cells_box.changed.connect(self._changed)
        self.traj_box = TrajBox()
        lay.addWidget(self.traj_box)
        self.labels_box = LabelsBox()
        self.labels_box.changed.connect(self._changed)
        column.addStretch(1)            # the room left under the boxes
        # the graphic options, placed in the right column by the 2D tab
        self.style_boxes = (kinds, self.colour, self.levels_box, self.lines,
                            self.arrows, self.streams)
        self.lower_boxes = (self.cells_box, self.labels_box)
        self._kind_changed(emit=False)
        self._tree_height()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self._tree_height()

    def show_balances(self, on):
        """The page of the Balances tab, or what the other tabs show."""
        self.main_part.setVisible(not on)
        for i in range(self.page_slot.count()):
            w = self.page_slot.itemAt(i).widget()
            if w is not None:
                w.setVisible(on)

    def _tree_height(self):
        """The quantity tree TREE_ROWS rows high, whatever is shown under
        it (it follows the font as the window scales)."""
        fm = QtGui.QFontMetrics(self.tree.font())
        rows = TREE_ROWS * (fm.height() + 4)
        self.tree.setFixedHeight(rows + self.tree.header().sizeHint()
                                 .height() + 2 * self.tree.frameWidth())

    # ---------------------------------------------------------- quantities
    def set_quantities(self, quantities):
        self.tree.clear()
        groups = {}
        for q in quantities:
            top = groups.get(q.group)
            if top is None:
                top = QtWidgets.QTreeWidgetItem([q.group])
                top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
                font = top.font(0)
                font.setBold(True)
                top.setFont(0, font)
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
        self.mark_groups()

    def _group_marked(self, top):
        """An open group with the background of a selected quantity."""
        brush = QtGui.QBrush(QtGui.QColor(theme.COLORS[theme.name()][
            "selection"])) if top.isExpanded() else QtGui.QBrush()
        for col in range(self.tree.columnCount()):
            top.setBackground(col, brush)

    def mark_groups(self):
        """The backgrounds of the groups (open or not, the theme)."""
        for i in range(self.tree.topLevelItemCount()):
            self._group_marked(self.tree.topLevelItem(i))

    def _clicked(self, item, *_):
        """A click (or Return) on a group: open or close it; on a
        quantity: plot it, or clear the plot if it is the one plotted; the
        second click of a double click is no new click."""
        last, when = self._last_click
        now = time.monotonic()
        self._last_click = (item, now)
        if item is last and now - when < \
                QtWidgets.QApplication.doubleClickInterval() / 1000.0:
            return
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
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
        self.current = q
        vector = q.source in ("vector", "evector")
        patch = self.is_mask(q) or bool(GUARD.fullmatch(q.name))
        self._fill_kinds(vector, patch)
        self._kind_changed(emit=False)
        self.quantity_chosen.emit(self.wanted())

    def is_mask(self, q=None):
        """The quantity (default the current one) is a mask: a label
        with an integer argument or a label of cells set to 1."""
        q = self.current if q is None else q
        return q is not None and bool(INTEGER.fullmatch(q.name) or
                                      FLAGS.fullmatch(q.name))

    def wanted(self):
        """The current quantity as plotted: a mask with the argument of
        the Mask box (name "1 ixeq")."""
        q = self.current
        if q is None or not INTEGER.fullmatch(q.name):
            return q
        n = self.mask_box.argument.value()
        return replace(q, name="%d %s" % (n, q.name),
                       description="%s, argument %d" % (q.description, n))

    def _argument(self, *_):
        if self.current is not None and INTEGER.fullmatch(self.current.name):
            self.quantity_chosen.emit(self.wanted())

    def select(self, name):
        """Select the quantity with this name, if listed (a mask with its
        argument: "1 ixeq")."""
        m = ARGUMENT.fullmatch(name)
        if m and INTEGER.fullmatch(m.group(2)):
            self.mask_box.set_argument(int(m.group(1)))
            name = m.group(2)
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
        old = self.wanted_species or self.chosen_species
        self.wanted_species = None
        self.species.blockSignals(True)
        self.species.clear()
        self.species.addItems(names)
        self.species.setCurrentIndex(names.index(old) if old in names else
                                     default_species(names[:len(columns)]))
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
        sum or selection, clvp contour levels."""
        eirene = q.source in ("eirene", "evector")
        ops = []
        prop = self.proportion() if q.source in ("matrix", "eirene") \
            else None
        if self.summed():
            ops.append(self._sum_op(eirene))
        elif prop is not None:
            col = max(self.species.currentIndex(), 0)
            ops.append("%d %s" % (col, "ezsel" if eirene else "zsel"))
        if prop is not None:
            npos, nneg = prop
            if eirene:
                ops += ["%d %d eclvp" % (nneg, npos), "guieclv", "0 eclvs"]
            else:
                ops += ["%d %d clvp" % (nneg, npos), "guiclv", "0 clvs"]
        return tuple(ops)

    def value_ops(self, q, all_species=False):
        """b2plot operations for writing the values of q as plotted: sum
        or species shown (unless all_species)."""
        eirene = q.source in ("eirene", "evector")
        ops = []
        if self.summed():
            ops.append(self._sum_op(eirene))
        elif not all_species and self.species.count() > 1:
            ops.append("%d %s" % (max(self.species.currentIndex(), 0),
                                  "ezsel" if eirene else "zsel"))
        return tuple(ops)

    def kind(self):
        return self.kind_combo.currentData() or "patch"

    def _fill_kinds(self, vector, patch):
        """The kinds of cell data or of face data (vectors) in the menu
        (patch only for masks): the one chosen kept for data of the same
        kind, else the first (patch, quiver)."""
        combo = self.kind_combo
        old = self.kind() if vector == self._vector else None
        self._vector = vector
        combo.blockSignals(True)
        combo.clear()
        for k in KINDS_VECTOR if vector else KINDS_FLAT:
            combo.addItem(KIND_TEXT[k], k)
            combo.model().item(combo.count() - 1).setEnabled(
                not patch or k == "patch")
        combo.setCurrentIndex(0 if patch or old is None else
                              max(combo.findData(old), 0))
        combo.blockSignals(False)

    def set_kind(self, kind):
        """Choose this kind if the menu offers it."""
        i = self.kind_combo.findData(kind)
        if i >= 0 and self.kind_combo.model().item(i).isEnabled():
            self.kind_combo.setCurrentIndex(i)

    def _kind_chosen(self, *_):
        self._kind_changed()

    def _kind_changed(self, emit=True):
        kind = self.kind()
        source = self.current.source if self.current is not None else ""
        self.lines.setVisible(kind in ("contour", "contourf"))
        self.lines.fill_lines.setVisible(kind == "contourf")
        self.arrows.setVisible(kind in ("quiver", "quiverstream"))
        self.streams.setVisible(kind in ("stream", "quiverstream"))
        self.overlay_box.setVisible(kind in KINDS_FLAT)
        self.cells_box.setVisible(source in ("matrix", "vector",
                                             "equilibrium"))
        mask = self.is_mask()
        self.mask_box.setVisible(mask)
        self.mask_box.show_argument(mask and bool(INTEGER.fullmatch(
            self.current.name)))
        self.colour.setVisible(not mask)
        self.levels_box.setVisible(kind in ("contourf", "contour")
                                   and not mask)
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
        if self.is_mask():
            fields.update(self.mask_box.style_fields())
        return PlotStyle(kind=self.kind(), column=0 if self.reduced()
                         else max(self.species.currentIndex(), 0), **fields)

    def _species_chosen(self, *_):
        """A species chosen (set_columns changes it silently): the one
        offered first from now on, where a quantity has it."""
        self.chosen_species = self.species.currentText()
        self._changed()

    def _changed(self, *_):
        self.style_changed.emit()

