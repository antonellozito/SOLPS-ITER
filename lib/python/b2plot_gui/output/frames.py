"""Export of every movie frame of the 2D tab: numbered image files, the
pages of one PDF, or a GIF (Pillow) or MP4 (ffmpeg) movie, the frames
drawn one after the other."""

import os
import shutil
import subprocess
import tempfile

from . import page
from .export import MOVIE_EXTS, FigureDialog
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
                " ", "_") + "_frames.png", parent=tab, movies=True)
            dlg.setWindowTitle("Export frames")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            path, dpi = dlg.path(), dlg.dpi.value()
            shape = dlg.shape.currentData()
        movie = os.path.splitext(path)[1].lower() in MOVIE_EXTS
        if movie and path.lower().endswith(".mp4") and \
                not shutil.which("ffmpeg"):
            tab.status.emit("MP4 needs ffmpeg on the PATH; GIF works "
                            "without it")
            return
        tab.time_box.play.setChecked(False)
        self.job = dict(path=path, shape=shape, dpi=dpi, movie=movie,
                        tmp=tempfile.mkdtemp(prefix="b2plot-frames-")
                        if movie else None,
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
        if job["movie"]:
            stem, ext = os.path.join(job["tmp"], "frame"), ".png"
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
        if job["movie"]:
            try:
                self._movie(job["files"], job["path"],
                            tab.time_box.fps.value())
            except Exception as err:
                tab.status.emit("Cannot write the movie: %s" % err)
                return
            finally:
                shutil.rmtree(job["tmp"], ignore_errors=True)
            job["files"] = [job["path"]]
        tab.status.emit("%d frames written to %s" % (
            n, job["files"][0] if len(job["files"]) == 1 else
            "%s ... %s" % (job["files"][0], job["files"][-1])))

    @staticmethod
    def _movie(frames, path, fps):
        """The frame images as a GIF (Pillow) or an MP4 (ffmpeg, frames of
        even size)."""
        if path.lower().endswith(".gif"):
            from PIL import Image
            images = [Image.open(f).convert("RGB") for f in frames]
            images[0].save(path, save_all=True, append_images=images[1:],
                           duration=int(1000 / max(fps, 1)), loop=0)
            return
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate",
                        str(fps), "-pattern_type", "glob", "-i",
                        os.path.join(os.path.dirname(frames[0]),
                                     "frame_*.png"), "-vf",
                        "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt",
                        "yuv420p", path], check=True, capture_output=True)
