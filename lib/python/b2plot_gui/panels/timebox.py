"""Tabs at the top of the 2D quantity panel: Final state, Run tracing
(b2time.nc, b2chords.nc, eirenechords.nc), Run movies (b2movies.nc,
eirenemovies.nc) or Balances (balance.nc, the final state
shown); with the movies (and in Run tracing), one frame, the means over a
range, a rolling window, consecutive blocks of frames or the frames one
window apart (phase), the standard deviation over a range, each minus a
reference."""

from ...qt import QtCore, QtWidgets, Qt, Signal

MODES = [("One frame", "frame"), ("Mean over frames", "range"),
         ("Standard deviation over frames", "std"),
         ("Rolling mean", "rolling"), ("Batch mean", "batch"),
         ("Phase mean", "phase")]
MINUS = [("nothing", None), ("the first frame", "first"),
         ("the last frame", "last"), ("the mean of all frames", "all"),
         ("the final state", "final")]
RANGE = ("range", "std")            # modes over the frames first to last
WINDOWED = ("rolling", "batch", "phase")    # modes with a window


TABS = (("Final state", "The final state of the run (b2fstate)"),
        ("Run tracing", "Time traces and profiles of b2time.nc, profiles "
         "along the chords of b2chords.nc and eirenechords.nc, of the "
         "latest run in the run directory"),
        ("Run movies", "The movie frames of the run: b2movies.nc and "
         "eirenemovies.nc of the run directory"),
        ("Balances", "Parallel and radial balances of volumes picked on "
         "the plot, from balance.nc (the final state shown)"))
TRACING, MOVIES, BALANCES = 1, 2, 3     # indices of the tabs
PAGES = (TRACING, BALANCES)         # tabs with a page of their own


class FrameBox(QtWidgets.QWidget):
    """The frames of a plot: one frame, a mean or standard deviation over
    frames, minus a reference; the slider of the positions, Play; the
    frame times of each file (set_times before use, set_file: the file of
    the quantity shown)."""

    frames_changed = Signal()       # frames of the plot
    save_movie = Signal()           # Save movie... pressed

    def __init__(self, final=True, save=True, parent=None):
        super().__init__(parent)
        self.times = {}                 # file -> frame times (s)
        self.file = 1                   # file of the quantity shown
        self.ready = lambda: True       # plot of the frame drawn
        self.prepare = None     # Play: True images drawn beforehand, None
        self.show_frame = None  # being drawn, False live; show_frame(p)
        self.cancel = None      # shows the image of p; cancel: Pause
        self._cached = False    # playing the images
        self._silent = False    # the plot behind is of another position
        self.drawing = None     # position drawn into an image (not shown)
        self.buffering = False  # playing images still drawn: wait for them
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.movie_part = QtWidgets.QWidget()
        lay.addWidget(self.movie_part)
        rows = QtWidgets.QVBoxLayout(self.movie_part)
        rows.setContentsMargins(0, 4, 0, 0)
        rows.setSpacing(4)
        self.mode = QtWidgets.QComboBox()
        for text, key in MODES:
            self.mode.addItem(text, key)
        self.mode.setToolTip("Means over the frames (rolling: a window "
                             "moved frame by frame; batch: consecutive "
                             "blocks of frames; phase: the frames one "
                             "window apart, as many positions as the "
                             "window)")
        self.minus = QtWidgets.QComboBox()
        for text, key in MINUS if final else MINUS[:-1]:
            self.minus.addItem(text, key)
        self.minus.setToolTip("Reference subtracted from what is shown")
        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setTracking(False)
        self.pos = QtWidgets.QSpinBox()
        self.pos.setKeyboardTracking(False)
        self.play = QtWidgets.QToolButton()
        self.play.setText("Play")
        self.play.setCheckable(True)
        self.play.setToolTip("Play the frames one after the other")
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
        self.window.setToolTip("Frames per window or block; phase: the "
                               "frames between those averaged together")
        self.align = QtWidgets.QComboBox()
        self.align.addItem("trailing", "trailing")
        self.align.addItem("centred", "centred")
        self.align.setToolTip("Trailing: the window ends at the frame; "
                              "centred: the frame is in its middle")

        def row(*widgets, stretch=()):
            """A row of widgets (texts: labels), stretch: the indices that
            take the room (none: the room left at the end)."""
            w = QtWidgets.QWidget()
            box = QtWidgets.QHBoxLayout(w)
            box.setContentsMargins(0, 0, 0, 0)
            for i, x in enumerate(widgets):
                box.addWidget(QtWidgets.QLabel(x) if isinstance(x, str)
                              else x, 1 if i in stretch else 0)
            if not stretch:
                box.addStretch(1)
            rows.addWidget(w)
            return w
        row("Show", self.mode, "minus", self.minus, stretch=(1, 3))
        self.position_row = row(self.slider, self.pos, stretch=(0,))
        self.frames_row = row("Frames", self.first, "to", self.last,
                              stretch=(1, 3))
        self.place = QtWidgets.QStackedWidget()     # one of the two, in a
        rows.insertWidget(1, self.place)            # place as high for both
        for w in (self.position_row, self.frames_row):
            self.place.addWidget(w)
        self.window_row = QtWidgets.QWidget()   # WINDOWED: right of
        box = QtWidgets.QHBoxLayout(self.window_row)    # Play, no own row
        box.setContentsMargins(0, 0, 0, 0)
        for w in (QtWidgets.QLabel("Window"), self.window, self.align):
            box.addWidget(w)
        self.save = QtWidgets.QPushButton("Save movie…")
        self.save.setToolTip("All positions of the slider as a movie file "
                             "(MP4, MOV, WebM, AVI with ffmpeg; animated "
                             "GIF) at the frame rate set")
        self.save.clicked.connect(lambda *_: self.save_movie.emit())
        self.save.setVisible(save)
        self.play_row = row(self.play, self.fps, self.loop, self.save,
                            QtWidgets.QWidget(), self.window_row,
                            stretch=(4,))
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.mode.currentIndexChanged.connect(lambda *_: self._layout())
        self.minus.currentIndexChanged.connect(lambda *_: self._layout())
        self.slider.valueChanged.connect(self.pos.setValue)
        self.slider.sliderMoved.connect(self._dragged)  # images: at once
        self.pos.valueChanged.connect(self._moved)
        self._settle = QtCore.QTimer(self)  # the live plot once the slider
        self._settle.setSingleShot(True)    # rests (images shown before)
        self._settle.setInterval(300)
        self._settle.timeout.connect(self._rest)
        self._wanted = None     # position dragged to, drawn once ready
        self._chase = QtCore.QTimer(self)
        self._chase.setSingleShot(True)
        self._chase.setInterval(20)
        self._chase.timeout.connect(self._follow)
        for w in (self.first, self.last, self.window):
            w.valueChanged.connect(lambda *_: self._layout())
        self.align.currentIndexChanged.connect(lambda *_: self._layout())
        self.play.toggled.connect(self._play)
        self.fps.valueChanged.connect(
            lambda v: self._timer.setInterval(int(1000 / v)))
        self._timer.setInterval(250)

    # ------------------------------------------------------------- state
    def active(self):
        """The frames are shown (the controls with them)."""
        return bool(self.times)

    def set_times(self, times, file=None):
        """Frame times of each file (file -> times), the file shown (the
        first by default); the whole range, a window of 5."""
        self.times = {f: list(t) for f, t in times.items() if len(t)}
        self.file = file if file in self.times else min(self.times) if \
            self.times else 1
        nt = self._ranges()
        self.first.setValue(1)
        self.last.setValue(max(nt, 1))
        self.window.blockSignals(True)
        self.window.setValue(min(5, max(nt, 1)))
        self.window.blockSignals(False)
        self.play.setChecked(False)
        self._layout(emit=False)

    def _ranges(self):
        """The frames of the file shown in the ranges of the first and last
        frames and of the window; its number of frames."""
        nt = self.nt()
        for s in (self.first, self.last, self.window):
            s.blockSignals(True)
            s.setRange(1, max(nt, 1))
            s.blockSignals(False)
        return nt

    def key(self):
        return self.mode.currentData()

    def nt(self, f=None):
        return len(self.times.get(self.file if f is None else f, []))

    def set_file(self, f):
        """File of the quantity shown."""
        if f in self.times and f != self.file:
            self.file = f
            self._ranges()
            self._layout(emit=False)

    def reference(self, f=None):
        """(first, last) frames of the reference subtracted, "final" or
        None."""
        nt = self.nt(f)
        return {"first": (1, 1), "last": (nt, nt), "all": (1, nt),
                "final": "final"}.get(self.minus.currentData())

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
        if key == "phase":
            return 1, max(min(w, nt), 1)
        return 1, max(nt, 1)

    def frames_at(self, p, f=None):
        """(first, last) frame of slider position p for file f (phase:
        those of the frames one window apart, frame_list)."""
        nt, w = self.nt(f), self.window.value()
        key = self.key()
        if key == "frame":
            k1 = k2 = p
        elif key in RANGE:
            k1, k2 = sorted((self.first.value(), self.last.value()))
        elif key == "rolling":
            h = w // 2 if self.align.currentData() == "centred" else w - 1
            k1, k2 = p - h, p - h + w - 1
        elif key == "phase":
            k1, k2 = p, p + w * (max(nt - p, 0) // w)
        else:
            k1, k2 = (p - 1) * w + 1, p * w
        k2 = min(k2, max(nt, 1))
        return min(max(k1, 1), k2), k2

    def frames(self, f=None):
        return self.frames_at(self.position(), f)

    def step(self):
        """Frames from one averaged to the next: the window with phase,
        else 1."""
        return self.window.value() if self.key() == "phase" else 1

    def frame_list(self, p=None, f=None):
        """The frames averaged at slider position p (default the one read
        and drawn) for file f."""
        k1, k2 = self.frames(f) if p is None else self.frames_at(p, f)
        return list(range(k1, k2 + 1, self.step()))

    def time_at(self, p, f=None):
        """Time of position p: its frame, the middle of the frames averaged
        (phase: the first of them, the phase within the first window)."""
        t = self.times.get(self.file if f is None else f, [])
        if not t:
            return None
        k1, k2 = self.frames_at(p, f)
        return t[k1 - 1] if self.key() == "phase" else \
            0.5 * (t[k1 - 1] + t[k2 - 1])

    def position(self):
        """The position whose frames are read and drawn: the one shown, or
        the one drawn into an image of the movie."""
        return self.pos.value() if self.drawing is None else self.drawing

    def draw_position(self, p):
        """The frames of position p read and drawn (into an image of the
        movie) while the slider stays; None: those shown again."""
        self.drawing = p
        self.frames_changed.emit()

    def positions(self):
        """Slider positions shown by Play (the chords: Show all)."""
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
            return "t = %.4g s%s" % (t[k1 - 1], minus)
        if self.key() == "phase":
            return "phase mean between t = %.4g – %.4g s%s" % (
                t[k1 - 1], t[k2 - 1], minus)
        return "%s between t = %.4g – %.4g s%s" % (
            "standard deviation" if self.key() == "std" else "mean",
            t[k1 - 1], t[k2 - 1], minus)

    def time_value(self, f=None):
        """Time of the position read and drawn (time_at)."""
        return self.time_at(self.position(), f)

    def _tip(self):
        """The frames and times shown, in the tooltips of the position."""
        text = self.time_text()
        for w in (self.slider, self.pos, self.first, self.last):
            w.setToolTip(text)

    def set_position(self, p):
        self.pos.setValue(p)

    # ---------------------------------------------------------- widgets
    def _layout(self, emit=True):
        active = self.active()
        key = self.key()
        self.movie_part.setVisible(active)
        if active:
            self.place.setCurrentWidget(self.frames_row if key in RANGE
                                        else self.position_row)
            self.window_row.setVisible(key in WINDOWED)
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
            self.pos.setPrefix({"batch": "block ", "phase": "phase "}.get(
                key, "frame "))
            self._tip()
        if emit and active:
            self.frames_changed.emit()

    def _image(self, p):
        """The prepared image of position p shown (not playing), the plot
        drawn once the slider rests; False if there is none for the plot
        of now."""
        if self.play.isChecked() or not self.show_frame or \
                not self.show_frame(p, True):
            return False
        self.jump(p)
        self._settle.start()
        return True

    def _dragged(self, p):
        """The slider dragged: prepared images follow it at once, else the
        plot is drawn at each position as soon as the one before is (the
        positions passed meanwhile skipped)."""
        if self._image(p):
            return
        self._wanted = p
        self._follow()

    def _follow(self):
        if self._wanted is None:
            return
        if not self.ready():
            self._chase.start()         # the frame before still loading
            return
        p, self._wanted = self._wanted, None
        self.pos.setValue(p)

    def rest(self):
        """The plot of the position shown drawn once the slider rests."""
        self._settle.start()

    def _rest(self):
        if self._silent and not self.play.isChecked():
            self._silent = False
            self.frames_changed.emit()

    def _moved(self, p):
        if self._image(p):
            return
        self._silent = False            # drawn now
        self.slider.blockSignals(True)
        self.slider.setValue(p)
        self.slider.blockSignals(False)
        self._tip()
        if self.active():
            self.frames_changed.emit()

    def next_position(self):
        """Position after the current one (None at the end, no loop)."""
        lo, hi = self._span()
        p = self.pos.value() + 1
        if p > hi:
            return lo if self.loop.isChecked() else None
        return p

    def _play(self, on):
        """Play: the images of the positions drawn first (prepare), then
        shown at the frame rate; Pause or the end: the plot of the
        position shown drawn again."""
        self.play.setText("Pause" if on else "Play")
        if on:
            ready = self.prepare() if self.prepare else False
            if ready is None:           # start() once drawn
                self.play.setText("Preparing…")
            else:
                self._cached = bool(ready)
                self._timer.start()
        else:
            self._timer.stop()
            self._cached = False
            if self.cancel:
                self.cancel()
            if self._silent:
                self._silent = False
                self.frames_changed.emit()

    def start(self):
        """The images drawn: the movie starts."""
        if self.play.isChecked():
            self.play.setText("Pause")
            self._cached = True
            self._timer.start()

    def playing_images(self):
        return self.play.isChecked() and self._cached

    def jump(self, p, silent=True):
        """Position p shown by its image (silent: the plot behind is of
        another position): the slider and the number follow, nothing is
        read or drawn."""
        for w in (self.slider, self.pos):
            w.blockSignals(True)
            w.setValue(p)
            w.blockSignals(False)
        self._tip()
        self._silent = silent

    def _tick(self):
        p = self.next_position()
        if self._cached:
            if p is None:
                self.play.setChecked(False)
            elif self.show_frame and self.show_frame(p):
                self.jump(p)
            elif not self.buffering:    # no image: as the frames come
                self._cached = False
            return                      # buffering: its image comes
        if not self.ready():
            return                      # the frame is still loading
        if p is None:
            self.play.setChecked(False)
        else:
            self.pos.setValue(p)


class TimeBox(FrameBox):
    """Source of the plotted data (the tabs, source: placed by the 2D tab
    over the scrolled panel, so that they never scroll away) and, with the
    movies, the frames of the plot."""

    source_changed = Signal()       # final state or movie frames

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mode.setToolTip("Means are computed by b2plot over the frames "
                             "(rolling: a window moved frame by frame; "
                             "batch: consecutive blocks of frames; phase: "
                             "the frames one window apart, as many "
                             "positions as the window)")
        self.minus.setToolTip("Reference subtracted from what is shown "
                              "(b2plot m-); the final state needs a movie "
                              "variable that is also a b2plot label")
        self.play.setToolTip("Play the movie; the next frame is loaded "
                             "while the current one is shown")
        self.source = QtWidgets.QTabBar()
        self.source.setExpanding(True)
        self.source.setDrawBase(True)
        for i, (text, tip) in enumerate(TABS):
            self.source.addTab(text)
            self.source.setTabToolTip(i, tip)
        self.source.currentChanged.connect(self._source_changed)
        self.set_movies({})
        self.set_tracing(False, "no run")
        self.set_balances(False, "no run")

    def active(self):
        return self.movie()

    # ------------------------------------------------------------- state
    def set_movies(self, movies, stale=(), final=True, why=""):
        """Frame times of the movie files of the latest run of a new run
        directory (data.MovieFile); stale: why the other ones are left out;
        final: a final state of the run (else why not; with why: what it
        is, the plasma when an error stopped B2.5)."""
        times = {f: m.times for f, m in movies.items() if m.nt}
        self.source.setTabEnabled(0, final)
        self.source.setTabToolTip(0, ("Final state: " + why if why else
                                      TABS[0][1]) if final else
                                  "No final state: " + why)
        self.source.setTabEnabled(MOVIES, bool(times))
        tip = TABS[MOVIES][1] if times else "No movie files (b2movies.nc, " \
            "eirenemovies.nc) of the latest run in the run directory"
        self.source.setTabToolTip(MOVIES, "\n".join([tip] + list(stale)))
        self.source.blockSignals(True)
        self.source.setCurrentIndex(MOVIES if not final and times else 0)
        self.source.blockSignals(False)
        self.set_times(times)

    def movie(self):
        return self.source.currentIndex() == MOVIES and bool(self.times)

    def balances(self):
        return self.source.currentIndex() == BALANCES

    def tracing(self):
        return self.source.currentIndex() == TRACING

    def page(self):
        """The tab with a page of its own shown (TRACING, BALANCES), or
        None."""
        i = self.source.currentIndex()
        return i if i in PAGES else None

    def set_balances(self, ok, why=""):
        """The Balances tab only with a balance.nc of this state (else
        why not in its tooltip)."""
        self.source.setTabEnabled(BALANCES, ok)
        self.source.setTabToolTip(BALANCES, TABS[BALANCES][1] if ok else
                                  "No balances: " + why)

    def set_tracing(self, ok, why=""):
        """The Run tracing tab only with tracing files of the latest run
        (else why not in its tooltip)."""
        self.source.setTabEnabled(TRACING, ok)
        self.source.setTabToolTip(TRACING, TABS[TRACING][1] if ok else
                                  "No run tracing: " + why)

    def final(self):
        """The final state of the run can be shown."""
        return self.source.isTabEnabled(0)

    def source_of(self, q, p=None):
        """(file, first, last[, statistic, reference]) of a movie quantity
        at slider position p (default the current one), None for the
        final state; the statistic "mean", "std" or ("step", n): the mean
        of every n-th frame from first to last."""
        if not getattr(q, "movie", 0) or not self.movie():
            return None
        source = (q.movie,) + (self.frames(q.movie) if p is None else
                               self.frames_at(p, q.movie))
        ref = self.reference(q.movie)
        stat = {"std": "std", "phase": ("step", self.step())}.get(
            self.key(), "mean")
        return source if stat == "mean" and ref is None else \
            source + (stat, ref)

    # ---------------------------------------------------------- widgets
    def _source_changed(self, *_):
        self.play.setChecked(False)
        self._layout(emit=False)
        self.source_changed.emit()
