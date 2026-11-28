"""Quantity panel of the 2D tab: what to plot and how."""

import re
import time
from dataclasses import replace

from .. import theme
from ..catalog import FLAGS, GUARD, INTEGER
from ..presets import ENTRY, ENTRY_PREFIX
from ..plot.styles import KINDS_FLAT, KINDS_VECTOR, PlotStyle
from ...qt import QtCore, QtGui, QtWidgets, Qt, Signal
from .choices import ChoicesBox
from .options import LabelsBox, LevelsBox, RegionsMenu
from .overlays import OverlayOptions, OverlaySection
from .plotopts import (ArrowsBox, ColourBox, LinesBox, MaskBox, SplitBox,
                       StreamBox,
                       TextureBox, WallBox)
from .species import ALL, SUM, SpeciesMenu
from .timebox import TimeBox
from .view3d import TracersBox

KIND_TEXT = {"patch": "Patch", "contourf": "Filled contour",
             "contour": "Contour lines", "quiver": "Quiver",
             "stream": "Streamlines", "quiverstream": "Quiver + streamlines",
             "texture": "Flow texture",
             "quivertexture": "Quiver + flow texture", "tracers": "Tracers"}
TREE_ROWS = 11                      # rows of the plasma quantity tree
MOVIE_ROWS = 7.5                    # Run movies: its 8 groups, closed
LEVELS = {"contourf": 100, "contour": 20}   # contour levels at first
VECTOR_ROWS = WALL_ROWS = 6         # rows of the vector and wall trees
EXTRA = ("vector", "wall", "overlay")   # the trees apart from the plasma one
ARGUMENT = re.compile(r"(-?\d+) (\S+)")     # "1 ixeq": a mask and its argument


def make_tree(title, what):
    """A tree of quantities in groups (title: its first column, what: what
    a click does), the Name column right of it; its species menu
    (SpeciesMenu) is added by the owner."""
    tree = QtWidgets.QTreeWidget()
    tree.setHeaderLabels([title, "Name"])
    tree.setRootIsDecorated(True)
    tree.setUniformRowHeights(True)
    tree.setVerticalScrollBarPolicy(    # columns as wide, groups open
        Qt.ScrollBarAlwaysOn)           # or not
    head = tree.header()
    head.setStretchLastSection(False)
    head.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
    head.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
    tree.setExpandsOnDoubleClick(False)
    tree.setToolTip("Click a group to open or close it, a quantity to "
                    "%s, click it again to clear it" % what)
    return tree


def fill_tree(tree, quantities, always=()):
    """The quantities (group, text, label) in their groups, in order; the
    groups always (in this order, first) there too without quantities,
    greyed out (no clicks)."""
    tree.clear()
    groups = {}
    for name in list(always) + [q.group for q in quantities]:
        if name not in groups:
            top = QtWidgets.QTreeWidgetItem([name])
            top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
            font = top.font(0)
            font.setBold(True)
            top.setFont(0, font)
            groups[name] = top
            tree.addTopLevelItem(top)
    for q in quantities:
        top = groups[q.group]
        item = QtWidgets.QTreeWidgetItem([q.text, q.label])
        item.setToolTip(0, q.text)
        item.setToolTip(1, q.label)
        item.setData(0, Qt.UserRole, q)
        top.addChild(item)
    for top in groups.values():
        top.setDisabled(not top.childCount())


def mark_group(top):
    """An open group with the background of a selected quantity, a group
    greyed out (fill_tree) in the grey of the theme (the style sheet sets
    the text colour of the trees, also of the items disabled)."""
    colors = theme.COLORS[theme.name()]
    brush = QtGui.QBrush(QtGui.QColor(colors["selection"])) if \
        top.isExpanded() else QtGui.QBrush()
    grey = QtGui.QBrush(QtGui.QColor(colors["disabled_text"])) if not \
        top.flags() & Qt.ItemIsEnabled else QtGui.QBrush()
    for col in range(top.treeWidget().columnCount()):
        top.setBackground(col, brush)
        top.setForeground(col, grey)


def tree_height(tree, rows):
    """The tree rows high (in its font, under its header)."""
    fm = QtGui.QFontMetrics(tree.font())
    head = tree.header()
    tree.setFixedHeight(int(round(rows * (fm.height() + 4))) + max(
        head.sizeHint().height(), head.minimumHeight()) +
        2 * tree.frameWidth())


class SingleClicks:
    """Clicks on the items of a tree: True for a new click, False for the
    second click of a double click (no new click)."""

    def __init__(self):
        self._last = (None, 0.0)        # item, time

    def __call__(self, item):
        last, when = self._last
        now = time.monotonic()
        self._last = (item, now)
        return not (item is last and now - when <
                    QtWidgets.QApplication.doubleClickInterval() / 1000.0)


class QuantityPanel(QtWidgets.QWidget):
    """The plasma, vector and wall quantity trees (each plotted alone or
    with the others, each with its species menu in its title), the
    overlay tree in its section, and the plot options."""

    quantity_chosen = Signal(object)
    vector_chosen = Signal(object)  # a vector quantity, None: none plotted
    wall_chosen = Signal(object)    # a wall quantity, None: no wall plot
    overlay_chosen = Signal(object)     # drawn over the plasma plot
    style_changed = Signal()
    seed_line = Signal(bool)
    calculator = Signal(str)        # open the calculator with this text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = None             # the plasma quantity plotted
        self.make_entry = None          # (entry, items) -> the Quantity of
        #                                 a quantity with choices (the tab)
        self.entry_species = None       # the species of its choices
        self._entry_labels = ()         # its choices to restore
        self.vector_current = None      # the vector quantity plotted
        self.wall_current = None        # the wall quantity plotted
        self.overlay_current = None     # the quantity overlaid
        self._new_click = SingleClicks()
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 6)   # the tabs: 6 px over it
        self.time_box = TimeBox()
        self.time_box.source_changed.connect(lambda *_: self._tab_shown())
        lay.addWidget(self.time_box)
        self.page_slot = QtWidgets.QVBoxLayout()    # the tabs with pages
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
        self.tree = self._make_tree("Plasma quantity", "plot it")
        self.vector_tree = self._make_tree(
            "Vector quantity", "plot it as arrows or streamlines (with a "
            "plasma quantity or alone)")
        self.wall_tree = self._make_tree("Wall quantity", "plot it along "
                                         "the wall (with a plasma quantity "
                                         "or alone)")
        lay.addLayout(row)
        lay.addWidget(self.tree)        # fixed heights (_tree_height)
        lay.addWidget(self.vector_tree)
        lay.addWidget(self.wall_tree)
        self.plasma_species = SpeciesMenu(self.tree, "Plasma quantity",
                                          "plasma", multi=True)  # chords
        self.vector_species = SpeciesMenu(self.vector_tree,
                                          "Vector quantity", "vector")
        self.wall_species = SpeciesMenu(self.wall_tree, "Wall quantity",
                                        "wall")
        self.overlay_tree = self._make_tree(    # in the Overlay section
            "Overlay quantity", "draw it as contour lines over the plasma "
            "plot")
        self.overlay_species = SpeciesMenu(self.overlay_tree,
                                           "Overlay quantity", "overlay")
        for menu in self.menus():
            menu.changed.connect(self._changed)
        self.species = self.plasma_species.combo    # of the plasma plot

        self.choices_box = ChoicesBox()     # of a quantity with choices,
        self.choices_box.changed.connect(self._choice)  # above the tools
        self.choices_box.hide()
        lay.addWidget(self.choices_box)
        row = QtWidgets.QHBoxLayout()   # the six sections
        self.overlay_button = QtWidgets.QPushButton("Overlay")
        self.overlay_button.setToolTip("Contour lines of a second quantity "
                                       "over the plasma plot (not with "
                                       "contour lines)")
        self.chords_button = QtWidgets.QPushButton("Chords")
        self.chords_button.setToolTip("Profiles of the quantity shown along "
                                      "chords drawn on the plot or typed, "
                                      "their integrals and averages")
        self.field_button = QtWidgets.QPushButton("Field line")
        self.field_button.setToolTip("The magnetic field line through a "
                                     "point picked on the plot, its "
                                     "connection lengths and the profile of "
                                     "the quantity shown along it")
        self.spectrum_button = QtWidgets.QPushButton("Spectrum")
        self.spectrum_button.setToolTip("The spectrum of the light quantity "
                                        "shown along chords drawn on the "
                                        "plot, typed or of the *.chords "
                                        "files: the line integral of each "
                                        "of its lines against the "
                                        "wavelength")
        self.camera_button = QtWidgets.QPushButton("Camera")
        self.camera_button.setToolTip("The image of the quantity shown seen "
                                      "by a camera: its line integral along "
                                      "the ray of each pixel up to the wall")
        self.stats_button = QtWidgets.QPushButton("Statistics")
        self.stats_button.setToolTip("Volume integral, average, minimum, "
                                     "maximum and histogram of the quantity "
                                     "shown over the cells shown, a box or "
                                     "a polygon")
        for b in (self.chords_button, self.field_button,
                  self.spectrum_button, self.camera_button,
                  self.overlay_button, self.stats_button):
            b.setCheckable(True)
            b.setProperty("bold", True)
            row.addWidget(b, 2)
        lay.addLayout(row)
        self.sections = QtWidgets.QVBoxLayout()  # the open one (tab)
        self.sections.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self.sections)
        self.overlay_section = OverlaySection(self.overlay_tree)
        self.overlay_section.hide()
        self.sections.addWidget(self.overlay_section)
        self.mask_box = MaskBox()
        self.mask_box.argument_changed.connect(self._argument)
        self.mask_box.changed.connect(self._changed)
        lay.addWidget(self.mask_box)

        self.kind_combo = QtWidgets.QComboBox()     # a menu of the kinds
        self.kind_combo.setToolTip("Patch, filled contour or contour lines")
        self._fill_kinds(False)
        self.kind_combo.currentIndexChanged.connect(self._kind_chosen)
        self.vector_kind = QtWidgets.QComboBox()
        self.vector_kind.setToolTip("Arrows, streamlines, flow texture, "
                                    "arrows over streamlines or the flow "
                                    "texture, or tracers")
        for k in KINDS_VECTOR:
            self.vector_kind.addItem(KIND_TEXT[k], k)
        self.vector_kind.currentIndexChanged.connect(self._kind_chosen)

        self.colour = ColourBox("Plasma plot options")  # with the plot type
        kinds = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Plot type")
        kinds.addWidget(label)
        kinds.addWidget(self.kind_combo, 1)
        self.colour.layout().insertLayout(0, kinds)
        self.only_2d = [label, self.kind_combo]    # hidden in the 3D view
        self.plasma_regions = RegionsMenu("plasma")     # at the end
        self.colour.layout().addWidget(self.plasma_regions)
        self.vector_box = ColourBox("Vector plot options", "magma",
                                    ("linear", "log"))  # of the magnitude
        kinds = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Plot type")
        kinds.addWidget(label)
        kinds.addWidget(self.vector_kind, 1)
        self.vector_box.layout().insertLayout(0, kinds)
        self.split = SplitBox()         # a vector as its components
        self.split.hide()
        self.vector_box.layout().insertWidget(1, self.split)
        self.split.changed.connect(self._changed)
        for w in (self.split.on, self.split.geo):
            w.toggled.connect(lambda *_: self._kind_changed(emit=False))
        self.only_2d += [label, self.vector_kind]
        self.vector_regions = RegionsMenu("vector")
        self.vector_box.layout().addWidget(self.vector_regions)
        self.vector_box.changed.connect(self._changed)
        self.wall_box = WallBox()
        self.wall_box.changed.connect(self._changed)
        self.only_2d += self.wall_box.line_row
        self.in3d = False               # the 3D view shown
        self.levels_box = LevelsBox()   # one Contours section
        self.lines = LinesBox()
        self.contour_box = QtWidgets.QGroupBox("Contours")
        contour = QtWidgets.QVBoxLayout(self.contour_box)
        contour.addWidget(self.levels_box)
        contour.addWidget(self.lines)
        self.arrows = ArrowsBox()
        self.streams = StreamBox()
        self.streams.seed_line.connect(self.seed_line)
        self.texture = TextureBox()
        self.tracers = TracersBox(in3d=False)
        self.tracers.draw2d.connect(self.seed_line)
        for box in (self.colour, self.levels_box, self.lines, self.arrows,
                    self.streams, self.texture, self.tracers,
                    self.plasma_regions, self.vector_regions):
            box.changed.connect(self._changed)
        self.overlay = OverlayOptions()
        for box in self.overlay.parts():
            box.changed.connect(self._changed)
        self.labels_box = LabelsBox()
        self.labels_box.changed.connect(self._changed)
        column.addStretch(1)            # the room left under the boxes
        # the graphic options, placed in the right column by the 2D tab
        self.style_boxes = (self.colour, self.contour_box, self.vector_box,
                            self.arrows, self.streams, self.texture,
                            self.tracers, self.wall_box) + \
            self.overlay.boxes()        # above the layers
        self.lower_boxes = (self.labels_box,)
        self._levels_of = dict(LEVELS)  # the number of each plot type
        self._last_kind = self.kind()
        self._shown = (False, False, False, False)  # plasma, vector, wall,
        #                                             overlay
        self._kind_changed(emit=False)
        self._tree_height()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self._tree_height()

    def show_page(self, page):
        """The page of the Run tracing or Balances tab (a widget of the
        page slot), or (None) what the other tabs show."""
        self.main_part.setVisible(page is None)
        for i in range(self.page_slot.count()):
            w = self.page_slot.itemAt(i).widget()
            if w is not None:
                w.setVisible(w is page)
                if getattr(w, "header", None) is not None:   # not scrolled
                    w.header.setVisible(w is page)

    def _make_tree(self, title, what):
        tree = make_tree(title, what)
        tree.itemActivated.connect(self._clicked)
        tree.itemClicked.connect(self._clicked)
        tree.itemExpanded.connect(self._group_marked)
        tree.itemCollapsed.connect(self._group_marked)
        return tree

    def _tab_shown(self):
        """Another tab: the wall tree only in Final state (the movies have
        no wall quantities), the heights of the trees."""
        self.wall_tree.setVisible(not self.time_box.movie())
        self._tree_height()

    def _tree_height(self):
        """The plasma quantity tree TREE_ROWS rows high (MOVIE_ROWS in the
        Run movies tab), the vector one VECTOR_ROWS, the wall one
        WALL_ROWS, whatever is shown under them (they follow the font as
        the window scales)."""
        for menu in self.menus():
            menu.fit()
        rows = MOVIE_ROWS if self.time_box.movie() else TREE_ROWS
        for tree, n in ((self.tree, rows), (self.vector_tree, VECTOR_ROWS),
                        (self.wall_tree, WALL_ROWS),
                        (self.overlay_tree, rows)):     # as the plasma one
            tree_height(tree, n)

    # ---------------------------------------------------------- quantities
    def set_quantities(self, quantities):
        self._fill_tree(self.tree, quantities)

    def set_vector_quantities(self, quantities):
        self._fill_tree(self.vector_tree, quantities)

    def set_wall_quantities(self, quantities):
        self._fill_tree(self.wall_tree, quantities)

    def set_overlay_quantities(self, quantities):
        self._fill_tree(self.overlay_tree, quantities)

    def trees(self):
        return (self.tree, self.vector_tree, self.wall_tree,
                self.overlay_tree)

    def menus(self):
        """The species menus of the plasma, vector, wall and overlay
        trees."""
        return (self.plasma_species, self.vector_species, self.wall_species,
                self.overlay_species)

    def _fill_tree(self, tree, quantities):
        fill_tree(tree, quantities)
        self._filter(self.search.text())

    def _filter(self, text):
        """The search in all the trees."""
        text = text.strip().lower()
        for tree in self.trees():
            for i in range(tree.topLevelItemCount()):
                top = tree.topLevelItem(i)
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
        mark_group(top)

    def mark_groups(self):
        """The backgrounds of the groups (open or not, the theme)."""
        for tree in self.trees():
            for i in range(tree.topLevelItemCount()):
                self._group_marked(tree.topLevelItem(i))

    def _clicked(self, item, *_):
        """A click (or Return) on a group: open or close it; on a
        quantity: plot it, or clear the plot if it is the one plotted; the
        second click of a double click is no new click."""
        if not self._new_click(item):
            return
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
            return
        q = item.data(0, Qt.UserRole)
        for kind in EXTRA:              # vector and wall trees
            if item.treeWidget() is getattr(self, kind + "_tree"):
                if q is not None and q is getattr(self, kind + "_current"):
                    self.unselect_extra(kind)
                    getattr(self, kind + "_chosen").emit(None)
                elif q is not None:
                    setattr(self, kind + "_current", q)
                    getattr(self, kind + "_chosen").emit(q)
                return
        if q is not None and q is self.current:
            self.unselect()
            self.quantity_chosen.emit(None)
            return
        self._activated(item)

    def unselect(self):
        """No plasma quantity chosen (the state at the start)."""
        self.current = None
        self.tree.clearSelection()
        self.tree.setCurrentItem(None)

    def unselect_extra(self, kind):
        """No vector or wall quantity chosen (kind "vector", "wall")."""
        setattr(self, kind + "_current", None)
        tree = getattr(self, kind + "_tree")
        tree.clearSelection()
        tree.setCurrentItem(None)

    def select_extra(self, kind, name):
        """Select (and plot) the vector or wall quantity with this name,
        if listed."""
        tree = getattr(self, kind + "_tree")
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            for j in range(top.childCount()):
                item = top.child(j)
                q = item.data(0, Qt.UserRole)
                if q.name == name:
                    tree.setCurrentItem(item)
                    setattr(self, kind + "_current", q)
                    getattr(self, kind + "_chosen").emit(q)
                    return True
        return False

    def _activated(self, item, *_):
        q = item.data(0, Qt.UserRole)
        if q is None or q is self.current:
            return
        self.current = q
        if q.source == "entry":         # its menus, the choices restored
            self.choices_box.set_entry(ENTRY[q.name[len(ENTRY_PREFIX):]],
                                       self.entry_species,
                                       self._entry_labels)
        self._entry_labels = ()
        patch = self.is_mask(q) or bool(GUARD.fullmatch(q.name))
        self._fill_kinds(patch)
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
        the Mask box (name "1 ixeq"), a quantity with choices as chosen
        (None while they are not known)."""
        q = self.current
        if q is not None and q.source == "entry":
            items = self.choices_box.items()
            return None if items is None or self.make_entry is None else \
                self.make_entry(ENTRY[q.name[len(ENTRY_PREFIX):]], items)
        if q is None or not INTEGER.fullmatch(q.name):
            return q
        n = self.mask_box.argument.value()
        return replace(q, name="%d %s" % (n, q.name),
                       description="%s, argument %d" % (q.description, n))

    def _choice(self):
        """A choice of the quantity with choices made: plotted as chosen."""
        if self.current is not None and self.current.source == "entry":
            self.quantity_chosen.emit(self.wanted())

    def set_entry_species(self, species):
        """The species of the run for the choices (again when the EIRENE
        species arrive): the menus of the quantity shown filled again."""
        self.entry_species = species
        q = self.current
        if q is not None and q.source == "entry":
            self.choices_box.set_entry(ENTRY[q.name[len(ENTRY_PREFIX):]], species,
                                       self.choices_box.labels())
            self.quantity_chosen.emit(self.wanted())

    def select_entry(self, name, labels):
        """Select the quantity with choices of this name with the choices
        labels (where offered)."""
        self._entry_labels = tuple(labels)
        ok = self.select(name)
        self._entry_labels = ()
        return ok

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
        """Species of the plasma data columns (keeps the choice if it
        can)."""
        self.plasma_species.set_columns(columns, species)

    # -------------------------------------------------------------- style
    def summed(self, menu=None):
        """True for the sum over all species or over one element (in the
        species menu, default the plasma one); the plot of a choice of
        several curves (All, X (all): the chords) is their sum."""
        menu = menu or self.plasma_species
        return menu.text() in (SUM, ALL) or bool(menu.partial.get(
            menu.text()))

    def _sum_op(self, eirene, menu=None):
        menu = menu or self.plasma_species
        lo, hi = menu.partial.get(menu.text()) or (0, -1)
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

    def overlay_reduced(self):
        """True if b2plot sends one column of the overlay quantity."""
        q = self.overlay_current
        return self.summed(self.overlay_species) or (
            self.overlay.levels.proportion() is not None and q is not None
            and q.source in ("matrix", "eirene"))

    def ops(self, q, overlay=False):
        """b2plot operations applied after the label of quantity q (the
        plasma one, or the overlay one): species sum or selection, clvp
        contour levels."""
        menu = self.overlay_species if overlay else self.plasma_species
        eirene = q.source in ("eirene", "evector")
        ops = []
        prop = (self.overlay.levels.proportion() if overlay else
                self.proportion()) if q.source in ("matrix", "eirene") \
            else None
        if self.summed(menu):
            ops.append(self._sum_op(eirene, menu))
        elif prop is not None:
            ops.append("%d %s" % (menu.column(),
                                  "ezsel" if eirene else "zsel"))
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
            ops.append("%d %s" % (self.plasma_species.column(),
                                  "ezsel" if eirene else "zsel"))
        return tuple(ops)

    def kind(self):
        return self.kind_combo.currentData() or "patch"

    def _fill_kinds(self, patch):
        """The kinds of the plasma plot in the menu (patch only for masks):
        the one chosen kept, else patch."""
        combo = self.kind_combo
        old = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for k in KINDS_FLAT:
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
        """Another plot type: the number of contour levels kept for each
        (LEVELS at first: 100 filled contours, 20 contour lines)."""
        old, new = self._last_kind, self.kind()
        number = self.levels_box.number
        if old in self._levels_of:
            self._levels_of[old] = number.value()
        if new != old and new in self._levels_of:
            number.blockSignals(True)
            number.setValue(self._levels_of[new])
            number.blockSignals(False)
        self._kind_changed()

    def set_plotted(self, plasma, vector, wall, overlay=False):
        """The options of each plot only with its quantity plotted."""
        self._shown = (plasma, vector, wall, overlay)
        self._kind_changed(emit=False)

    def vector_kind_name(self):
        return self.vector_kind.currentData() or "quiver"

    def _kind_changed(self, emit=True):
        kind, vkind = self.kind(), self.vector_kind_name()
        self._last_kind = kind
        source = self.current.source if self.current is not None else ""
        vsource = self.vector_current.source if self.vector_current else ""
        on, vector, wall, overlay = self._shown
        osource = self.overlay_current.source if self.overlay_current \
            else ""
        for box in self.overlay.boxes():
            box.setVisible(overlay)
        self.overlay.regions.setVisible(osource in ("matrix", "equilibrium",
                                                    "neutrals"))
        self.lines.fill_lines.setVisible(kind == "contourf")
        self.lines.mono.setVisible(kind == "contour")   # filled: no use
        self.vector_box.setVisible(vector)
        self.split.setVisible(vector and not self.in3d)
        self.split.allow(vkind == "quiver")     # arrows only
        split = vector and bool(self.split.mode())
        self.vector_kind.setEnabled(not split)
        b, a = self.vector_box, self.arrows     # options without effect
        for w in (b.cmap, b.reverse, b.scale, b.auto, a.normalize,
                  a.by_magnitude, a.arrow_color):
            w.setEnabled(not split)
        for w in (b.vmin, b.vmax):
            w.setEnabled(not split and not b.auto.isChecked())
        self.arrows.setVisible(vector and vkind in (
            "quiver", "quiverstream", "quivertexture"))
        self.streams.setVisible(vector and vkind in ("stream",
                                                     "quiverstream"))
        self.texture.setVisible(vector and vkind in ("texture",
                                                     "quivertexture"))
        self.tracers.setVisible(vector and vkind == "tracers")
        self.wall_box.setVisible(wall)
        self.plasma_regions.setVisible(source in ("matrix", "equilibrium",
                                                  "neutrals", "entry"))
        self.choices_box.setVisible(source == "entry")
        self.vector_regions.setVisible(vsource == "vector")  # B2.5 cells
        mask = self.is_mask()
        self.mask_box.setVisible(mask)
        self.mask_box.show_argument(mask and bool(INTEGER.fullmatch(
            self.current.name)))
        self.colour.setVisible(on and not mask)
        self.contour_box.setVisible(on and kind in ("contourf", "contour")
                                    and not mask)
        if self.in3d:                   # the boxes of the 2D plot alone
            for box in (self.arrows, self.streams, self.texture,
                        self.tracers, self.contour_box, self.labels_box) + \
                    self.overlay.boxes():
                box.setVisible(False)
        self.labels_box.setVisible(not self.in3d)
        for w in self.only_2d:
            w.setVisible(not self.in3d)
        for box in (self.colour, self.vector_box, self.wall_box):
            box.show_modes(self.in3d)   # transparency: the 3D view only
        if emit:
            self._changed()

    def set_3d(self, on):
        """The options of the 3D view: those of the 2D plot alone
        hidden."""
        self.in3d = bool(on)
        self._kind_changed(emit=False)

    def set_range(self, lo, hi):
        self.colour.set_range(lo, hi)

    def set_wall_range(self, lo, hi):
        self.wall_box.set_range(lo, hi)

    def set_seeds(self, seeds):
        self.streams.set_seeds(seeds)

    def style(self):
        """The PlotStyle of the plasma plot."""
        fields = {}
        for box in (self.colour, self.levels_box, self.lines,
                    self.plasma_regions):
            fields.update(box.style_fields())
        if self.is_mask():
            fields.update(self.mask_box.style_fields())
        return PlotStyle(kind=self.kind(), column=0 if self.reduced()
                         else self.plasma_species.column(), **fields)

    def vector_style(self, column):
        """The PlotStyle of the vector plot (species column column)."""
        fields = {}
        for box in (self.vector_box, self.arrows, self.streams,
                    self.texture, self.tracers, self.vector_regions,
                    self.split):
            fields.update(box.style_fields())
        if self.in3d:
            fields["split"] = ""
        return PlotStyle(kind=self.vector_kind_name(), column=column,
                         **fields)

    def set_split_parts(self, parts):
        """The physical components of the vector quantity [(name, text,
        colour, zero)], or None: none offered."""
        self.split.set_parts(parts)
        self._kind_changed(emit=False)

    def set_vector_range(self, lo, hi):
        self.vector_box.set_range(lo, hi)

    def overlay_style(self):
        """The PlotStyle of the overlay: contour lines."""
        fields = {}
        for box in self.overlay.parts():
            fields.update(box.style_fields())
        fields["fill_lines"] = False
        return PlotStyle(kind="contour", column=0 if self.overlay_reduced()
                         else self.overlay_species.column(), **fields)

    def set_overlay_range(self, lo, hi):
        self.overlay.colour.set_range(lo, hi)

    def _changed(self, *_):
        self.style_changed.emit()

