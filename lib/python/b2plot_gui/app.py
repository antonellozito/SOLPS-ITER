"""Main window of the b2plot GUI: run line with the run commands and
the theme switch, the 2D view, status bar.

One b2pl.exe per open run serves the data (data.Run); a QTimer
drains its events in the GUI thread and hands finished requests to the
view. There is no console and no b2plot command input. Outside a run
directory the window opens empty (Open run). The window opens on the
whole screen and keeps that aspect ratio; nothing is saved on the system
but the list of runs opened in the SOLPS-ITER session (session.Recent):
every start begins from the same state.
"""

import os
import time

from ..b2plot import backend
from . import data, runline, session, theme
from ..qt import QtCore, QtGui, QtWidgets
from .output import state
from .output.composer import Composer
from .tab2d import Tab2D

POLL_MS = 20
POLL_BUDGET = 0.05
LIVE = ((0, "off"), (10, "every 10 s"), (30, "every 30 s"),
        (60, "every minute"), (300, "every 5 minutes"))
STATE_FILES = ("b2fstate", os.path.join("b2mn.exe.dir", "b2fstate"))


def _roomy(combo):
    """A combo box and its list wide enough for the longest item."""
    fm = combo.fontMetrics()
    text = max(fm.horizontalAdvance(combo.itemText(i))
               for i in range(combo.count()))
    combo.setMinimumWidth(text + 4 * fm.averageCharWidth() + 24)
    combo.view().setMinimumWidth(text + 6 * fm.averageCharWidth())


class SessionSettings:
    """Settings of one session (QSettings interface), in memory only."""

    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class MainWindow(QtWidgets.QMainWindow):
    """Run line with, at its right, the run commands, live update and the
    theme; the 2D view under it; no menu bar."""

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.settings = SessionSettings()
        self.recent_runs = session.Recent()
        theme.install_indicators(QtWidgets.QApplication.instance())
        self.setStyleSheet(theme.stylesheet())  # before the widgets exist
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

        self.runline = runline.RunLine()
        self.tab2d = Tab2D(self.settings)
        self.tab2d.request.connect(self._request)
        self.tab2d.status.connect(self._status)
        self.tab2d.species_known.connect(self._species_line)
        self.composer = Composer(self.settings, self)
        self.composer.status.connect(self._status)
        self.tab2d.add_to_page.connect(self._add_to_page)
        self.tab2d.composer.connect(self._show_composer)
        body = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(body)
        lay.setContentsMargins(6, 4, 6, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.runline, 1)
        top.addWidget(self._corner())
        lay.addLayout(top)
        lay.addWidget(self.tab2d, 1)
        self.setCentralWidget(body)

        self.state = QtWidgets.QLabel()
        self.busy = QtWidgets.QProgressBar()
        self.busy.setRange(0, 0)
        self.busy.setMaximumWidth(90)
        self.busy.hide()
        self.statusBar().addWidget(self.state, 1)
        self.statusBar().addPermanentWidget(self.busy)
        self._shortcuts()
        self.resize(1500, 950)
        self.tab2d.apply_theme()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._poll)
        self._live = QtCore.QTimer(self)
        self._live.timeout.connect(self._live_check)

    def _corner(self):
        """Open run, Recent runs, Reload run, Live update and the theme, at
        the right of the run line."""
        w = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.run_buttons = {}
        for key, text, tip, slot in (
                ("open", "Open run\u2026", "Open another run directory "
                 "(Ctrl+O)", self.choose_run),
                ("recent", "Recent runs", "Runs opened in this SOLPS-ITER "
                 "session (since source setup.csh)", None),
                ("reload", "Reload run", "Read the run again, with the "
                 "plot settings (Ctrl+R)", self.reload)):
            b = QtWidgets.QPushButton(text)
            b.setToolTip(tip)
            if slot is not None:
                b.clicked.connect(lambda *_, f=slot: f())
            row.addWidget(b)
            self.run_buttons[key] = b
        self.recent = QtWidgets.QMenu(self)
        self.recent.aboutToShow.connect(self._fill_recent)
        self.run_buttons["recent"].setMenu(self.recent)
        row.addSpacing(10)
        row.addWidget(QtWidgets.QLabel("Live update"))
        self.live_combo = QtWidgets.QComboBox()
        for secs, text in LIVE:
            self.live_combo.addItem(text, secs)
        self.live_combo.setToolTip("Reload the run, with the plot settings, "
                                   "when its b2fstate changes")
        self.live_combo.activated.connect(
            lambda i: self.set_live(self.live_combo.itemData(i)))
        row.addWidget(self.live_combo)
        self.live_info = QtWidgets.QLabel()     # time of the b2fstate read
        self.live_info.setProperty("muted", True)
        self.live_info.setToolTip("Time of the b2fstate file read")
        self.live_info.hide()
        row.addWidget(self.live_info)
        row.addSpacing(10)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(theme.NAMES)
        self.theme_combo.setToolTip("Switch between Light and Dark mode")
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        row.addWidget(self.theme_combo)
        for combo in (self.live_combo, self.theme_combo):
            _roomy(combo)
        return w

    def _shortcuts(self):
        """The keys of the commands (there is no menu)."""
        tab = self.tab2d
        for key, slot in (("Ctrl+O", self.choose_run),
                          ("Ctrl+R", self.reload),
                          ("Ctrl+S", tab.print_figure),
                          ("Ctrl+D", tab._add_to_page),
                          ("Ctrl+P", self._show_composer),
                          ("Ctrl+Q", self.close)):
            QtGui.QShortcut(QtGui.QKeySequence(key), self).activated.connect(
                lambda f=slot: f())

    # ---------------------------------------------------------------- run
    def choose_run(self):
        start = os.path.dirname(self.run.rundir) if self.run is not None \
            else self.args.rundir
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Open run directory", start)
        if path:
            self.open_run(path)

    def _fill_recent(self):
        self.recent.clear()
        runs = self.recent_runs.runs()
        for path in runs:
            self.recent.addAction(path).triggered.connect(
                lambda *_, p=path: self.open_run(p))
        if not runs:
            self.recent.addAction("No run opened in this session yet"
                                  ).setEnabled(False)

    def no_run(self):
        """The empty window, outside a run directory."""
        self.tab2d.setEnabled(False)
        self._run_commands()
        self.runline.set("", "No run directory: Open run (Ctrl+O) or "
                         "Recent runs")
        self._status("Not in a run directory: open one with Open run")

    def _run_commands(self):
        """Reload run and Live update only with a run."""
        self.run_buttons["reload"].setEnabled(self.run is not None)
        self.live_combo.setEnabled(self.run is not None)

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
        self.live_combo.setCurrentIndex(max(self.live_combo.findData(secs),
                                            0))
        if secs:
            self._stamp = self._state_time()
            self._live.start(int(secs * 1000))
            self._status("Live update every %d s: the run is reloaded when "
                         "its b2fstate changes" % secs)
        self._live_info()

    def _live_info(self):
        """b2fstate of HH:MM:SS next to Live update, while it is on."""
        on = self._live.isActive() and self._stamp is not None
        if on:
            self.live_info.setText("b2fstate of %s" % time.strftime(
                "%H:%M:%S", time.localtime(self._stamp)))
        self.live_info.setVisible(on)

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
        if not session.is_run(path):
            self._status("Not a run directory: %s" % path)
            self._error("%s is not a run directory (no %s)." % (
                path, ", ".join(session.RUN_FILES)), "")
            return
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
        self._run_commands()
        self.recent_runs.add(path)
        self.runline.set(session.shown(path))
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
            self._status("b2plot is not running: Reload run starts it")
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
            if role not in ("prefetch", "species", "traj", "tools",
                            "eqdata", "balance"):
                self._status("Loading %s\u2026" % q.label)
        else:
            self.tab2d.deliver(want, res)

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
        self.tab2d.set_run(run)
        keep, self._keep = self._keep, None
        if keep is not None:
            state.restore(self.tab2d, keep)
        self._status("Reloaded, with the plot settings" if keep is not None
                     else "Ready")
        self._live_info()
        self._species_line()

    def _species_line(self):
        """The run line, again when b2plot sent the EIRENE species."""
        if self.run is not None and self.run.geometry is not None:
            self.runline.set(session.shown(self.run.rundir),
                             runline.details(self.run,
                                             self.tab2d.eirene_names))

    def _crashed(self, run):
        self._status("b2plot stopped (exit status %s)" % run.exit_status)
        self._error("b2plot stopped unexpectedly (exit status %s). "
                    "Reload run starts it again." % run.exit_status,
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

    # ------------------------------------------------------------- theme
    def apply_theme(self, name):
        """Light or Dark: the widgets (stylesheet) and every plot."""
        theme.set_dark(name == "Dark")
        if self.theme_combo.currentText() != name:
            self.theme_combo.setCurrentText(name)
        self.setStyleSheet(theme.stylesheet(self._font))
        self.tab2d.apply_theme()
        self._species_line()
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
    if session.is_run(args.rundir):
        win.open_run(args.rundir)
    else:
        win.no_run()
    return app.exec()
