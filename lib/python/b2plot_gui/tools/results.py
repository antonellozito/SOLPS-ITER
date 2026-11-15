"""Results of the mouse tools in a small window over the main one (the
plot keeps its place), scaling with its size: a title and a summary, a
table in groups (cell inspector) or a small figure (profile along a line,
histogram) in the colours of the theme, with its options (colour, style,
width and markers of each curve, bins, axis limits, logarithmic axes,
grid; the wheel zooms, dragging moves the view), and the rows behind them
for Export (CSV)."""

import csv
import os
import re

from matplotlib import colors as mcolors
from matplotlib.figure import Figure

from ...b2plot import labels
from .. import theme
from ..output import printfig
from ..panels.glyphs import LineStyleChooser, MarkerChooser, WidthChooser
from ..panels.layers import ColorButton
from ..panels.plotarea import ScaledCanvas
from ..scaling import Navigator, Scaled
from ...qt import QtGui, QtWidgets, Qt

TABLE_SIZE, FIGURE_SIZE = (900, 640), (600, 560)    # first sizes (pixels)
PLOT_ASPECT = 0.75                  # height / width of the plot box (4:3)
HIST = "#4c72b0"                    # bars of a histogram at first


def _number(edit):
    try:
        return float(edit.text())
    except ValueError:
        return None


class FigureOptions(QtWidgets.QGroupBox):
    """Options of the small figure: a row per curve (colour, style, width,
    markers) or the bars of a histogram (colour, bins), then the axes
    (limits, empty: automatic; logarithmic; grid); changed() after each
    choice."""

    def __init__(self, changed, parent=None):
        super().__init__("Plot options", parent)
        self.changed = changed
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.grid = QtWidgets.QGridLayout()     # the curves or the bars
        self.grid.setColumnStretch(5, 1)
        axes = QtWidgets.QGridLayout()          # the axes, compact
        axes.setColumnStretch(6, 1)
        lay.addLayout(self.grid)
        lay.addLayout(axes)
        self.curves = []                # (name, colour, style, width, marker)
        self.bars = ColorButton(HIST)
        self.bars.changed.connect(lambda *_: changed())
        self.bins = QtWidgets.QSpinBox()
        self.bins.setRange(5, 500)
        self.bins.setValue(30)
        self.bins.setKeyboardTracking(False)
        self.bins.setToolTip("Bins of the histogram")
        self.bins.valueChanged.connect(lambda *_: changed())
        self.limits = []
        for _ in range(4):
            e = QtWidgets.QLineEdit()
            e.setValidator(QtGui.QDoubleValidator())
            e.setPlaceholderText("auto")
            e.editingFinished.connect(lambda: changed())
            self.limits.append(e)
        self.logx, self.logy = (QtWidgets.QCheckBox("log x"),
                                QtWidgets.QCheckBox("log y"))
        self.show_grid = QtWidgets.QCheckBox("grid")
        self.show_grid.setChecked(True)
        for w in (self.logx, self.logy, self.show_grid):
            w.toggled.connect(lambda *_: changed())
        for i, axis in enumerate("xy"):
            lo, hi = self.limits[2 * i:2 * i + 2]
            for c, w in enumerate((QtWidgets.QLabel(axis + " from"), lo,
                                   QtWidgets.QLabel("to"), hi,
                                   (self.logx, self.logy)[i])):
                axes.addWidget(w, i, c)
        axes.addWidget(self.show_grid, 1, 5)
        self.kind = None

    def set_curves(self, kind, lines):
        """The rows of a figure of this kind ("line": its lines, Line2D;
        "hist"), kept when the curves are the same."""
        names = [ln.get_label() if not ln.get_label().startswith("_") else
                 "Profile" for ln in lines] if kind == "line" else []
        if kind == self.kind and names == [c[0] for c in self.curves]:
            return
        self.kind = kind
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                if w not in (self.bars, self.bins):
                    w.deleteLater()
        self.curves = []
        for r, (name, ln) in enumerate(zip(names, lines)):
            row = (name, ColorButton(mcolors.to_hex(ln.get_color())),
                   LineStyleChooser("-", with_none=True), WidthChooser(1.5),
                   MarkerChooser("None"))
            row[1].changed.connect(lambda *_: self.changed())
            for w in row[2:]:
                w.currentIndexChanged.connect(lambda *_: self.changed())
            self.grid.addWidget(QtWidgets.QLabel(name), r, 0)
            for c, w in enumerate(row[1:], 1):
                self.grid.addWidget(w, r, c)
            self.curves.append(row)
        if kind == "hist":
            for c, w in enumerate((QtWidgets.QLabel("Bars"), self.bars,
                                   QtWidgets.QLabel("bins"), self.bins)):
                self.grid.addWidget(w, 0, c)
        for i in range(self.grid.count()):
            self.grid.itemAt(i).widget().show()
        for e in self.limits:
            e.clear()

    def apply(self, ax):
        """The choices on the axes drawn (the curves in order)."""
        lines = list(ax.lines)
        for (_, colour, style, width, marker), ln in zip(self.curves, lines):
            ln.set_gid(colour.color())
            ln.set_linestyle(style.currentData())
            ln.set_linewidth(width.value())
            ln.set_marker(marker.currentData())
        if self.kind == "hist":
            for p in ax.patches:
                p.set_gid(self.bars.color())
        ax.set_xscale("log" if self.logx.isChecked() else "linear")
        ax.set_yscale("log" if self.logy.isChecked() else "linear")
        x0, x1, y0, y1 = (_number(e) for e in self.limits)
        ax.set_xlim(left=x0, right=x1)
        ax.set_ylim(bottom=y0, top=y1)
        if self.show_grid.isChecked():
            ax.grid(True, alpha=0.3)
        else:
            ax.grid(False)


class LineEnds(QtWidgets.QGroupBox):
    """R, Z and the toroidal angle phi (degrees) of the two ends of a line
    cut; moved(coords) when one is changed."""

    def __init__(self, parent=None):
        super().__init__("Line", parent)
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setColumnStretch(7, 1)
        self.moved = None
        self.edits = []
        for r, end in enumerate(("Start", "End")):
            grid.addWidget(QtWidgets.QLabel(end), r, 0)
            for c, name in enumerate(("R (m)", "Z (m)", "phi (°)")):
                e = QtWidgets.QLineEdit()
                e.setValidator(QtGui.QDoubleValidator())
                e.setToolTip("%s of the %s of the line" % (name, end.lower()))
                e.editingFinished.connect(self._changed)
                grid.addWidget(QtWidgets.QLabel(name), r, 2 * c + 1)
                grid.addWidget(e, r, 2 * c + 2)
                self.edits.append(e)

    FORMATS = ("%.4f", "%.4f", "%g") * 2

    def set(self, coords, moved):
        """coords: R0, Z0, phi0, R1, Z1, phi1."""
        self.moved = moved
        for e, v, fmt in zip(self.edits, coords, self.FORMATS):
            e.blockSignals(True)
            e.setText(fmt % v)
            e.blockSignals(False)
        self._coords = tuple(float(v) for v in coords)

    def _changed(self):
        """The values typed; a field not changed keeps its value (not the
        rounded text)."""
        values = [old if e.text() == fmt % old else _number(e) for e, old,
                  fmt in zip(self.edits, self._coords, self.FORMATS)]
        if None in values or self.moved is None:
            return
        if any(abs(a - b) > 1e-12 for a, b in zip(values, self._coords)):
            self._coords = tuple(values)
            self.moved(self._coords)


class ResultsPanel(Scaled, QtWidgets.QWidget):
    """Hidden until a tool shows something; Close hides it again. It
    opens at the top right of parent the first time."""

    def __init__(self, settings, parent=None):
        super().__init__(parent, Qt.Tool)
        self.setWindowTitle("b2plot — results")
        self.settings = settings
        self.placed = False
        self.mode = None                # "table" or "figure", as sized
        self.header, self.rows = [], []
        self.draw = None
        self.title = QtWidgets.QLabel()
        self.title.setProperty("bold", True)
        self.title.setWordWrap(True)
        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.figure = Figure(figsize=(5.0, 2.6))
        self.canvas = ScaledCanvas(self.figure)
        self.canvas.setMinimumHeight(120)
        self.ax = self.figure.add_subplot(111)
        self.nav = Navigator(self.canvas, self.ax)
        self.options = FigureOptions(self._redraw)
        self.ends = LineEnds()
        export = QtWidgets.QPushButton("Export…")
        export.setToolTip("The values of the table or curve as a CSV file")
        export.clicked.connect(lambda *_: self.export())
        self.print_button = QtWidgets.QPushButton("Save plot")
        self.print_button.setToolTip("The plot as an image or vector file: "
                                     "format, resolution, colour space and "
                                     "theme")
        self.print_button.clicked.connect(lambda *_: self.print_figure())
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(lambda *_: self.hide())
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.title, 1)
        top.addWidget(self.print_button)
        top.addWidget(export)
        top.addWidget(close)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.text)
        lay.addWidget(self.ends)
        lay.addWidget(self.table, 1)
        lay.addWidget(self.canvas, 1)
        lay.addWidget(self.options)
        self.resize(*FIGURE_SIZE)
        self.scaled()
        self.hide()

    def canvases(self):
        return [self.canvas]

    def show_table(self, title, header, rows):
        self._set(title, "", header, rows, figure=False)
        self.table.clearSpans()
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.table.setColumnCount(len(header))
        self.table.setHorizontalHeaderLabels(header)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(
                    labels.any_to_plain(str(v))))
        self.table.resizeColumnsToContents()

    def show_groups(self, title, header, groups):
        """Groups of rows under a bold title row each; Export writes the
        group as the first column."""
        rows = [[g] + list(r) for g, rs in groups for r in rs]
        self._set(title, "", ["Group"] + list(header), rows, figure=False)
        t = self.table
        t.clearSpans()
        t.setColumnCount(len(header))
        t.setHorizontalHeaderLabels(header)
        t.setRowCount(sum(len(rs) + 1 for _, rs in groups))
        t.setWordWrap(True)
        i = 0
        for title_, rs in groups:
            item = QtWidgets.QTableWidgetItem(title_)
            bold = QtGui.QFont(t.font())
            bold.setBold(True)
            item.setFont(bold)
            t.setItem(i, 0, item)
            t.setSpan(i, 0, 1, len(header))
            i += 1
            for r in rs:
                for j, v in enumerate(r):
                    t.setItem(i, j, QtWidgets.QTableWidgetItem(str(v)))
                i += 1
        value = header.index("Value") if "Value" in header else -1
        h = t.horizontalHeader()
        for j in range(len(header)):        # all columns in the window
            h.setSectionResizeMode(j, QtWidgets.QHeaderView.Stretch
                                   if j == value else
                                   QtWidgets.QHeaderView.ResizeToContents)
        t.resizeRowsToContents()

    def show_figure(self, title, text, draw, header, rows, kind="line",
                    logx=False, line=None, moved=None):
        """draw(ax, options) makes the small figure (kind "line": curves,
        "hist": a histogram, at first on a logarithmic axis with logx);
        rows are what Export writes; line: R, Z, phi of the ends of a line
        cut, editable (moved(coords) after a change)."""
        self.draw = draw
        if line is not None:
            self.ends.set(line, moved)
        self.ends.setVisible(line is not None)
        self.ax.clear()
        draw(self.ax, self.options)
        new = kind != self.options.kind
        self.options.set_curves(kind, list(self.ax.lines))
        if kind == "hist" and new:
            self.options.logx.blockSignals(True)
            self.options.logx.setChecked(logx)
            self.options.logx.blockSignals(False)
        self._set(title, text, header, rows, figure=True)
        self._redraw()

    def _redraw(self):
        """The figure again with the options, its whole view the home of
        the mouse zoom."""
        if self.draw is None:
            return
        self.ax.clear()
        self.draw(self.ax, self.options)
        self.options.apply(self.ax)
        self.ax.set_box_aspect(PLOT_ASPECT)     # 4:3 in any window
        self.apply_theme()
        self.nav.set_home()

    def refresh_theme(self):
        if self.draw is not None:
            self.apply_theme()

    def apply_theme(self):
        """The small figure in the colours of the theme (each curve and
        bar in the colour chosen, its gid)."""
        ax, color = self.ax, theme.text()
        self.figure.set_facecolor(theme.figure_bg())
        ax.set_facecolor("#424242" if theme.is_dark() else "#ffffff")
        ax.tick_params(colors=color, which="both")
        for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
            item.set_color(color)
        for spine in ax.spines.values():
            spine.set_color(color)
        lines = list(ax.lines)
        for a in lines + list(ax.patches):     # gid: the colour chosen
            line = a in lines
            if a.get_gid() is None:
                a.set_gid(mcolors.to_hex(a.get_color() if line else
                                         a.get_facecolor()))
            (a.set_color if line else a.set_facecolor)(theme.rgb(a.get_gid()))
        legend = ax.get_legend()
        if legend is not None:           # again, with the new line colours
            legend = ax.legend(fontsize="small")
            legend.get_frame().set_facecolor(theme.figure_bg())
            for t in legend.get_texts():
                t.set_color(color)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _set(self, title, text, header, rows, figure):
        self.header, self.rows = list(header), list(rows)
        self.title.setText(title)
        self.text.setText(text)
        self.text.setVisible(bool(text))
        self.table.setVisible(not figure)
        if not figure:
            self.ends.hide()
        self.canvas.setVisible(figure)
        self.options.setVisible(figure)
        self.print_button.setVisible(figure)
        mode = "figure" if figure else "table"
        if mode != self.mode:           # the size of that content at first
            self.mode = mode
            self.rebase(*(FIGURE_SIZE if figure else TABLE_SIZE))
            if figure:                  # as wide, the plot box 4:3
                self.layout().activate()
                self.canvas.resize(self.canvas.size())
                self.figure.tight_layout()
                pos = self.ax.get_position()
                w = pos.width * self.canvas.width()
                h = FIGURE_SIZE[1] + round(PLOT_ASPECT * w - pos.height *
                                           self.canvas.height())
                screen = self.screen()
                if screen is not None:
                    h = min(h, round(0.9 * screen.availableGeometry()
                                     .height()))
                self.rebase(FIGURE_SIZE[0], h)
        if not self.placed and self.parentWidget() is not None:
            top = self.parentWidget().window()
            corner = top.mapToGlobal(top.rect().topRight())
            y = corner.y() + 80
            if self.screen() is not None:   # its bottom on the screen
                y = max(min(y, self.screen().availableGeometry().bottom() -
                            self.height() - 30), 0)
            self.move(corner.x() - self.width() - 20, y)
            self.placed = True
        self.show()
        self.raise_()

    def print_figure(self, path=None, options=None):
        """Save plot: the plot as Save plot of the main window does
        (options dialog and file dialog unless given); returns the path or
        None."""
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), self, "Save plot")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            folder = self.settings.value("export_dir", os.getcwd())
            name = re.sub(r"[^A-Za-z0-9_.+-]+", "_", self.title.text()) or \
                "plot"
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save plot", os.path.join(folder, name + "." + fmt),
                printfig.FILTERS[fmt])
            if not path:
                return None
            self.settings.setValue("export_dir", os.path.dirname(path))
        path = printfig.with_suffix(path, fmt)
        dark = theme.is_dark()
        try:
            theme.set_dark(options.get("theme", theme.name().lower())
                           == "dark")
            self.apply_theme()
            printfig.save(self.figure, path, options)
        except (OSError, ValueError, RuntimeError):
            return None
        finally:                # the plot in the theme of the GUI again
            theme.set_dark(dark)
            self.apply_theme()
        return path

    def export(self, path=None):
        """Write the rows as CSV (dialog unless path is given); returns the
        path or None."""
        if not self.rows:
            return None
        if path is None:
            folder = self.settings.value("export_dir", os.getcwd())
            start = os.path.join(folder, "values.csv")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Export values", start, "CSV (*.csv)")
            if not path:
                return None
        with open(path, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(self.header)
            out.writerows(self.rows)
        self.settings.setValue("export_dir", os.path.dirname(path))
        return path
