"""Results of the mouse tools under the plot: a title and a summary, a
table (cell inspector) or a small figure (profile along a line,
histogram), and the rows behind them for Export (CSV)."""

import csv
import os

from matplotlib.figure import Figure

from ...b2plot import labels
from ...qt import FigureCanvasQTAgg, NavigationToolbar2QT, QtWidgets, Qt


class ResultsPanel(QtWidgets.QWidget):
    """Hidden until a tool shows something; Close hides it again."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.header, self.rows = [], []
        self.title = QtWidgets.QLabel()
        self.title.setStyleSheet("font-weight: bold;")
        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(170)
        self.figure = Figure(figsize=(5.0, 1.9))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(170)
        self.nav = NavigationToolbar2QT(self.canvas, self)
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
        lay.setContentsMargins(0, 4, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.text)
        lay.addWidget(self.table)
        lay.addWidget(self.nav)
        lay.addWidget(self.canvas)
        self.hide()

    def show_table(self, title, header, rows):
        self._set(title, "", header, rows, figure=False)
        self.table.setColumnCount(len(header))
        self.table.setHorizontalHeaderLabels(header)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(
                    labels.any_to_plain(str(v))))
        self.table.resizeColumnsToContents()

    def show_figure(self, title, text, draw, header, rows):
        """draw(ax) makes the small figure; rows are what Export writes."""
        self._set(title, text, header, rows, figure=True)
        self.ax.clear()
        draw(self.ax)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _set(self, title, text, header, rows, figure):
        self.header, self.rows = list(header), list(rows)
        self.title.setText(title)
        self.text.setText(text)
        self.text.setVisible(bool(text))
        self.table.setVisible(not figure)
        self.canvas.setVisible(figure)
        self.nav.setVisible(figure)
        self.show()

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
