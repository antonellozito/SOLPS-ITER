"""Export of every movie frame of the 2D tab: numbered image files or the
pages of one PDF, the frames drawn one after the other."""

import os

from . import page
from .export import FigureDialog
from ...qt import QtCore, QtWidgets


class FrameExport:
    """The frame export job of a 2D tab (tab.time_box, tab.snapshot ...)."""

    def __init__(self, tab):
        self.tab = tab
        self.job = None

    def start(self, path=None, shape="shown", dpi=150):
        """Every slider position (dialog unless path is given)."""
        tab = self.tab
        if tab.run is None or tab.wanted is None or \
                not tab._source(tab.wanted):
            tab.status.emit("Export frames needs movie frames: Time > "
                            "Movie frames")
            return
        if path is None:
            dlg = FigureDialog(tab.settings, tab.wanted.name.replace(
                " ", "_") + "_frames.png", parent=tab)
            dlg.setWindowTitle("Export frames")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            path, dpi = dlg.path(), dlg.dpi.value()
            shape = dlg.shape.currentData()
        tab.time_box.play.setChecked(False)
        self.job = dict(path=path, shape=shape, dpi=dpi,
                        todo=tab.time_box.positions(), snaps=[], files=[],
                        start=tab.time_box.pos.value())
        self._next()

    def _next(self):
        if not self.job["todo"]:
            self._finish()
            return
        p = self.job["todo"][0]
        if p == self.tab.time_box.pos.value() and self.tab._shown():
            QtCore.QTimer.singleShot(0, self.ready)
        else:
            self.tab.time_box.set_position(p)

    def ready(self):
        """Save the frame drawn (PNG, SVG) or keep it for the PDF."""
        tab, job = self.tab, self.job
        if job is None or not job["todo"] or not tab._shown() or \
                tab.time_box.pos.value() != job["todo"][0]:
            return
        p = job["todo"].pop(0)
        stem, ext = os.path.splitext(job["path"])
        size = page.SHAPES[job["shape"]][1]
        try:
            if ext.lower() == ".pdf":
                snap = tab.snapshot()
                if size is None:
                    size = tuple(tab.figure.get_size_inches())
                job["size"] = size
                job["snaps"].append(snap)
            else:
                name = "%s_%04d%s" % (stem, p, ext)
                if size is None:
                    tab.figure.savefig(name, dpi=job["dpi"])
                else:
                    page.save(name, [tab.snapshot()], size, job["dpi"],
                              own=True)
                job["files"].append(name)
        except Exception as err:
            self.job = None
            tab.status.emit("Cannot export the frames: %s" % err)
            return
        tab.status.emit("Exporting frames: %d left" % len(job["todo"]))
        self._next()

    def _finish(self):
        job, self.job = self.job, None
        tab = self.tab
        if job["snaps"]:
            try:
                job["files"] = page.save(job["path"], job["snaps"],
                                         job["size"], job["dpi"], own=True)
            except Exception as err:
                tab.status.emit("Cannot export the frames: %s" % err)
                return
        tab.time_box.set_position(job["start"])
        n = len(job["snaps"]) or len(job["files"])
        tab.status.emit("%d frames written to %s" % (
            n, job["files"][0] if len(job["files"]) == 1 else
            "%s ... %s" % (job["files"][0], job["files"][-1])))
