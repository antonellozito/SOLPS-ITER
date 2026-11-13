"""Windows of the balances, always over the window they come from: the
balance window (options, total radial and poloidal balance, comparison of
the residuals), the decomposition of one of its lines and the terms or
strata of a group of sources. They scale with their size as the main
window does."""

import re

from ...qt import QtGui, QtWidgets, Qt
from . import calc, equations, plots, style, terms
from .tip import EquationTip
from .views import Output, PlotView, Scaled, SpeciesBox, shrinkable

GAP = 12                            # pixels under the commands



def _combo(items, tip):
    c = QtWidgets.QComboBox()
    for key, text in items:
        c.addItem(text, key)
    c.setToolTip(tip)
    return c


def _place(win, ref, dx, dy):
    """win at an offset from the top left corner of ref (once)."""
    if getattr(win, "_placed", False) or ref is None:
        return
    g = ref.frameGeometry()
    win.move(g.x() + dx, g.y() + dy)
    win._placed = True


class BalanceWindow(Output, Scaled, QtWidgets.QWidget):
    """The options, the total radial and poloidal balance and the
    comparison of the residuals."""

    def __init__(self, controller, parent):
        super().__init__(parent, Qt.Tool)
        self.controller = controller
        self.setWindowTitle("Parallel balance")
        self.result, self.terms = None, None
        self.detail = None
        self.quantity = _combo(terms.QUANTITIES, "Equation balanced")
        self.species = SpeciesBox()
        self.areatype = _combo(calc.AREA_TYPES, "Area the fluxes and sources "
                               "are divided by")
        self.areaend = _combo(calc.AREA_ENDS, "End of each flux tube whose "
                              "area divides its fluxes and sources")
        self.coord = _combo(plots.COORDINATES, "Radial coordinate of the "
                            "radial balance")
        self.distance = _combo(calc.DISTANCES, "Distance along the flux tube "
                               "next to the separatrix in the poloidal "
                               "balance")
        self.smoothing = QtWidgets.QCheckBox("Smoothing")
        self.smoothing.setToolTip("Light smoothing of every profile (linear: "
                                  "the smoothed terms still add up)")
        self.residuals = QtWidgets.QCheckBox("Residuals")
        self.residuals.setToolTip("Show the residual of B2.5 and the "
                                  "post-processed one")
        save = QtWidgets.QPushButton("Save plots…")
        save.setToolTip("Both plots as png, jpg, eps, pdf or svg")
        save.clicked.connect(lambda *_: self.save_plots())
        export = QtWidgets.QPushButton("Export data…")
        export.setToolTip("The values of both plots: CSV, text, netCDF or "
                          "HDF5")
        export.clicked.connect(lambda *_: self.export_data())
        self.buttons = (save, export)
        top = self.top = QtWidgets.QGridLayout()
        row = [("Quantity", self.quantity), ("Species", self.species),
               ("Area type", self.areatype), ("Area at", self.areaend),
               ("Radial coordinate", self.coord),
               ("Poloidal distance", self.distance), ("", self.smoothing),
               ("", self.residuals), ("", save), ("", export)]
        for k, (text, w) in enumerate(row):
            label = QtWidgets.QLabel(text)
            top.addWidget(label, 0, k)
            top.addWidget(w, 1, k)
            top.setColumnStretch(k, 1)
            shrinkable(label, w)
        self.radial = PlotView(controller)
        self.poloidal = PlotView(controller)
        self.messages = [self.radial.below, self.poloidal.below]
        self.radial.equation.reserve = plots.all_texts("radial")
        self.poloidal.equation.reserve = plots.all_texts("poloidal")
        plots_ = QtWidgets.QGridLayout()
        for k, view in enumerate((self.radial, self.poloidal)):
            view.clicked.connect(self._open)
            plots_.addWidget(view.equation, 0, k, Qt.AlignLeft | Qt.AlignTop)
            plots_.addWidget(view.canvas, 1, k)
            plots_.addWidget(view.below, 2, k, Qt.AlignLeft | Qt.AlignTop)
        self.notes = QtWidgets.QLabel()
        self.notes.setWordWrap(True)
        self.notes.setProperty("muted", True)
        shrinkable(self.notes)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addLayout(plots_, 1)
        lay.addWidget(self.notes)
        for w in (self.quantity, self.areatype, self.areaend, self.coord,
                  self.distance):
            w.currentIndexChanged.connect(self._changed)
        self.species.changed.connect(self._changed)
        self.smoothing.toggled.connect(lambda *_: self.draw())
        self.residuals.toggled.connect(lambda *_: self.draw())
        self.scale_parts(1.0)
        self.scaled()

    def views(self):
        return [self.radial, self.poloidal]

    def scale_parts(self, k):
        self.top.setContentsMargins(0, 0, 0, round(GAP * k))

    def opened(self):
        return self.detail

    # ------------------------------------------------------------ setup
    def set_file(self, bf, rhop):
        """Choices of the run: the quantities balance.nc has, its species,
        rho poloidal only with a psi map."""
        for w in (self.quantity, self.coord):
            w.blockSignals(True)
        model = self.quantity.model()
        for i, (key, _) in enumerate(terms.QUANTITIES):
            why = terms.available(bf, key)
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

    def level(self):
        return style.SMOOTH if self.smoothing.isChecked() else 0

    def _changed(self, *_):
        self._enable()
        self.refresh()

    # ---------------------------------------------------------- results
    def refresh(self):
        """The balance of the volume again (new volume or options)."""
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
                               o.areaend, self.controller.vol.reverse)

    def draw(self):
        if self.result is None:
            return
        res = self.residuals.isChecked()
        self.radial.show_panel(plots.radial(
            self.result, self.terms, self.coord.currentData(), res,
            self.level(), self.area_text()))
        self.poloidal.show_panel(plots.poloidal(
            self.result, self.terms, self.distance.currentData(), res,
            self.level(), self.area_text()))
        if self.detail is not None and self.detail.isVisible():
            self.detail.refresh()

    def _open(self, key):
        """Third-level window with the decomposition of a line (one at a
        time)."""
        if self.detail is None:
            self.detail = DetailWindow(self.controller, self, 3)
        self.detail.set_key(key)

    def apply_theme(self):
        self.restyle()
        self.draw()

    def panels(self):
        return [v.panel for v in (self.radial, self.poloidal)
                if v.panel is not None]

    def stem(self):
        return "balance_" + (self.quantity.currentData() or "")

    def result_unit(self):
        return self.result.unit if self.result is not None else ""

    def meta(self):
        c = self.controller
        return [("run", c.rundir()), ("volume", c.describe()),
                ("quantity", self.quantity.currentText()),
                ("species", self.species.toolTip()
                 if self.species.isEnabled() else "-"),
                ("area type", self.areatype.currentText()),
                ("area at", self.areaend.currentText()),
                ("smoothing", "light" if self.level() else "none")]

    def closeEvent(self, event):
        if self.detail is not None:
            self.detail.close()
        self.controller.closed()
        super().closeEvent(event)


class DetailWindow(Output, Scaled, QtWidgets.QWidget):
    """Level 3: the decomposition of a line of the balance window; level
    4: the terms (EIRENE: strata) of a group of sources."""

    def __init__(self, controller, owner, level):
        super().__init__(owner, Qt.Tool)
        self.controller, self.owner, self.level = controller, owner, level
        self.key, self.child, self.title = None, None, ""
        self.view = PlotView(controller, column=True)
        self.view.equation.reserve = plots.all_texts("parts")
        self.view.clicked.connect(self._clicked)
        self.view.hovered.connect(self._hovered)
        self.tip = EquationTip()
        self.show_total = QtWidgets.QCheckBox("Show total")
        self.show_total.setToolTip("The sum of the lines (black)")
        self.show_total.toggled.connect(lambda *_: self.refresh())
        self.show_eq = QtWidgets.QCheckBox("Show equation term")
        self.show_eq.setToolTip("The equation of the term under the mouse "
                                "(line or legend entry), near the mouse")
        self.show_eq.toggled.connect(lambda on: on or self.tip.hide())
        save = QtWidgets.QPushButton("Save plot…")
        save.setToolTip("The plot as png, jpg, eps, pdf or svg")
        save.clicked.connect(lambda *_: self.save_plots())
        export = QtWidgets.QPushButton("Export data…")
        export.setToolTip("The values of the plot: CSV, text, netCDF or "
                          "HDF5")
        export.clicked.connect(lambda *_: self.export_data())
        self.buttons = (save, export)
        b = self.balance()                  # buttons as wide as there
        self.button = b.buttons[0].width() * (b._width or b.width()) / max(
            b.width(), 1)
        top = self.top = QtWidgets.QHBoxLayout()   # as the balance window
        top.addWidget(self.show_total)
        top.addWidget(self.show_eq)
        top.addStretch(1)
        top.addWidget(save)
        top.addWidget(export)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.view.equation, 0, Qt.AlignLeft | Qt.AlignTop)
        lay.addWidget(self.view.canvas, 1)
        self.scale_parts(1.0)
        self.scaled()

    def views(self):
        return [self.view]

    def scale_parts(self, k):
        self.top.setContentsMargins(0, 0, 0, round(GAP * k))
        for b in self.buttons:
            b.setFixedWidth(round(self.button * k))

    def opened(self):
        return self.child

    def balance(self):
        w = self.owner
        while not isinstance(w, BalanceWindow):
            w = w.owner
        return w

    def set_key(self, key):
        self.key = key
        if self.child is not None:
            self.child.close()
        self.refresh()
        self.prepare()
        _place(self, self.owner, 60, 60)
        self.show()
        self.raise_()

    def refresh(self):
        b = self.balance()
        if b.result is None or self.key is None:
            return
        if self.level == 3:
            panel = plots.decomposition(b.result, b.terms, self.key,
                                        b.coord.currentData(),
                                        b.distance.currentData(), b.level())
        else:
            try:
                panel = plots.members(b.result, b.terms, self.key,
                                      b.coord.currentData(),
                                      b.distance.currentData(), b.level(),
                                      self.controller.strata)
            except KeyError:            # the group is gone (new quantity)
                self.close()
                return
        self.setWindowTitle("Parallel balance — " + panel.title)
        self.title = panel.title
        if not self.show_total.isChecked():
            panel.series = [s for s in panel.series if not s.total]
        self.view.show_panel(panel)
        if self.child is not None and self.child.isVisible():
            self.child.refresh()

    def _hovered(self, series, point):
        """The equation of the line under the mouse near it, if asked."""
        parts = None
        if self.show_eq.isChecked() and series is not None:
            parts = equations.of_series(self.balance().terms.quantity,
                                        series.term)
        if parts is None:
            self.tip.hide()
            return
        self.tip.show_at(series.label, parts, point,
                         self.font().pointSizeF())

    def hideEvent(self, event):
        self.tip.hide()
        super().hideEvent(event)

    def _clicked(self, key):
        if key[0] == "stratum":
            self.controller.highlight_stratum(key[1])
            return
        if self.level == 3:
            if self.child is None:
                self.child = DetailWindow(self.controller, self, 4)
            self.child.set_key(key)

    def apply_theme(self):
        self.restyle()
        self.view.redraw()
        if self.child is not None and self.child.isVisible():
            self.child.apply_theme()

    def panels(self):
        return [self.view.panel] if self.view.panel is not None else []

    def stem(self):
        return "balance_" + re.sub(r"[^A-Za-z0-9]+", "_",
                                   self.title).strip("_").lower()

    def result_unit(self):
        r = self.balance().result
        return r.unit if r is not None else ""

    def meta(self):
        return self.balance().meta() + [("plot", self.title)]

    def closeEvent(self, event):
        if self.child is not None:
            self.child.close()
        if self.level == 4:
            self.controller.highlight_stratum(None)
        super().closeEvent(event)


def screen_room(win, ref):
    """Keep win inside the available area of the screen of ref."""
    screen = ref.screen() or QtGui.QGuiApplication.primaryScreen()
    if screen is None:
        return
    g = screen.availableGeometry()
    w, h = min(win.width(), g.width()), min(win.height(), g.height())
    win.resize(w, h)
    x = min(max(win.x(), g.x()), g.x() + g.width() - w)
    y = min(max(win.y(), g.y()), g.y() + g.height() - h)
    win.move(x, y)

