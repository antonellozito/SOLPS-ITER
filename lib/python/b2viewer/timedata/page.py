"""The page of the Run tracing tab in the quantity column: the tabs Time
traces, Profiles and Chords (each with its files only); for the time
traces what is shown with them (mean and standard deviation, rolling or
batch means) and the place chosen on the plot, for the profiles and the
chords the frames shown (as in Run movies, with Show all); in each tab
the table of its quantities (a species menu in its title), what is shown,
its plot; the chords their set, a tab per chord and the line integrals or
averages against the chord number and in time."""

import html
import re

from ...qt import QtCore, QtWidgets, Qt, Signal
from .. import catalog
from ..panels.quantity import (MOVIE_ROWS, SingleClicks, fill_tree,
                               make_tree, mark_group, tree_height)
from ..panels.species import SpeciesMenu
from ..panels.timebox import FrameBox
from ..scaling import squeezable
from ..tools.figure import FigureView
from ..tools.sections import ChordSums, ChordTab, _button

TABS = (("Time traces", "trace", "Time traces of b2time.nc: values at the "
         "separatrix at the outer midplane and at the targets, maxima and "
         "integrals over the targets, fluxes, totals"),
        ("Profiles", "profile", "Profiles of b2time.nc at the midplanes "
         "and along the targets"),
        ("Chords", "chord", "Profiles along the chords of the *.chords "
         "files of the run (b2chords.nc, eirenechords.nc), their line "
         "integrals and averages in time"),
        ("Volume tallies", "vtally", "Time traces of b2tallies.nc by "
         "volume region: averages, sources, atomic processes, energy "
         "terms, residuals"),
        ("Surface tallies", "stally", "Time traces of b2tallies.nc by face "
         "region: the fluxes through its faces"))
TRACES = ("trace", "vtally", "stally")  # time traces: the Show menu
ROWS = MOVIE_ROWS                   # rows of a table: as in Run movies
HINT = "Choose a quantity in the table"
SHOW = (("Only time trace", "trace"), ("Mean + standard deviation", "mean"),
        ("Rolling mean", "rolling"), ("Batch mean", "batch"),
        ("Phase mean", "phase"))
WINDOWED = ("rolling", "batch", "phase")
RAISED = {"sup": str.maketrans("0123456789+-", "\u2070\u00b9\u00b2\u00b3"
                               "\u2074\u2075\u2076\u2077\u2078\u2079"
                               "\u207a\u207b"),
          "sub": str.maketrans("0123456789+-", "\u2080\u2081\u2082"
                               "\u2083\u2084\u2085\u2086\u2087"
                               "\u2088\u2089\u208a\u208b")}


def plain(rich):
    """The rich text of a label (units with powers) as plain text, the
    powers raised or lowered with their characters."""
    text = re.sub(r"<(sup|sub)>(.*?)</\1>",
                  lambda m: m.group(2).translate(RAISED[m.group(1)]), rich)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


class OneRow(QtWidgets.QLabel):
    """A label always in one row: its text (rich text taken as plain) cut
    at its right end with an ellipsis where it is longer, all of it in the
    tooltip then; text() all of it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full = ""
        self.setTextFormat(Qt.PlainText)
        self.setWordWrap(False)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Preferred)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def setText(self, text):
        self._full = plain(text)
        self._fit()

    def text(self):
        return self._full

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self._fit()

    def _fit(self):
        shown = self.fontMetrics().elidedText(
            self._full, Qt.ElideRight, self.contentsRect().width())
        super().setText(shown)
        self.setToolTip(self._full if shown != self._full else "")


class TraceBox(QtWidgets.QWidget):
    """What is shown with a time trace (SHOW) and the window of frames of
    the rolling and batch means, in one row; changed() after a choice."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = QtWidgets.QComboBox()
        for text, key in SHOW:
            self.mode.addItem(text, key)
        self.mode.setToolTip("The time trace alone, with its mean and "
                             "standard deviation over the whole trace, "
                             "with its rolling means (every window of "
                             "consecutive frames), its batch means "
                             "(consecutive blocks of frames) or its phase "
                             "means (the frames one window apart, as many "
                             "means as the window)")
        self.window = QtWidgets.QSpinBox()
        self.window.setKeyboardTracking(False)
        self.window.setToolTip("Frames per window or block; phase: the "
                               "frames between those averaged together")
        self.window_label = QtWidgets.QLabel("Window")
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.addWidget(QtWidgets.QLabel("Show"))
        lay.addWidget(self.mode, 1)
        lay.addWidget(self.window_label)
        lay.addWidget(self.window)
        self.mode.currentIndexChanged.connect(self._chosen)
        self.window.valueChanged.connect(lambda *_: self.changed.emit())
        self._chosen(emit=False)

    def key(self):
        return self.mode.currentData()

    def set_frames(self, nt):
        """The window at most the nt frames of the traces (5 at first)."""
        self.window.blockSignals(True)
        self.window.setRange(1, max(nt, 1))
        self.window.setValue(min(5, max(nt, 1)))
        self.window.blockSignals(False)

    def _chosen(self, *_, emit=True):
        for w in (self.window_label, self.window):
            w.setEnabled(self.key() in WINDOWED)
        if emit:
            self.changed.emit()


class Part(QtWidgets.QWidget):
    """A tab of the page: its table, what is shown at the position, Save
    plot and Export, the plot (hidden without a quantity); chosen(item)
    after a click in the table (None: cleared)."""

    chosen = Signal(object)

    def __init__(self, title, what, settings, parent=None):
        super().__init__(parent)
        self.current = None
        self.where = QtWidgets.QLabel()     # the place of the time traces
        self.where.setWordWrap(True)
        self.where.setTextFormat(Qt.RichText)
        self.where.hide()
        self.tree = make_tree(title, "plot it")
        self.species = SpeciesMenu(self.tree, title, what, multi=True)
        self._new_click = SingleClicks()
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemActivated.connect(self._clicked)
        self.tree.itemExpanded.connect(mark_group)
        self.tree.itemCollapsed.connect(mark_group)
        self.text = OneRow()
        self.text.setText(HINT)
        self.view = FigureView(settings)
        self.view.hide()
        self.save = _button("Save plot", "This plot as an image or vector "
                            "file", lambda: self.view.save())
        self.export = _button("Export…", "The values of this plot as "
                              "a CSV file", lambda: self.view.export())
        # the fluxes along the targets: per target area (the flux density
        # on the target surface, as flush probes measure it) or per
        # poloidal contact area (the poloidal flux density)
        self.area = QtWidgets.QComboBox()
        self.area.addItem("Per target area", "target")
        self.area.addItem("Per poloidal contact area", "contact")
        self.area.setToolTip("Flux along the target divided by the target "
                             "area (the flux density on the target "
                             "surface, as flush probes measure it) or by "
                             "the poloidal contact area (the poloidal flux "
                             "density)")
        self.area.hide()
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.addWidget(self.where)
        self.lay.addWidget(self.tree)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.text, 1)
        row.addWidget(self.area)
        row.addWidget(self.save)
        row.addWidget(self.export)
        self.lay.addLayout(row)
        self.lay.addWidget(self.view)
        self._buttons(False)

    def _buttons(self, on):
        for w in (self.save, self.export):
            w.setEnabled(on)

    def set_items(self, items, keep=False, always=()):
        """The quantities of the table, every group closed (keep: those
        open before open again); the groups always there, greyed out
        without quantities."""
        tops = [self.tree.topLevelItem(i)
                for i in range(self.tree.topLevelItemCount())]
        was = {t.text(0) for t in tops if t.isExpanded()} if keep else ()
        items = catalog.components(list(items))
        fill_tree(self.tree, items, always)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            top.setExpanded(top.childCount() > 0 and top.text(0) in was)
            mark_group(top)
        self.clear()

    def items(self):
        """(tree item, quantity) of the table."""
        return [(top.child(j), top.child(j).data(0, Qt.UserRole))
                for top in (self.tree.topLevelItem(i) for i in
                            range(self.tree.topLevelItemCount()))
                for j in range(top.childCount())]

    def select(self, q):
        """q, one of the quantities of the table, chosen as by a click."""
        for it, x in self.items():
            if x is q:
                self.tree.setCurrentItem(it)
                self.current = q

    def clear(self):
        """No quantity chosen."""
        self.current = None
        self.tree.clearSelection()
        self.tree.setCurrentItem(None)
        self.species.set_columns([""])
        self.show_plot(False)

    def show_plot(self, on, text=HINT):
        self.view.setVisible(on)
        self._buttons(on)
        self.text.setText(text)

    def _clicked(self, item, *_):
        """A group: open or close it; a quantity: plot it, or clear the
        plot if it is the one plotted; a group greyed out: nothing."""
        if not item.flags() & Qt.ItemIsEnabled or not self._new_click(item):
            return
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
            return
        q = item.data(0, Qt.UserRole)
        if q is self.current:
            self.clear()
            self.chosen.emit(None)
        elif q is not None:
            self.current = q
            self.chosen.emit(q)

    def fit(self):
        tree_height(self.tree, ROWS)
        self.species.fit()

    def apply_theme(self):
        for i in range(self.tree.topLevelItemCount()):
            mark_group(self.tree.topLevelItem(i))
        if self.view.draw is not None:
            self.view.apply_theme()


class ChordPart(Part):
    """The Chords tab: the set of chords over the table; under it, as in
    the Chords section of the plots, a tab per chord of the set (numbered
    as on the plot: how it is drawn there, its ends, its line integral and
    average at the position, its profile) and the line integrals or
    averages against the chord number (two or more chords) and in time (a
    curve per chord); restyled() after a change of how a chord is drawn,
    sums_changed() after the other sums chosen."""

    restyled = Signal()
    sums_changed = Signal()

    def __init__(self, title, what, settings, parent=None):
        super().__init__(title, what, settings, parent)
        self.settings = settings
        self.set_menu = QtWidgets.QComboBox()
        self.set_menu.setToolTip("The chords of one *.chords file of the "
                                 "run")
        top = QtWidgets.QHBoxLayout()
        for w in (QtWidgets.QLabel("Chords of"), self.set_menu):
            top.addWidget(w)
        top.addStretch(1)
        self.lay.insertLayout(0, top)
        for w in (self.save, self.export, self.view):   # in the chord tabs
            w.hide()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        bar = self.tabs.tabBar()
        bar.setDrawBase(False)          # no dark band beside the tabs
        bar.setUsesScrollButtons(True)  # never wider with more chords
        bar.setExpanding(False)
        self.tabs.currentChanged.connect(self._shown)
        self.chords = []                # ChordTab
        self.board = ChordSums(settings, self.sums_changed.emit,
                               margins=(0, 0, 0, 0))
        self.which, self.sums, self.trace = (self.board.which,
                                             self.board.sums,
                                             self.board.trace)
        self.lay.addWidget(self.tabs)
        self.lay.addWidget(self.board)
        self.tabs.hide()

    def _buttons(self, on):             # the plots: in the chord tabs
        pass

    def _shown(self, *_):
        """The tabs as high as the chord shown (not as the highest)."""
        w = self.tabs.currentWidget()
        if w is not None:
            w.updateGeometry()
        self.tabs.updateGeometry()

    def set_count(self, n):
        """n chord tabs (numbered 1 to n), their ends not editable."""
        while len(self.chords) < n:
            tab = ChordTab(self.settings, self.restyled.emit)
            tab.ends.set_editable(False)
            self.chords.append(tab)
            self.tabs.addTab(tab, str(len(self.chords)))
            squeezable(tab)
        while len(self.chords) > n:
            tab = self.chords.pop()
            self.tabs.removeTab(self.tabs.indexOf(tab))
            tab.deleteLater()

    def show_plot(self, on, text=HINT):
        """The chord tabs and the sums under them (on), else the text."""
        self.text.setText(text)
        self.text.setVisible(not on)
        self.tabs.setVisible(on and bool(self.chords))
        if not on:
            self.board.set_shown(False, False)
        else:
            self.board.set_shown(len(self.chords) >= 2, bool(self.chords))

    def apply_theme(self):
        super().apply_theme()
        for tab in self.chords:
            if tab.view.draw is not None:
                tab.view.apply_theme()
        self.board.apply_theme()


class TracingPage(QtWidgets.QWidget):
    """The page: the tabs and the frames (header: never scrolled), the tab
    shown (key: "trace", "profile" or "chord"); changed() after another
    tab."""

    changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setExpanding(True)
        self.tabs.setDrawBase(True)
        for i, (text, _, tip) in enumerate(TABS):
            self.tabs.addTab(text)
            self.tabs.setTabToolTip(i, tip)
        self.frames = FrameBox(final=False, save=False)
        self.frames.set_times({})
        self.trace_box = TraceBox()
        self.show_all = QtWidgets.QCheckBox("Show all")
        self.show_all.setToolTip("The profiles of all the positions of the "
                                 "slider, the one shown over them, colours "
                                 "along them")
        self.frames.play_row.layout().addWidget(self.show_all)
        self.parts = {
            "trace": Part("Time trace", "time trace", settings),
            "profile": Part("Profile", "profile", settings),
            "chord": ChordPart("Chord quantity", "chord quantity",
                               settings),
            "vtally": Part("Volume tally", "volume tally", settings),
            "stally": Part("Surface tally", "surface tally", settings)}
        for k in TRACES:
            self.parts[k].view.options.xaxes = False
        # the tabs and the rows of the frames or of the time traces: over
        # the scrolled column (placed by the 2D tab), shown with the page
        self.header = QtWidgets.QWidget()
        hl = QtWidgets.QVBoxLayout(self.header)
        hl.setContentsMargins(0, 0, 0, 6)
        hl.addWidget(self.tabs)
        hl.addWidget(self.trace_box)
        hl.addWidget(self.frames)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        for part in self.parts.values():
            lay.addWidget(part)
            squeezable(part)
        self.tabs.currentChanged.connect(self._shown)
        self._shown()

    def key(self):
        return TABS[max(self.tabs.currentIndex(), 0)][1]

    def part(self):
        return self.parts[self.key()]

    def set_tabs(self, whys):
        """The tabs with their files ({key: why not, "" if it has them});
        the first of them shown."""
        self.tabs.blockSignals(True)
        for i, (_, key, tip) in enumerate(TABS):
            why = whys.get(key, "")
            self.tabs.setTabEnabled(i, not why)
            self.tabs.setTabToolTip(i, tip if not why else why)
        if not self.tabs.isTabEnabled(self.tabs.currentIndex()):
            first = next((i for i in range(len(TABS))
                          if self.tabs.isTabEnabled(i)), 0)
            self.tabs.setCurrentIndex(first)
        self.tabs.blockSignals(False)
        self._shown()

    def _shown(self, *_):
        key = self.key()
        for k, part in self.parts.items():
            part.setVisible(k == key)
        self.trace_box.setVisible(key in TRACES)
        self.frames.setVisible(key not in TRACES)
        self.frames.play.setChecked(False)
        self.changed.emit()

    def fit(self):
        for part in self.parts.values():
            part.fit()
