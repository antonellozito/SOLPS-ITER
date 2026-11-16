"""Results of the cell inspector in a small window over the main one (the
plot keeps its place), scaling with its size: a title and a table in
groups, and Export (CSV) of its rows."""

import csv
import os

from ...b2plot import labels
from ..scaling import Scaled
from ...qt import QtGui, QtWidgets, Qt

TABLE_SIZE = (900, 640)             # first size (pixels)


class ResultsPanel(Scaled, QtWidgets.QWidget):
    """Hidden until a tool shows something; Close hides it again. It
    opens at the top right of parent the first time."""

    def __init__(self, settings, parent=None):
        super().__init__(parent, Qt.Tool)
        self.setWindowTitle("b2plot — results")
        self.settings = settings
        self.placed = False
        self.sized = False
        self.header, self.rows = [], []
        self.title = QtWidgets.QLabel()
        self.title.setProperty("bold", True)
        self.title.setWordWrap(True)
        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        export = QtWidgets.QPushButton("Export…")
        export.setToolTip("The values of the table as a CSV file")
        export.clicked.connect(lambda *_: self.export())
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(lambda *_: self.hide())
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.title, 1)
        top.addWidget(export)
        top.addWidget(close)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table, 1)
        self.resize(*TABLE_SIZE)
        self.scaled()
        self.hide()

    def show_table(self, title, header, rows):
        self._set(title, header, rows)
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
        self._set(title, ["Group"] + list(header), rows)
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

    def _set(self, title, header, rows):
        self.header, self.rows = list(header), list(rows)
        self.title.setText(title)
        if not self.sized:
            self.rebase(*TABLE_SIZE)
            self.sized = True
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
