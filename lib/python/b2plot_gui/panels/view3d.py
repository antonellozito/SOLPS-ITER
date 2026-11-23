"""Options of the 3D view, in the right column when it is shown: the view
(sector of the torus, vertical range, vertical and horizontal angles,
restore, save the image), the opacity of each group of the scene, the
tracers of the vector quantity, the rendering."""

from ...qt import Qt, QtCore, QtGui, QtWidgets, Signal
from .. import theme
from ..plot3d import GROUPS
from ..tools import births
from .layers import left_form, spin
from .plotopts import _Box


def _ispin(lo, hi, step, value, tip, suffix=""):
    w = QtWidgets.QSpinBox()
    w.setRange(lo, hi)
    w.setSingleStep(step)
    w.setValue(value)
    w.setSuffix(suffix)
    w.setKeyboardTracking(False)
    w.setToolTip(tip)
    return w


class _Check(QtWidgets.QCheckBox):
    """A check box whose text ends in an ellipsis where its column is too
    narrow for it (the column never scrolls sideways); whole otherwise."""

    def __init__(self, text, tip=""):
        super().__init__(text)
        self._full = text
        self.setToolTip(tip)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                           QtWidgets.QSizePolicy.Fixed)

    def _extra(self):
        """The width of the box and the gap before the text."""
        return super().sizeHint().width() - \
            self.fontMetrics().horizontalAdvance(self.text())

    def sizeHint(self):
        s = super().sizeHint()
        return QtCore.QSize(self._extra() + self.fontMetrics()
                            .horizontalAdvance(self._full), s.height())

    def minimumSizeHint(self):
        s = super().minimumSizeHint()
        return QtCore.QSize(self._extra() + self.fontMetrics()
                            .horizontalAdvance("…"), s.height())

    def resizeEvent(self, event):
        text = self._full if self.width() >= self.sizeHint().width() else \
            self.fontMetrics().elidedText(self._full, Qt.ElideRight,
                                          max(self.width() - self._extra(),
                                              0))
        if text != self.text():
            self.setText(text)
        super().resizeEvent(event)


def _row(*widgets):
    row = QtWidgets.QHBoxLayout()
    for w in widgets:
        row.addWidget(w)
    row.addStretch(1)
    return row


def _slider(lo, hi, value, tip):
    s = QtWidgets.QSlider(Qt.Horizontal)
    s.setRange(lo, hi)
    s.setValue(value)
    s.setToolTip(tip)
    return s


class RangeSlider(QtWidgets.QWidget):
    """Two handles on one groove, positions 0 to n + 1 (low before high),
    drawn as the sliders of the theme (the groove, the part between the
    handles in the accent colour, round handles); changed: the handles
    moved."""

    changed = Signal(int, int)

    def __init__(self, n, parent=None):
        super().__init__(parent)
        self.n, self.lo, self.hi = n, 0, n + 1
        self._drag = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Fixed)

    def _k(self):
        """Sizes follow the font, as in the stylesheet of the theme."""
        base = QtWidgets.QApplication.font().pointSizeF()
        return self.font().pointSizeF() / base if base > 0 else 1.0

    def sizeHint(self):
        return QtCore.QSize(100, round(20 * self._k()))

    def minimumSizeHint(self):
        return QtCore.QSize(40, round(20 * self._k()))

    def _margin(self):
        return 7 * self._k() + 1

    def _x(self, v):
        m = self._margin()
        return m + max(self.width() - 2 * m, 1) * v / (self.n + 1)

    def _value(self, x):
        m = self._margin()
        w = max(self.width() - 2 * m, 1)
        return int(min(max(round((x - m) / w * (self.n + 1)), 0),
                       self.n + 1))

    def paintEvent(self, event):
        c = theme.COLORS[theme.name()]
        k = self._k()
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        y, h, r = self.height() / 2.0, 4 * k, 7 * k
        m = self._margin()
        p.setPen(Qt.NoPen)
        p.setBrush(QtGui.QColor(c["soft_border"]))
        p.drawRoundedRect(QtCore.QRectF(m, y - h / 2, self.width() - 2 * m,
                                        h), h / 2, h / 2)
        x0, x1 = self._x(self.lo), self._x(self.hi)
        p.setBrush(QtGui.QColor(theme.ACCENT))
        p.drawRoundedRect(QtCore.QRectF(x0, y - h / 2, x1 - x0, h), h / 2,
                          h / 2)
        p.setPen(QtGui.QPen(QtGui.QColor(c["border"]), 1))
        p.setBrush(QtGui.QColor(c["control"]))
        for x in (x0, x1):
            p.drawEllipse(QtCore.QPointF(x, y), r, r)

    def mousePressEvent(self, event):
        x = event.position().x()
        self._drag = 0 if abs(x - self._x(self.lo)) <= abs(
            x - self._x(self.hi)) else 1
        if self.lo == self.hi - 1 and x > self._x(self.hi):
            self._drag = 1
        self._move(x)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self._move(event.position().x())

    def mouseReleaseEvent(self, event):
        self._drag = None

    def _move(self, x):
        v = self._value(x)
        lo, hi = (min(v, self.hi - 1), self.hi) if self._drag == 0 else \
            (self.lo, max(v, self.lo + 1))
        if (lo, hi) != (self.lo, self.hi):
            self.lo, self.hi = lo, hi
            self.update()
            self.changed.emit(lo, hi)


class ViewBox(_Box):
    """The sector shown (degrees), the angles of the camera, the
    projection; Restore view, Save image."""

    angles = Signal(float, float)       # vertical, horizontal (degrees)
    restore = Signal()
    save = Signal()
    STEPS = 100                         # heights of the vertical range

    def __init__(self, parent=None):
        super().__init__("3D view", parent)
        form = left_form(self)
        self.start = _ispin(0, 359, 10, 0, "Start of the sector shown, "
                            "toroidal angle", "°")
        self.end = _ispin(1, 360, 10, 90, "End of the sector shown, "
                          "toroidal angle (360 with 0: the full torus)", "°")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.start)
        row.addWidget(QtWidgets.QLabel("to"))
        row.addWidget(self.end)
        row.addStretch(1)
        form.addRow("Sector", row)
        self.zrange = RangeSlider(self.STEPS)
        self.zrange.setToolTip("Heights shown, from the lowest to the "
                               "highest point of the grids (at the ends: "
                               "all): the scene cut at the bottom and the "
                               "top")
        self.zrange.changed.connect(lambda *_: self.changed.emit())
        form.addRow("Vertical range", self.zrange)
        self.vertical = _slider(-90, 90, 0, "Elevation of the camera "
                                "(degrees), around the point looked at")
        self.horizontal = _slider(-180, 180, 0, "Turn of the camera around "
                                  "the vertical through the point looked "
                                  "at (degrees; 0: facing the cut face at "
                                  "the start of the sector)")
        self.vtext, self.htext = QtWidgets.QLabel(), QtWidgets.QLabel()
        for name, s, t in (("Vertical", self.vertical, self.vtext),
                           ("Horizontal", self.horizontal, self.htext)):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(s, 1)
            row.addWidget(t)
            t.setMinimumWidth(t.fontMetrics().horizontalAdvance("-180°"))
            form.addRow(name, row)
            s.valueChanged.connect(self._angles)
        row = QtWidgets.QHBoxLayout()
        for text, tip, sig in (
                ("Restore view", "The camera at the angles looking at "
                 "the cut face at the start of the sector, fitted in the "
                 "view", self.restore),
                ("Save image", "The 3D view in a PNG file, at twice the "
                 "resolution of the screen", self.save)):
            b = QtWidgets.QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda *_, s=sig: s.emit())
            row.addWidget(b)
        form.addRow(row)
        self._watch((), (), (self.start, self.end), ())
        self._angles(emit=False)

    def heights(self, z0, z1):
        """(bottom, top) heights kept in [z0, z1] (None: no cut)."""
        lo, hi, n = self.zrange.lo, self.zrange.hi, self.STEPS

        def z(v):
            return z0 + (v - 1) * (z1 - z0) / (n - 1)
        bottom = None if lo == 0 else z(lo)
        top = None if hi == n + 1 else z(hi)
        self.zrange.setToolTip("Heights shown: %s to %s (from the lowest "
                               "to the highest point of the grids; at the "
                               "ends: all)" % (
                                   "the bottom" if bottom is None else
                                   "%.2f m" % bottom,
                                   "the top" if top is None else
                                   "%.2f m" % top))
        return bottom, top

    def sector(self):
        """(start, end) in degrees, end after start."""
        a, b = self.start.value(), self.end.value()
        return (a, b) if b > a else (a, a + 1)

    def _angles(self, *_, emit=True):
        v, h = self.vertical.value(), self.horizontal.value()
        self.vtext.setText("%d°" % v)
        self.htext.setText("%d°" % h)
        if emit:
            self.angles.emit(float(v), float(h))

    def angle_values(self):
        return float(self.vertical.value()), float(self.horizontal.value())

    def show_angles(self, vertical, horizontal):
        """The sliders at the angles turned with the mouse (no signal)."""
        for s, v in ((self.vertical, vertical), (self.horizontal,
                                                 horizontal)):
            s.blockSignals(True)
            s.setValue(int(round(v)))
            s.blockSignals(False)
        self._angles(emit=False)


class GroupsBox(_Box):
    """The opacity of each group of the scene (2 to 100 %), multiplying
    the opacity of its parts; with a plasma quantity and rzpsi.dat, the
    band of rho_p it is shown in (its innermost and outermost flux
    surfaces)."""

    factor = Signal(str, float)
    band = Signal()

    def __init__(self, parent=None):
        super().__init__("Opacity", parent)
        form = left_form(self)
        self.sliders = {}
        for g in GROUPS:
            s = _slider(2, 100, 100, "Opacity of the %s, in percent of "
                        "their own" % g.lower())
            s.valueChanged.connect(
                lambda v, g=g: self.factor.emit(g, v / 100.0))
            form.addRow(g, s)
            self.sliders[g] = s
        self.rho = []                   # min, max rho_p
        for text, tip in (("min ρp", "Innermost flux surface of the plasma "
                           "quantity (rho_p)"),
                          ("max ρp", "Outermost flux surface of the plasma "
                           "quantity (rho_p)")):
            w = spin(0.0, 9.999, 0.01, 0.0, 3, tip)
            w.valueChanged.connect(lambda *_: self.band.emit())
            form.addRow(text, w)
            self.rho.append(w)

    def show_groups(self, shown, rho=False):
        """Only the rows of the groups in shown; the band of rho_p if
        rho."""
        form = self.layout()
        for g, s in self.sliders.items():
            form.setRowVisible(s, g in shown)
        for w in self.rho:
            form.setRowVisible(w, rho)

    def set_band(self, lo, hi):
        """The band of rho_p shown (no signal)."""
        for w, v in zip(self.rho, (lo, hi)):
            w.blockSignals(True)
            w.setValue(v)
            w.blockSignals(False)

    def band_values(self):
        return tuple(w.value() for w in self.rho)


class TracersBox(_Box):
    """The tracers of the vector quantity: how many, the length of their
    tails, their size, their speed (true or log-compressed), where they
    are born (the line to draw on the 3D view: draw, on the 2D plot:
    draw2d), whether they live
    shorter where the magnitude is smaller, paused."""

    draw = Signal(bool)                 # the line clicked on the 3D view
    draw2d = Signal(bool)               # on the 2D plot

    def __init__(self, parent=None):
        super().__init__("Tracers", parent)
        form = left_form(self)
        self.n = _ispin(100, 20000, 500, 5000, "Number of tracers")
        self.tail = _ispin(2, 60, 2, 10, "Positions in the tail of each "
                           "tracer")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.n)
        row.addWidget(QtWidgets.QLabel("Tail"))
        row.addWidget(self.tail)
        row.addStretch(1)
        form.addRow("Number", row)
        self.size = spin(0.2, 5.0, 0.1, 1.5, 1, "Size of the heads and "
                         "of the tails")
        self.speed = spin(0.1, 10.0, 0.1, 1.0, 1, "Speed of the tracers "
                          "(the fastest cross a quarter of the view in a "
                          "second)")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.size)
        row.addWidget(QtWidgets.QLabel("Speed"))
        row.addWidget(self.speed)
        row.addStretch(1)
        form.addRow("Size", row)
        self.born = QtWidgets.QComboBox()
        for text, key in births.KINDS:
            self.born.addItem(text, key)
        self.born.setToolTip("Where the tracers are born")
        self.line = QtWidgets.QPushButton("Draw line")
        self.line.setToolTip("Click the two ends of the line on the 3D "
                             "view (on the plasma or the structure, else on "
                             "the cut face at the start of the sector; "
                             "click again to cancel); the seed line of the "
                             "streamlines too")
        self.line.clicked.connect(lambda on: self.draw.emit(bool(on)))
        self.line2d = QtWidgets.QPushButton("In 2D")
        self.line2d.setToolTip("The 2D plot in place of the 3D view: click "
                               "the two ends of the line, then the 3D view "
                               "comes back (click again to cancel)")
        self.line2d.clicked.connect(lambda on: self.draw2d.emit(bool(on)))
        row = QtWidgets.QHBoxLayout()
        for b in (self.line, self.line2d):
            b.setCheckable(True)
            b.setEnabled(False)
            row.addWidget(b)
        self.born.currentIndexChanged.connect(lambda *_: [
            b.setEnabled(self.born.currentData() == "line")
            for b in (self.line, self.line2d)])
        form.addRow("Born", self.born)
        form.addRow("", row)
        self.fade = _Check("fade", "Fade where weaker: shorter "
                           "lives where the magnitude is smaller (ageing up "
                           "to 20 times faster)")
        self.fade.setChecked(True)
        self.log = _Check("log speeds", "Log speeds: compressed "
                          "logarithmically (the slow flow moves too), else "
                          "proportional")
        self.log.setChecked(True)
        self.pause = _Check("pause", "Pause: the tracers stopped where they "
                            "are")
        form.addRow(_row(self.fade, self.log, self.pause))
        self._watch((self.born,), (self.log, self.fade),
                    (self.n, self.tail, self.size, self.speed), ())

    def drawing(self, on, in2d=False):
        """Draw line (In 2D) shows whether the line is being drawn on the
        3D view (on the 2D plot)."""
        b = self.line2d if in2d else self.line
        b.blockSignals(True)
        b.setChecked(on)
        b.blockSignals(False)

    def options(self):
        return dict(n=self.n.value(), tail=self.tail.value(),
                    size=self.size.value(), speed=self.speed.value(),
                    log=self.log.isChecked(), born=self.born.currentData(),
                    fade=self.fade.isChecked())


class RenderBox(_Box):
    """Anti-aliasing, smooth shading, eye-dome lighting, ambient
    occlusion."""

    AA = (("No", "none"), ("Low", "fxaa"), ("Medium", "msaa"),
          ("High", "ssaa"))

    def __init__(self, parent=None):
        super().__init__("Rendering", parent)
        form = left_form(self)
        self.aa = QtWidgets.QComboBox()
        for text, key in self.AA:
            self.aa.addItem(text, key)
        self.aa.setCurrentIndex(3)
        self.aa.setToolTip("Quality of the anti-aliasing: no, low (fast "
                           "approximate, FXAA), medium (multisample, MSAA), "
                           "high (supersample, SSAA; multisample while the "
                           "vessel or the structure is made transparent)")
        self.smooth = _Check("smooth", "Smooth shading: surfaces "
                             "shaded smoothly, their sharp edges kept")
        self.smooth.setChecked(True)
        self.edl = _Check("eye-dome", "Eye-dome lighting: outlines "
                          "in depth (shapes behind others)")
        self.ssao = _Check("ambient occlusion", "Ambient occlusion: darker "
                           "corners and creases (slower)")
        form.addRow("Anti-aliasing", _row(self.aa, self.smooth))
        form.addRow(_row(self.edl, self.ssao))
        self._watch((self.aa,), (self.smooth, self.edl, self.ssao), (), ())

    def options(self):
        return dict(aa=self.aa.currentData(), smooth=self.smooth.isChecked(),
                    edl=self.edl.isChecked(), ssao=self.ssao.isChecked())


class Options3D(QtWidgets.QWidget):
    """The option boxes of the 3D view, one under the other."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view, self.groups = ViewBox(), GroupsBox()
        self.tracers, self.render = TracersBox(), RenderBox()
        for w in (self.view, self.groups, self.tracers, self.render):
            lay.addWidget(w)
