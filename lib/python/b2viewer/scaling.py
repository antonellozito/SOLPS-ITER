"""Windows whose content scales with their size, as the main window: the
aspect ratio of the first size is kept and the fonts follow the width;
the mouse navigation of a small plot (wheel zoom, drag to pan, never
out of the whole plot); the wheel never changes a menu or a number box
and scrolls on over a plot; number fields that may be emptied."""

import time
import weakref

import numpy as np

from . import theme
from ..qt import QtCore, QtGui, QtWidgets, Qt

SMALLEST = 0.6                      # of its first size, a window at least
_WINDOWS = weakref.WeakSet()        # the scaled windows (theme switch)
DRAG = 4.0                          # pixels the mouse moves to pan
WHEEL_GAP = 0.8                     # s between the wheel steps of one scroll


def aspect_size(window, event, aspect):
    """(size, aspect) for a resize (event) of a window that keeps its aspect
    ratio: size is the corrected (w, h), the side moved more deciding,
    smaller when the window and its frame would not fit the available area
    of its screen; None when no correction is needed, or when the window
    manager refused the same size before (a maximized or tiled window,
    a frame added after the start), the window then keeping the size and
    aspect it got."""
    w, h = event.size().width(), event.size().height()
    if abs(w / max(h, 1) - aspect) * h < 2:
        window._asked = None
        return None, aspect
    old = event.oldSize()
    if abs(w - old.width()) >= abs(h - old.height()):
        h = round(w / aspect)
    else:
        w = round(h * aspect)
    screen = window.screen() or QtGui.QGuiApplication.primaryScreen()
    if screen is not None:
        room, frame = screen.availableGeometry(), window.frameGeometry()
        k = min(1.0, (room.width() - frame.width() + window.width()) /
                max(w, 1), (room.height() - frame.height() +
                            window.height()) / max(h, 1))
        w, h = (int(w * k), int(h * k)) if k < 1.0 else (w, h)
    if getattr(window, "_asked", None) == (w, h):
        window._asked = None
        return None, event.size().width() / max(event.size().height(), 1)
    window._asked = (w, h)
    return (w, h), aspect


class Scaled:
    """Mixin of a window (with a layout) whose content scales with it;
    scaled() after the widgets exist. Its plots (views(): objects with a
    canvas, size0 and scale(k)) keep their size in inches (their
    resolution follows the width) and shrink when the rest leaves them
    less room."""

    def scaled(self):
        _WINDOWS.add(self)
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self._aspect = self._width = None
        self._sizing = False
        self._fonts = QtCore.QTimer(self)
        self._fonts.setSingleShot(True)
        self._fonts.setInterval(120)
        self._fonts.timeout.connect(self.restyle)
        self.restyle()

    def views(self):
        """The plots of the window."""
        return []

    def canvases(self):
        """Canvases (plotarea.ScaledCanvas) frozen at the first size."""
        return [v.canvas for v in self.views()]

    def restyle(self):
        """The stylesheet of the theme with the font of the width, then
        the plots of that width, smaller if the rest (controls that do not
        scale as much as the fonts) leaves them less room."""
        base = QtWidgets.QApplication.font().pointSizeF()
        k = self.width() / self._width if self._width else 1.0
        self.setStyleSheet(theme.stylesheet("%.2fpt" % max(
            (base if base > 0 else 13.0) * k, 4.0)))
        if self._width:
            QtCore.QTimer.singleShot(0, self._fit)

    def refit(self):
        """The plots fitted again (after a text changed), soon."""
        if self._width:
            QtCore.QTimer.singleShot(0, self, self._fit)

    def _fit(self):
        """The plots of the width once the fonts are there, smaller if
        the rest leaves them less room (the largest that fits; their texts
        are as wide as them)."""
        views = self.views()
        if not views:
            return
        k = self.width() / self._width
        if self._over(k) <= 0:
            return
        # the narrower the plots, the more lines their texts take: the
        # largest size that fits from the top, else the one missing least
        low = max(20 / views[0].size0[1], 0.5 * k)
        steps = np.linspace(k, low, 11)[1:]
        over = []
        for i, f in enumerate(steps):
            over.append(self._over(f))
            if over[-1] <= 0:
                hi, lo = (k if i == 0 else steps[i - 1]), f
                for _ in range(8):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if self._over(mid) <= 0 else (lo, mid)
                self._over(lo)
                return
        self._over(steps[int(np.argmin(over))])

    def _over(self, k):
        """Height missing with the plots at k times their size at first."""
        self._scale(k)
        lay = self.layout()
        lay.activate()
        need = lay.heightForWidth(self.width()) if lay.hasHeightForWidth() \
            else lay.sizeHint().height()
        return need - self.height()

    def prepare(self):
        """The size of the content (the plots at their size at first),
        set before the window is shown: the reference of the scaling from
        then on, whatever happens to the window while it opens."""
        if self._aspect is not None:
            return
        self.ensurePolished()
        self.layout().activate()
        w = self.sizeHint().width()
        h = self.heightForWidth(w) if self.hasHeightForWidth() else -1
        h = h if h > 0 else self.sizeHint().height()
        self.rebase(w, h)

    def rebase(self, w, h):
        """This size (pixels) the new reference of the scaling, with the
        fonts of the start."""
        again = self._width is not None
        self._aspect = self._width = None
        if again:
            self.restyle()
        self._sizing = True
        self.resize(w, h)
        self._sizing = False
        self.setMinimumSize(round(SMALLEST * w), round(SMALLEST * h))
        self._aspect, self._width = w / max(h, 1), w
        self.layout().activate()
        for c in self.canvases():
            c.freeze()

    def showEvent(self, event):
        self.prepare()
        super().showEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._aspect is None or self._sizing:
            return
        self._fonts.start()
        size, self._aspect = aspect_size(self, event, self._aspect)
        if size is None:
            self._scale(event.size().width() / self._width)
            return
        QtCore.QTimer.singleShot(0, lambda: self._resize(*size))

    def _resize(self, w, h):
        self._sizing = True
        self.resize(w, h)
        self._sizing = False
        self._scale(self.width() / self._width)
        self._fonts.start()

    def _scale(self, k):
        """The plots at k times their size at first, the rest of the
        window at the scale of its width."""
        for v in self.views():
            v.scale(k)
        self.scale_parts(self.width() / self._width if self._width else 1.0)

    def scale_parts(self, k):
        """Parts of the window at k times their size at first."""

    def refresh_theme(self):
        """What the stylesheet does not change, in the theme (after a
        switch; plots drawn by others stay to them)."""


class _Choice(Scaled, QtWidgets.QDialog):
    """A list to choose from, OK and Cancel."""

    def __init__(self, parent, title, label, items):
        super().__init__(parent)
        self.setWindowTitle(title)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(QtWidgets.QLabel(label))
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(list(items))
        lay.addWidget(self.combo)
        box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                         QtWidgets.QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        lay.addWidget(box)
        self.scaled()


def choose(parent, title, label, items):
    """(item, True) of the list chosen in a window that scales, or (item,
    False) on Cancel."""
    dlg = _Choice(parent, title, label, items)
    ok = dlg.exec() == QtWidgets.QDialog.Accepted
    return dlg.combo.currentText(), ok


def restyle_all():
    """Every scaled window (shown or not) in the current theme."""
    for w in list(_WINDOWS):
        try:
            w.restyle()
            w.refresh_theme()
        except RuntimeError:            # its Qt window is gone
            _WINDOWS.discard(w)


def squeezable(root, minimum=24):
    """The fields under root (combo boxes, spin boxes, line edits) may
    shrink to minimum pixels, their text cut, so that a narrow column
    never needs to scroll sideways; they keep their size where there is
    room."""
    for cls in (QtWidgets.QComboBox, QtWidgets.QAbstractSpinBox,
                QtWidgets.QLineEdit):
        for w in root.findChildren(cls):
            if w.minimumWidth() == 0 or w.minimumWidth() > minimum:
                w.setMinimumWidth(minimum)
            policy = w.sizePolicy()     # spin boxes: Minimum, no shrinking
            if policy.horizontalPolicy() == QtWidgets.QSizePolicy.Minimum:
                policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Preferred)
                w.setSizePolicy(policy)


def zoomed(lim, at, f, home):
    """Range lim zoomed by f around at, inside home (home if wider)."""
    lo, hi = min(lim), max(lim)
    hlo, hhi = min(home), max(home)
    lo, hi = at - (at - lo) * f, at + (hi - at) * f
    if hi - lo >= hhi - hlo:
        return tuple(home)
    shift = max(hlo - lo, 0.0) - max(hi - hhi, 0.0)
    return (lo + shift, hi + shift)


class ZoomBox:
    """A zoom box dragged with the right button on the axes ax of a
    canvas: a rubber band from the press to the mouse (inside the axes);
    on release its limits, (x, y) in data, or None for a click (moved less
    than DRAG)."""

    def __init__(self, canvas, ax):
        self.canvas, self.ax, self.start = canvas, ax, None
        self.band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle,
                                          canvas)

    def _inside(self, event):
        b = self.ax.bbox
        return (min(max(event.x, b.x0), b.x1), min(max(event.y, b.y0), b.y1))

    def _widget(self, p):
        dpr = getattr(self.canvas, "device_pixel_ratio", 1.0) or 1.0
        return QtCore.QPoint(round(p[0] / dpr),
                             round(self.canvas.height() - p[1] / dpr))

    def press(self, event):
        """True when a box starts (right button on the axes)."""
        if event.button != 3 or event.inaxes is not self.ax:
            return False
        self.start = self._inside(event)
        return True

    def motion(self, event):
        """True while a box is dragged (the rubber band follows)."""
        if self.start is None:
            return False
        p = self._inside(event)
        if np.hypot(p[0] - self.start[0], p[1] - self.start[1]) >= DRAG:
            self.band.setGeometry(QtCore.QRect(
                self._widget(self.start), self._widget(p)).normalized())
            self.band.show()
        return True

    def release(self, event):
        """(xlim, ylim) of the box, None for a click or no box."""
        if self.start is None or event.button != 3:
            return None
        p, q, self.start = self.start, self._inside(event), None
        self.band.hide()
        if abs(q[0] - p[0]) < DRAG or abs(q[1] - p[1]) < DRAG:
            return None
        inv = self.ax.transData.inverted()
        (x0, y0), (x1, y1) = inv.transform([p, q])
        return (min(x0, x1), max(x0, x1)), (min(y0, y1), max(y0, y1))


class Navigator:
    """Wheel zoom around the mouse (15 % a step), drag with the left
    button and a zoom box with the right one on one axes of a canvas,
    never out of home (the whole plot, set by set_home after each
    drawing); moved() after each change."""

    def __init__(self, canvas, ax, moved=None):
        self.canvas, self.ax, self.moved = canvas, ax, moved
        self.home, self._drag = None, None
        self.box = ZoomBox(canvas, ax)
        canvas.mpl_connect("scroll_event", self._scroll)
        canvas.mpl_connect("button_press_event", self._press)
        canvas.mpl_connect("motion_notify_event", self._motion)
        canvas.mpl_connect("button_release_event", self._release)

    def set_home(self):
        self.home = (self.ax.get_xlim(), self.ax.get_ylim())

    def _set(self, x, y):
        self.ax.set_xlim(x)
        self.ax.set_ylim(y)
        self.canvas.draw_idle()
        if self.moved is not None:
            self.moved()

    def _scroll(self, event):
        if event.inaxes is not self.ax or self.home is None:
            return
        gui = event.guiEvent
        steps = gui.angleDelta().y() / 120.0 if hasattr(
            gui, "angleDelta") else event.step
        f = 0.85 ** float(np.clip(steps, -3.0, 3.0))
        self._set(self._lim(self.ax.get_xlim(), event.xdata, f, 0),
                  self._lim(self.ax.get_ylim(), event.ydata, f, 1))

    def _lim(self, lim, at, f, i):
        """zoomed, on the axis scale (log axes in decades)."""
        log = (self.ax.get_xscale(), self.ax.get_yscale())[i] == "log"
        home = self.home[i]
        if log and min(lim) > 0 and min(home) > 0 and at > 0:
            return tuple(10.0 ** np.asarray(zoomed(
                np.log10(lim), np.log10(at), f, np.log10(home))))
        return zoomed(lim, at, f, home)

    def _press(self, event):
        if self.home is not None and self.box.press(event):
            return
        if event.button == 1 and event.inaxes is self.ax and \
                self.home is not None:
            self._drag = (event.x, event.y, self.ax.get_xlim(),
                          self.ax.get_ylim(), False)

    def _motion(self, event):
        if self.box.motion(event) or self._drag is None:
            return
        x0, y0, xlim, ylim, moved = self._drag
        dx, dy = event.x - x0, event.y - y0
        if not moved:
            if np.hypot(dx, dy) < DRAG:
                return
            self._drag = (x0, y0, xlim, ylim, True)
            self.canvas.setCursor(Qt.ClosedHandCursor)
        box = self.ax.bbox
        lims = []
        for i, (lim, d, size) in enumerate(((xlim, dx, box.width),
                                            (ylim, dy, box.height))):
            log = (self.ax.get_xscale(), self.ax.get_yscale())[i] == "log"
            a = np.log10(lim) if log and min(lim) > 0 else np.asarray(lim)
            a = a - d * (a[1] - a[0]) / size
            home = np.log10(self.home[i]) if log and min(lim) > 0 and \
                min(self.home[i]) > 0 else self.home[i]
            a = zoomed(a, 0.5 * (a[0] + a[1]), 1.0, home)
            lims.append(tuple(10.0 ** np.asarray(a)) if log and min(lim) > 0
                        else a)
        self._set(*lims)

    def _release(self, event):
        lims = self.box.release(event)
        if lims is not None:
            self._set(*lims)
        if self._drag is not None and self._drag[4]:
            self.canvas.unsetCursor()
        self._drag = None


class Number(QtGui.QDoubleValidator):
    """A number or nothing: an emptied field reports its change (empty:
    automatic or the default), as a number typed does."""

    def validate(self, text, pos):
        if not text.strip():
            return QtGui.QValidator.Acceptable, text, pos
        return super().validate(text, pos)


class WheelGuard(QtCore.QObject):
    """The wheel never changes a menu or a number box (the area around
    them scrolls instead); a plot inside a scrolled area zooms only when
    the wheel starts over it: while the area scrolls (steps less than
    WHEEL_GAP apart) it goes on scrolling over the plots it meets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scrolled = 0.0             # time of the last step that scrolled

    def eventFilter(self, obj, event):
        if event.type() != QtCore.QEvent.Wheel or \
                not isinstance(obj, QtWidgets.QWidget):
            return False
        now = time.monotonic()
        if isinstance(obj, (QtWidgets.QComboBox,
                            QtWidgets.QAbstractSpinBox)):
            event.ignore()              # on to the widgets around it
            return True
        area = obj.parentWidget()
        if isinstance(area, QtWidgets.QAbstractScrollArea) and \
                obj is area.viewport():
            self.scrolled = now
            return False
        if hasattr(obj, "figure") and _scrolled_area(obj) is not None and \
                now - self.scrolled < WHEEL_GAP:
            self.scrolled = now
            event.ignore()              # the area goes on scrolling
            return True
        return False


def _scrolled_area(w):
    """The scroll area that w is inside, or None."""
    w = w.parentWidget()
    while w is not None:
        if isinstance(w, QtWidgets.QScrollArea):
            return w
        w = w.parentWidget()
    return None


def guard_wheel(app):
    """WheelGuard on the whole application (once)."""
    if getattr(app, "wheel_guard", None) is None:
        app.wheel_guard = WheelGuard(app)
        app.installEventFilter(app.wheel_guard)
