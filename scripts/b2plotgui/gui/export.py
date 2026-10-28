"""Export dialogs of the 2D tab: figure or pages (shape and resolution)
and the values of a quantity (written by b2plot mprt, mtab or eprt)."""

import os

from .. import page
from ..qt import QtWidgets

FIGURE_EXTS = (".pdf", ".png", ".svg", ".eps")


def component_paths(path, q):
    """One file per component of a vector, one for a scalar."""
    if q.source not in ("vector", "evector"):
        return [path]
    stem, ext = os.path.splitext(path)
    return ["%s_%s%s" % (stem, n, ext) for n in (q.poloidal, q.radial)]


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
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export figure" if shape else "Export pages")
        self.settings = settings
        form = QtWidgets.QFormLayout(self)
        self.where = PathRow(settings, page.FORMATS, default)
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
        if os.path.splitext(path)[1].lower() not in FIGURE_EXTS:
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


class ValuesDialog(QtWidgets.QDialog):
    """File and format of the values of a quantity, written by b2plot in
    the formats of the CLI."""

    def __init__(self, settings, q, species, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export values of %s" % q.name)
        self.settings, self.q = settings, q
        eirene = q.source in ("eirene", "evector")
        form = QtWidgets.QFormLayout(self)
        self.where = PathRow(settings, "Text (*.txt *.dat);;All files (*)",
                             q.name.replace(" ", "_") + ".txt")
        form.addRow("File", self.where)
        self.fmt = QtWidgets.QComboBox()
        if eirene:
            self.fmt.addItem("One value per line (b2plot eprt)", False)
        else:
            self.fmt.addItem("One value per line (b2plot mprt)", False)
            self.fmt.addItem("Table, one cell per line (b2plot mtab)", True)
        form.addRow("Format", self.fmt)
        self.shown = QtWidgets.QRadioButton("as plotted (%s)" % species)
        self.every = QtWidgets.QRadioButton("all species")
        self.shown.setChecked(True)
        if species in ("", "—"):
            self.every.setEnabled(False)
        form.addRow("Species", self.shown)
        form.addRow("", self.every)
        note = "b2plot writes the values with the scale factor of the plot."
        if q.source in ("vector", "evector"):
            note += "\nOne file per component: name_%s and name_%s." % (
                q.poloidal, q.radial)
        hint = QtWidgets.QLabel(note)
        hint.setStyleSheet("color: palette(mid);")
        form.addRow(hint)
        form.addRow(_buttons(self))

    def accept(self):
        if not _confirm(self, self.paths(), self.where.chosen):
            return
        self.settings.setValue("export_dir",
                               os.path.dirname(self.where.path()))
        super().accept()

    def paths(self):
        return component_paths(self.where.path(), self.q)

    def table(self):
        return bool(self.fmt.currentData())

    def all_species(self):
        return self.every.isChecked()
