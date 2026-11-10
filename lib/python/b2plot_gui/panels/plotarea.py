"""Layout of the 2D tab: columns with fixed fractions of the width, the
commands of the plot in a narrow column at its left (Zoom, Unzoom,
Rezoom, Restore; the mouse tools; Add to page, Page composer; Print
figure, Export field; the cursor readout) and a canvas whose plot scales
with the window."""

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


class Readout(QtWidgets.QWidget):
    """The cursor readout, plain text on the background, one item under
    the other: R, Z, rho poloidal (with a psi map), "value =" and under it
    the number and unit of the quantity shown, in bold. The lines keep
    their height wherever the cursor is; one font for all of them, smaller
    when the widest line possible would not fit."""

    LINES = 5                       # R, Z, rhop, "value =", number

    def __init__(self, text=READOUT, parent=None):
        super().__init__(parent)
        self.setObjectName("readout")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.lines = []
        for _ in range(self.LINES):
            label = QtWidgets.QLabel()
            label.setTextFormat(Qt.RichText)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                QtWidgets.QSizePolicy.Fixed)
            lay.addWidget(label)
            self.lines.append(label)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Fixed)
        self._line, self._unit, self._size = "", None, None
        self._base, self._busy = None, False
        self.setText(text)

    def setText(self, text):
        self._line = " ".join(str(text).splitlines()) or " "
        self._show()

    def text(self):
        """The readout as one plain line, the items separated by three
        blanks."""
        return self._line

    def rows(self):
        """The lines shown, as plain text."""
        return [label.text() and QtGui.QTextDocumentFragment.fromHtml(
            label.text()).toPlainText() for label in self.lines]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if not self._busy and event.type() in (QtCore.QEvent.FontChange,
                                               QtCore.QEvent.StyleChange):
            self._base = None           # the window font changed
            self._fit()

    def _items(self):
        """{R, Z, rhop, value: text after " = "} of the line."""
        out = {}
        for part in self._line.split("   "):
            name, _, value = part.strip().partition(" = ")
            if value:
                out[name] = value
        return out

    def _show(self):
        items = self._items()
        number = items.get("value", "")
        unit = number.partition(" ")[2]
        texts = ["%s = %s" % (k, _html(items[k])) if k in items else ""
                 for k in ("R", "Z", "rhop")]
        texts += ["value =" if number else "",
                  "<b>%s</b>" % _html(number, True) if number else ""]
        for label, text in zip(self.lines, texts):
            label.setText(text)
        if unit != self._unit:
            self._unit = unit
            self._fit()

    def _fit(self):
        """One font size for the lines: the window font, or smaller so
        that the widest line possible (a coordinate, the number of the
        value with its unit) fits the width."""
        if self._busy:
            return
        self._busy = True
        try:
            if self._base is None:
                for label in self.lines:
                    label.setStyleSheet("")
                self._size = None
                self._base = self.lines[0].font().pointSizeF()
                height = QtGui.QFontMetrics(self.lines[0].font()).height()
                for label in self.lines:
                    label.setFixedHeight(height + 1)
            avail = self.contentsRect().width() - 2
            f = QtGui.QFont(self.lines[0].font())
            f.setPointSizeF(self._base)
            width = max(QtGui.QFontMetricsF(f).horizontalAdvance(t) for t in
                        ("Z = -1.2345 m", "rhop = 0.9876"))
            f.setBold(True)
            width = max(width, QtGui.QFontMetricsF(f).horizontalAdvance(
                "-1.234e+20 " + (self._unit or "").replace("^", "")))
            size = self._base if width <= avail or avail <= 0 else max(
                0.6 * self._base, int(4 * self._base * avail / width) / 4.0)
            if size != (self._size or self._base):
                for label in self.lines:
                    label.setStyleSheet("" if size == self._base else
                                        "font-size: %.2fpt;" % size)
                self._size = size
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
    b.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                    QtWidgets.QSizePolicy.Fixed)
    if slot is not None:
        (b.toggled if checkable else b.clicked).connect(
            lambda *a: slot(*a[:1]) if checkable else slot())
    return b


class PlotCommands(QtWidgets.QWidget):
    """The commands of the plot in a narrow column at its left, one under
    the other in groups: the view (Zoom to Restore), the mouse tools
    (Inspect to Statistics), the pages (Add to page, Page composer), the
    files (Print figure, Export field), then the cursor readout; the
    first button at the height of the top of the plot box. The
    buttons get a smaller font only when a label would not fit the
    column. A Tab2D's hidden matplotlib navigation bar does the box
    zoom; the tab pans and zooms with the mouse."""

    SPACING, GAP = 0.5, 2.0         # in lines: between buttons, groups

    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.tab, self.nav = tab, tab.toolbar
        self.buttons = {}
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 2, 6)     # as far from the scroll bar
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
        for b in list(bar.buttons.values()) + [bar.stats]:
            b.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                            QtWidgets.QSizePolicy.Fixed)
        lay.addWidget(bar)
        bar.changed.connect(self.sync)
        for group in ((("page", "Add to\npage", "Add this plot with all its "
                        "settings to the page composer (Ctrl+D)",
                        tab._add_to_page),
                       ("composer", "Page\ncomposer", "The pages of the plots "
                        "added (Ctrl+P)", tab.composer.emit)),
                      (("print", "Print\nfigure", "The plot as an image or "
                        "vector file: format, resolution, colour space and "
                        "theme (Ctrl+S)", tab.print_figure),
                       ("field", "Export\nfield", "The values of the quantity "
                        "shown with the grid: CSV, text, netCDF or HDF5",
                        tab.export_field))):
            gap()
            for key, text, tip, slot in group:
                self.buttons[key] = _button(text, tip, slot)
                lay.addWidget(self.buttons[key])
        gap()
        self.readout = Readout()
        self.readout.setToolTip("Position, cell and value under the cursor "
                                "(the mouse wheel zooms)")
        lay.addWidget(self.readout)
        lay.addStretch(1)
        self._base, self._busy = None, False

    def set_top(self, top):
        """The first button at this height (pixels from the top of the
        column): the top of the plot box."""
        m = self.layout().contentsMargins()
        top = max(int(top), 0)
        if m.top() != top:
            self.layout().setContentsMargins(m.left(), top, m.right(),
                                             m.bottom())

    def all_buttons(self):
        bar = self.tab.tools.bar
        return list(self.buttons.values()) + list(bar.buttons.values()) + \
            [bar.stats]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if not self._busy and event.type() in (QtCore.QEvent.FontChange,
                                               QtCore.QEvent.StyleChange):
            self._base = None
            self._fit()

    def _fit(self):
        """The font of the window on the buttons, or smaller when the
        widest label (bold, as a checked button) would not fit; the
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
            avail = self.contentsRect().width()
            f = QtGui.QFont(buttons[0].font())
            f.setPointSizeF(self._base)
            f.setBold(True)
            fm = QtGui.QFontMetricsF(f)
            width = 16 + max(fm.horizontalAdvance(line) for b in buttons
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
