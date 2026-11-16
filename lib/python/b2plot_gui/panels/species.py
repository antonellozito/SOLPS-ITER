"""Species menus of the quantity trees: one in the title of each tree,
"Plasma quantity (species: menu)", with the species of the quantity
plotted from that tree (the run species where b2plot sends no name, the
EIRENE names for atoms, molecules and test ions), their sum and the sum of
each element with several; grey without a quantity or with one that is
not resolved in species."""

import re

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Signal

SUM = "Sum over species"
NAME_CHARS = 13         # the Name column of every tree: this many letters
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


class SpeciesMenu(QtWidgets.QWidget):
    """The title of a tree and "(species: menu)" right of it, in one row
    over the first column of its header (the header has no text there);
    the menu as wide as the species shown, grey without a species; the
    Name column of the same width in every tree, whatever is open (longer
    names cut, whole in their tooltips)."""

    changed = Signal()

    def __init__(self, tree, title, what):
        super().__init__(tree.header().viewport())
        self.tree, self.title = tree, title
        tree.headerItem().setText(0, "")
        self.label = QtWidgets.QLabel(title)
        self.part = QtWidgets.QWidget()     # grey without a species
        self.part.setObjectName("speciesPart")  # on the colour of the head
        self.part.setStyleSheet("#speciesPart { background-color: "
                                "transparent; }")
        self.combo = QtWidgets.QComboBox()
        self.combo.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setToolTip("Species of the %s quantity plotted: one, "
                              "their sum or the sum of an element" % what)
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
        self.partial = {}               # "Sum D": (first, last column)
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
        self.partial = {}
        if len(names) > 1:
            names.append(SUM)
            elements = [re.match(r"[A-Za-z]*", n).group(0) for n in names]
            for e in dict.fromkeys(elements[:-1]):
                cols = [i for i, x in enumerate(elements[:-1]) if x == e]
                if e and 1 < len(cols) < len(names) - 1:
                    names.append("Sum %s" % e)
                    self.partial[names[-1]] = (cols[0], cols[-1])
        old = self.wanted or self.chosen
        self.wanted = None
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        self.combo.setCurrentIndex(names.index(old) if old in names else
                                   default_species(names[:len(columns)]))
        self.part.setEnabled(len(names) > 1)
        self.combo.blockSignals(False)
        view = self.combo.view()        # the list: every species whole
        fm = view.fontMetrics()
        view.setMinimumWidth(max(fm.horizontalAdvance(n) for n in names) +
                             3 * fm.height())
        self._fit_text()

    def _fit_text(self):
        """The menu as wide as the species shown."""
        self.combo.setMinimumContentsLength(max(len(self.text()), 2))
        self.place()

    def text(self):
        return self.combo.currentText()

    def _chosen(self, *_):
        """A species chosen (set_columns changes it silently): the one
        offered first from now on, where a quantity has it."""
        self.chosen = self.combo.currentText()
        self._fit_text()
        self.changed.emit()
