"""Page composer: snapshots of the 2D plot (quantity with all its
settings) laid out nx by ny on pages, as b2plot page, for export. The
interactive plot of the tab stays one."""

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg

from .. import labels, page
from ..qt import QtCore, QtGui, QtWidgets, Qt, Signal
from .export import FigureDialog

PREVIEW_DPI = 60


class Composer(QtWidgets.QWidget):
    """Window with the list of plots, the page options and a preview."""

    status = Signal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("b2plot — page composer")
        self.settings = settings
        self.snaps = []
        self.values = {}

        self.list = QtWidgets.QListWidget()
        self.list.setToolTip("Plots in page order: left to right, then "
                             "top to bottom")
        self.list.currentRowChanged.connect(self._show_page_of)
        buttons = QtWidgets.QHBoxLayout()
        for text, slot in (("Up", lambda: self._move(-1)),
                           ("Down", lambda: self._move(1)),
                           ("Remove", self._remove), ("Clear", self.clear)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda *_, f=slot: f())
            buttons.addWidget(b)

        self.nx = QtWidgets.QSpinBox()
        self.ny = QtWidgets.QSpinBox()
        for s, tip in ((self.nx, "Plots per row"),
                       (self.ny, "Rows per page")):
            s.setRange(0, 6)
            s.setSpecialValueText("auto")
            s.setToolTip(tip + " (b2plot page); auto fits all plots")
            s.valueChanged.connect(lambda *_: self._changed())
        self.shape = QtWidgets.QComboBox()
        for key, (text, size) in page.SHAPES.items():
            if size is not None:
                self.shape.addItem(text, key)
        self.shape.setCurrentIndex(max(self.shape.findData("a4l"), 0))
        self.shape.currentIndexChanged.connect(lambda *_: self._changed())
        self.header = QtWidgets.QLineEdit()
        self.header.setPlaceholderText("global header over each page "
                                       "(b2plot glob)")
        self.header.setClearButtonEnabled(True)
        self.header.editingFinished.connect(self._changed)
        self.page = QtWidgets.QSpinBox()
        self.page.setRange(1, 1)
        self.page.setPrefix("page ")
        self.page.valueChanged.connect(lambda *_: self._timer.start())
        export = QtWidgets.QPushButton("Export pages…")
        export.clicked.connect(lambda *_: self.export())

        form = QtWidgets.QFormLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.nx)
        row.addWidget(QtWidgets.QLabel("by"))
        row.addWidget(self.ny)
        row.addStretch(1)
        form.addRow("Layout", row)
        form.addRow("Shape", self.shape)
        form.addRow("Header", self.header)
        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.list, 1)
        left.addLayout(buttons)
        left.addLayout(form)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.page)
        row.addStretch(1)
        row.addWidget(export)
        left.addLayout(row)

        self.preview = QtWidgets.QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(420, 320)
        self.preview.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                   QtWidgets.QSizePolicy.Ignored)
        self.preview.setStyleSheet("background: palette(dark);")
        lay = QtWidgets.QHBoxLayout(self)
        box = QtWidgets.QWidget()
        box.setLayout(left)
        box.setMaximumWidth(380)
        lay.addWidget(box)
        lay.addWidget(self.preview, 1)
        self._image = None
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._render)
        self.resize(1100, 640)

    # ------------------------------------------------------------ plots
    def add(self, snap, values=None):
        self.snaps.append(snap)
        self.values = values or self.values
        title = snap.labels.title if snap.labels and snap.labels.title \
            else snap.title
        self.list.addItem("%s  (%s)" % (labels.tex_to_plain(title),
                                        snap.style.kind))
        self.list.setCurrentRow(len(self.snaps) - 1)
        self._changed()

    def clear(self):
        self.snaps = []
        self.list.clear()
        self._changed()

    def _remove(self):
        i = self.list.currentRow()
        if 0 <= i < len(self.snaps):
            del self.snaps[i]
            self.list.takeItem(i)
            self._changed()

    def _move(self, step):
        i = self.list.currentRow()
        j = i + step
        if 0 <= i < len(self.snaps) and 0 <= j < len(self.snaps):
            self.snaps[i], self.snaps[j] = self.snaps[j], self.snaps[i]
            item = self.list.takeItem(i)
            self.list.insertItem(j, item)
            self.list.setCurrentRow(j)
            self._changed()

    # ----------------------------------------------------------- pages
    def grid(self):
        return page.layout(len(self.snaps), self.nx.value(), self.ny.value())

    def size(self):
        return page.SHAPES[self.shape.currentData()][1]

    def _changed(self):
        nx, ny = self.grid()
        n = len(page.pages(self.snaps, nx, ny))
        self.page.blockSignals(True)
        self.page.setRange(1, n)
        self.page.setSuffix(" of %d" % n)
        self.page.blockSignals(False)
        self._timer.start()

    def _show_page_of(self, row):
        nx, ny = self.grid()
        if row >= 0:
            self.page.setValue(row // max(1, nx * ny) + 1)

    def _render(self):
        """Preview of the current page, drawn as it is exported."""
        nx, ny = self.grid()
        group = page.pages(self.snaps, nx, ny)[self.page.value() - 1]
        fig = page.figure(self.size())
        canvas = FigureCanvasAgg(fig)
        try:
            page.draw_page(fig, group, nx, ny, self.header.text(),
                           self.values)
            fig.set_dpi(PREVIEW_DPI)
            canvas.draw()
        except Exception as err:     # a bad snapshot must not end the GUI
            self.status.emit("Cannot draw the page: %s" % err)
            return
        rgba = np.asarray(canvas.buffer_rgba()).copy()
        h, w = rgba.shape[:2]
        self._image = QtGui.QImage(rgba.data, w, h, 4 * w,
                                   QtGui.QImage.Format_RGBA8888).copy()
        self._fit()

    def _fit(self):
        if self._image is not None:
            self.preview.setPixmap(QtGui.QPixmap.fromImage(self._image).scaled(
                self.preview.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def export(self, path=None, dpi=None):
        """Write all pages (dialog unless path is given); returns files."""
        if not self.snaps:
            self.status.emit("The page composer has no plots")
            return []
        if path is None:
            dlg = FigureDialog(self.settings, "b2plot_pages.pdf", shape=False,
                               parent=self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return []
            path, dpi = dlg.path(), dlg.dpi.value()
        nx, ny = self.grid()
        try:
            files = page.save(path, self.snaps, self.size(), dpi or 150, nx,
                              ny, self.header.text(), self.values)
        except Exception as err:
            self.status.emit("Cannot export the pages: %s" % err)
            return []
        self.status.emit("Pages written to %s" % ", ".join(files))
        return files
