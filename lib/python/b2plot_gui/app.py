"""Main window of the b2plot GUI: run line, tabs, theme switch, status
bar.

One b2pl.exe per open run serves the data (data.Run); a QTimer
drains its events in the GUI thread and hands finished requests to the
tabs. There is no console and no b2plot command input. The window opens
on the whole screen and keeps that aspect ratio; nothing is saved on the
system: every start begins from the same state.
"""

import os
import sys
import time

from ..b2plot import __version__, backend, labels
from . import data, theme
from ..qt import PYSIDE6_VERSION, QtCore, QtGui, QtWidgets, Qt
from .output import state
from .output.composer import Composer
from .tab2d import Tab2D

POLL_MS = 20
POLL_BUDGET = 0.05
PLACEHOLDERS = ["Profiles", "Chords", "Time traces"]
LIVE = ((0, "Off"), (10, "Every 10 s"), (30, "Every 30 s"),
        (60, "Every minute"), (300, "Every 5 minutes"))
STATE_FILES = ("b2fstate", os.path.join("b2mn.exe.dir", "b2fstate"))


def _placeholder(name):
    w = QtWidgets.QWidget()
    lay = QtWidgets.QVBoxLayout(w)
    label = QtWidgets.QLabel("%s: coming in a later version." % name)
    label.setAlignment(Qt.AlignCenter)
    label.setEnabled(False)
    lay.addWidget(label)
    return w


class SessionSettings:
    """Settings of one session (QSettings interface), in memory only."""

    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.settings = SessionSettings()
        theme.install_frames(QtWidgets.QApplication.instance())
        self.run = None
        self.record = open(args.record, "wb") if args.record else None
        self.waiting = {}           # request ident -> [(tab, want)]
        self.crash_shown = False
        self._keep = None           # plot settings kept over a reload
        self._stamp = None          # time of b2fstate (live update)
        self._aspect = None         # width / height, fixed at the start
        self._sizing = False
        self._base = None           # (width, font size) at the start
        self._font = ""             # font size of the stylesheet
        self._fonts = QtCore.QTimer(self)
        self._fonts.setSingleShot(True)
        self._fonts.setInterval(120)
        self._fonts.timeout.connect(self._scale_fonts)

        self.runline = QtWidgets.QLabel()
        self.runline.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.runline.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                   QtWidgets.QSizePolicy.Preferred)
        self.tabs = QtWidgets.QTabWidget()
        self.tab2d = Tab2D(self.settings)
        self.tab2d.request.connect(self._request)
        self.tab2d.export.connect(self._export)
        self.tab2d.status.connect(self._status)
        self.composer = Composer(self.settings, self)
        self.composer.status.connect(self._status)
        self.tab2d.add_to_page.connect(self._add_to_page)
        self.tabs.addTab(self.tab2d, "2D plots")
        for name in PLACEHOLDERS:
            self.tabs.addTab(_placeholder(name), name)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(theme.NAMES)
        self.theme_combo.setToolTip("Switch between Light and Dark mode")
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.tabs.setCornerWidget(self.theme_combo, Qt.TopRightCorner)
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
        self.apply_theme("Light")
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._poll)
        self._live = QtCore.QTimer(self)
        self._live.timeout.connect(self._live_check)

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
        a = m.addAction("Print figure\u2026")
        a.setShortcut(QtGui.QKeySequence(keys.Save))
        a.triggered.connect(lambda *_: self.tab2d.print_figure())
        a = m.addAction("Export values\u2026")
        a.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        a.setToolTip("Values of the quantity shown, written by b2plot")
        a.triggered.connect(lambda *_: self.tab2d.export_values())
        a = m.addAction("Export field with geometry\u2026")
        a.setShortcut(QtGui.QKeySequence("Ctrl+Shift+E"))
        a.triggered.connect(lambda *_: self.tab2d.export_field())
        a = m.addAction("Copy figure")
        a.setShortcut(QtGui.QKeySequence("Ctrl+Shift+C"))
        a.triggered.connect(lambda *_: self.tab2d.copy_figure())
        m.addSeparator()
        m.addAction("Save plot settings\u2026").triggered.connect(
            lambda *_: self.tab2d.save_settings())
        m.addAction("Load plot settings\u2026").triggered.connect(
            lambda *_: self.tab2d.load_settings())
        live = m.addMenu("Live update")
        live.setToolTip("Reload the run, with the plot settings, when its "
                        "b2fstate changes")
        group = QtGui.QActionGroup(self)
        self.live_actions = {}
        for secs, text in LIVE:
            a = live.addAction(text)
            a.setCheckable(True)
            a.setChecked(secs == 0)
            group.addAction(a)
            a.triggered.connect(lambda *_, t=secs: self.set_live(t))
            self.live_actions[secs] = a
        m.addSeparator()
        a = m.addAction("Quit")
        a.setShortcut(QtGui.QKeySequence(keys.Quit))
        a.triggered.connect(lambda *_: self.close())
        m = self.menuBar().addMenu("&Page")
        a = m.addAction("Add plot to page")
        a.setShortcut(QtGui.QKeySequence("Ctrl+D"))
        a.triggered.connect(lambda *_: self.tab2d._add_to_page())
        a = m.addAction("Page composer\u2026")
        a.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        a.triggered.connect(lambda *_: self._show_composer())
        m.addAction("Maps from plot settings files\u2026").triggered.connect(
            lambda *_: self.tab2d.maps_to_page())
        m = self.menuBar().addMenu("&Help")
        m.addAction("About the b2plot GUI").triggered.connect(
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
        """The run read again, with the plot settings shown."""
        if self.run is not None:
            keep = state.capture(self.tab2d) if self.tab2d.run is not None \
                else None
            self.open_run(self.run.rundir)
            self._keep = keep

    def set_live(self, secs):
        """Check b2fstate every secs seconds (0: never)."""
        self._live.stop()
        self.live_actions[secs].setChecked(True)
        if secs:
            self._stamp = self._state_time()
            self._live.start(int(secs * 1000))
            self._status("Live update every %d s: the run is reloaded when "
                         "its b2fstate changes" % secs)

    def _state_time(self):
        if self.run is None:
            return None
        times = [os.path.getmtime(p) for p in (os.path.join(
            self.run.rundir, f) for f in STATE_FILES) if os.path.isfile(p)]
        return max(times) if times else None

    def _live_check(self):
        if self.run is None or self.run.pending:
            return
        t = self._state_time()
        if t is not None and t != self._stamp:
            self._stamp = t
            self.reload()

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
        self.waiting[req.ident] = []
        self._keep = None
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
        role, q, ops, source = want
        if self.run is None or not self.run.alive():
            self._status("b2plot is not running: File > Reload run")
            return
        if role == "traj":
            res = self.run.overlay("trajectories", ops[0])
        elif q.source in ("vector", "evector"):
            res = self.run.vector(q.poloidal, q.radial,
                                  eirene=q.source == "evector", ops=ops,
                                  source=source)
        else:
            res = self.run.field(q.name, eirene=q.source == "eirene",
                                 ops=ops, source=source,
                                 wall=q.source == "wall")
        if isinstance(res, data.Request):
            self.waiting.setdefault(res.ident, []).append((self.tab2d, want))
            if role not in ("prefetch", "species", "marks", "traj",
                            "tools"):
                self._status("Loading %s\u2026" % q.label)
        else:
            self.tab2d.deliver(want, res)

    def _export(self, job):
        q, names, paths, ops, table, source = job
        want = ("export", q, ops, source)
        if self.run is None or not self.run.alive():
            self._status("b2plot is not running: File > Reload run")
            return
        try:
            req = self.run.export(names, paths, q.source in (
                "eirene", "evector"), ops, table, source)
        except (OSError, ValueError) as err:
            self.tab2d.deliver(want, None, str(err))
            return
        self.waiting.setdefault(req.ident, []).append((self.tab2d, want))
        self._status("b2plot writes the values of %s\u2026" % q.label)

    def _add_to_page(self, snap):
        self.composer.add(snap, snap.values)
        self._show_composer()
        self._status("Added to the page composer (%d plots)"
                     % len(self.composer.snaps))

    def _show_composer(self):
        self.composer.show()
        self.composer.raise_()

    # -------------------------------------------------------------- poll
    def _poll(self):
        run = self.run
        if run is None:
            return
        for req in run.poll(POLL_BUDGET):
            receivers = self.waiting.pop(req.ident, [])
            if req.kind == "init":
                self._initialised(req)
            if receivers and req.result is not None:
                self._status("")
            for tab, want in receivers:
                tab.deliver(want, req.result,
                            "".join(req.console))
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
                ", EIRENE triangles: %d" % len(run.trimesh.triangles)) + (
                "   \u2014   live update, b2fstate of %s" % time.strftime(
                    "%H:%M:%S", time.localtime(self._stamp))
                if self._live.isActive() and self._stamp else ""))
        self.tab2d.set_run(run)
        keep, self._keep = self._keep, None
        if keep is not None:
            state.restore(self.tab2d, keep)
        self._status("Reloaded, with the plot settings" if keep is not None
                     else "Ready")

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
            self, "About the b2plot GUI",
            "b2plot GUI %s\nPython %d.%d.%d, PySide6 %s, "
            "matplotlib %s\nData from b2pl.exe; drawing by matplotlib."
            % (__version__, v[0], v[1], v[2],
               PYSIDE6_VERSION, matplotlib.__version__))

    # ------------------------------------------------------------- theme
    def apply_theme(self, name):
        """Light or Dark: the widgets (stylesheet) and every plot."""
        theme.set_dark(name == "Dark")
        if self.theme_combo.currentText() != name:
            self.theme_combo.setCurrentText(name)
        self.setStyleSheet(theme.stylesheet(self._font))
        self.tab2d.apply_theme()
        if self.composer.isVisible():
            self.composer._changed()

    # ------------------------------------------------------------ geometry
    def showEvent(self, event):
        super().showEvent(event)
        if self._aspect is None:
            self.fit_to_screen()
            QtCore.QTimer.singleShot(0, self.fit_to_screen)

    def fit_to_screen(self):
        """The window on the available area of its screen (frame
        included); its aspect ratio is kept from then on and the plot
        scales with it."""
        screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
        if screen is None:
            return
        g = screen.availableGeometry()
        frame, inner = self.frameGeometry(), self.geometry()
        left, top = inner.x() - frame.x(), inner.y() - frame.y()
        right = frame.width() - inner.width() - left
        bottom = frame.height() - inner.height() - top
        rect = QtCore.QRect(g.x() + left, g.y() + top,
                            g.width() - left - right,
                            g.height() - top - bottom)
        self._sizing = True
        self.setGeometry(rect)
        self._sizing = False
        self._aspect = rect.width() / max(rect.height(), 1)
        self._base = (rect.width(), QtGui.QFont(self.font()))
        self._font = ""
        QtCore.QTimer.singleShot(0, self.tab2d.freeze_scale)

    def resizeEvent(self, event):
        """A resize keeps the aspect ratio of the start: the side moved
        more decides the size."""
        super().resizeEvent(event)
        if self._aspect is None or self._sizing:
            return
        self._fonts.start()
        w, h = event.size().width(), event.size().height()
        if abs(w / max(h, 1) - self._aspect) * h < 2:
            return
        old = event.oldSize()
        if abs(w - old.width()) >= abs(h - old.height()):
            h = round(w / self._aspect)
        else:
            w = round(h * self._aspect)
        QtCore.QTimer.singleShot(0, lambda: self._resize(w, h))

    def _resize(self, w, h):
        self._sizing = True
        self.resize(w, h)
        self._sizing = False
        self._fonts.start()

    def _scale_fonts(self):
        """Fonts in proportion to the width of the window, so that every
        part keeps its proportions (the plot scales by itself)."""
        if self._base is None:
            return
        width, base = self._base
        k = self.width() / width
        font = "%.2fpt" % max(base.pointSizeF() * k, 4.0) if \
            base.pointSizeF() > 0 else "%dpx" % max(round(
                base.pixelSize() * k), 5)
        if abs(k - 1.0) < 0.005:
            font = ""
        if font != self._font:
            self._font = font
            self.setStyleSheet(theme.stylesheet(font))

    def closeEvent(self, event):
        self._timer.stop()
        self.stop_run()
        if self.record is not None:
            self.record.close()
        event.accept()


def main(args):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
        ["b2plot_gui"])
    app.setApplicationName("b2plot_gui")
    win = MainWindow(args)
    win.show()
    win.open_run(args.rundir)
    return app.exec()
