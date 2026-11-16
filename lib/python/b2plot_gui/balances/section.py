"""The Balances tab of the quantity column: the buttons Parallel fluxes and
Radial fluxes, then the balance of the volume picked: its options, then
the radial balance and the poloidal balance in two sections, each with its
explanation over the plot and the comparison of the residuals under it. A
click on a line opens its decomposition right of the column, level with
its plot (extension.py)."""

from ...qt import QtWidgets, Qt
from ..scaling import squeezable
from . import calc, plots, terms
from .extension import Extension
from .kinds import KINDS
from .views import Output, PlotView, SpeciesBox, shrinkable

HINT = ("Parallel fluxes: pick the upstream and the downstream surface of a "
        "volume on the plot. Radial fluxes: pick its inner and outer flux "
        "surface.")


def combo(items, tip):
    c = QtWidgets.QComboBox()
    for key, text in items:
        c.addItem(text, key)
    c.setToolTip(tip)
    return c


class BalancePage(QtWidgets.QWidget):
    """The page of the Balances tab: the buttons of the controller (the
    one of the balance shown pressed), a hint until a volume is picked,
    then its section."""

    def __init__(self, buttons, parent=None):
        super().__init__(parent)
        row = QtWidgets.QHBoxLayout()
        for b in buttons:
            b.setProperty("bold", True)
            row.addWidget(b, 1)
        self.hint = QtWidgets.QLabel(HINT)
        self.hint.setWordWrap(True)
        self.hint.setProperty("muted", True)
        shrinkable(self.hint)
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.addLayout(row)
        self.lay.addWidget(self.hint)
        self.section = None

    def set_section(self, section):
        """The section shown (None: the hint)."""
        if self.section is not None:
            self.section.dispose()
            self.lay.removeWidget(self.section)
            self.section.hide()
            self.section.deleteLater()
        self.section = section
        if section is not None:
            self.lay.addWidget(section)
        self.hint.setVisible(section is None)


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
        save = QtWidgets.QPushButton("Save plots…")
        save.setToolTip("Both plots as png, jpg, eps, pdf or svg")
        save.clicked.connect(lambda *_: self.save_plots())
        export = QtWidgets.QPushButton("Export data…")
        export.setToolTip("The values of both plots: CSV, text, netCDF or "
                          "HDF5")
        export.clicked.connect(lambda *_: self.export_data())
        self.buttons = (save, export)
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
        last.addStretch(1)
        for w in self.buttons:          # they shrink rather than widen it
            w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                            QtWidgets.QSizePolicy.Fixed)
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
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.addLayout(top)
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
        lay.addWidget(self.notes)
        squeezable(self)                # the menus shrink, never the column
        self.quantity.currentIndexChanged.connect(self._quantity)
        for w in (self.areatype, self.areaend, self.coord, self.distance):
            w.currentIndexChanged.connect(self._changed)
        self.species.changed.connect(self._changed)
        for w in (self.residuals, self.grid, self.logy):
            w.toggled.connect(lambda *_: self.draw())

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
        m.item(0).setToolTip("" if rhop else "rho poloidal needs the psi map "
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
            return
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
