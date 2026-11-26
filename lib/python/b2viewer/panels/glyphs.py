"""Choosers of plot styles that show what they choose: colour maps (the
name, the bar of the colours at its right), line styles, line widths,
marker sizes and marker symbols (drawn, in the list and in the closed
box), in the colours of the theme."""

from matplotlib import colormaps

from .. import theme
from ..plot.styles import DIVERGING
from ...qt import QtCore, QtGui, QtWidgets, Qt, Signal

CMAPS = [n for n in (
    "jet", "turbo", "rainbow", "gnuplot", "hot", "cool", "spring", "summer",
    "autumn", "winter", "gray", "bone", "copper", "viridis", "plasma",
    "inferno", "magma", "cividis", "ocean", "gist", "hsv", "twilight",
    "spectral", "coolwarm", "bwr", "seismic", "berlin", "vanimo")
    if {"gist": "gist_earth", "spectral": "Spectral"}.get(n, n)
    in colormaps]                       # berlin, vanimo: matplotlib 3.10
MPL_NAMES = {"gist": "gist_earth", "spectral": "Spectral"}
CENTRED_TIP = ("Centre colour at zero: of each side as much as the range "
               "covers; from the centre to one end when all values have "
               "one sign")
LINESTYLES = (("solid", "-"), ("dashed", "--"), ("dotted", ":"),
              ("dash-dot", "-."))
PEN_STYLES = {"-": Qt.SolidLine, "--": Qt.DashLine, ":": Qt.DotLine,
              "-.": Qt.DashDotLine}
WIDTHS = (0.1, 0.15, 0.25, 0.4, 0.5, 0.6, 0.8, 1, 1.2, 1.5, 2, 2.5, 3, 4, 5,
          6, 8, 10)                     # points
MARKERS = (("none", "None"), ("circle", "o"), ("plus", "+"), ("star", "*"),
           ("point", "."), ("cross", "x"), ("square", "s"),
           ("diamond", "D"), ("triangle up", "^"), ("triangle down", "v"),
           ("triangle left", "<"), ("triangle right", ">"))


def colour_map(name):
    """The colour map of a name of the list, as drawn in the theme."""
    return theme.cmap(colormaps[MPL_NAMES.get(name, name)])


def _glyph_colour(enabled=True):
    c = theme.COLORS[theme.name()]
    return QtGui.QColor(c["text"] if enabled else c["disabled_text"])


def paint_glyph(painter, rect, kind, value, color):
    """A line of the style or width, a dot of the size or a marker,
    centred in rect."""
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    r = QtCore.QRectF(rect)
    y = r.center().y()
    if kind == "style" and value == "None":       # no line: the word
        painter.setPen(color)
        painter.drawText(r, Qt.AlignCenter, "none")
    elif kind in ("style", "width"):
        pen = QtGui.QPen(color, max(float(value), 0.4) if kind == "width"
                         else 1.5)
        pen.setStyle(Qt.SolidLine if kind == "width" else
                     PEN_STYLES.get(value, Qt.SolidLine))
        pen.setCapStyle(Qt.FlatCap if kind == "width" else Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QtCore.QPointF(r.left(), y),
                         QtCore.QPointF(r.right(), y))
    elif kind in ("size o", "size x"):
        d = min(float(value), r.height())
        if kind == "size o":
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(r.center(), 0.5 * d, 0.5 * d)
        else:
            pen = QtGui.QPen(color, max(d / 5.0, 1.0))
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            c, h = r.center(), 0.5 * d
            painter.drawLine(QtCore.QPointF(c.x() - h, c.y() - h),
                             QtCore.QPointF(c.x() + h, c.y() + h))
            painter.drawLine(QtCore.QPointF(c.x() - h, c.y() + h),
                             QtCore.QPointF(c.x() + h, c.y() - h))
    elif kind == "marker":
        _marker(painter, r.center(), value, color)
    painter.restore()


def _marker(painter, c, marker, color):
    """The marker symbols, about 9 pixels wide, filled where closed."""
    x, y = c.x(), c.y()
    pen = QtGui.QPen(color, 1.6)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(color)

    def poly(*pts):
        painter.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x + u, y + v)
                                             for u, v in pts]))

    def lines(*segs):
        for u0, v0, u1, v1 in segs:
            painter.drawLine(QtCore.QPointF(x + u0, y + v0),
                             QtCore.QPointF(x + u1, y + v1))
    if marker == "o":
        painter.drawEllipse(c, 3.2, 3.2)
    elif marker == ".":
        painter.drawEllipse(c, 1.6, 1.6)
    elif marker == "+":
        lines((0, -4, 0, 4), (-4, 0, 4, 0))
    elif marker == "*":
        lines((0, -4, 0, 4), (-3.8, -2, 3.8, 2), (-3.8, 2, 3.8, -2))
    elif marker == "x":
        lines((-3.8, -3.8, 3.8, 3.8), (-3.8, 3.8, 3.8, -3.8))
    elif marker == "s":
        painter.drawRect(QtCore.QRectF(x - 3.8, y - 3.8, 7.6, 7.6))
    elif marker == "D":
        poly((0, -4.4), (4.2, 0), (0, 4.4), (-4.2, 0))
    elif marker == "^":
        poly((0, -4.2), (4.3, 3.8), (-4.3, 3.8))
    elif marker == "v":
        poly((-4.3, -3.8), (4.3, -3.8), (0, 4.2))
    elif marker == "<":
        poly((-4.2, 0), (4.2, -4.2), (4.2, 4.2))
    elif marker == ">":
        poly((-4.2, -4.2), (4.2, 0), (-4.2, 4.2))


class _Previews(QtWidgets.QStyledItemDelegate):
    """Rows of the list of a chooser: the name and the colour bar, or the
    glyph alone."""

    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QtCore.QSize(size.width(), max(size.height(), round(
            1.5 * option.fontMetrics.height())))

    def paint(self, painter, option, index):
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        kind, value = self.combo.KIND, index.data(Qt.UserRole)
        style = opt.widget.style() if opt.widget is not None else \
            QtWidgets.QApplication.style()
        if kind != "cmap":
            opt.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter,
                          opt.widget)
        rect = opt.rect
        gap = max(8, round(rect.height() * 0.35))
        if kind == "cmap":
            width = max(42, round(rect.height() * 2.9))
            bar = QtCore.QRect(rect.right() - width - gap + 1, rect.top() + 3,
                               width, max(6, rect.height() - 6))
            _colour_bar(painter, bar, value, opt.palette)
        else:
            paint_glyph(painter, rect.adjusted(gap, 3, -gap, -3), kind,
                        value, _glyph_colour())


def _colour_bar(painter, rect, name, palette):
    """The colours of the map left to right, rounded, thin frame."""
    cm = colour_map(name)
    grad = QtGui.QLinearGradient(QtCore.QPointF(rect.topLeft()),
                                 QtCore.QPointF(rect.topRight()))
    for i in range(7):
        r, g, b, a = cm(i / 6.0)
        grad.setColorAt(i / 6.0, QtGui.QColor.fromRgbF(r, g, b, a))
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtGui.QPen(palette.color(QtGui.QPalette.Mid), 1.0))
    painter.setBrush(QtGui.QBrush(grad))
    painter.drawRoundedRect(QtCore.QRectF(rect), 3.0, 3.0)
    painter.restore()


class _Chooser(QtWidgets.QComboBox):
    """A combo box whose list draws its rows (_Previews); items: (text,
    value) with the value as data."""

    KIND = ""

    def __init__(self, items, parent=None):
        super().__init__(parent)
        view = QtWidgets.QListView(self)     # (a native list draws none)
        view.setUniformItemSizes(True)
        self.setView(view)
        self.setItemDelegate(_Previews(self))
        for text, value in items:
            self.addItem(text, value)

    def showPopup(self):
        fm = self.fontMetrics()
        text = max([fm.horizontalAdvance(self.itemText(i))
                    for i in range(self.count())] + [0])
        extra = 5 * fm.height() if self.KIND == "cmap" else 0
        self.view().setMinimumWidth(max(self.width(), text + extra + 40))
        super().showPopup()


class CmapChooser(_Chooser):
    """Colour maps by name (data: the name of the list); the diverging
    ones with their tip, or (diverging False) without them."""

    KIND = "cmap"

    def __init__(self, value="turbo", parent=None, diverging=True):
        names = [n for n in CMAPS if diverging or
                 MPL_NAMES.get(n, n) not in DIVERGING]
        super().__init__([(n, n) for n in names], parent)
        for i, n in enumerate(names):
            if MPL_NAMES.get(n, n) in DIVERGING:
                self.setItemData(i, CENTRED_TIP, Qt.ToolTipRole)
        self.setCurrentIndex(max(self.findText(value), 0))

        self.setMinimumContentsLength(4)
        self.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.currentIndexChanged.connect(self._named)
        self._named()

    def name(self):
        """The matplotlib name of the map chosen."""
        return MPL_NAMES.get(self.currentText(), self.currentText())

    def _named(self, *_):
        """The name of the map shown is in the tooltip."""
        self.setToolTip("Colour map: " + self.currentText())

    def paintEvent(self, event):
        """Closed: the colours of the map chosen instead of its name."""
        p = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = ""
        p.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
        rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_ComboBox, opt,
            QtWidgets.QStyle.SC_ComboBoxEditField, self).adjusted(3, 3, -3, -3)
        if self.currentIndex() >= 0 and rect.width() > 4:
            if not self.isEnabled():
                p.setOpacity(0.4)
            _colour_bar(p, rect, self.currentText(), opt.palette)


class _GlyphChooser(_Chooser):
    """A chooser showing the glyph of the choice also when closed."""

    def __init__(self, items, parent=None):
        super().__init__(items, parent)
        self.setMinimumContentsLength(4)
        self.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)

    def paintEvent(self, event):
        p = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = ""
        p.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
        rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_ComboBox, opt,
            QtWidgets.QStyle.SC_ComboBoxEditField, self).adjusted(4, 2, -4, -2)
        if self.currentIndex() >= 0:
            paint_glyph(p, rect, self.KIND, self.currentData(),
                        _glyph_colour(self.isEnabled()))


class LineStyleChooser(_GlyphChooser):
    """Line styles; with_none: also no line (data drawn as markers)."""

    KIND = "style"

    def __init__(self, value="-", with_none=False, parent=None):
        super().__init__(LINESTYLES + ((("none", "None"),) if with_none
                                       else ()), parent)
        self.setCurrentIndex(max(self.findData(value), 0))
        self.setToolTip("Line style")


class MarkerChooser(_GlyphChooser):
    """Marker symbols (data: the matplotlib marker, "None" for none)."""

    KIND = "marker"

    def __init__(self, value="None", parent=None):
        super().__init__(MARKERS, parent)
        self.setCurrentIndex(max(self.findData(value), 0))
        self.setToolTip("Markers at the points")


class WidthChooser(_GlyphChooser):
    """Line widths (points), as a spin box: value(), setValue(),
    valueChanged; a value not in the list joins it."""

    KIND = "width"
    valueChanged = Signal(float)

    def __init__(self, value=1.0, choices=WIDTHS, tip="Line width (pt)",
                 parent=None):
        super().__init__([("%g" % w, float(w)) for w in choices], parent)
        self.setToolTip(tip)
        self.setValue(value)
        self.currentIndexChanged.connect(
            lambda *_: self.valueChanged.emit(self.value()))

    def value(self):
        v = self.currentData()
        return float(v) if v is not None else 0.0

    def setValue(self, value):
        value = float(value)
        i = self.findData(value)
        if i < 0:
            i = sum(1 for k in range(self.count())
                    if self.itemData(k) < value)
            self.insertItem(i, "%g" % value, value)
        self.setCurrentIndex(i)


class SizeChooser(WidthChooser):
    """Marker sizes (points), drawn as the marker: symbol "o" (a filled
    circle) or "x"."""

    def __init__(self, value=8.0, choices=WIDTHS, tip="Marker size (pt)",
                 symbol="o", parent=None):
        self.KIND = "size " + symbol
        super().__init__(value, choices, tip, parent)
