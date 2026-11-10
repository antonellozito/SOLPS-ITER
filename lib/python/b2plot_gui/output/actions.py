"""Output of the 2D tab: snapshots for the page composer, Print figure,
figure, values, frames, the field with its geometry, the clipboard and the
plot settings files (mixed into Tab2D)."""

import io
import os
import re
from dataclasses import replace

from . import fieldfile, page, printfig, state
from .. import theme
from .export import FigureDialog, ValuesDialog
from ..plot.snapshot import Snapshot
from ...qt import QtGui, QtWidgets


class TabOutput:
    """Export actions of a Tab2D (run, data, plot, settings, status)."""

    def snapshot(self):
        """The plot shown with all its settings, or None."""
        if self.run is None or not self._current():
            return None
        return Snapshot(
            run=self.run, data=self.data, style=self.quantity.style(),
            unit=self._unit(), overlays=self._overlay_data(),
            layers={k: replace(s) for k, s in self.layers.styles().items()},
            view=self.plot.get_view(),
            labels=self.quantity.labels_box.style(), title=self._title(),
            values=self.label_values())

    def _add_to_page(self):
        snap = self.snapshot()
        if snap is None:
            self.status.emit("No plot to add to the page")
            return
        self.add_to_page.emit(snap)

    def export_figure(self, path=None, shape="shown", dpi=150):
        """Write the plot (dialog unless path is given); returns files."""
        snap = self.snapshot()
        if snap is None:
            self.status.emit("No plot to export")
            return []
        if path is None:
            dlg = FigureDialog(self.settings, self.wanted.name.replace(
                " ", "_") + ".pdf", parent=self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return []
            path, dpi = dlg.path(), dlg.dpi.value()
            shape = dlg.shape.currentData()
        size = page.SHAPES[shape][1]
        try:
            if size is None:            # as shown: the figure of the tab
                self.figure.savefig(path, dpi=dpi)
                files = [path]
            else:
                files = page.save(path, [snap], size, dpi, own=True)
        except Exception as err:
            self.status.emit("Cannot export the figure: %s" % err)
            return []
        self.status.emit("Figure written to %s" % ", ".join(files))
        return files

    def print_figure(self, path=None, options=None):
        """Print figure, as AUGVIEW (output.printfig): the options dialog
        and the file dialog unless options and path are given. Returns
        the path written or None."""
        if self.run is None or not self._current():
            self.status.emit("No plot to print")
            return None
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            path = self._file("Print figure", re.sub(
                r"[^A-Za-z0-9_.+-]+", "_", self.wanted.label) + "." + fmt,
                printfig.FILTERS[fmt])
            if path is None:
                return None
        path = printfig.with_suffix(path, fmt)
        dark = theme.is_dark()
        try:
            theme.set_dark(options.get("theme", theme.name().lower())
                           == "dark")
            if theme.is_dark() != dark:
                self.apply_theme()
            note = printfig.save(self.figure, path, options)
        except (OSError, ValueError, RuntimeError) as err:
            self.status.emit("Cannot print the figure: %s" % err)
            return None
        finally:            # the plot of the GUI theme again
            theme.set_dark(dark)
            self.apply_theme()
        self.status.emit(("Figure printed to %s. %s" % (path, note)).strip())
        return path

    def export_values(self, paths=None, table=False, all_species=False):
        """Ask b2plot to write the values of the quantity shown (dialog
        unless paths are given)."""
        q = self.wanted
        if self.run is None or q is None:
            return
        if paths is None:
            dlg = ValuesDialog(self.settings, q,
                               self.quantity.species.currentText(), self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            paths, table = dlg.paths(), dlg.table()
            all_species = dlg.all_species()
        names = [q.poloidal, q.radial] if q.source in ("vector", "evector") \
            else [q.name]
        self.export.emit((q, names, list(paths),
                          self.quantity.value_ops(q, all_species), table,
                          self._source(q)))

    def export_frames(self, path=None, shape="shown", dpi=150):
        """Every movie frame as image files or one PDF (output.frames)."""
        self.frames.start(path, shape, dpi)

    def copy_figure(self):
        """The plot as shown, as an image on the clipboard."""
        if self.run is None or not self._current():
            self.status.emit("No plot to copy")
            return False
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=self.figure.dpi)
        QtWidgets.QApplication.clipboard().setImage(
            QtGui.QImage.fromData(buf.getvalue()))
        self.status.emit("Figure copied to the clipboard")
        return True

    def _file(self, title, name, filters, save=True, key="export_dir"):
        """Path from a file dialog in the folder of key, or None."""
        start = os.path.join(self.settings.value(key, os.getcwd()), name)
        ask = QtWidgets.QFileDialog.getSaveFileName if save else \
            QtWidgets.QFileDialog.getOpenFileName
        path = ask(self, title, start, filters)[0]
        if path:
            self.settings.setValue(key, os.path.dirname(path))
        return path or None

    def export_field(self, path=None):
        """The field shown with its geometry: CSV, VTK or netCDF (dialog
        unless path is given); returns the path written or None."""
        if self.run is None or not self._current():
            self.status.emit("No plot to export")
            return None
        path = path or self._file("Export field with geometry", re.sub(
            r"[^A-Za-z0-9_.+-]+", "_", self.wanted.label) + ".csv",
            fieldfile.FORMATS)
        if path is None:
            return None
        try:
            fieldfile.write(path, self.run, self.data, self._species())
        except (OSError, ValueError) as err:
            self.status.emit("Cannot export the field: %s" % err)
            return None
        self.status.emit("Field with geometry written to %s" % path)
        return path

    def save_settings(self, path=None):
        """Plot settings to a JSON file (a template for any run)."""
        if self.run is None:
            return None
        path = path or self._file("Save plot settings", "plot.json",
                                  "Plot settings (*.json)", key="state_dir")
        if path is not None:
            state.save(path, state.capture(self))
            self.status.emit("Plot settings written to %s" % path)
        return path

    def load_settings(self, path=None):
        """Plot settings from a JSON file, applied to the run shown."""
        if self.run is None:
            return False
        path = path or self._file("Load plot settings", "", "Plot settings "
                                  "(*.json)", save=False, key="state_dir")
        if path is None:
            return False
        try:
            ok = state.restore(self, state.load(path))
        except (OSError, ValueError) as err:
            self.status.emit("Cannot load the plot settings: %s" % err)
            return False
        if not ok:
            self.status.emit("Plot settings applied; the quantity is not "
                             "in this run")
        return ok

    def maps_to_page(self, paths=None):
        """A map for each plot settings file, all on the page composer."""
        if self.run is None:
            return
        if paths is None:
            paths = QtWidgets.QFileDialog.getOpenFileNames(
                self, "Maps from plot settings files", self.settings.value(
                    "state_dir", os.getcwd()), "Plot settings (*.json)")[0]
        if paths:
            self.maps.start(list(paths))

