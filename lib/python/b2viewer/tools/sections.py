"""Sections of the quantity column for the chords and the statistics of the
quantity shown (opened from the Species row): buttons, the summary, the
figure and its options. The chords have a tab each (numbered as on the
plot: how it is drawn there, its ends, its profile), and under the tabs
the line integrals or averages against the chord number (two or more
chords) and in time (ChordSums; the Chords tab of Run tracing has the same
tabs and plots)."""

from ..panels.glyphs import LineStyleChooser, WidthChooser
from ..panels.layers import ColorButton
from ..scaling import squeezable
from ...qt import QtCore, QtWidgets, Qt
from .figure import FigureView, LineEnds

SOURCES = (("Drawn", "drawn"), (".chords files", "run"))
TARGETS = (("Plasma", "plasma"), ("Vector", "vector"))
LOOK = ("#d62728", 1.3, "--", True)     # colour, width, style, number
SUMS = (("Line integrals", "integral"), ("Line averages", "average"))


def _button(text, tip, slot, checkable=False):
    b = QtWidgets.QPushButton(text)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    (b.toggled if checkable else b.clicked).connect(
        lambda *a: slot(*a[:1]) if checkable else slot())
    return b


def _text():
    label = QtWidgets.QLabel()
    label.setWordWrap(True)
    label.setTextFormat(Qt.RichText)    # units with superscripts
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


class ChordTab(QtWidgets.QWidget):
    """One chord: how it is drawn on the plot, its ends, the sums along
    it with Save plot and Export of its profile at their right, its
    profile; under it (second, shown with a plasma and a vector quantity
    plotted) the same for the vector quantity; restyled() after a change
    of how it is drawn."""

    def __init__(self, settings, restyled, parent=None):
        super().__init__(parent)
        self.line_colour = ColorButton(LOOK[0])
        self.line_colour.setToolTip("Colour of the chord on the plot")
        self.line_width = WidthChooser(LOOK[1])
        self.line_style = LineStyleChooser(LOOK[2])
        self.number = QtWidgets.QCheckBox("number")
        self.number.setChecked(LOOK[3])
        self.number.setToolTip("The number of the chord at its end")
        self.line_colour.changed.connect(lambda *_: restyled())
        self.line_width.currentIndexChanged.connect(lambda *_: restyled())
        self.line_style.currentIndexChanged.connect(lambda *_: restyled())
        self.number.toggled.connect(lambda *_: restyled())
        look = QtWidgets.QHBoxLayout()
        look.addWidget(QtWidgets.QLabel("On the plot"))
        for w in (self.line_colour, self.line_width, self.line_style,
                  self.number):
            look.addWidget(w)
        look.addStretch(1)
        self.text = _text()
        self.ends = LineEnds()
        self.view = FigureView(settings)
        save = _button("Save plot", "The profile of this chord as an image "
                       "or vector file", lambda: self.view.save())
        export = _button("Export…", "The profile of this chord as a CSV "
                         "file", lambda: self.view.export())
        sums = QtWidgets.QHBoxLayout()
        sums.addWidget(self.text, 1)
        sums.addWidget(save)
        sums.addWidget(export)
        self.text_v = _text()           # the vector quantity, under it
        self.view_v = FigureView(settings)
        self.second = QtWidgets.QWidget()
        rows = QtWidgets.QVBoxLayout(self.second)
        rows.setContentsMargins(0, 0, 0, 0)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.text_v, 1)
        row.addWidget(_button("Save plot", "The profile of the vector "
                              "quantity along this chord as an image or "
                              "vector file", lambda: self.view_v.save()))
        row.addWidget(_button("Export…", "The profile of the vector "
                              "quantity along this chord as a CSV file",
                              lambda: self.view_v.export()))
        rows.addLayout(row)
        rows.addWidget(self.view_v)
        self.second.hide()
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 6, 4, 0)
        lay.addLayout(look)
        lay.addWidget(self.ends)
        lay.addLayout(sums)
        lay.addWidget(self.view)
        lay.addWidget(self.second)

    def sizeHint(self):                 # hidden: no room taken in the tabs
        s = super().sizeHint()
        return s if not self.isHidden() else QtCore.QSize(s.width(), 0)

    def minimumSizeHint(self):          # the height: for its width only
        return QtCore.QSize(super().minimumSizeHint().width(), 0)

    def heightForWidth(self, w):
        return super().heightForWidth(w) if not self.isHidden() else 0

    def look(self):
        """(colour, width, line style, number) of the chord on the plot."""
        return (self.line_colour.color(), self.line_width.value(),
                self.line_style.currentData(), self.number.isChecked())

    def set_look(self, look):
        widgets = (self.line_colour, self.line_width, self.line_style,
                   self.number)
        for w in widgets:
            w.blockSignals(True)
        self.line_colour.set_color(look[0])
        self.line_width.setValue(look[1])
        i = self.line_style.findData(look[2])
        self.line_style.setCurrentIndex(max(i, 0))
        self.number.setChecked(look[3])
        for w in widgets:
            w.blockSignals(False)


class ChordSums(QtWidgets.QWidget):
    """Under the chord tabs: the line integrals or averages (one menu for
    all the plots, in the row of the first one shown) against the chord
    number (two or more chords) and in time (a curve per chord), each plot
    with Save plot and Export; with a plasma and a vector quantity both
    (second: sums_v, trace_v under the plasma ones); changed() after
    another choice in the menu."""

    def __init__(self, settings, changed, margins=(4, 0, 4, 0),
                 parent=None):
        super().__init__(parent)
        self.which = QtWidgets.QComboBox()
        for text, key in SUMS:
            self.which.addItem(text, key)
        self.which.setToolTip("The line integrals or the line averages, "
                              "against the chord number and in time")
        self.which.currentIndexChanged.connect(lambda *_: changed())
        self.sums, self.sums_box, self.sums_row = self._plot(
            settings, "The integrals and averages of the chords as a CSV "
            "file", margins)
        self.trace, self.trace_box, self.trace_row = self._plot(
            settings, "The integrals and averages of the chords in time as "
            "a CSV file", margins)
        self.sums_v, self.sums_v_box, _ = self._plot(
            settings, "The integrals and averages of the vector quantity "
            "along the chords as a CSV file", margins)
        self.trace_v, self.trace_v_box, _ = self._plot(
            settings, "The integrals and averages of the vector quantity "
            "along the chords in time as a CSV file", margins)
        self.margins = margins
        self.trace.options.xaxes = False
        self.trace_v.options.xaxes = False
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        for box in (self.sums_box, self.sums_v_box, self.trace_box,
                    self.trace_v_box):
            lay.addWidget(box)
        squeezable(self)
        self.set_shown(False, False)

    @staticmethod
    def _plot(settings, tip, margins):
        view = FigureView(settings)
        save = _button("Save plot", "This plot as an image or vector file",
                       lambda: view.save())
        export = _button("Export…", tip, lambda: view.export())
        box = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(save)
        row.addWidget(export)
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(*margins)
        lay.setSpacing(2)
        lay.addLayout(row)
        lay.addWidget(view)
        squeezable(box)
        return view, box, row

    def key(self):
        """"integral" or "average"."""
        return self.which.currentData()

    def set_shown(self, sums, trace, second=False):
        """The plot against the chord number, the one in time (second: those
        of the vector quantity too); the menu in the row of the first
        one."""
        row = self.sums_row if sums or not trace else self.trace_row
        if row.indexOf(self.which) != 0:
            for other in (self.sums_row, self.trace_row):
                other.removeWidget(self.which)
            row.insertWidget(0, self.which)
        left, top, right, bottom = self.margins
        self.trace_box.layout().setContentsMargins(     # apart from the
            left, top + (8 if sums else 0), right, bottom)  # options above
        self.sums_box.setVisible(sums)
        self.trace_box.setVisible(trace)
        self.sums_v_box.setVisible(sums and second)
        self.trace_v_box.setVisible(trace and second)
        for box in (self.sums_v_box, self.trace_v_box):
            box.layout().setContentsMargins(left, top + 8, right, bottom)
        self.setVisible(sums or trace)

    def apply_theme(self):
        for view in (self.sums, self.trace, self.sums_v, self.trace_v):
            if view.draw is not None:
                view.apply_theme()


class ChordsSection(QtWidgets.QGroupBox):
    """The chords drawn or typed, or (never mixed) those of the *.chords
    files of the run; Draw chord (two clicks on the plot, one chord each,
    as long as it is on), Show all (with the movies: the profiles and
    sums of all the frames), with a plasma and a vector quantity plotted
    the one measured, Close;
    tabs: one per chord (x removes a drawn one), "+" adds one to type its
    ends, Clear all removes them all; under them (ChordSums) the line
    integrals or averages against the chord number (two or more) and,
    with a movie quantity, in time. The owner (tools.control.Tools) fills
    it."""

    def __init__(self, owner, settings, parent=None):
        super().__init__("Chords", parent)
        self.owner, self.settings = owner, settings
        self.source = QtWidgets.QComboBox()
        for text, key in SOURCES:
            self.source.addItem(text, key)
        self.source.setToolTip("The chords drawn on the plot or typed, or "
                               "those of the *.chords files of the run "
                               "(the two are kept apart)")
        self.source.currentIndexChanged.connect(
            lambda *_: owner.set_source(self.source.currentData()))
        self.draw = _button("Draw chord", "Click the two ends of a chord on "
                            "the plot (each two clicks a new chord, until "
                            "this is off)", owner.draw_chords, True)
        close = _button("Close", "Close the section (the chords are kept)",
                        lambda: owner.open_section(None))
        self.target = QtWidgets.QComboBox()     # with both plotted only
        for text, key in TARGETS:
            self.target.addItem(text, key)
        self.target.setToolTip("The sums under the tabs of the plasma "
                               "quantity or of the vector quantity plotted "
                               "(the tabs show the profiles of both)")
        self.target.currentIndexChanged.connect(owner.set_target)
        self.target.hide()
        self.show_all = QtWidgets.QCheckBox("Show all")
        self.show_all.setToolTip("The profiles and the sums of all the "
                                 "frames, the frame shown over them, colours "
                                 "along the frames")
        self.show_all.toggled.connect(lambda on: owner.set_show_all(on))
        self.show_all.hide()            # with the movies only
        self.per_sr = QtWidgets.QCheckBox("per steradian")
        self.per_sr.setToolTip("The spectrum and its total per steradian "
                               "(the emission in all directions over 4π)")
        self.per_sr.hide()              # with the spectrum only
        self.shapes = QtWidgets.QCheckBox("Line shapes")
        self.shapes.setToolTip(
            "The lines with their shapes: Doppler broadening at the "
            "temperature of their emitters, shift by the flow along the "
            "chord (seen from its first end), Zeeman splitting, Stark "
            "broadening of Balmer alpha and beta, the instrument width")
        self.continua = QtWidgets.QCheckBox("Continua")
        self.continua.setChecked(True)
        self.continua.setToolTip("Bremsstrahlung and recombination "
                                 "continua of all the ions under the lines")
        self.instrument = QtWidgets.QDoubleSpinBox()
        self.instrument.setRange(0.0, 10.0)
        self.instrument.setDecimals(3)
        self.instrument.setSingleStep(0.01)
        self.instrument.setSuffix(" nm")
        self.instrument.setToolTip("Full width at half maximum of the "
                                   "instrument function (Gaussian)")
        self.shape_row = QtWidgets.QWidget()   # with the spectrum only
        row = QtWidgets.QHBoxLayout(self.shape_row)
        row.setContentsMargins(0, 0, 0, 0)
        for w in (self.shapes, self.continua,
                  QtWidgets.QLabel("instrument width"), self.instrument):
            row.addWidget(w)
        row.addStretch(1)
        self.shapes.toggled.connect(self._shape_states)
        self._shape_states()
        self.shape_row.hide()
        top = QtWidgets.QHBoxLayout()
        for w in (self.source, self.draw):
            top.addWidget(w)
        top.addStretch(1)
        top.addWidget(self.show_all)
        top.addWidget(self.per_sr)
        top.addWidget(self.target)
        top.addWidget(close)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        bar = self.tabs.tabBar()
        bar.setDrawBase(False)          # no dark band beside the tabs
        bar.setUsesScrollButtons(True)  # never wider with more chords
        bar.setExpanding(False)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._shown)
        corner = QtWidgets.QWidget()
        cl = QtWidgets.QHBoxLayout(corner)
        cl.setContentsMargins(0, 0, 0, 0)
        add = QtWidgets.QToolButton()
        add.setText("+")
        add.setToolTip("A new chord whose ends you type (at first those of "
                       "the chord shown)")
        add.clicked.connect(lambda *_: owner.add_chord())
        clear = QtWidgets.QToolButton()
        clear.setText("Clear all")
        clear.setToolTip("Remove every chord")
        clear.clicked.connect(lambda *_: owner.clear_chords())
        cl.addWidget(add)
        cl.addWidget(clear)
        self.add, self.clear = add, clear
        self.tabs.setCornerWidget(corner)
        self.hint = QtWidgets.QLabel("No chord yet: Draw chord, or + to type "
                                     "the ends of one")
        self.hint.setProperty("muted", True)
        # under the tabs: against the chord number (two or more chords)
        # and in time (Run movies), one menu for both
        self.board = ChordSums(settings, owner.show_sums)
        self.which, self.sums, self.trace = (self.board.which,
                                             self.board.sums,
                                             self.board.trace)
        self.sums_v, self.trace_v = self.board.sums_v, self.board.trace_v
        self.sums_box = self.board.sums_box
        self.chords = []                # ChordTab
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.shape_row)
        lay.addWidget(self.hint)
        lay.addWidget(self.tabs)
        lay.addWidget(self.board)

    def set_spectrum(self, on):
        """The section as Spectrum (the spectrum of each chord) or as
        Chords."""
        self.setTitle("Spectrum" if on else "Chords")
        self.per_sr.setVisible(on)
        self.shape_row.setVisible(on)
        for t in self.chords:
            t.view.options.keep_limits = False

    def _shape_states(self, *_):
        for w in (self.continua, self.instrument):
            w.setEnabled(self.shapes.isChecked())

    def shape_options(self):
        """(instrument width nm, continua) of the line shapes."""
        return (self.instrument.value(), self.continua.isChecked())

    def set_editable(self, on):
        """Chords drawn or typed (True) or those of the run (False)."""
        for w in (self.draw, self.add, self.clear):
            w.setEnabled(on)
        self._crosses()
        for tab in self.chords:
            tab.ends.set_editable(on)
        self.hint.setText("No chord yet: Draw chord, or + to type the ends "
                          "of one" if on else "No *.chords file in the run "
                          "directory")

    def current(self):
        """The FigureView of the chord shown."""
        w = self.tabs.currentWidget()
        return w.view if isinstance(w, ChordTab) else FigureView(
            self.settings)

    def _crosses(self):
        """The crosses of the tabs only for chords drawn or typed: hidden,
        not removed (without them the tab bar is lower than the buttons
        beside it, and Qt leaves the difference empty under the tab)."""
        bar = self.tabs.tabBar()
        for i in range(bar.count()):
            for side in (QtWidgets.QTabBar.LeftSide,
                         QtWidgets.QTabBar.RightSide):
                b = bar.tabButton(i, side)
                if b is not None:
                    b.setVisible(self.add.isEnabled())

    def _shown(self, *_):
        """The tabs as high as the chord shown (not as the highest)."""
        w = self.tabs.currentWidget()
        if w is not None:
            w.updateGeometry()
        self.tabs.updateGeometry()

    def _close_tab(self, i):
        w = self.tabs.widget(i)
        if isinstance(w, ChordTab):
            self.owner.remove_chord(self.chords.index(w))

    def set_count(self, n, trace=False, second=False):
        """n chord tabs (numbered 1 to n); the sums with two or more, the
        sums in time (trace) with one or more (second: those of the vector
        quantity too)."""
        while len(self.chords) < n:
            k = len(self.chords)
            tab = ChordTab(self.settings, lambda k=k: self.owner.restyle(k))
            self.chords.append(tab)
            self.tabs.addTab(tab, str(k + 1))
            squeezable(tab)
        while len(self.chords) > n:
            tab = self.chords.pop()
            self.tabs.removeTab(self.tabs.indexOf(tab))
            tab.deleteLater()
        for k, tab in enumerate(self.chords):
            self.tabs.setTabText(k, str(k + 1))
            tab.ends.set_editable(self.add.isEnabled())
        self._crosses()
        self.tabs.setVisible(n > 0)
        self.hint.setVisible(n == 0)
        self.board.set_shown(n >= 2, trace and n >= 1, second)

    def moved(self, tab, coords):
        """New ends typed in a chord tab."""
        if tab in self.chords:
            self.owner.move_chord(self.chords.index(tab), coords)

    def show_chord(self, k):
        self.tabs.setCurrentWidget(self.chords[k])


class StatisticsSection(QtWidgets.QGroupBox):
    """Statistics of the quantity shown over the whole domain shown (the
    cells in the view), a box or a polygon drawn on the plot; Save plot,
    Export, Close; the summary and the histogram of the last choice."""

    def __init__(self, owner, settings, parent=None):
        super().__init__("Statistics", parent)
        self.owner = owner
        domain = _button("Whole domain", "Over the cells shown in the view "
                         "(again after each zoom or pan)",
                         lambda: owner.statistics_of("shown"))
        self.box = _button("Draw box", "Click two corners on the plot",
                           lambda on: owner.draw_statistics("box", on), True)
        self.polygon = _button("Draw polygon", "Click the corners on the "
                               "plot, then the first one again",
                               lambda on: owner.draw_statistics("polygon",
                                                                on), True)
        self.view = FigureView(settings)
        save = _button("Save plot", "The histogram as an image or vector "
                       "file", lambda: self.view.save())
        export = _button("Export…", "The values of the cells as a CSV file",
                         lambda: self.view.export())
        close = _button("Close", "Close the section",
                        lambda: owner.open_section(None))
        top = QtWidgets.QGridLayout()
        for c, b in enumerate((domain, self.box, self.polygon)):
            top.addWidget(b, 0, c)
        for c, b in enumerate((save, export)):
            top.addWidget(b, 1, c)
        top.addWidget(close, 1, 2)
        self.heading = _text()
        self.heading.setTextFormat(Qt.PlainText)
        self.heading.setProperty("bold", True)
        self.text = _text()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.heading)
        lay.addWidget(self.text)
        lay.addWidget(self.view)
