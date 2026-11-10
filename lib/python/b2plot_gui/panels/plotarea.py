"""Layout of the 2D tab: three columns with fixed fractions of
the width, the commands over the plot (Zoom, Unzoom, Rezoom, Restore,
Pan and the mouse tools; under them Add to page, Page composer, Print
figure, Export field and the cursor readout) and a canvas whose plot
scales with the window."""

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


class Readout(QtWidgets.QLabel):
    """The cursor readout: always two lines (the position, then the cell
    and the value), so that its height, and the plot under it, never
    change."""

    def __init__(self, text=READOUT, parent=None):
        super().__init__(parent)
        self.setObjectName("readout")
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Fixed)
        self.setText(text)

    def setText(self, text):
        lines = [t.strip() for t in str(text).split("\n")]
        rest = "  ".join(t for t in lines[1:] if t)
        super().setText("%s\n%s" % (lines[0] or " ", rest or " "))


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
        second = QtWidgets.QHBoxLayout()
        second.setSpacing(4)
        for key, text, tip, slot in (
                ("page", "Add to page", "Add this plot with all its settings "
                 "to the page composer (Ctrl+D)", tab._add_to_page),
                ("composer", "Page composer", "The pages of the plots added "
                 "(Ctrl+P)", tab.composer.emit),
                ("print", "Print figure", "The plot as an image or vector "
                 "file: format, resolution, colour space and theme "
                 "(Ctrl+S)", tab.print_figure),
                ("field", "Export field", "The values of the quantity shown "
                 "with the grid: CSV, text, netCDF or HDF5",
                 tab.export_field)):
            self.buttons[key] = _button(text, tip, slot)
            second.addWidget(self.buttons[key], 1)
        second.addSpacing(10)
        self.readout = Readout()
        self.readout.setToolTip("Position, cell and value under the cursor "
                                "(the mouse wheel zooms)")
        second.addWidget(self.readout, 4)
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
        self.tab.restore()
