"""Main window of the b2plot.py GUI: run line, tabs, status bar.

One b2pl_gui.exe per open run serves the data (data.Run); a QTimer
drains its events in the GUI thread and hands finished requests to the
tabs. There is no console and no b2plot command input.
"""

import os
import sys

from .. import PROTOCOL_VERSION, __version__, backend, data, labels
from ..qt import PYSIDE6_VERSION, QtCore, QtGui, QtWidgets, Qt
from .tab2d import Tab2D

POLL_MS = 20
POLL_BUDGET = 0.05
PLACEHOLDERS = ["Profiles", "Chords", "Wall and targets", "Time traces"]


def _placeholder(name):
    w = QtWidgets.QWidget()
    lay = QtWidgets.QVBoxLayout(w)
    label = QtWidgets.QLabel("%s: coming in a later version." % name)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color: palette(mid);")
    lay.addWidget(label)
    return w


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.settings = QtCore.QSettings("SOLPS-ITER", "b2plot.py")
        self.run = None
        self.record = open(args.record, "wb") if args.record else None
        self.waiting = {}           # request ident -> (tab, quantity)
        self.crash_shown = False

        self.runline = QtWidgets.QLabel()
        self.runline.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.runline.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                   QtWidgets.QSizePolicy.Preferred)
        self.tabs = QtWidgets.QTabWidget()
        self.tab2d = Tab2D(self.settings)
        self.tab2d.request.connect(self._request)
        self.tab2d.status.connect(self._status)
        self.tabs.addTab(self.tab2d, "2D plots")
        for name in PLACEHOLDERS:
            self.tabs.addTab(_placeholder(name), name)
        body = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(body)
        lay.setContentsMargins(6, 4, 6, 0)
        lay.addWidget(self.runline)
        lay.addWidget(self.tabs, 1)
        self.setCentralWidget(body)

        self.state = QtWidgets.QLabel()
        self.busy = QtWidgets.QProgressBar()
        self.busy.setRange(0, 0)
        self.busy.setMaximumWidth(90)
        self.busy.hide()
        self.statusBar().addWidget(self.state, 1)
        self.statusBar().addPermanentWidget(self.busy)
        self._menus()
        self.resize(1500, 950)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._poll)

    def _menus(self):
        keys = QtGui.QKeySequence.StandardKey
        m = self.menuBar().addMenu("&File")
        a = m.addAction("Open run directory\u2026")
        a.setShortcut(QtGui.QKeySequence(keys.Open))
        a.triggered.connect(lambda *_: self.choose_run())
        self.recent = m.addMenu("Recent runs")
        self.recent.aboutToShow.connect(self._fill_recent)
        a = m.addAction("Reload run")
        a.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        a.triggered.connect(lambda *_: self.reload())
        m.addSeparator()
        a = m.addAction("Export figure\u2026")
        a.setShortcut(QtGui.QKeySequence(keys.Save))
        a.triggered.connect(lambda *_: self.tab2d.toolbar.save_figure())
        m.addSeparator()
        a = m.addAction("Quit")
        a.setShortcut(QtGui.QKeySequence(keys.Quit))
        a.triggered.connect(lambda *_: self.close())
        m = self.menuBar().addMenu("&Help")
        m.addAction("About b2plot.py").triggered.connect(
            lambda *_: self.about())

    # ---------------------------------------------------------------- run
    def choose_run(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Open run directory", self.args.rundir)
        if path:
            self.open_run(path)

    def _fill_recent(self):
        self.recent.clear()
        for path in self.settings.value("recent", []) or []:
            self.recent.addAction(path).triggered.connect(
                lambda *_, p=path: self.open_run(p))

    def reload(self):
        if self.run is not None:
            self.open_run(self.run.rundir)

    def open_run(self, path):
        path = os.path.abspath(path)
        self.stop_run()
        self.args.rundir = path
        self.run = data.Run(backend.command(self.args), path, self.record)
        self.crash_shown = False
        try:
            req = self.run.start()
        except OSError as err:
            self._status("Cannot start b2plot: %s" % err)
            self.run = None
            return
        self.waiting[req.ident] = (None, None)
        self.tab2d.setEnabled(False)
        recent = [path] + [p for p in (self.settings.value("recent", [])
                                       or []) if p != path]
        self.settings.setValue("recent", recent[:10])
        self.runline.setText(path)
        self.setWindowTitle("b2plot \u2014 " + path)
        self._status("Reading the run with b2plot\u2026")
        self._timer.start()

    def stop_run(self):
        if self.run is not None:
            self.run.stop()
        self.run = None
        self.waiting.clear()

    def _request(self, want):
        q, ops = want
        if self.run is None or not self.run.alive():
            self._status("b2plot is not running: File > Reload run")
            return
        if q.source in ("vector", "evector"):
            res = self.run.vector(q.poloidal, q.radial,
                                  eirene=q.source == "evector", ops=ops)
        else:
            res = self.run.field(q.name, eirene=q.source == "eirene",
                                 ops=ops)
        if isinstance(res, data.Request):
            self.waiting[res.ident] = (self.tab2d, want)
            self._status("Loading %s\u2026" % q.name)
        else:
            self.tab2d.deliver(want, res)

    # -------------------------------------------------------------- poll
    def _poll(self):
        run = self.run
        if run is None:
            return
        for req in run.poll(POLL_BUDGET):
            tab, q = self.waiting.pop(req.ident, (None, None))
            if req.kind == "init":
                self._initialised(req)
            elif tab is not None:
                tab.deliver(q, req.result, "".join(req.console[-3:]).strip())
                if req.result is not None:
                    self._status("")
        self.busy.setVisible(bool(run.pending))
        ended = run.ended >= {"eof", "console_eof", "exit"}
        if ended and not self.crash_shown:
            self.crash_shown = True
            self.busy.hide()
            if not run.bye:
                self._crashed(run)

    def _initialised(self, req):
        run = self.run
        if run.geometry is None:
            self._status("b2plot sent no grid (see the details)")
            self._error("b2plot did not send the grid of this run.",
                        "".join(run.console[-30:]))
            return
        info = run.info or {}
        names = [labels.species_text(s) for s in info.get("species", [])]
        sp = ", ".join(names if len(names) <= 8 else
                       names[:4] + ["\u2026"] + names[-2:])
        sp = "%d (%s)" % (len(names), sp)
        self.runline.setText(
            "%s   \u2014   %d cells, %s grid, species: %s%s" % (
                run.rundir, len(run.geometry.cells),
                "classical" if run.geometry.classical else "unstructured",
                sp, "" if run.trimesh is None else
                ", EIRENE triangles: %d" % len(run.trimesh.triangles)))
        self.tab2d.set_run(run)
        self._status("Ready")

    def _crashed(self, run):
        self._status("b2plot stopped (exit status %s)" % run.exit_status)
        self._error("b2plot stopped unexpectedly (exit status %s). "
                    "File > Reload run starts it again." % run.exit_status,
                    "".join(run.console[-30:]))

    # ----------------------------------------------------------- helpers
    def _status(self, text):
        self.state.setText(text)

    def _error(self, text, details):
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("b2plot")
        box.setText(text)
        box.setDetailedText(details)
        box.open()

    def about(self):
        import matplotlib
        v = sys.version_info
        QtWidgets.QMessageBox.about(
            self, "About b2plot.py",
            "b2plot.py %s (protocol %d)\nPython %d.%d.%d, PySide6 %s, "
            "matplotlib %s\nData from b2pl_gui.exe; drawing by matplotlib."
            % (__version__, PROTOCOL_VERSION, v[0], v[1], v[2],
               PYSIDE6_VERSION, matplotlib.__version__))

    def closeEvent(self, event):
        self._timer.stop()
        self.stop_run()
        if self.record is not None:
            self.record.close()
        event.accept()


def main(args):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
        ["b2plot.py"])
    app.setApplicationName("b2plot.py")
    win = MainWindow(args)
    win.show()
    win.open_run(args.rundir)
    return app.exec()
