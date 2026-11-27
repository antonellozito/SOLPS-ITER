"""Neutrals, the third part of the Balances tab: the particles of the
EIRENE neutrals of an element in tables (neutrals.py). The ionisation
(balance.nc alone): rows the birth places and the sputtered particles,
columns the regions and Total; a number puts its source on the 2D plot.
The balance (all the neutrals): the sources and the sinks (ionised in each
region, absorbed, pumped, deposited), the residual under it. The fate
(with the pumped fluxes by stratum of fort.44): what the neutrals of each
birth place become. A row makes its surfaces glow (the gas puff a
diamond), a column (an Ionised row) outlines its region, the cell, row or
column chosen framed; an empty cell or place takes the map away; Draw
region adds a column to the ionisation."""

import csv
import os
import re
import textwrap

import numpy as np
from matplotlib.path import Path

from ...qt import QtCore, QtGui, QtWidgets, Qt
from .. import theme
from ..scaling import squeezable
from ..tools.sections import _button
from . import neutrals, style
from .section import combo

VALUES = (("total", "% of all the ionisation"),
          ("row", "% of each source"),
          ("abs", "Atoms per second (a molecule counts its atoms)"))
FATE_VALUES = {"total": "% of all the neutrals launched",
               "row": "% of those launched by each source",
               "abs": "atoms per second"}
VISIBLE = 5                     # value columns shown without scrolling
WRAP = 18                       # characters of a row name line
SHADE = 0.6                     # strongest cell colour over the base
POWER = 0.33                    # colour as the value to this power (between
#                                 linear, 1, and logarithmic)
GAP = 10                        # pixels above the title of the balance
POSITIVE, NEGATIVE = "#0072bd", "#d95319"   # sources, sinks
DRAWN = "Drawn region"
MARK = 3                        # pixels: the frame of the cells chosen
GROUPS = {"recycling": "born", "puff": "born", "recombination": "born",
          "source": "born", "deposited": "pumped"}    # lines between groups
LINE = 2                        # pixels of the lines between groups
ION, BAL, FATE = "ionisation", "balance", "fate"


def _short(v):
    """1.6e22 for 1.6e+22, 0 for 0."""
    return "0" if v == 0 else ("%.2e" % v).replace("e+", "e")


class NeutralsTool:
    """The Neutrals part of a BalanceTool (its tab): its section, the
    Origin of the run (also the maps of the Final state)."""

    def __init__(self, balance):
        self.balance, self.tab = balance, balance.tab
        self.tip = ""                   # of the Neutrals tab
        self.origin = self.run = self.path = None
        self.section = None
        self.row = None                 # (ION or BAL, row name) chosen
        self.column = None              # region (column of the ionisation)
        self.mapped = None              # (key, region or None) on the plot
        self.drawn = None               # cells of the region drawn
        self.drawing = False
        self.cell = None                # (table, row name or None, column
        #                                 or None) clicked: framed
        self.tab.tools.bar.changed.connect(self._bar)

    def _bar(self):
        """Draw region cancelled when the polygon mode goes off."""
        if self.tab.tools.bar.mode != "polygon" and self.drawing:
            self.drawing = False
            self._sync()

    def _sync(self):
        """Draw region highlighted while drawing."""
        if self.section is None:
            return
        b = self.section.draw_button
        b.blockSignals(True)
        b.setChecked(self.drawing)
        b.blockSignals(False)

    # ------------------------------------------------------------- run
    def set_run(self, run, path, why):
        """A new run: nothing kept; the tip of the tab."""
        self.close()
        if self.origin is not None:
            self.origin.close()
        self.origin, self.run, self.path = None, run, path
        self.drawn = self.row = self.column = self.mapped = None
        self.cell = None
        self.tip = "The neutrals of each element: where they are born, " \
            "where they are ionised, absorbed or pumped (balance.nc by " \
            "stratum, fort.44)" if path else why

    def get(self):
        """The Origin of the run (None without balance.nc)."""
        if self.origin is None and self.path is not None:
            try:
                self.origin = neutrals.Origin(self.run, self.path)
            except (OSError, KeyError, ValueError, IndexError) as err:
                self.tab.status.emit("Neutrals: cannot read balance.nc "
                                     "(%s)" % err)
                self.path = None
        return self.origin

    def quantities(self):
        """The maps of the Final state."""
        o = self.get()
        return o.quantities() if o is not None else []

    def field(self, name, ops=()):
        o = self.get()
        return o.field(name, ops) if o is not None else None

    # ------------------------------------------------------- open, close
    def open(self):
        """The tables (the Neutrals tab; as they were left if they were);
        why not ("" if open)."""
        b = self.balance
        if self.section is not None:
            b.page.show(self.section)
            self.show_map()
            return ""
        o = self.get()
        if o is None or o.why or not o.elements:
            why = "Neutrals: " + (o.why if o is not None and o.why else
                                  "no neutral sources in balance.nc")
            self.tab.status.emit(why)
            return why
        if not b._load():               # the grid for the faces
            return "Neutrals: cannot read balance.nc"
        self.tab.tools.bar.set_mode(None)
        self.section = NeutralsSection(self)
        b.page.show(self.section)
        if o.f44 is None:
            self.tab.status.emit("Neutrals: no fort.44 of the same strata, "
                                 "the ionisation alone")
        self.update()
        return ""

    def hide(self):
        """Another tab: the tables kept (hidden by the page), their
        drawings and map off the plot (the map chosen kept)."""
        if self.drawing:
            self.drawing = False
            self.tab.tools.bar.set_mode(None)
            self._sync()
        for key in ("nbirth", "nregion", "npuff"):
            self.balance._remove(key)
        q = self.tab.wanted
        if q is not None and q.source == "neutrals" and "." in q.name:
            self.tab._chosen(None)

    def close(self):
        """The section, its map and its drawings go."""
        self.drawing = False
        for key in ("nbirth", "nregion", "npuff"):
            self.balance._remove(key)
        self.clear_map()
        if self.section is not None:
            self.balance.page.drop(self.section)
        self.section = None

    def set_shown(self, on):
        """The Balances tab shown again: the map back (after the tab has
        cleared its plot)."""
        if on and self.section is not None and \
                self.balance.page.section is self.section:
            QtCore.QTimer.singleShot(0, self.show_map)

    # ----------------------------------------------------------- choice
    def choose(self, row=None, column=None, mapped=None):
        """A row ((table, name)), a region column, a source to map (key of
        the ionisation table)."""
        if row is not None:
            self.row = row
        if column is not None:
            self.column = column
        if mapped is not None:
            self.mapped = mapped
        self.update()

    def element(self):
        return self.section.element.currentData()

    def process(self):
        return self.section.process.currentData()

    def tables(self):
        """(ionisation, balance, fate) of the element."""
        o, el = self.origin, self.element()
        extra = [(DRAWN, self.drawn)] if self.drawn is not None else []
        return o.ionisation(el, self.process(), extra), \
            o.balance(el) if o.f44 is not None else None, o.fate(el)

    def update(self):
        """The tables and the map again."""
        if self.section is None:
            return
        ion, bal, fate = self.tables()
        names = {(ION, r[0]) for r in ion["rows"]} | (
            {(BAL, r[0]) for r in bal["rows"]} if bal else set()) | (
            {(FATE, r[0]) for r in fate["rows"]} if fate else set())
        if self.row not in names:
            self.row = None
        if self.mapped is not None and self.mapped[0] not in {
                r[3] for r in ion["rows"]}:
            self.clear_map()            # not there for this element
        if self.column is not None and self.column > len(ion["columns"]):
            self.column = None
        self.section.show(ion, bal, fate)
        self.show_map()

    def _chosen_row(self):
        """The Row (or region index of an Ionised row) chosen, or None."""
        if self.row is None or self.section is None:
            return None
        table, name = self.row
        data = {ION: self.section.ion, BAL: self.section.bal,
                FATE: self.section.fate}[table]
        if data is None:
            return None
        return next((r[2] for r in data["rows"] if r[0] == name), None)

    def show_map(self):
        """The source whose number was clicked on the 2D plot, the
        surfaces of the row chosen glowing (the gas puff a diamond), the
        region chosen outlined."""
        if self.section is None or not self.balance.shown:
            return
        from .picker import ZORDER
        o, b, el = self.origin, self.balance, self.element()
        if self.mapped is not None:
            q = o.describe(self.mapped[0], el, self.process(),
                           self.mapped[1])
            w = self.tab.wanted
            if w is None or w.name != q.name:
                self.tab._chosen(q)
        for key in ("nbirth", "npuff"):
            b._remove(key)
        row = self._chosen_row()
        if isinstance(row, neutrals.Row):
            segs = list(b._segments(sorted(set(row.faces)))) if \
                row.faces else []
            if row.walls and o.f44 is not None:
                segs += list(o.f44.walls()[row.walls])
            if segs:
                b._lines("nbirth", np.array(segs), style.STRATUM, 4.0,
                         ZORDER + 0.5, strong=True)
            pts = np.array(o.puffs(row, el)) if row.points else []
            if len(pts):
                ln, = self.tab.plot.ax.plot(
                    pts[:, 0], pts[:, 1], linestyle="none",
                    marker="D", markersize=11,
                    color=theme.rgb(style.STRATUM), markeredgecolor="white",
                    markeredgewidth=1.2, zorder=ZORDER + 1)
                ln.set_path_effects(style.glow(5.0, style.STRATUM,
                                               on_map=True))
                b.artists["npuff"] = [ln]
            elif row.kind == "puff":
                self.tab.status.emit("Neutrals: the position of the gas puff "
                                     "is not known (an EIRENE surface source "
                                     "in eirene.input.json)")
        b._remove("nregion")
        cells = self._cells(self.column)
        if cells is not None:           # the whole outline of the region
            g = b.grid
            inner = cells & (np.arange(len(cells)) < g.nCi)
            edge = np.flatnonzero(inner[g.fc[:, 0]] != inner[g.fc[:, 1]])
            b._lines("nregion", b._segments(edge), style.colour("source"),
                     2.0)
        self.tab.canvas.draw_idle()

    def clear_map(self):
        """No source on the plot (an empty cell or place clicked)."""
        self.mapped = None
        q = self.tab.wanted
        if q is not None and q.source == "neutrals" and "." in q.name:
            self.tab._chosen(None)

    def _cells(self, column):
        """Cells (nCv,) of a column, None for the total or none chosen."""
        regions = self.origin.regions
        if column is None:
            return None
        if column < len(regions):
            return regions[column][1]
        if column == len(regions) and self.drawn is not None:
            return self.drawn
        return None

    def draw_region(self, on=True):
        """Draw region: a polygon on the plot (take); off again:
        cancelled."""
        self.drawing = bool(on)
        self.tab.tools.bar.set_mode("polygon" if on else None)
        self._sync()
        if on:
            self.tab.status.emit("Neutrals: click the corners of the "
                                 "region, close it on the first corner")

    def take(self, pts):
        """The polygon drawn, if Draw region asked for it: its cells (by
        their centres) a column of the ionisation; True if taken."""
        if not self.drawing or self.section is None:
            return False
        self.drawing = False
        self._sync()
        self.tab.tools.bar.set_mode(None)
        bf = self.origin.bf
        xy = np.column_stack((bf.raw("cvX"), bf.raw("cvY"))).astype(float)
        inside = Path(np.asarray(pts, float)).contains_points(xy) & \
            (self.origin.vol > 0)
        self.tab.tools.bar._draw([])
        if not inside.any():
            self.tab.status.emit("Neutrals: no cell in the region")
            return True
        self.drawn = self.origin.drawn = inside
        self.choose(column=len(self.origin.regions))
        return True

    def apply_theme(self):
        if self.section is not None:
            self.section.recolour()
            self.show_map()


def _line(painter, rect, colour):
    painter.save()
    pen = QtGui.QPen(colour)
    pen.setWidth(LINE)
    painter.setPen(pen)
    painter.drawLine(rect.topLeft(), rect.topRight())
    painter.restore()


class Lines(QtWidgets.QStyledItemDelegate):
    """Cells with a thicker line above the first row of a group."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.starts = set()
        self.marked = set()             # (row, column) framed

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.row() in self.starts:
            _line(painter, option.rect,
                  option.palette.color(QtGui.QPalette.Text))
        if (index.row(), index.column()) in self.marked:
            painter.save()
            pen = QtGui.QPen(QtGui.QColor(theme.rgb(style.STRATUM)), MARK)
            pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(MARK // 2, MARK // 2,
                                                  -(MARK + 1) // 2,
                                                  -(MARK + 1) // 2))
            painter.restore()


class Header(QtWidgets.QHeaderView):
    """The row names, with the lines of Lines."""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.starts = set()
        self.setSectionsClickable(True)

    def paintSection(self, painter, rect, index):
        super().paintSection(painter, rect, index)
        if index in self.starts:
            _line(painter, rect, self.palette().color(QtGui.QPalette.Text))


class Table(QtWidgets.QTableWidget):
    """A table of the section: VISIBLE value columns share its width, more
    scroll sideways under the row names, which stay; lines between the
    groups of rows; empty() on a click where there is no cell."""

    empty = QtCore.Signal()

    def __init__(self, tip, parent=None):
        super().__init__(parent)
        self.setVerticalHeader(Header(Qt.Vertical, self))
        self.setItemDelegate(Lines(self))
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Fixed)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.setToolTip(tip)
        self.columns = []               # the headers, wrapped by fit

    def mousePressEvent(self, event):
        if not self.indexAt(event.position().toPoint()).isValid():
            self.empty.emit()
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()

    def fit(self):
        n = self.columnCount()
        if not n:
            return
        room = self.width() - self.verticalHeader().width() - \
            2 * self.frameWidth()
        w = max(room // min(n, VISIBLE), 24)
        for c in range(n):
            self.setColumnWidth(c, w)
        chars = max(4, (w - 8) // max(self.horizontalHeader().fontMetrics()
                                      .averageCharWidth(), 1))
        self.setHorizontalHeaderLabels(["\n".join(textwrap.wrap(c, chars))
                                        or c for c in self.columns])
        bar = self.horizontalScrollBar().sizeHint().height() if \
            n > VISIBLE else 0
        # the header as tall as its titles just wrapped (its height is
        # updated only later), so that no row is scrolled out of sight
        self.setFixedHeight(self.horizontalHeader().sizeHint().height() + sum(
            self.rowHeight(i) for i in range(self.rowCount())) + bar +
            2 * self.frameWidth())
        self.verticalScrollBar().setValue(0)    # from the first row

    def fill(self, rows, kinds, cols, text, values, bold):
        """Rows (names, kinds for the lines), columns, the text and the
        value (for the colours) of each cell, bold cells."""
        self.blockSignals(True)
        self.clear()
        self.setRowCount(len(rows))
        self.setColumnCount(len(cols))
        self.setVerticalHeaderLabels(["\n".join(textwrap.wrap(r, WRAP)) or r
                                      for r in rows])
        self.columns = list(cols)       # headers wrapped to the width
        for i in range(len(rows)):
            for j in range(len(cols)):
                item = QtWidgets.QTableWidgetItem(text[i][j])
                item.setTextAlignment(Qt.AlignCenter)
                if bold[i][j]:
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.setItem(i, j, item)
        group = [GROUPS.get(k, k) for k in kinds]
        starts = {i for i in range(1, len(group)) if group[i] != group[i - 1]}
        self.verticalHeader().starts = self.itemDelegate().starts = starts
        self.values = values
        self.recolour()
        self.blockSignals(False)
        self.resizeRowsToContents()
        self.fit()

    def recolour(self):
        """Cells coloured by the size of their value to the power POWER
        (blue sources, orange sinks), the last row not; the text black."""
        v = getattr(self, "values", None)
        if v is None or not len(v):
            return
        body = v[:-1]
        top = float(np.nanmax(np.abs(body))) if np.isfinite(body).any() \
            else 0.0
        base = np.array(self.palette().color(QtGui.QPalette.Base)
                        .getRgbF()[:3])
        for i in range(v.shape[0] - 1):
            for j in range(v.shape[1]):
                item, x = self.item(i, j), v[i, j]
                if item is None or top <= 0 or not np.isfinite(x):
                    continue
                a = SHADE * min(abs(x) / top, 1.0) ** POWER
                accent = np.array(QtGui.QColor(theme.rgb(
                    POSITIVE if x >= 0 else NEGATIVE)).getRgbF()[:3])
                item.setBackground(QtGui.QColor.fromRgbF(
                    *((1.0 - a) * base + a * accent)))

    def mark(self, cells):
        """The cells chosen ((row, column)) framed."""
        self.itemDelegate().marked = set(cells)
        self.viewport().update()


class NeutralsSection(QtWidgets.QWidget):
    """Element, process and values, Draw region and Export; the ionisation
    table; the balance table and its residual."""

    def __init__(self, tool, parent=None):
        super().__init__(parent)
        self.tool, o = tool, tool.origin
        self.ion = self.bal = self.fate = None
        self.element = combo([(e, e) for e in o.elements],
                             "Element whose neutrals are shown")
        self.process = combo([(k, t) for k, t, _ in neutrals.PROCESSES],
                             "Collisions whose ionisation fills the "
                             "ionisation table and the map: atoms "
                             "(ionisation), molecules (negative where they "
                             "take ions), molecular ions, or all; the "
                             "balance is that of all the neutrals")
        self.values = combo(VALUES, "Values of the ionisation table: in "
                            "percent of all the ionisation, of the "
                            "ionisation of each source, or as they are; of "
                            "the fate: in percent of all the neutrals "
                            "launched, of those of each source, or as they "
                            "are")
        for c in (self.element, self.process, self.values):
            c.currentIndexChanged.connect(lambda *_: tool.update())
        form = QtWidgets.QGridLayout()
        form.addWidget(QtWidgets.QLabel("Element"), 0, 0)
        form.addWidget(self.element, 0, 1)
        self.draw_button = _button(
            "Draw region", "A region drawn on the plot as one more column "
            "of the ionisation (the cells whose centres are inside); "
            "highlighted while drawing, a click again cancels",
            tool.draw_region, checkable=True)
        form.addWidget(self.draw_button, 0, 2)
        form.addWidget(QtWidgets.QLabel("Process"), 1, 0)
        form.addWidget(self.process, 1, 1, 1, 2)
        form.addWidget(QtWidgets.QLabel("Values"), 2, 0)
        form.addWidget(self.values, 2, 1)
        form.addWidget(_button("Export…", "The tables as a CSV file (the "
                               "values shown)", self.export), 2, 2)
        form.setColumnStretch(1, 1)
        self.ion_table = Table(
            "Particles the plasma gets from the neutrals of each source "
            "(balance.nc), in each region; Total: their sum. Click a "
            "number: its source on the plot; a row: its surfaces glow; a "
            "column (or a region on the plot): its outline")
        self.bal_table = Table(
            "The particles of all the neutrals of the element: sources "
            "(launched) positive, sinks (ionised, absorbed, pumped, "
            "deposited) negative. Click a row: its surfaces glow (an "
            "Ionised row: its region)")
        self.fate_table = Table(
            "What the neutrals of each birth place become (its strata; "
            "Sputtered: the strata of the other elements): launched by the "
            "source, sputtered in these strata, ionised in the regions, "
            "absorbed, pumped, deposited, the residual. Click a row: its "
            "surfaces glow; a number of Ionised: its source on the plot")
        self.fate_table.cellClicked.connect(
            lambda r, c: self._pick(FATE, r, c, cell=True))
        self.fate_table.verticalHeader().sectionClicked.connect(
            lambda r: self._pick(FATE, r))
        self.ion_table.cellClicked.connect(
            lambda r, c: self._pick(ION, r, c, cell=True))
        self.ion_table.verticalHeader().sectionClicked.connect(
            lambda r: self._pick(ION, r))
        self.ion_table.horizontalHeader().sectionClicked.connect(
            lambda c: self._pick(ION, None, c))
        self.bal_table.cellClicked.connect(lambda r, c: self._pick(BAL, r))
        self.bal_table.verticalHeader().sectionClicked.connect(
            lambda r: self._pick(BAL, r))
        for t in (self.ion_table, self.bal_table, self.fate_table):
            t.empty.connect(tool.clear_map)
        self.residual = QtWidgets.QLabel()
        self.residual.setWordWrap(True)
        self.residual.setProperty("muted", True)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.addLayout(form)
        lay.addWidget(self._title("Neutrals ionisation sources"))
        lay.addWidget(self.ion_table)
        self.bal_title = self._title("Total neutrals balance")
        lay.addSpacing(GAP)
        lay.addWidget(self.bal_title)
        lay.addWidget(self.bal_table)
        lay.addWidget(self.residual)
        self.fate_title = self._title("Fate of the neutrals of each birth "
                                      "place")
        lay.addSpacing(GAP)
        lay.addWidget(self.fate_title)
        lay.addWidget(self.fate_table)
        squeezable(self)

    @staticmethod
    def _title(text):
        label = QtWidgets.QLabel(text)
        label.setProperty("bold", True)
        label.setWordWrap(True)
        return label

    def dispose(self):
        pass

    def mousePressEvent(self, event):
        """A click on an empty place of the section: no source plotted."""
        self.tool.clear_map()
        super().mousePressEvent(event)

    def _pick(self, table, r=None, c=None, cell=False):
        """A row (of table) or a column; a cell of the ionisation with a
        number: its source on the plot, an empty one takes it away; an
        Ionised row of the balance: its region."""
        tool = self.tool
        if table == FATE:               # no region
            tool.column = None
            name, _, _, key = self.fate["rows"][r]
            ionised = self.fate["columns"].index("Ionised")
            if cell and c == ionised and self.fate["values"][r, c]:
                tool.column = None
                tool.cell = (FATE, name, c)
                tool.choose((FATE, name), None, (key, None))
            else:
                if cell:
                    tool.clear_map()
                tool.cell = (FATE, name, None)
                tool.choose((FATE, name))
            return
        if table == BAL:
            if r >= len(self.bal["rows"]):      # Residual: nothing to show
                tool.clear_map()
                tool.row = tool.column = tool.cell = None
                tool.update()
                return
            name, kind, what = self.bal["rows"][r][:3]
            o = tool.origin
            tool.cell = (BAL, name, None)
            if kind == "ionised":       # all the neutrals, in the region
                tool.choose((BAL, name), what, (neutrals.TOTAL, what))
            elif isinstance(what, neutrals.Row) and what in o.sources and \
                    kind != "sputtered":    # a birth place: its source
                tool.column = None
                tool.choose((BAL, name), None,
                            (str(o.sources.index(what)), None))
            else:                       # sputtered, sinks: no map
                tool.clear_map()
                tool.column = None
                tool.choose((BAL, name))
            return
        row = None if r is None else (ION, self.ion["rows"][r][0])
        tool.cell = (ION, None if row is None else row[1],
                     c if cell or r is None else None)
        # the region of the column clicked, none for a row or Total
        tool.column = c if c is not None and c < len(self.ion["columns"]) \
            else None
        if cell and r is not None:
            x = np.column_stack((self.ion["values"],
                                 self.ion["values"].sum(axis=1)))[r, c]
            if np.isfinite(x) and x != 0:
                region = c if c < len(self.ion["columns"]) else None
                key = self.ion["rows"][r][3]
                tool.choose(row, region, (key, region if key ==
                                          neutrals.TOTAL else None))
                return
            tool.clear_map()
        tool.choose(row, c if c is not None and
                    c < len(self.ion["columns"]) else None)

    # --------------------------------------------------------- display
    def _marks(self, table, rows, ncols):
        """The cells of table framed: the one clicked, or all those of the
        row or column clicked (nothing if it is not shown)."""
        cell = self.tool.cell
        if cell is None or cell[0] != table:
            return set()
        _, name, c = cell
        if name is None:
            return {(i, c) for i in range(len(rows))} if c is not None and \
                c < ncols else set()
        if name not in rows:
            return set()
        r = rows.index(name)
        return {(r, c)} if c is not None and c < ncols else \
            {(r, j) for j in range(ncols)}

    def _ion_shown(self, ion):
        """(rows, columns + Total) of the ionisation in the values chosen."""
        full = np.column_stack((ion["values"], ion["values"].sum(axis=1)))
        mode = self.values.currentData()
        if mode == "abs":
            return full
        with np.errstate(divide="ignore", invalid="ignore"):
            if mode == "row":
                return 100.0 * full / full[:, -1:]
            return 100.0 * full / full[-1, -1]

    def show(self, ion, bal, fate=None):
        """The tables of the element."""
        self.ion, self.bal, self.fate = ion, bal, fate
        self._show_fate(fate)
        absolute = self.values.currentData() == "abs"
        v = self._ion_shown(ion)
        rows = [r[0] for r in ion["rows"]]
        cols = list(ion["columns"]) + ["Total"]
        last = len(rows) - 1
        self.ion_table.fill(
            rows, [r[1] for r in ion["rows"]], cols,
            [["" if not np.isfinite(x) else _short(x) if absolute
              else "%.2f" % x for x in line] for line in v],
            np.column_stack((ion["values"], ion["values"].sum(axis=1))),
            [[i == last or j == len(cols) - 1 for j in range(len(cols))]
             for i in range(len(rows))])
        self.ion_table.mark(self._marks(ION, rows, len(cols)))
        for w in (self.bal_title, self.bal_table, self.residual):
            w.setVisible(bal is not None)
        if bal is None:
            return
        src = bal["sources"] or 1.0
        names = [b[0] for b in bal["rows"]]
        val = np.asarray(bal["values"], float)
        self.bal_table.fill(
            names + ["Residual"], [b[1] for b in bal["rows"]] + ["residual"],
            ["Atoms per second", "% of the sources"],
            [[_short(x), "%.2f" % (100.0 * x / src)] for x in val] +
            [[_short(bal["missing"]), "%.2f" % (100.0 * bal["missing"] /
                                                src)]],
            np.vstack((np.column_stack((val, val)),
                       [[bal["missing"]] * 2])),
            [[False, False]] * len(val) + [[True, True]])
        self.bal_table.mark(self._marks(BAL, names, 2))
        res = bal["missing"]
        self.residual.setText(
            "Residual (sources minus sinks): %s atoms/s, %.2g %% of the "
            "sources%s" % (_short(res), 100.0 * res / src,
                           ": the balance closes" if abs(res) <=
                           neutrals.QUIET * src else "; " +
                           self.tool.origin.why_missing(
                               self.element.currentData())))

    def _fate_shown(self, fate):
        """The fate in the values chosen: % of all the neutrals launched
        (the Total row), of those of each row, or atoms per second."""
        v = fate["values"]
        mode = self.values.currentData()
        if mode == "abs":
            return v
        out = v[:, :2].sum(axis=1)[:, None]
        with np.errstate(divide="ignore", invalid="ignore"):
            return 100.0 * v / (out if mode == "row" else out[-1, 0])

    def _show_fate(self, fate):
        for w in (self.fate_title, self.fate_table):
            w.setVisible(fate is not None)
        if fate is None:
            return
        absolute = self.values.currentData() == "abs"
        v = self._fate_shown(fate)
        rows = [r[0] for r in fate["rows"]]
        cols = fate["columns"]
        sign = np.array([1.0, 1.0] + [-1.0] * (len(cols) - 3) + [1.0])
        self.fate_table.fill(
            rows, [r[1] for r in fate["rows"]], cols,
            [["" if not np.isfinite(x) else _short(x) if absolute
              else "%.2f" % x for x in line] for line in v],
            fate["values"] * sign,
            [[i == len(rows) - 1 or j == len(cols) - 1
              for j in range(len(cols))] for i in range(len(rows))])
        self.fate_table.mark(self._marks(FATE, rows, len(cols)))

    def recolour(self):
        for t in (self.ion_table, self.bal_table, self.fate_table):
            t.recolour()

    def export(self):
        """The tables as CSV (the values shown)."""
        if self.ion is None:
            return
        settings = self.tool.tab.settings
        folder = settings.value("export_dir", os.getcwd())
        el = self.element.currentData()
        name = "neutrals_%s" % re.sub(r"\W+", "_", el)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export the neutrals", os.path.join(folder, name + ".csv"),
            "CSV (*.csv)")
        if not path:
            return
        settings.setValue("export_dir", os.path.dirname(path))
        with open(path, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(["Ionisation of %s, %s (%s)" % (
                el, self.process.currentText(), self.values.currentText())] +
                list(self.ion["columns"]) + ["Total"])
            for r, line in zip(self.ion["rows"], self._ion_shown(self.ion)):
                out.writerow([r[0]] + ["" if not np.isfinite(x) else
                                       "%.6g" % x for x in line])
            if self.bal is not None:
                src = self.bal["sources"] or 1.0
                out.writerow([])
                out.writerow(["Balance of %s" % el, "Atoms per second",
                              "% of the sources"])
                for b, x in zip(self.bal["rows"], self.bal["values"]):
                    out.writerow([b[0], "%.6g" % x, "%.6g" % (100 * x / src)])
                out.writerow(["Residual", "%.6g" % self.bal["missing"],
                              "%.6g" % (100 * self.bal["missing"] / src)])
            if self.fate is not None:
                out.writerow([])
                out.writerow(["Fate of the neutrals of %s (%s)" % (
                    el, FATE_VALUES[self.values.currentData()])] +
                    list(self.fate["columns"]))
                for r, line in zip(self.fate["rows"],
                                   self._fate_shown(self.fate)):
                    out.writerow([r[0]] + ["" if not np.isfinite(x) else
                                           "%.6g" % x for x in line])
