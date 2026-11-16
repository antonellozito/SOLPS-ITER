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
        w, h = event.size().width(), event.size().height()
        if abs(w / max(h, 1) - self._aspect) * h < 2:
            self._scale(w / self._width)
            return
        old = event.oldSize()
        if abs(w - old.width()) >= abs(h - old.height()):
            h = round(w / self._aspect)
        else:
            w = round(h * self._aspect)
        QtCore.QTimer.singleShot(0, lambda: self._resize(w, h))

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


def zoomed(lim, at, f, home):
    """Range lim zoomed by f around at, inside home (home if wider)."""
    lo, hi = min(lim), max(lim)
    hlo, hhi = min(home), max(home)
    lo, hi = at - (at - lo) * f, at + (hi - at) * f
    if hi - lo >= hhi - hlo:
        return tuple(home)
    shift = max(hlo - lo, 0.0) - max(hi - hhi, 0.0)
    return (lo + shift, hi + shift)


class Navigator:
    """Wheel zoom around the mouse (15 % a step) and drag with the left
    button on one axes of a canvas, never out of home (the whole plot,
    set by set_home after each drawing); moved() after each change."""

    def __init__(self, canvas, ax, moved=None):
        self.canvas, self.ax, self.moved = canvas, ax, moved
        self.home, self._drag = None, None
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
        if event.button == 1 and event.inaxes is self.ax and \
                self.home is not None:
            self._drag = (event.x, event.y, self.ax.get_xlim(),
                          self.ax.get_ylim(), False)

    def _motion(self, event):
        if self._drag is None:
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
