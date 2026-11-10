"""Layout of the 2D tab, as AUGVIEW: three columns with fixed fractions of
the width, the commands over the plot (Zoom, Unzoom, Rezoom, Restore,
Pan, the mouse tools, Add to page, Print figure; the view and the cursor
readout under them) and a canvas whose plot scales with the window."""

from ...qt import FigureCanvasQTAgg, QtCore, QtWidgets, Qt

NAV = (("Zoom", "zoom", "Drag a box to zoom in"),
       ("Unzoom", "back", "Back to the previous view"),
       ("Rezoom", "forward", "Forward to the next view"),
       ("Restore", "restore", "The full view of the run"),
       ("Pan", "pan", "Drag to move the view"))
READOUT = "R = --\nZ = --"


class ScaledCanvas(FigureCanvasQTAgg):
    """Canvas whose figure keeps its size in inches once frozen: the dpi
    follows the width of the widget, so that texts, margins and lines
    grow and shrink with the window and the plot box keeps its place."""

    def __init__(self, figure, resized=None):
        super().__init__(figure)
        self.inches = None
        self.resized = resized      # called after each resize

    def freeze(self):
        """The present size becomes the reference."""
        if self.width() > 0:
            self.inches = self.width() / self.figure._original_dpi

    def resizeEvent(self, event):
        if self.inches and event.size().width() > 0:
            dpi = event.size().width() / self.inches
            self.figure._original_dpi = dpi
            self.figure._set_dpi(dpi * self.device_pixel_ratio,
                                 forward=False)
        super().resizeEvent(event)
        if self.resized is not None:
            self.resized()


class Columns(QtWidgets.QWidget):
    """Widgets side by side at fixed fractions of the width (no splitter:
    the columns cannot be resized)."""

    def __init__(self, widgets, fractions, parent=None):
        super().__init__(parent)
        self.widgets, self.fractions = list(widgets), list(fractions)
        for w in self.widgets:
            w.setParent(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        x, width, height = 0, self.width(), self.height()
        for i, (w, f) in enumerate(zip(self.widgets, self.fractions)):
            dx = width - x if i == len(self.widgets) - 1 else round(f * width)
            w.setGeometry(x, 0, dx, height)
            x += dx

    def minimumSizeHint(self):
        return QtCore.QSize(0, 0)


def _button(text, tip, slot=None, checkable=False):
    b = QtWidgets.QPushButton(text)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Fixed)
    if slot is not None:
        (b.toggled if checkable else b.clicked).connect(
            lambda *a: slot(*a[:1]) if checkable else slot())
    return b


class PlotCommands(QtWidgets.QWidget):
    """The commands over the plot of a Tab2D (its hidden matplotlib
    navigation bar does the zooming and panning)."""

    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.tab, self.nav = tab, tab.toolbar
        self.buttons = {}
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)
        for text, key, tip in NAV:
            checkable = key in ("zoom", "pan")
            slot = (lambda on, k=key: self._mode(k, on)) if checkable else \
                {"back": lambda: self._step(self.nav.back),
                 "forward": lambda: self._step(self.nav.forward),
                 "restore": self.restore}[key]
            self.buttons[key] = _button(text, tip, slot, checkable)
            row.addWidget(self.buttons[key], 1)
        row.addSpacing(10)
        bar = tab.tools.bar
        for b in list(bar.buttons.values()) + [bar.stats]:
            b.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                            QtWidgets.QSizePolicy.Fixed)
        row.addWidget(bar, len(bar.buttons) + 1)
        bar.changed.connect(self.sync)
        row.addSpacing(10)
        self.buttons["page"] = _button(
            "Add to page", "Add this plot with all its settings to the page "
            "composer", tab._add_to_page)
        self.buttons["print"] = _button(
            "Print figure", "The plot as an image or vector file: format, "
            "resolution, colour space and theme", tab.print_figure)
        row.addWidget(self.buttons["page"], 1)
        row.addWidget(self.buttons["print"], 1)
        self.readout = QtWidgets.QLabel(READOUT)
        self.readout.setObjectName("readout")
        self.readout.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.readout.setToolTip("Position, cell and value under the cursor")
        self.readout.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                   QtWidgets.QSizePolicy.Preferred)
        second = QtWidgets.QHBoxLayout()
        second.addWidget(tab.viewbar)
        second.addWidget(self.readout, 1)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)
        lay.addLayout(row)
        lay.addLayout(second)

    def _mode(self, key, on):
        """Zoom or Pan on or off (the mouse tools go off)."""
        nav = self.nav
        if on:
            self.tab.tools.bar.set_mode(None)
        current = str(nav.mode)
        want = {"zoom": "zoom rect", "pan": "pan/zoom"}[key]
        if on != (current == want):
            nav.zoom() if key == "zoom" else nav.pan()
        self.sync()

    def _step(self, move):
        """Unzoom or Rezoom; that view is the one kept on a resize."""
        move()
        self.tab.plot.requested = self.tab.plot.get_view()

    def sync(self):
        """Zoom and Pan show the mode of the navigation bar."""
        current = str(self.nav.mode)
        for key, mode in (("zoom", "zoom rect"), ("pan", "pan/zoom")):
            b = self.buttons[key]
            b.blockSignals(True)
            b.setChecked(current == mode)
            b.blockSignals(False)

    def restore(self):
        """The full view of the run."""
        view = self.tab.viewbar
        if self.tab.run is not None and view.combo.count():
            view.combo.setCurrentIndex(0)
            view._chosen(0)
