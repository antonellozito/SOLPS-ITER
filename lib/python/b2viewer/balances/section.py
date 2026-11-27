"""The Balances tab of the quantity column: the tabs Parallel fluxes,
Radial fluxes and Neutrals over the column, then the balance of the
volume picked: its options (from the start), then, once a volume is
picked, the radial balance and the poloidal balance in two sections, each
with its explanation over the plot and the comparison of the residuals
under it. A click on a line opens its decomposition right of the column,
level with its plot (extension.py)."""

from ...qt import QtCore, QtWidgets, Qt
from ..scaling import squeezable
from . import calc, plots, terms
from .extension import Extension
from .kinds import KINDS
from .views import Output, PlotView, SpeciesBox, shrinkable

HINTS = {"parallel": "Click the upstream and then the downstream surface "
         "of a volume on the plot: its balance comes here (click the tab "
         "again to pick another volume, Escape cancels).",
         "radial": "Click the inner and then the outer flux surface of a "
         "volume on the plot: its balance comes here (click the tab again "
         "to pick another volume, Escape cancels).",
         "neutrals": "Where the neutrals giving the plasma its particles "
         "were born, by region, and what they become."}


def combo(items, tip):
    c = QtWidgets.QComboBox()
    for key, text in items:
        c.addItem(text, key)
    c.setToolTip(tip)
    return c


class BalancePage(QtWidgets.QWidget):
    """The page of the Balances tab: the tabs (keys, (text, tip)) in its
    header (over the scrolled column, as the Run tracing tabs), a hint
    while the tab shows no section, then its section (the sections of the
    other tabs kept hidden)."""

    def __init__(self, tabs, parent=None):
        super().__init__(parent)
        self.keys = [k for k, _ in tabs]
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setExpanding(True)
        self.tabs.setDrawBase(True)
        for i, (_, (text, tip)) in enumerate(tabs):
            self.tabs.addTab(text)
            self.tabs.setTabToolTip(i, tip)
        self.header = QtWidgets.QWidget()   # placed by the 2D tab
        hl = QtWidgets.QVBoxLayout(self.header)
        hl.setContentsMargins(0, 0, 0, 6)
        hl.addWidget(self.tabs)
        self.hint = QtWidgets.QLabel(HINTS[self.keys[0]])
        self.hint.setWordWrap(True)
        self.hint.setProperty("muted", True)
        shrinkable(self.hint)
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.addWidget(self.hint)
        self.section = None             # the one shown
        self.sections = []              # all, shown or kept

    def key(self):
        """The tab shown: "parallel", "radial" or "neutrals"."""
        return self.keys[max(self.tabs.currentIndex(), 0)]

    def show_tab(self, key):
        """The tab of key shown (no signal)."""
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(self.keys.index(key))
        self.tabs.blockSignals(False)
        self.hint.setText(HINTS[key])

    def show(self, section):
        """The section shown (None: the hint), the others kept hidden."""
        if section is not None and section not in self.sections:
            self.lay.addWidget(section)
            self.sections.append(section)
        for s in self.sections:
            s.setVisible(s is section)
        self.section = section
        self.hint.setText(HINTS[self.key()])
        self.hint.setVisible(section is None)

    def drop(self, section):
        """A section goes for good (its extensions with it)."""
        if section is None or section not in self.sections:
            return
        section.dispose()
        self.lay.removeWidget(section)
        section.hide()
        section.deleteLater()
        self.sections.remove(section)
        if self.section is section:
            self.show(None)


class Row(QtWidgets.QWidget):
    """A plot of the section: its explanation, the plot, the text under it
    (the residuals), the texts from the left edge of the plot; its
    extension follows it."""

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self.view = view
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(view.equation)
        lay.addWidget(view.canvas)
        lay.addWidget(view.below)
        shrinkable(view.equation, view.below)


class BalanceSection(Output, QtWidgets.QWidget):
    """The options, the radial and the poloidal balance and the comparison
    of the residuals; of the parallel balance (along the field lines) or of
    the radial one (across the flux surfaces). host: the widget the
    extensions are drawn over (the 2D tab), column and area: the column
    they start right of and its scroll area."""

    def __init__(self, controller, host, column, area, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.kind = controller.kind
        kind = KINDS[self.kind]
        self.result, self.terms = None, None
        self.quantity = combo(terms.QUANTITIES, "Equation balanced")
        self.species = SpeciesBox()
        self.areatype = combo(kind.area_types, "Area the fluxes and sources "
                              "are divided by")
        self.areatype.setCurrentIndex(self.areatype.findData("contact"))
        self.areaend = combo(kind.area_ends, kind.area_tip)
        self.coord = combo(plots.COORDINATES, "Radial coordinate of the "
                           "radial balance and of the plots opened from it")
        self.distance = combo(calc.DISTANCES, "Distance along the flux tube "
                              "next to the separatrix in the poloidal "
                              "balance and in the plots opened from it")
        self.residuals = QtWidgets.QCheckBox("Residuals")
        self.residuals.setToolTip("Show the residual of B2.5 and the "
                                  "post-processed one")
        self.grid = QtWidgets.QCheckBox("Grid")
        self.grid.setChecked(True)
        self.grid.setToolTip("Grid lines in every balance plot")
        self.logy = QtWidgets.QCheckBox("log y")
        self.logy.setToolTip("Logarithmic y axis in every balance plot "
                             "(values that are not positive left out)")
        clear = QtWidgets.QPushButton("Clear")
        clear.setToolTip("The volume and its balance go; pick a new one")
        clear.clicked.connect(lambda *_: controller.clear_volume())
        save = QtWidgets.QPushButton("Save plots…")
        save.setToolTip("Both plots as png, jpg, eps, pdf or svg")
        save.clicked.connect(lambda *_: self.save_plots())
        export = QtWidgets.QPushButton("Export data…")
        export.setToolTip("The values of both plots: CSV, text, netCDF or "
                          "HDF5")
        export.clicked.connect(lambda *_: self.export_data())
        self.buttons = (clear, save, export)
        top = QtWidgets.QGridLayout()   # two choices a row, each label
        pairs = [("Quantity", self.quantity), ("Species", self.species),
                 ("Area type", self.areatype), ("Area at", self.areaend),
                 ("Radial coordinate", self.coord),
                 ("Poloidal distance", self.distance)]
        for k, (text, w) in enumerate(pairs):     # right next to its menu
            label = QtWidgets.QLabel(text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setBuddy(w)
            top.addWidget(label, k // 2, 2 * (k % 2))
            top.addWidget(w, k // 2, 2 * (k % 2) + 1)
            shrinkable(w)
        top.setColumnStretch(1, 1)
        top.setColumnStretch(3, 1)
        last = QtWidgets.QHBoxLayout()
        for w in (self.residuals, self.grid, self.logy):
            last.addWidget(w)
        for w in self.buttons:          # the rest of the row; they shrink
            w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,  # rather than
                            QtWidgets.QSizePolicy.Fixed)    # widen it
            w.setMinimumWidth(w.fontMetrics().horizontalAdvance("Save…"))
            last.addWidget(w, 1)
        top.addLayout(last, len(pairs) // 2, 0, 1, 4)
        self.radial = PlotView(controller, follow=True)
        self.poloidal = PlotView(controller, follow=True)
        self.messages = [self.radial.below, self.poloidal.below]
        self.rows, self.extensions = {}, {}
        self.notes = QtWidgets.QLabel()
        self.notes.setWordWrap(True)
        self.notes.setProperty("muted", True)
        shrinkable(self.notes)
        self.waiting = QtWidgets.QLabel(HINTS[self.kind])
        self.waiting.setWordWrap(True)
        self.waiting.setProperty("muted", True)
        shrinkable(self.waiting)
        self.boxes = []                 # the plots: once a volume is picked
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.waiting)
        for name, title, view in (("radial", "Radial balance", self.radial),
                                  ("poloidal", "Poloidal balance",
                                   self.poloidal)):
            box = QtWidgets.QGroupBox(title)
            inside = QtWidgets.QVBoxLayout(box)
            row = self.rows[name] = Row(view)
            inside.addWidget(row)
            self.extensions[name] = Extension(self, row, host, column, area)
            view.clicked.connect(lambda key, n=name: self._open(n, key))
            lay.addWidget(box)
            self.boxes.append(box)
        lay.addWidget(self.notes)
        self._plots(False)
        squeezable(self)                # the menus shrink, never the column
        self.quantity.currentIndexChanged.connect(self._quantity)
        for w in (self.areatype, self.areaend, self.coord, self.distance):
            w.currentIndexChanged.connect(self._changed)
        self.species.changed.connect(self._changed)
        for w in (self.residuals, self.grid, self.logy):
            w.toggled.connect(lambda *_: self.draw())

    def _plots(self, on):
        """The plots (a volume picked) or the hint; plots just shown fitted
        to the column once it is laid out (hidden, they had no width)."""
        shown = self.boxes[0].isVisibleTo(self)
        for box in self.boxes:
            box.setVisible(on)
        self.waiting.setVisible(not on)
        if not on:
            self.notes.setVisible(False)
        elif not shown:
            QtCore.QTimer.singleShot(0, self._fit_plots)

    def _fit_plots(self):
        for v in self.views():
            v._resized()

    def views(self):
        return [self.radial, self.poloidal]

    def detail_views(self):
        """The plots of the extensions shown."""
        return [p.view for e in self.extensions.values() for p in e.shown()]

    # ------------------------------------------------------------ setup
    def set_file(self, bf, rhop):
        """Choices of the run: the quantities balance.nc has, its species,
        rho poloidal only with a psi map."""
        for w in (self.quantity, self.coord):
            w.blockSignals(True)
        model = self.quantity.model()
        for i, (key, _) in enumerate(terms.QUANTITIES):
            why = terms.available(bf, key)
            if key in KINDS[self.kind].left_out:
                why = KINDS[self.kind].left_out_why
            model.item(i).setEnabled(not why)
            model.item(i).setToolTip(why)
        self.species.set_file(bf)
        m = self.coord.model()
        m.item(0).setEnabled(rhop)
        m.item(0).setToolTip("" if rhop else "ρₚ needs the psi map "
                             "of rzpsi.dat")
        self.coord.setCurrentIndex(0 if rhop else 1)
        for w in (self.quantity, self.coord):
            w.blockSignals(False)
        self._enable()

    def _enable(self):
        q = self.quantity.currentData()
        self.species.setEnabled(q in terms.SPECIES)
        fixed = q in ("totpress", "force")
        self.areatype.setEnabled(not fixed)
        self.areaend.setEnabled(not fixed and
                                self.areatype.currentData() != "none")

    def options(self):
        return calc.Options(areatype=self.areatype.currentData(),
                            areaend=self.areaend.currentData(),
                            distance=self.distance.currentData())

    def _quantity(self, *_):
        """Another equation: what was opened from the plots goes."""
        self.close_all()
        self._changed()

    def _changed(self, *_):
        self._enable()
        self.refresh()

    # ---------------------------------------------------------- results
    def refresh(self):
        """The balance of the volume again (new volume or options); the
        plots opened from it follow."""
        c = self.controller
        if c.vol is None:
            self._plots(False)
            return
        self._plots(True)
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            q = self.quantity.currentData()
            species = self.species.selection() if q in terms.SPECIES \
                else None
            self.terms = c.terms(q, species)
            self.result = c.compute(self.terms, self.options(),
                                    self.coord.currentData())
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        for label, text in zip(self.messages, self.result.messages()):
            label.setText(text)
        self.notes.setText(self.result.note)
        self.notes.setVisible(bool(self.result.note))
        self.draw()

    def area_text(self):
        o = self.options()
        return plots.area_text(self.quantity.currentData(), o.areatype,
                               o.areaend, self.controller.vol.reverse,
                               self.kind)

    def draw(self):
        if self.result is None:
            return
        args = (self.coord.currentData(), self.residuals.isChecked(),
                self.area_text(), self.distance.currentData())
        for view, axis in ((self.radial, "radial"),
                           (self.poloidal, "poloidal")):
            view.show_panel(plots.total(self.result, self.terms, axis,
                                        *args))
        for e in self.extensions.values():
            e.refresh()

    def _open(self, name, key):
        """The decomposition of a line right of the plot it was clicked
        in, the line glowing while it is shown."""
        self.extensions[name].open(3, key)

    def apply_theme(self):
        self.draw()

    def close_all(self):
        for e in self.extensions.values():
            e.close_all()

    def dispose(self):
        """The section goes, and its extensions with it."""
        for e in self.extensions.values():
            e.dispose()
        self.extensions = {}

    def panels(self):
        return [v.panel for v in (self.radial, self.poloidal)
                if v.panel is not None]

    def stem(self):
        return "balance_" + (self.quantity.currentData() or "")

    def result_unit(self):
        return self.result.unit if self.result is not None else ""

    def meta(self):
        c = self.controller
        return [("run", c.rundir()), ("balance", c.name),
                ("volume", c.describe()),
                ("quantity", self.quantity.currentText()),
                ("species", self.species.toolTip()
                 if self.species.isEnabled() else "-"),
                ("area type", self.areatype.currentText()),
                ("area at", self.areaend.currentText()),
                ("radial coordinate", self.coord.currentText()),
                ("poloidal distance", self.distance.currentText())]
