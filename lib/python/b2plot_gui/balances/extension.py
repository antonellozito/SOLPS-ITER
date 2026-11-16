"""The extension of a plot of the balance section, right of the column:
the decomposition of a line clicked there (level 3) and, over the legend of
that, the terms (EIRENE: strata) of a group of sources clicked in it
(level 4). Their plot boxes are as large as the one of the section plot
and level with it; the plots take the radial coordinate and the poloidal
distance of the section. The extension is drawn over the 2D plot, follows
its plot when the column scrolls and shrinks to stay in the window."""

import re

from ...qt import QtCore, QtGui, QtWidgets
from . import equations, plots
from .tip import EquationTip
from .views import Output, PlotView

GAP = 4                             # pixels from the column and the window
PAD = 6                             # pixels inside the frame
ROOM = 4                            # pixels between the text and the plot
LIFT = 10                           # pixels between the controls and the text


class DetailPanel(Output, QtWidgets.QWidget):
    """Level 3: the decomposition of a line of the section, with its
    explanation; level 4: the terms (EIRENE: strata) of a group of
    sources. Save plot, Export data and close over the plot; the equation
    of the line under the mouse is shown next to it. Placed by the
    extension (arrange)."""

    def __init__(self, ext, level, parent=None):
        super().__init__(parent)
        self.ext, self.level = ext, level
        self.section = ext.section
        self.controller = self.section.controller
        self.key, self.panel_title, self.active = None, "", False
        self.view = PlotView(self.controller, column=True)
        self.view.clicked.connect(self._clicked)
        self.view.hovered.connect(self._hovered)
        self.tip = EquationTip()
        save = QtWidgets.QPushButton("Save plot…")
        save.setToolTip("The plot as png, jpg, eps, pdf or svg")
        save.clicked.connect(lambda *_: self.save_plots())
        export = QtWidgets.QPushButton("Export data…")
        export.setToolTip("The values of the plot: CSV, text, netCDF or "
                          "HDF5")
        export.clicked.connect(lambda *_: self.export_data())
        close = QtWidgets.QToolButton()
        close.setText("✕")
        close.setToolTip("Close this plot" + (" and the one opened from it"
                                              if level == 3 else ""))
        close.clicked.connect(lambda *_: self.ext.close_level(self.level))
        self.controls = QtWidgets.QWidget(self)
        top = QtWidgets.QHBoxLayout(self.controls)
        top.setContentsMargins(0, 0, 0, 0)
        top.addStretch(1)
        for w in (save, export, close):
            top.addWidget(w)
        self.view.equation.setParent(self)
        self.view.equation.setVisible(level == 3)   # level 4: none
        self.view.canvas.setParent(self)
        self.hide()

    def arrange(self, width, controls, text, box):
        """Controls controls pixels high, the explanation (level 3) text
        pixels high under them, then the plot with a box box pixels wide;
        width: what is shown of it (its legend may be covered)."""
        v = self.view
        v.set_box(box)
        w, h = v.size_for(box)
        self.controls.setGeometry(0, 0, width, controls)
        v.equation.setContentsMargins(0, 0, 0, 0)
        v.equation.setGeometry(0, controls + LIFT, width, text)
        v.canvas.move(0, controls + LIFT + ROOM + text)
        self.resize(width, controls + LIFT + ROOM + text + h)

    def set_key(self, key):
        """The line key decomposed."""
        self.key, self.active = key, True
        self.show()
        self.refresh()

    def refresh(self):
        s = self.section
        if not self.active or s.result is None or self.key is None:
            return
        coord, distance = s.coord.currentData(), s.distance.currentData()
        if self.level == 3:
            panel = plots.decomposition(s.result, s.terms, self.key, coord,
                                        distance)
        else:
            try:
                panel = plots.members(s.result, s.terms, self.key, coord,
                                      distance, self.controller.strata)
            except KeyError:            # the group is gone
                self.ext.close_level(4)
                return
        self.panel_title = panel.title
        self.view.show_panel(panel)

    def close_panel(self):
        self.active, self.key = False, None
        self.view.pin(None)
        self.tip.hide()
        self.hide()
        if self.level == 4:
            self.controller.highlight_stratum(None)

    def _hovered(self, series, point):
        """The equation of the line under the mouse near it."""
        parts = None
        if series is not None:
            parts = equations.of_series(self.section.terms.quantity,
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
            self.ext.open(4, key)

    def panels(self):
        return [self.view.panel] if self.view.panel is not None else []

    def title(self):
        return self.controller.name + " — " + self.panel_title

    def stem(self):
        return "balance_" + re.sub(r"[^A-Za-z0-9]+", "_",
                                   self.panel_title).strip("_").lower()

    def result_unit(self):
        r = self.section.result
        return r.unit if r is not None else ""

    def meta(self):
        return self.section.meta() + [("plot", self.panel_title)]


class Extension(QtWidgets.QFrame):
    """Levels 3 and 4 opened from the plot of row, over host (the 2D tab)
    right of column: the plot boxes level with and as large as the one of
    the row (smaller only where the window has no room), level 4 over the
    legend of level 3; only the part beside the visible part of the scroll
    area of the column is shown."""

    def __init__(self, section, row, host, column, area):
        super().__init__(host)
        self.section, self.row, self.host = section, row, host
        self.column, self.area = column, area
        self.setObjectName("balanceExtension")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setAutoFillBackground(True)
        self.levels = [DetailPanel(self, 3, self), DetailPanel(self, 4, self)]
        self.hide()
        self._later = QtCore.QTimer(self)
        self._later.setSingleShot(True)
        self._later.setInterval(0)
        self._later.timeout.connect(self.place)
        self._watched = (row, column, area.viewport(), host)
        for w in self._watched:
            w.installEventFilter(self)
        area.verticalScrollBar().valueChanged.connect(self._later.start)

    WATCH = (QtCore.QEvent.Move, QtCore.QEvent.Resize, QtCore.QEvent.Show,
             QtCore.QEvent.Hide, QtCore.QEvent.LayoutRequest)

    def eventFilter(self, obj, event):
        if event.type() in self.WATCH:
            self._later.start()
        return False

    def shown(self):
        return [p for p in self.levels if p.active]

    # ------------------------------------------------------------ levels
    def open(self, level, key):
        """Level 3 (the level 4 of an earlier one goes) or 4 for the line
        key; the line clicked glows while it is shown."""
        source = self.row.view if level == 3 else self.levels[0].view
        if level == 3:
            self.levels[1].close_panel()
        source.pin(key)
        self.levels[level - 3].set_key(key)
        self.place()

    def close_level(self, level):
        """Closing level 3 closes level 4 too."""
        for p in self.levels[level - 3:]:
            p.close_panel()
        (self.row.view if level == 3 else self.levels[0].view).pin(None)
        self.place()

    def close_all(self):
        self.close_level(3)

    def refresh(self):
        for p in self.shown():
            p.refresh()
        if self.shown():
            self.place()

    def dispose(self):
        """The section goes: so does its extension."""
        self.close_all()
        for w in self._watched:
            w.removeEventFilter(self)
        self.area.verticalScrollBar().valueChanged.disconnect(
            self._later.start)
        self.deleteLater()

    # ---------------------------------------------------------- placing
    def place(self):
        """Right of the column, the plot boxes level with the one of the
        row and as large (smaller where the window has no room), the
        frame as large as its content, clipped to the scroll area of the
        column."""
        shown = self.shown()
        row, host = self.row, self.host
        if not shown or not row.isVisible():
            self.hide()
            return
        main = row.view
        canvas = main.canvas
        top_left = canvas.mapTo(host, QtCore.QPoint(0, 0))
        box = main.box_for(canvas.width(), canvas.height())
        x0 = self.column.mapTo(host, QtCore.QPoint(
            self.column.width(), 0)).x() + GAP
        room = host.width() - x0 - GAP - 2 * PAD
        v = self.levels[0].view
        left, right, _, _ = main.margins()
        legend = v.margins()[1] - right
        two = len(shown) == 2
        # widths: level 3 without its legend when level 4 covers it
        need = (2 if two else 1) * (left + box + right) + legend
        if need > room:
            box = max(40.0, box - (need - room) / (2 if two else 1))
        cut = round(left + box + right)
        full = v.size_for(box)[0]
        controls = max(p.controls.sizeHint().height() for p in shown)
        first = cut if two else full
        text = self.levels[0].view.equation.need(first)
        for p, width in zip(shown, (first, full)):
            p.arrange(width, controls, text, box)
        self.levels[0].move(PAD, PAD)
        if two:
            self.levels[1].move(PAD + cut, PAD)
            self.levels[1].raise_()
        width = 2 * PAD + (cut + full if two else full)
        height = 2 * PAD + self.levels[0].height()
        y0 = top_left.y() - PAD - controls - LIFT - ROOM - text
        self.setGeometry(x0, y0, width, height)
        port = self.area.viewport()
        top = port.mapTo(host, QtCore.QPoint(0, 0)).y()
        lo, hi = max(top, y0), min(top + port.height(), y0 + height)
        if hi <= lo:
            self.hide()
            return
        if lo == y0 and hi == y0 + height:
            self.clearMask()
        else:
            self.setMask(QtGui.QRegion(0, lo - y0, width, hi - lo))
        self.show()
        self.raise_()
