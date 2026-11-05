"""Time group of the 2D quantity panel: final state or movie frames
(b2movies.nc, eirenemovies.nc), one frame or the means b2plot computes
over a range, a rolling window or consecutive blocks of frames."""

from ..qt import QtCore, QtWidgets, Qt, Signal

MODES = [("One frame", "frame"), ("Mean over frames", "range"),
         ("Rolling mean", "rolling"), ("Batch mean", "batch")]


class TimeBox(QtWidgets.QGroupBox):
    """Source of the plotted data and the movie frames of the plot."""

    source_changed = Signal()       # final state or movie frames
    frames_changed = Signal()       # frames of the movie plot
    export_frames = Signal()

    def __init__(self, parent=None):
        super().__init__("Time", parent)
        self.times = {}                 # file -> frame times (s)
        self.file = 1                   # file of the quantity shown
        self.ready = lambda: True       # plot of the frame drawn
        form = QtWidgets.QFormLayout(self)
        self.source = QtWidgets.QComboBox()
        self.source.addItem("Final state (b2fstate)", False)
        self.source.addItem("Movie frames", True)
        self.source.setToolTip("Movie frames: b2movies.nc and "
                               "eirenemovies.nc of the run directory")
        self.mode = QtWidgets.QComboBox()
        for text, key in MODES:
            self.mode.addItem(text, key)
        self.mode.setToolTip("Means are computed by b2plot over the frames "
                             "(rolling: a window moved frame by frame; "
                             "batch: consecutive blocks of frames)")
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
        form.addRow("Data", self.source)
        form.addRow("Show", self.mode)
        form.addRow("Position", row(self.slider, self.pos))
        form.addRow("Frames", row(self.first, QtWidgets.QLabel("to"),
                                  self.last))
        form.addRow("Window", row(self.window, self.align))
        form.addRow("", row(self.play, self.fps, self.loop, export))
        form.addRow(self.info)
        self.form = form
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.source.currentIndexChanged.connect(self._source_changed)
        self.mode.currentIndexChanged.connect(lambda *_: self._layout())
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

    # ------------------------------------------------------------- state
    def set_movies(self, movies):
        """Frame times of the movie files of a new run (data.MovieFile)."""
        self.times = {f: list(m.times) for f, m in movies.items() if m.nt}
        self.source.blockSignals(True)
        self.source.setCurrentIndex(0)
        self.source.blockSignals(False)
        item = self.source.model().item(1)
        item.setEnabled(bool(self.times))
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
        return bool(self.source.currentData()) and bool(self.times)

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
        elif key == "range":
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

    def source_of(self, q):
        """(file, first, last) of a movie quantity, None for the final
        state."""
        if not getattr(q, "movie", 0) or not self.movie():
            return None
        return (q.movie,) + self.frames(q.movie)

    def positions(self):
        """Slider positions shown by Play and by Export frames."""
        if self.key() == "range":
            return [self.pos.value()]
        lo, hi = self._span()
        return list(range(lo, hi + 1))

    def time_text(self, f=None):
        """Frames and times of the current position."""
        t = self.times.get(self.file if f is None else f, [])
        if not t:
            return ""
        k1, k2 = self.frames(f)
        if k1 == k2:
            return "frame %d of %d, t = %.4g s" % (k1, len(t), t[k1 - 1])
        return "mean of frames %d\u2013%d of %d, t = %.4g\u2013%.4g s" % (
            k1, k2, len(t), t[k1 - 1], t[k2 - 1])

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
        for i in range(1, 7):
            self.form.setRowVisible(i, movie)
        if movie:
            self.form.setRowVisible(2, key != "range")
            self.form.setRowVisible(3, key == "range")
            self.form.setRowVisible(4, key in ("rolling", "batch"))
            self.align.setVisible(key == "rolling")
            self.play.setEnabled(key != "range")
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
