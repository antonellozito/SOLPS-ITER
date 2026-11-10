"""Export dialogs of the 2D tab: figure or pages (shape and resolution)
and the values of a quantity (written by b2plot mprt, mtab or eprt)."""

import os

from . import page
from ...qt import QtWidgets

FIGURE_EXTS = (".pdf", ".png", ".svg", ".eps")
MOVIE_EXTS = (".gif", ".mp4")
MOVIE_FORMATS = ";;GIF movie (*.gif);;MP4 movie (*.mp4, needs ffmpeg)"


class PathRow(QtWidgets.QWidget):
    """File name with a Browse button (save dialog)."""

    def __init__(self, settings, filters, default, parent=None):
        super().__init__(parent)
        self.settings, self.filters = settings, filters
        self.chosen = None              # confirmed by the save dialog
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.edit = QtWidgets.QLineEdit(os.path.join(
            settings.value("export_dir", os.getcwd()), default))
        self.edit.setMinimumWidth(360)
        browse = QtWidgets.QPushButton("Browse…")
        browse.clicked.connect(lambda *_: self._browse())
        lay.addWidget(self.edit, 1)
        lay.addWidget(browse)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export", self.edit.text(), self.filters)
        if path:
            self.edit.setText(path)
            self.chosen = path

    def path(self):
        return os.path.abspath(os.path.expanduser(self.edit.text().strip()))


def _confirm(parent, paths, chosen):
    """Ask before replacing files not confirmed in the save dialog."""
    old = [p for p in paths if os.path.exists(p) and p != chosen]
    if not old:
        return True
    return QtWidgets.QMessageBox.question(
        parent, "Export", "Replace %s?" % ", ".join(old)) \
        == QtWidgets.QMessageBox.Yes


def _buttons(dialog):
    box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok
                                     | QtWidgets.QDialogButtonBox.Cancel)
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    return box


class FigureDialog(QtWidgets.QDialog):
    """File, shape and resolution of an exported figure or page."""

    def __init__(self, settings, default="b2plot.pdf", shape=True,
                 parent=None, movies=False):
        super().__init__(parent)
        self.setWindowTitle("Export figure" if shape else "Export pages")
        self.settings = settings
        self.exts = FIGURE_EXTS + MOVIE_EXTS * movies
        form = QtWidgets.QFormLayout(self)
        self.where = PathRow(settings, page.FORMATS + MOVIE_FORMATS * movies,
                             default)
        form.addRow("File", self.where)
        self.shape = QtWidgets.QComboBox()
        for key, (text, _) in page.SHAPES.items():
            self.shape.addItem(text, key)
        i = self.shape.findData(settings.value("export_shape", "shown"))
        self.shape.setCurrentIndex(max(i, 0))
        if shape:
            form.addRow("Shape", self.shape)
        self.dpi = QtWidgets.QSpinBox()
        self.dpi.setRange(50, 1200)
        self.dpi.setValue(int(settings.value("export_dpi", 150)))
        self.dpi.setSuffix(" dpi")
        self.dpi.setToolTip("Resolution of PNG files (dots per inch)")
        form.addRow("Resolution", self.dpi)
        form.addRow(_buttons(self))

    def accept(self):
        path = self.path()
        if os.path.splitext(path)[1].lower() not in self.exts:
            path += ".pdf"
            self.where.edit.setText(path)
        if not _confirm(self, [path], self.where.chosen):
            return
        self.settings.setValue("export_dir", os.path.dirname(path))
        self.settings.setValue("export_shape", self.shape.currentData())
        self.settings.setValue("export_dpi", self.dpi.value())
        super().accept()

    def path(self):
        return self.where.path()
