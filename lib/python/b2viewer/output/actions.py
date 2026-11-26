"""Output of the 2D tab: snapshots for the page composer, Save plot,
figure files and the field with its grid (mixed into Tab2D)."""

import os
import re
from dataclasses import replace

from . import fieldfile, page, printfig
from .. import scaling, theme
from .export import FigureDialog
from ..plot.snapshot import Snapshot
from ...qt import QtWidgets


class TabOutput:
    """Export actions of a Tab2D (run, data, plot, settings, status)."""

    def _plotted(self):
        """The quantity naming the plot shown (plasma, else vector, else
        wall quantity), or None."""
        if self.run is None:
            return None
        return self.wanted if self._current() else self.vector_wanted if \
            self._vector_args() else self.wall_wanted if \
            self._wall_pair() else None

    def snapshot(self):
        """The plot shown with all its settings (the plasma, vector and
        wall plots shown), or None."""
        q = self._plotted()
        if q is None:
            return None
        plasma = q is self.wanted
        overlays = self._overlay_data() if plasma else {}
        for key, args in (("vectors", self._vector_args()),
                          ("wall", self._wall_pair())):
            if args:
                overlays[key] = args
        return Snapshot(
            run=self.run, data=self.data if plasma else None,
            style=self.quantity.style(), unit=self._unit(),
            overlays=overlays,
            layers={k: replace(s) for k, s in
                    self.plot.layer_styles.items()},
            view=self.plot.get_view(),
            labels=self.quantity.labels_box.style(),
            title=self._title(),
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
            dlg = FigureDialog(self.settings, self._plotted().name.replace(
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
        """Save plot (output.printfig): the options dialog and the
        file dialog unless options and path are given. Returns the path
        written or None."""
        q = self._plotted()
        if q is None:
            self.status.emit("No plot to save")
            return None
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            path = self._file("Save plot", re.sub(
                r"[^A-Za-z0-9_.+-]+", "_", q.label) + "." + fmt,
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
            self.status.emit("Cannot save the plot: %s" % err)
            return None
        finally:            # the plot of the GUI theme again
            theme.set_dark(dark)
            self.apply_theme()
        self.status.emit(("Plot saved to %s. %s" % (path, note)).strip())
        return path

    def _file(self, title, name, filters, save=True, key="export_dir"):
        """Path from a file dialog in the folder of key, or None."""
        start = os.path.join(self.settings.value(key, os.getcwd()), name)
        ask = QtWidgets.QFileDialog.getSaveFileName if save else \
            QtWidgets.QFileDialog.getOpenFileName
        path = ask(self, title, start, filters)[0]
        if path:
            self.settings.setValue(key, os.path.dirname(path))
        return path or None

    def export_field(self, path=None, which=None):
        """The plasma or the vector quantity shown (which: "plasma",
        "vector"; asked when both are plotted, default the plasma one with
        a path) with its grid (output.fieldfile), every species: the
        format first, then the file, unless path is given; returns the
        path written or None."""
        shown = [k for k, on in (
            ("plasma", self.run is not None and self._current()),
            ("vector", self._vector_args() is not None)) if on]
        if not shown:
            self.status.emit("No plot to export")
            return None
        if which not in shown and len(shown) == 2 and path is None:
            texts = ["Plasma quantity", "Vector quantity"]
            choice, ok = scaling.choose(self, "Export field", "Quantity",
                                        texts)
            if not ok:
                return None
            which = shown[texts.index(choice)]
        which = which if which in shown else shown[0]
        data, q = (self.data, self.wanted) if which == "plasma" else (
            self.vector_data, self.vector_wanted)
        if path is None:
            choice, ok = scaling.choose(self, "Export field",
                                        "Output format",
                                        list(fieldfile.FORMATS))
            if not ok:
                return None
            ext = fieldfile.FORMATS[choice]
            path = self._file("Export field", re.sub(
                r"[^A-Za-z0-9_.+-]+", "_", q.label) + ext,
                fieldfile.FILTERS[ext])
            if path is None:
                return None
            if not path.lower().endswith(ext):
                path += ext
        try:
            fieldfile.write(path, self.run, data, self._species(), q.label)
        except (OSError, ValueError) as err:
            self.status.emit("Cannot export the field: %s" % err)
            return None
        self.status.emit("Field and grid written to %s" % path)
        return path
