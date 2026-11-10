"""Layout of the 2D tab: three columns with fixed fractions of
the width, the commands over the plot (Zoom, Unzoom, Rezoom, Restore and
the mouse tools; under them Add to page, Page composer, Print
figure, Export field and the cursor readout) and a canvas whose plot
scales with the window."""

import re

from ...qt import FigureCanvasQTAgg, QtCore, QtGui, QtWidgets, Qt

NAV = (("Zoom", "zoom", "Drag a box to zoom in"),
       ("Unzoom", "back", "Back to the previous view"),
       ("Rezoom", "forward", "Forward to the next view"),
       ("Restore", "restore", "The full view of the run (the plot moves "
        "when dragged with the left button, the mouse wheel zooms)"))
READOUT = "R = --   Z = --"
VALUE = re.compile(r"value = (.+)$")      # number and unit, in bold


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
    """The cursor readout: one line (R, Z, rho poloidal, value, its number
    and unit in bold) of fixed height; its text gets smaller when the line
    is wider than the box, so that every number shows."""

    def __init__(self, text=READOUT, parent=None):
        super().__init__(parent)
        self.setObjectName("readout")
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setTextFormat(Qt.RichText)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Fixed)
        self._line, self._size, self._base, self._busy = "", None, None, False
        self.setText(text)

    def setText(self, text):
        self._line = " ".join(str(text).splitlines()) or " "
        self._fit()

    def text(self):
        """The line as plain text."""
        return self._line

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if not self._busy and event.type() in (QtCore.QEvent.FontChange,
                                               QtCore.QEvent.StyleChange):
            self._base = None           # the window font changed
            self._fit()

    def _fit(self):
        if self._busy:
            return
        self._busy = True
        try:
            if self._base is None:      # font of the window, line height
                self.setStyleSheet("")
                self._size = None
                self._base = self.font().pointSizeF()
                super().setText("R")
                self.setFixedHeight(self.sizeHint().height())
            avail = self.contentsRect().width() - 4
            f = QtGui.QFont(self.font())
            f.setPointSizeF(self._base)
            width = QtGui.QFontMetricsF(f).horizontalAdvance(self._line)
            number = VALUE.search(self._line)
            if number:                      # number and unit in bold
                f.setBold(True)
                width += QtGui.QFontMetricsF(f).horizontalAdvance(
                    number.group(1))
                f.setBold(False)
                width -= QtGui.QFontMetricsF(f).horizontalAdvance(
                    number.group(1))
            size = self._base if width <= avail or avail <= 0 else max(
                0.6 * self._base, int(4 * self._base * avail / width) / 4.0)
            if size != (self._size or self._base):
                self.setStyleSheet("" if size == self._base else
                                   "font-size: %.2fpt;" % size)
                self._size = size
            html = self._line.replace("&", "&amp;").replace(
                "<", "&lt;").replace("   ", "&nbsp;&nbsp; ")
            super().setText(VALUE.sub(r"value = <b>\1</b>", html))
        finally:
            self._busy = False


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
    navigation bar does the box zoom; the tab pans and zooms with the
    mouse)."""

    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.tab, self.nav = tab, tab.toolbar
        self.buttons = {}
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)
        for text, key, tip in NAV:
            checkable = key == "zoom"
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
        """Zoom on or off (the mouse tools go off)."""
        nav = self.nav
        if on:
            self.tab.tools.bar.set_mode(None)
        current = str(nav.mode)
        if on != (current == "zoom rect"):
            nav.zoom()
        self.sync()

    def _step(self, move):
        """Unzoom or Rezoom; that view is the one kept on a resize."""
        move()
        self.tab.plot.requested = self.tab.plot.get_view()

    def sync(self):
        """Zoom shows the mode of the navigation bar."""
        b = self.buttons["zoom"]
        b.blockSignals(True)
        b.setChecked(str(self.nav.mode) == "zoom rect")
        b.blockSignals(False)

    def restore(self):
        """The full view of the run."""
        self.tab.restore()
