"""Layout of the 2D tab: columns with fixed fractions of the width, the
commands of the plot in a narrow column at its right (Zoom, Unzoom,
Rezoom, Restore; the mouse tools; Add to page, Page composer; Print
figure, Export field; at the bottom the parallel and the radial
balance), the cursor readout under the plot box and a canvas whose plot
scales with the window."""

import re

from ...qt import FigureCanvasQTAgg, QtCore, QtGui, QtWidgets, Qt

NAV = (("Zoom", "zoom", "Drag a box to zoom in"),
       ("Unzoom", "back", "Back to the previous view"),
       ("Rezoom", "forward", "Forward to the next view"),
       ("Restore", "restore", "The full view of the run (the plot moves "
        "when dragged with the left button, the mouse wheel zooms)"))
READOUT = "R = --   Z = --"


class ScaledCanvas(FigureCanvasQTAgg):
    """Canvas whose figure keeps its size in inches once frozen: the dpi
    follows the width of the widget, so that texts, margins and lines
    grow and shrink with the window and the plot box keeps its place."""

    def __init__(self, figure, resized=None):
        super().__init__(figure)
        self.inches = None
        self.resized = resized      # called after each resize

    def freeze(self):
        """The present size becomes the reference (again: with the
        resolution of the first one)."""
        if self.width() <= 0:
            return
        if self.inches is None:
            self._dpi0 = self.figure._original_dpi
        else:
            self.figure._original_dpi = self._dpi0
            self.figure._set_dpi(self._dpi0 * self.device_pixel_ratio,
                                 forward=False)
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
    """The cursor readout in one line under the plot box, from its left
    edge (a label over the canvas that lets the mouse through): R, Z, rho
    poloidal (with a psi map) and the value of the quantity shown with its
    unit in bold, in a font a little larger than the one of the window,
    the same whatever is shown."""

    SCALE = 1.15                    # of the font of the window

    def __init__(self, text=READOUT, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.RichText)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._line, self._busy = "", False
        self._font()
        self.setText(text)

    def setText(self, text):
        self._line = " ".join(str(text).splitlines()) or " "
        parts = []
        for part in self._line.split("   "):
            name, _, value = part.strip().partition(" = ")
            if value:
                parts.append("%s = %s" % (name, "<b>%s</b>" % _html(
                    value, True) if name == "value" else _html(value)))
        super().setText("&nbsp;&nbsp;&nbsp;&nbsp;".join(parts) or " ")
        self.adjustSize()

    def text(self):
        """The readout as one plain line, the items separated by three
        blanks."""
        return self._line

    def rows(self):
        """The items shown, as plain text."""
        return [p.strip() for p in self._line.split("   ") if p.strip()]

    def changeEvent(self, event):
        super().changeEvent(event)
        if not self._busy and event.type() in (QtCore.QEvent.FontChange,
                                               QtCore.QEvent.StyleChange):
            self._font()                # the window font changed

    def _font(self):
        """SCALE times the font of the window."""
        self._busy = True
        try:
            self.setStyleSheet("")
            size = self.font().pointSizeF()
            self.setStyleSheet("background: transparent; font-size: %.2fpt;"
                               % (self.SCALE * (size if size > 0 else 13.0)))
            self.adjustSize()
        finally:
            self._busy = False


def _html(text, sup=False):
    """Text for a rich text label; with sup, the exponents of a unit
    (m^-3) as superscripts."""
    text = text.replace("&", "&amp;").replace("<", "&lt;")
    return re.sub(r"\^\{?([-+]?[0-9.]+)\}?", r"<sup>\1</sup>", text) \
        if sup else text


class Columns(QtWidgets.QWidget):
    """Widgets side by side at fixed fractions of the width (no splitter:
    the columns cannot be resized); before: empty fraction before each
    widget."""

    def __init__(self, widgets, fractions, before=None, parent=None):
        super().__init__(parent)
        self.widgets, self.fractions = list(widgets), list(fractions)
        self.before = list(before or [0.0] * len(self.widgets))
        for w in self.widgets:
            w.setParent(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        x, width, height = 0, self.width(), self.height()
        for i, (w, f, b) in enumerate(zip(self.widgets, self.fractions,
                                          self.before)):
            x += round(b * width)
            dx = width - x if i == len(self.widgets) - 1 else round(f * width)
            w.setGeometry(x, 0, dx, height)
            x += dx

    def minimumSizeHint(self):
        return QtCore.QSize(0, 0)


def _button(text, tip, slot=None, checkable=False):
    b = QtWidgets.QPushButton(text)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                    QtWidgets.QSizePolicy.Fixed)
    if slot is not None:
        (b.toggled if checkable else b.clicked).connect(
            lambda *a: slot(*a[:1]) if checkable else slot())
    return b


class PlotCommands(QtWidgets.QWidget):
    """The commands of the plot in a narrow column at its right, one under
    the other in groups: the view (Zoom to Restore), the mouse tools
    (Inspect to Statistics), the pages (Add to page, Page composer), the
    files (Save plot, Export field), and the parallel and the radial
    balance at the bottom, from the left edge of the column, narrower
    than it (room to the layers); the first button at
    the height of the top of the plot box, the last one at the height of
    its bottom. The buttons get a smaller font only when a label would not
    fit the column. A Tab2D's hidden matplotlib navigation bar does the box
    zoom; the tab pans and zooms with the mouse."""

    SPACING, GAP = 0.5, 2.0         # in lines: between buttons, groups
    ROOM = 0.18                     # of the width, right of the buttons

    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.tab, self.nav = tab, tab.toolbar
        self.buttons = {}
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 6, 6)     # right: ROOM (resizeEvent)
        self.gaps = []                          # as from the plot

        def gap():
            self.gaps.append(QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Minimum,
                QtWidgets.QSizePolicy.Fixed))
            lay.addItem(self.gaps[-1])
        for text, key, tip in NAV:
            checkable = key == "zoom"
            slot = (lambda on, k=key: self._mode(k, on)) if checkable else \
                {"back": lambda: self._step(self.nav.back),
                 "forward": lambda: self._step(self.nav.forward),
                 "restore": self.restore}[key]
            self.buttons[key] = _button(text, tip, slot, checkable)
            lay.addWidget(self.buttons[key])
        gap()
        bar = tab.tools.bar
        for b in bar.buttons.values():
            b.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                            QtWidgets.QSizePolicy.Fixed)
        lay.addWidget(bar)
        bar.changed.connect(self.sync)
        for group in ((("page", "Add to\npage", "Add this plot with all its "
                        "settings to the page composer (Ctrl+D)",
                        tab._add_to_page),
                       ("composer", "Page\ncomposer", "The pages of the plots "
                        "added (Ctrl+P)", tab.composer.emit)),
                      (("print", "Save\nplot", "The plot as an image or "
                        "vector file: format, resolution, colour space and "
                        "theme (Ctrl+S)", tab.print_figure),
                       ("field", "Export\nfield", "The values of the quantity "
                        "shown with the grid: CSV, text, netCDF or HDF5",
                        tab.export_field))):
            gap()
            for key, text, tip, slot in group:
                self.buttons[key] = _button(text, tip, slot)
                lay.addWidget(self.buttons[key])
        lay.addStretch(1)
        for b in self.all_buttons():
            b.setProperty("bold", True)
        self._base, self._busy = None, False

    def set_top(self, top):
        """The first button at this height (pixels from the top of the
        column): the top of the plot box."""
        m = self.layout().contentsMargins()
        top = max(int(top), 0)
        if m.top() != top:
            self.layout().setContentsMargins(m.left(), top, m.right(),
                                             m.bottom())

    def set_bottom(self, bottom):
        """The last button with its bottom at this distance (pixels) from
        the bottom of the column: the bottom of the plot box."""
        m = self.layout().contentsMargins()
        bottom = max(int(bottom), 0)
        if m.bottom() != bottom:
            self.layout().setContentsMargins(m.left(), m.top(), m.right(),
                                             bottom)

    def all_buttons(self):
        bar = self.tab.tools.bar
        return list(self.buttons.values()) + list(bar.buttons.values())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        m = self.layout().contentsMargins()
        right = round(self.ROOM * self.width())
        if m.right() != right:
            self.layout().setContentsMargins(m.left(), m.top(), right,
                                             m.bottom())
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if not self._busy and event.type() in (QtCore.QEvent.FontChange,
                                               QtCore.QEvent.StyleChange):
            self._base = None
            self._fit()

    def _fit(self):
        """The font of the window on the buttons, or smaller when the
        widest label (bold) would not fit; the
        spaces between the buttons and the groups in lines of that
        font."""
        if self._busy:
            return
        self._busy = True
        try:
            buttons = self.all_buttons()
            if self._base is None:
                for b in buttons:
                    b.setStyleSheet("")
                self._base = buttons[0].font().pointSizeF()
                line = QtGui.QFontMetrics(buttons[0].font()).height()
                for lay in (self.layout(), self.tab.tools.bar.layout()):
                    lay.setSpacing(round(self.SPACING * line))
                for item in self.gaps:
                    item.changeSize(0, round(self.GAP * line),
                                    QtWidgets.QSizePolicy.Minimum,
                                    QtWidgets.QSizePolicy.Fixed)
                self.layout().invalidate()
            m = self.layout().contentsMargins()      # the buttons
            avail = self.contentsRect().width() - m.left() - m.right()
            f = QtGui.QFont(buttons[0].font())
            f.setPointSizeF(self._base)
            f.setBold(True)
            fm = QtGui.QFontMetricsF(f)
            app = QtWidgets.QApplication.font().pointSizeF()
            pad = 16 * self._base / app if app > 0 else 16  # as the theme
            width = pad + max(fm.horizontalAdvance(line) for b in buttons
                              for line in b.text().splitlines())
            size = self._base if width <= avail or avail <= 0 else max(
                0.6 * self._base, int(4 * self._base * avail / width) / 4.0)
            for b in buttons:
                b.setStyleSheet("" if size == self._base else
                                "font-size: %.2fpt;" % size)
        finally:
            self._busy = False

    def _mode(self, key, on):
        """Zoom on or off (the mouse tools go off)."""
        nav = self.nav
        if on:
            self.tab.tools.bar.set_mode(None)
            self.tab.balance.cancel()
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
