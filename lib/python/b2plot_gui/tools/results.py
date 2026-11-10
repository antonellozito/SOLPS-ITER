"""Results of the mouse tools in a small window over the main one (the
plot keeps its place): a title and a summary, a table in groups (cell
inspector) or a small figure (profile along a line, histogram) in the
colours of the theme, and the rows behind them for Export (CSV)."""

import csv
import os

from matplotlib import colors as mcolors
from matplotlib.figure import Figure

from ...b2plot import labels
from .. import theme
from ...qt import FigureCanvasQTAgg, QtGui, QtWidgets, Qt


class ResultsPanel(QtWidgets.QWidget):
    """Hidden until a tool shows something; Close hides it again. It
    opens at the top right of parent the first time."""

    def __init__(self, settings, parent=None):
        super().__init__(parent, Qt.Tool)
        self.setWindowTitle("b2plot — results")
        self.settings = settings
        self.placed = False
        self.sized = False          # made larger for the inspector once
        self.header, self.rows = [], []
        self.title = QtWidgets.QLabel()
        self.title.setStyleSheet("font-weight: bold;")
        self.title.setWordWrap(True)
        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.figure = Figure(figsize=(5.0, 2.6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(220)
        self.ax = self.figure.add_subplot(111)
        export = QtWidgets.QPushButton("Export…")
        export.setToolTip("The values of the table or curve as a CSV file")
        export.clicked.connect(lambda *_: self.export())
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(lambda *_: self.hide())
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.title, 1)
        top.addWidget(export)
        top.addWidget(close)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.text)
        lay.addWidget(self.table, 1)
        lay.addWidget(self.canvas, 1)
        self.resize(560, 420)
        self.hide()

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
        bold = QtGui.QFont(t.font())
        bold.setBold(True)
        i = 0
        for title_, rs in groups:
            item = QtWidgets.QTableWidgetItem(title_)
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
        if not self.sized:
            self.resize(max(self.width(), 900), max(self.height(), 640))
            self.sized = True
        t.resizeRowsToContents()

    def show_figure(self, title, text, draw, header, rows):
        """draw(ax) makes the small figure; rows are what Export writes."""
        self._set(title, text, header, rows, figure=True)
        self.ax.clear()
        draw(self.ax)
        self.apply_theme()

    def apply_theme(self):
        """The small figure in the colours of the theme."""
        ax, color = self.ax, theme.text()
        self.figure.set_facecolor(theme.figure_bg())
        ax.set_facecolor("#424242" if theme.is_dark() else "#ffffff")
        ax.tick_params(colors=color)
        for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
            item.set_color(color)
        for spine in ax.spines.values():
            spine.set_color(color)
        lines = list(ax.lines)
        for a in lines + list(ax.patches):     # gid: the colour drawn
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
        self.canvas.setVisible(figure)
        if not self.placed and self.parentWidget() is not None:
            top = self.parentWidget().window()
            corner = top.mapToGlobal(top.rect().topRight())
            self.move(corner.x() - self.width() - 20, corner.y() + 80)
            self.placed = True
        self.show()
        self.raise_()

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
