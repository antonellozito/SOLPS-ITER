"""Tabs at the top of the 2D quantity panel: Final state, Run movies
(b2movies.nc, eirenemovies.nc, b2tallies.nc) or Balances (balance.nc,
the final state shown); with the movies, one frame,
the means b2plot computes over a range, a rolling window or consecutive
blocks of frames, the standard deviation over a range, each minus a
reference."""

from ...qt import QtCore, QtWidgets, Qt, Signal

MODES = [("One frame", "frame"), ("Mean over frames", "range"),
         ("Rolling mean", "rolling"), ("Batch mean", "batch"),
         ("Standard deviation over frames", "std")]
MINUS = [("nothing", None), ("the first frame", "first"),
         ("the last frame", "last"), ("the mean of all frames", "all"),
         ("the final state", "final")]
RANGE = ("range", "std")            # modes over the frames first to last


TABS = (("Final state", "The final state of the run (b2fstate)"),
        ("Run movies", "The movie frames of the run: b2movies.nc, "
         "eirenemovies.nc and b2tallies.nc of the run directory"),
        ("Balances", "Parallel and radial balances of volumes picked on "
         "the plot, from balance.nc (the final state shown)"))
BALANCES = 2                        # index of the Balances tab


class TimeBox(QtWidgets.QWidget):
    """Source of the plotted data (the tabs, source: placed by the 2D tab
    over the scrolled panel, so that they never scroll away) and, with the
    movies, the frames of the plot."""

    source_changed = Signal()       # final state or movie frames
    frames_changed = Signal()       # frames of the movie plot
    export_frames = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.times = {}                 # file -> frame times (s)
        self.file = 1                   # file of the quantity shown
        self.ready = lambda: True       # plot of the frame drawn
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.source = QtWidgets.QTabBar()
        self.source.setExpanding(True)
        self.source.setDrawBase(True)
        for i, (text, tip) in enumerate(TABS):
            self.source.addTab(text)
            self.source.setTabToolTip(i, tip)
        self.movie_part = QtWidgets.QWidget()
        lay.addWidget(self.movie_part)
        form = QtWidgets.QFormLayout(self.movie_part)
        form.setContentsMargins(0, 4, 0, 0)
        self.mode = QtWidgets.QComboBox()
        for text, key in MODES:
            self.mode.addItem(text, key)
        self.mode.setToolTip("Means are computed by b2plot over the frames "
                             "(rolling: a window moved frame by frame; "
                             "batch: consecutive blocks of frames)")
        self.minus = QtWidgets.QComboBox()
        for text, key in MINUS:
            self.minus.addItem(text, key)
        self.minus.setToolTip("Reference subtracted from what is shown "
                              "(b2plot m-); the final state needs a movie "
                              "variable that is also a b2plot label")
        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setTracking(False)
        self.pos = QtWidgets.QSpinBox()
        self.pos.setKeyboardTracking(False)
        self.play = QtWidgets.QToolButton()
        self.play.setText("Play")
        self.play.setCheckable(True)
        self.play.setToolTip("Play the movie; the next frame is loaded "
                             "while the current one is shown")
        self.fps = QtWidgets.QSpinBox()
        self.fps.setRange(1, 30)
        self.fps.setValue(4)
        self.fps.setSuffix(" fps")
        self.loop = QtWidgets.QCheckBox("loop")
        self.first = QtWidgets.QSpinBox()
        self.last = QtWidgets.QSpinBox()
        for s in (self.first, self.last):
            s.setKeyboardTracking(False)
        self.window = QtWidgets.QSpinBox()
        self.window.setKeyboardTracking(False)
        self.window.setToolTip("Frames per window or block")
        self.align = QtWidgets.QComboBox()
        self.align.addItem("trailing", "trailing")
        self.align.addItem("centred", "centred")
        self.align.setToolTip("Trailing: the window ends at the frame; "
                              "centred: the frame is in its middle")
        self.info = QtWidgets.QLabel(" ")
        self.info.setWordWrap(True)
        export = QtWidgets.QPushButton("Export frames…")
        export.setToolTip("Every position of the slider as an image file "
                          "or as the pages of one PDF")
        export.clicked.connect(lambda *_: self.export_frames.emit())

        def row(*widgets):
            box = QtWidgets.QHBoxLayout()
            for w in widgets:
                box.addWidget(w)
            return box
        form.addRow("Show", self.mode)
        form.addRow("Minus", self.minus)
        form.addRow("Position", row(self.slider, self.pos))
        form.addRow("Frames", row(self.first, QtWidgets.QLabel("to"),
                                  self.last))
        form.addRow("Window", row(self.window, self.align))
        form.addRow("", row(self.play, self.fps, self.loop, export))
        form.addRow(self.info)
        self.form = form
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.source.currentChanged.connect(self._source_changed)
        self.mode.currentIndexChanged.connect(lambda *_: self._layout())
        self.minus.currentIndexChanged.connect(lambda *_: self._layout())
        self.slider.valueChanged.connect(self.pos.setValue)
        self.pos.valueChanged.connect(self._moved)
        for w in (self.first, self.last, self.window):
            w.valueChanged.connect(lambda *_: self._layout())
        self.align.currentIndexChanged.connect(lambda *_: self._layout())
        self.play.toggled.connect(self._play)
        self.fps.valueChanged.connect(
            lambda v: self._timer.setInterval(int(1000 / v)))
        self._timer.setInterval(250)
        self.set_movies({})
        self.set_balances(False, "no run")

    # ------------------------------------------------------------- state
    def set_movies(self, movies, stale=(), final=True, why=""):
        """Frame times of the movie files of the latest run of a new run
        directory (data.MovieFile); stale: why the other ones are left out;
        final: a final state of the run (else why not; with why: what it
        is, the plasma when an error stopped B2.5)."""
        self.times = {f: list(m.times) for f, m in movies.items() if m.nt}
        self.source.setTabEnabled(0, final)
        self.source.setTabToolTip(0, ("Final state: " + why if why else
                                      TABS[0][1]) if final else
                                  "No final state: " + why)
        self.source.setTabEnabled(1, bool(self.times))
        tip = TABS[1][1] if self.times else "No movie files (b2movies.nc, " \
            "eirenemovies.nc, b2tallies.nc) of the latest run in the run " \
            "directory"
        self.source.setTabToolTip(1, "\n".join([tip] + list(stale)))
        self.source.blockSignals(True)
        self.source.setCurrentIndex(1 if not final and self.times else 0)
        self.source.blockSignals(False)
        self.file = min(self.times) if self.times else 1
        nt = self.nt()
        for s in (self.first, self.last):
            s.blockSignals(True)
            s.setRange(1, max(nt, 1))
            s.blockSignals(False)
        self.first.setValue(1)
        self.last.setValue(max(nt, 1))
        self.window.blockSignals(True)
        self.window.setRange(1, max(nt, 1))
        self.window.setValue(min(5, max(nt, 1)))
        self.window.blockSignals(False)
        self.play.setChecked(False)
        self._layout(emit=False)

    def movie(self):
        return self.source.currentIndex() == 1 and bool(self.times)

    def balances(self):
        return self.source.currentIndex() == BALANCES

    def set_balances(self, ok, why=""):
        """The Balances tab only with a balance.nc of this state (else
        why not in its tooltip)."""
        self.source.setTabEnabled(BALANCES, ok)
        self.source.setTabToolTip(BALANCES, TABS[BALANCES][1] if ok else
                                  "No balances: " + why)

    def final(self):
        """The final state of the run can be shown."""
        return self.source.isTabEnabled(0)

    def key(self):
        return self.mode.currentData()

    def nt(self, f=None):
        return len(self.times.get(self.file if f is None else f, []))

    def set_file(self, f):
        """Movie file of the quantity shown (1 B2.5, 2 EIRENE)."""
        if f in self.times and f != self.file:
            self.file = f
            self._layout(emit=False)

    # ---------------------------------------------------------- frames
    def _span(self):
        """Slider range of the current mode."""
        nt, w = self.nt(), self.window.value()
        key = self.key()
        if key == "rolling":
            h = w // 2 if self.align.currentData() == "centred" else w - 1
            return 1 + h, nt - (w - 1 - h)
        if key == "batch":
            return 1, max(nt // w, 1)
        return 1, max(nt, 1)

    def frames_at(self, p, f=None):
        """(first, last) frame of slider position p for file f."""
        nt, w = self.nt(f), self.window.value()
        key = self.key()
        if key == "frame":
            k1 = k2 = p
        elif key in RANGE:
            k1, k2 = sorted((self.first.value(), self.last.value()))
        elif key == "rolling":
            h = w // 2 if self.align.currentData() == "centred" else w - 1
            k1, k2 = p - h, p - h + w - 1
        else:
            k1, k2 = (p - 1) * w + 1, p * w
        k2 = min(k2, max(nt, 1))
        return min(max(k1, 1), k2), k2

    def frames(self, f=None):
        return self.frames_at(self.pos.value(), f)

    def source_of(self, q, p=None):
        """(file, first, last[, statistic, reference]) of a movie quantity
        at slider position p (default the current one), None for the
        final state."""
        if not getattr(q, "movie", 0) or not self.movie():
            return None
        source = (q.movie,) + (self.frames(q.movie) if p is None else
                               self.frames_at(p, q.movie))
        nt = self.nt(q.movie)
        ref = {"first": (1, 1), "last": (nt, nt), "all": (1, nt),
               "final": "final"}.get(self.minus.currentData())
        stat = "std" if self.key() == "std" else "mean"
        return source if stat == "mean" and ref is None else \
            source + (stat, ref)

    def positions(self):
        """Slider positions shown by Play and by Export frames."""
        if self.key() in RANGE:
            return [self.pos.value()]
        lo, hi = self._span()
        return list(range(lo, hi + 1))

    def time_text(self, f=None):
        """Frames and times of the current position."""
        t = self.times.get(self.file if f is None else f, [])
        if not t:
            return ""
        k1, k2 = self.frames(f)
        minus = "" if self.minus.currentData() is None else \
            ", minus " + self.minus.currentText()
        if k1 == k2 and self.key() != "std":
            return "frame %d of %d, t = %.4g s%s" % (k1, len(t), t[k1 - 1],
                                                     minus)
        return "%s of frames %d\u2013%d of %d, t = %.4g\u2013%.4g s%s" % (
            "standard deviation" if self.key() == "std" else "mean", k1, k2,
            len(t), t[k1 - 1], t[k2 - 1], minus)

    def time_value(self, f=None):
        """Time of the frame, or the middle of the frames averaged."""
        t = self.times.get(self.file if f is None else f, [])
        if not t:
            return None
        k1, k2 = self.frames(f)
        return 0.5 * (t[k1 - 1] + t[k2 - 1])

    def set_position(self, p):
        self.pos.setValue(p)

    # ---------------------------------------------------------- widgets
    def _source_changed(self, *_):
        self.play.setChecked(False)
        self._layout(emit=False)
        self.source_changed.emit()

    def _layout(self, emit=True):
        movie = self.movie()
        key = self.key()
        self.movie_part.setVisible(movie)
        if movie:
            self.form.setRowVisible(2, key not in RANGE)
            self.form.setRowVisible(3, key in RANGE)
            self.form.setRowVisible(4, key in ("rolling", "batch"))
            self.align.setVisible(key == "rolling")
            self.play.setEnabled(key not in RANGE)
            lo, hi = self._span()
            hi = max(hi, lo)
            for w in (self.slider, self.pos):
                w.blockSignals(True)
                w.setRange(lo, hi)
                w.blockSignals(False)
            self.pos.blockSignals(True)
            self.pos.setValue(min(max(self.pos.value(), lo), hi))
            self.pos.blockSignals(False)
            self.slider.blockSignals(True)
            self.slider.setValue(self.pos.value())
            self.slider.blockSignals(False)
            self.pos.setPrefix({"batch": "block "}.get(key, "frame "))
            self.info.setText(self.time_text())
        if emit and movie:
            self.frames_changed.emit()

    def _moved(self, p):
        self.slider.blockSignals(True)
        self.slider.setValue(p)
        self.slider.blockSignals(False)
        self.info.setText(self.time_text())
        if self.movie():
            self.frames_changed.emit()

    def next_position(self):
        """Position after the current one (None at the end, no loop)."""
        lo, hi = self._span()
        p = self.pos.value() + 1
        if p > hi:
            return lo if self.loop.isChecked() else None
        return p

    def _play(self, on):
        self.play.setText("Pause" if on else "Play")
        if on:
            self._timer.start()
        else:
            self._timer.stop()

    def _tick(self):
        if not self.ready():
            return                      # the frame is still loading
        p = self.next_position()
        if p is None:
            self.play.setChecked(False)
        else:
            self.pos.setValue(p)
