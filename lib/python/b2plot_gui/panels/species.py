"""Species menus of the quantity trees: one in the title of each tree,
"Plasma quantity (species: menu)", with the species of the quantity
plotted from that tree (the run species where b2plot sends no name, the
EIRENE names for atoms, molecules and test ions) element by element, each
element with several followed by its sum ("D (sum)"), all at the end
("Sum"); a menu with several curves per plot (multi) also offers all the
species of an element ("D (all)") and all of them ("All"), each its own
curve; grey without a quantity or with one that is not resolved in
species."""

import re

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Signal

SUM = "Sum"                         # of all the species
ALL = "All"                         # all the species, a curve each
NAME_CHARS = 13         # the Name column of every tree: this many letters
CHARGE = re.compile(r"([A-Za-z]*)\s*\+?(\d*)")     # D0, D+, N+7, N7+


def default_species(names):
    """Index of the highest charge state of the first species in names
    (D+ of D0, D+, N0, ...), among those of its element that follow it
    directly: not the EIRENE atoms, molecules and test ions after the run
    species (D2 is no charge state of D)."""
    def parse(n):
        m = CHARGE.match(n)
        charge = int(m.group(2)) if m.group(2) else 1 if "+" in n else 0
        return m.group(1), charge
    first = parse(names[0])[0] if names else ""
    same = []
    for i, n in enumerate(names):
        if parse(n)[0] != first:
            break
        same.append((parse(n)[1], -i))
    return -max(same)[1] if same else 0


def element(name):
    """The element of a species name (D of D+1)."""
    return re.match(r"[A-Za-z]*", name).group(0)


def entries(names, multi=False):
    """[(text, columns)] of a species menu: element by element its species,
    with several (and other elements) its curves "X (all)" (multi) and its
    sum "X (sum)"; then "All" (multi) and "Sum"."""
    if len(names) <= 1:
        return [(names[0] if names else "", (0,))]
    elements = [element(n) for n in names]
    out = []
    for e in dict.fromkeys(elements):
        cols = tuple(i for i, x in enumerate(elements) if x == e)
        out += [(names[i], (i,)) for i in cols]
        if e and 1 < len(cols) < len(names):
            out += ([("%s (all)" % e, cols)] if multi else []) + [
                ("%s (sum)" % e, cols)]
    whole = tuple(range(len(names)))
    return out + ([(ALL, whole)] if multi else []) + [(SUM, whole)]


def is_multi(text):
    """A choice of several curves (All, X (all))."""
    return text == ALL or text.endswith(" (all)")


def column_names(columns, species=None):
    """Species names of the field columns (the run species where b2plot
    sends no name)."""
    names = [labels.species_text(c) or (
        labels.species_text(species[i]) if species and i < len(species)
        else "") for i, c in enumerate(columns)]
    return [n or "column %d" % (i + 1) for i, n in enumerate(names)]


def chosen_columns(names, chosen):
    """Columns summed (or each a curve: All, X (all)) for the choice of a
    species menu (names: the species of the columns): the species chosen,
    all of them, those of an element, else the first."""
    if len(names) <= 1:
        return (0,)
    return dict(entries(names, True)).get(chosen, (0,))


class SpeciesMenu(QtWidgets.QWidget):
    """The title of a tree and "(species: menu)" right of it, in one row
    over the first column of its header (the header has no text there);
    the menu as wide as the species shown, grey without a species; the
    Name column of the same width in every tree, whatever is open (longer
    names cut, whole in their tooltips)."""

    changed = Signal()

    def __init__(self, tree, title, what, multi=False):
        super().__init__(tree.header().viewport())
        self.tree, self.title, self.multi = tree, title, multi
        self.names = []                 # the species of the columns
        tree.headerItem().setText(0, "")
        self.label = QtWidgets.QLabel(title)
        self.part = QtWidgets.QWidget()     # grey without a species
        self.part.setObjectName("speciesPart")  # on the colour of the head
        self.part.setStyleSheet("#speciesPart { background-color: "
                                "transparent; }")
        self.combo = QtWidgets.QComboBox()
        self.combo.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setToolTip(
            "Species of the %s quantity plotted: one, the sum of an "
            "element or of all%s" % (what, "; X (all), All: each species "
                                     "of the element or every species a "
                                     "curve of its own" if multi else ""))
        part = QtWidgets.QHBoxLayout(self.part)
        part.setContentsMargins(0, 0, 0, 0)
        part.setSpacing(2)
        for w in (QtWidgets.QLabel("(species:"), self.combo,
                  QtWidgets.QLabel(")")):
            part.addWidget(w)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(round(0.3 * self.label.fontMetrics().height()))
        lay.addWidget(self.label)
        lay.addWidget(self.part)
        lay.addStretch(1)
        for w in self.findChildren(QtWidgets.QLabel):
            w.setProperty("bold", True)     # as the titles of the header
        self.partial = {}               # "D (sum)": (first, last column)
        self.wanted = None              # species name to choose next
        self.chosen = None              # the species last chosen by hand
        self.combo.currentIndexChanged.connect(self._chosen)
        self._later = QtCore.QTimer(self)
        self._later.setSingleShot(True)
        self._later.timeout.connect(self.place)
        head = tree.header()
        head.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        head.viewport().installEventFilter(self)
        self.set_columns([""])

    def _schedule(self, *_):
        self._later.start(0)

    def eventFilter(self, obj, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show,
                            QtCore.QEvent.StyleChange,
                            QtCore.QEvent.FontChange):
            self._schedule()
        return False

    def fit(self):
        """The header as high as the row (the font may have changed)."""
        self.tree.header().setMinimumHeight(self.sizeHint().height() + 2)
        self.place()

    def place(self):
        """The Name column NAME_CHARS letters wide (in the font of the
        trees: the same in every tree); the row over the first column."""
        head = self.tree.header()
        fm = self.label.fontMetrics()
        pad = round(0.3 * fm.height()) + 1
        width = self.tree.fontMetrics().horizontalAdvance(
            "n" * NAME_CHARS) + 2 * pad
        if head.sectionSize(1) != width:
            head.resizeSection(1, width)
        height = min(self.sizeHint().height(), head.height())
        self.setGeometry(head.sectionViewportPosition(0) + pad,
                         (head.height() - height) // 2,
                         max(head.sectionSize(0) - 2 * pad, 0), height)

    def set_columns(self, columns, species=None):
        """Species names of the data columns, the sums with several (keeps
        the choice if it can); [""]: no quantity (grey)."""
        names = column_names(columns, species)
        if len(columns) == 1 and not columns[0].strip():
            names = ["—"]
        self.names = names
        menu = entries(names, self.multi)
        self.partial = {text: (cols[0], cols[-1]) for text, cols in menu
                        if 1 < len(cols) < len(names)}
        texts = [text for text, _ in menu]
        old = self.wanted or self.chosen
        self.wanted = None
        self.combo.blockSignals(True)
        self.combo.clear()
        for text, cols in menu:
            self.combo.addItem(text, cols)
        first = (default_species(names),)
        self.combo.setCurrentIndex(texts.index(old) if old in texts else
                                   next((i for i, (_, c) in enumerate(menu)
                                         if c == first), 0))
        self.part.setEnabled(len(names) > 1)
        self.combo.blockSignals(False)
        view = self.combo.view()        # the list: every species whole
        fm = view.fontMetrics()
        view.setMinimumWidth(max(fm.horizontalAdvance(n) for n in texts) +
                             3 * fm.height())
        self._fit_text()

    def _fit_text(self):
        """The menu as wide as the species shown."""
        self.combo.setMinimumContentsLength(max(len(self.text()), 2))
        self.place()

    def text(self):
        return self.combo.currentText()

    def columns(self):
        """The columns of the choice (summed, or each a curve)."""
        return tuple(self.combo.currentData() or (0,))

    def column(self):
        """The column of the species chosen (one species), else 0."""
        cols = self.columns()
        return cols[0] if len(cols) == 1 else 0

    def is_multi(self):
        """Every species of the choice a curve of its own."""
        return is_multi(self.text())

    def curves(self):
        """[(species name, column)] of a choice of several curves."""
        return [(self.names[c] if c < len(self.names) else "column %d" %
                 (c + 1), c) for c in self.columns()]

    def _chosen(self, *_):
        """A species chosen (set_columns changes it silently): the one
        offered first from now on, where a quantity has it."""
        self.chosen = self.combo.currentText()
        self._fit_text()
        self.changed.emit()
