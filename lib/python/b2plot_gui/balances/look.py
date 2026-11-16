"""The look of a line of a balance plot, chosen with a right click on it
(or on its legend entry): a small window with its colour (the colour
dialog), width, style and marker (none or a glyph), each a menu. The
choices are kept for the line (by plot title and line name) while the run
is open, also when the plot is drawn again. The colours of the lines of
the total balances are those of their roles (style.colour), shared by
both plots and the volume on the 2D plot; the flux across the volume,
coloured from one to the other, has two."""

from dataclasses import replace

from ..panels.glyphs import LineStyleChooser, MarkerChooser, WidthChooser
from ..panels.layers import ColorButton
from ...qt import QtCore, QtGui, QtWidgets, Qt
from . import style


def apply(panel, looks):
    """The panel with the looks chosen for its lines."""
    series = []
    for s in panel.series:
        look = looks.get((panel.title, s.label))
        series.append(replace(s, **look) if look else s)
    return replace(panel, series=series)


class _Colour(ColorButton):
    """The colour of the line: the popup steps aside while the colour
    dialog is open (else it would close), then comes back."""

    def __init__(self, popup, color):
        super().__init__(color)
        self.popup = popup

    def _pick(self):
        self.popup.hide()
        c = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.color()),
                                            self.popup.parentWidget())
        if c.isValid():
            self.set_color(c.name())
            self.changed.emit(self.color())
        self.popup.show()


class LinePopup(QtWidgets.QFrame):
    """The look of the line series, at a point of the screen; changed(look)
    with the fields of the series to replace after each choice, recolour
    (role, colour) for the colour of a role; ends: the names of the lines
    whose colours the two ends of a line across take."""

    def __init__(self, series, changed, recolour, ends, parent):
        super().__init__(parent, Qt.Popup)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.changed, self.role = changed, series.role
        self.gradient = series.gradient
        roles = [series.role] if series.role not in (None, "across") else \
            ["up", "down"] if series.role == "across" else []
        self.colours = []               # (role or None, button)
        for role in roles or [None]:
            b = _Colour(self, series.color if role is None else
                        style.colour(role))
            if role is None:
                b.changed.connect(lambda *_: self._changed(True))
            else:
                b.changed.connect(lambda c, r=role: recolour(r, c))
            self.colours.append((role, b))
        self.colour = self.colours[0][1]
        self.colour.setToolTip("Colour of the line" + (
            ", also of the same line in the other plot and of the volume "
            "on the 2D plot" if series.role not in (None, "across") else ""))
        self.line_width = WidthChooser(series.width)
        self.line_style = LineStyleChooser(series.style)
        self.line_marker = MarkerChooser(series.marker or "None")
        self.line_marker.setToolTip("Marker at each point of the line")
        title = QtWidgets.QLabel(series.label)
        title.setProperty("bold", True)
        form = QtWidgets.QFormLayout(self)
        form.addRow(title)
        if series.role == "across":
            for (role, b), text, name in zip(self.colours, ("Start colour",
                                                            "End colour"),
                                             ends):
                b.setToolTip("As the %s in the other plot and on the 2D "
                             "plot" % name)
                form.addRow(text, b)
        else:
            form.addRow("Colour", self.colour)
        form.addRow("Width", self.line_width)
        form.addRow("Style", self.line_style)
        form.addRow("Marker", self.line_marker)
        self.colour.changed.connect(lambda *_: self._changed(True))
        for w in (self.line_width, self.line_style, self.line_marker):
            w.currentIndexChanged.connect(lambda *_: self._changed(False))

    def _changed(self, colour):
        marker = self.line_marker.currentData()
        fields = dict(width=self.line_width.value(),
                      style=self.line_style.currentData(),
                      marker=None if marker in (None, "None") else marker)
        if self.role is None:           # its own colour
            fields["color"] = self.colour.color()
        self.changed(fields)

    def show_at(self, point):
        """Open with its top left corner at point (global), inside the
        screen."""
        self.adjustSize()
        screen = QtGui.QGuiApplication.screenAt(point) or \
            QtGui.QGuiApplication.primaryScreen()
        g = screen.availableGeometry()
        x = min(max(point.x(), g.left()), g.right() - self.width())
        y = min(max(point.y(), g.top()), g.bottom() - self.height())
        self.move(QtCore.QPoint(x, y))
        self.show()
