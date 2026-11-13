"""Parts of the balance windows: a plot with its equation (the line under
the mouse glows, a click on a line opens what it is made of), the scaling
of a window with its size as the main window does, the species check
boxes, and save and export of the plots."""

import os
import re

import numpy as np
from matplotlib.figure import Figure

from .. import theme
from ..output import printfig
from ..panels.plotarea import ScaledCanvas
from ...qt import QtCore, QtWidgets, Qt, Signal
from . import datafile, plots, style

BOX = (420, 315)                    # plot box at first (pixels, 4:3)
LEFT, RIGHT, TOP, BOTTOM = 80, 18, 34, 54   # around it (pixels)
LEGEND = 300                        # legend column of a decomposition
HOT = 2.2                           # points added to a line under the mouse
PICK = 6.0                          # pixels from a line that take it
DRAG = 4.0                          # pixels the mouse moves to pan
SMALLEST = 0.6                      # of its first size, a window at least
TIE = 1.5                           # pixels preferring a line that opens more


def _pixels(art, event):
    """Distance in pixels from the mouse to the line art."""
    if hasattr(art, "get_segments"):
        segs = art.get_segments()
        pts = [p for seg in segs for p in seg[:1]] + ([segs[-1][-1]]
                                                      if segs else [])
        xy = np.asarray(pts, float).reshape(-1, 2)
    else:
        xy = np.column_stack(art.get_data()).astype(float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) == 0:
        return np.inf
    p = art.axes.transData.transform(xy)
    q = np.array((event.x, event.y), float)
    if len(p) == 1:
        return float(np.hypot(*(p[0] - q)))
    a, b = p[:-1], p[1:]
    ab = b - a
    t = np.clip(((q - a) * ab).sum(1) / np.maximum((ab * ab).sum(1),
                                                    1e-12), 0.0, 1.0)
    return float(np.min(np.hypot(*(a + t[:, None] * ab - q).T)))


def shrinkable(*widgets):
    """Widgets that let their window get small (their text scales)."""
    for w in widgets:
        w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                        w.sizePolicy().verticalPolicy())
        w.setMinimumWidth(0)


class Text(QtWidgets.QLabel):
    """A text wrapped at a fixed width, always tall enough for all its
    lines, and for those of the longest of reserve (the texts it may show:
    its height, and so the plots, does not change with the text)."""

    def __init__(self):
        super().__init__()
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.reserve = ()
        self._probe, self._room = None, {}

    def fit(self):
        self.setMinimumHeight(0)        # else it bounds the height below
        w = self.maximumWidth()
        h = self.heightForWidth(w) if self.text() else 0
        self.setMinimumHeight(max(h, self._reserved(w)))

    def _reserved(self, w):
        """Height of the longest text of reserve at width w."""
        if not self.reserve:
            return 0
        m = self.contentsMargins()
        key = (w, self.font().key(), m.left(), self.reserve)
        if key not in self._room:
            if self._probe is None:
                self._probe = QtWidgets.QLabel()
                self._probe.setWordWrap(True)
            p = self._probe
            p.setTextFormat(self.textFormat())
            p.setFont(self.font())
            p.setContentsMargins(m)
            heights = []
            for t in self.reserve:
                p.setText(t)
                heights.append(p.heightForWidth(w))
            self._room[key] = max(heights)
        return self._room[key]

    def setText(self, text):
        super().setText(text)
        self.fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self.fit()


class PlotView(QtCore.QObject):
    """An equation (a label) and one plot of a Panel (a canvas), placed
    by the window; emits clicked(key) for a click on a line (or its legend
    entry) that opens something, hovered(series or None, global point)
    for the line under the mouse. Every plot box has the same size at
    first (BOX, 4:3) and the same margins; a decomposition has the column
    of its legend at the right. The layout is fixed, so that nothing moves
    when a line glows. The mouse wheel zooms in and out (never out of the
    view of the whole plot), dragging with the left button moves the view
    (inside the whole plot; a press without moving is a click); group.zoom
    passes the x range to the other plots of the same balance (radial or
    poloidal)."""

    clicked = Signal(object)
    hovered = Signal(object, object)

    def __init__(self, group, column=False, parent=None):
        super().__init__(parent)
        self.group, self.side, self.home = group, "", None
        self.equation = Text()
        self.equation.setTextFormat(Qt.RichText)
        self.equation.setProperty("muted", True)
        self.below = Text()                 # a text under the plot box
        self.below.setTextInteractionFlags(Qt.TextSelectableByMouse)
        w = LEFT + BOX[0] + RIGHT + (LEGEND if column else 0)
        self.text_width = LEFT + BOX[0] + (LEGEND if column else 0)
        h = TOP + BOX[1] + BOTTOM
        self.figure = Figure(figsize=(w / 100.0, h / 100.0))
        self.canvas = ScaledCanvas(self.figure)
        self.canvas.setFixedSize(w, h)
        self.size0 = (w, h)
        self.ax = self.figure.add_axes([LEFT / w, BOTTOM / h, BOX[0] / w,
                                        BOX[1] / h])
        self.legend_box = ((LEFT + BOX[0] + RIGHT) / w, (h - TOP) / h,
                           (LEGEND - RIGHT) / w, (h - TOP) / h) if column \
            else None
        self.panel, self.items, self.legend, self.hot = None, [], None, None
        self._drag = None
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self.canvas.mpl_connect("button_press_event", self._press)
        self.canvas.mpl_connect("button_release_event", self._release)
        self.canvas.mpl_connect("figure_leave_event", self._leave)
        self.canvas.mpl_connect("scroll_event", self._scroll)
        self.scale(1.0)

    def scale(self, k):
        """The plot at k times its size at first, the equation over its
        box (and its legend column) and the text under it (as wide as the
        box)."""
        self.canvas.setFixedSize(round(self.size0[0] * k),
                                 round(self.size0[1] * k))
        for label, width in ((self.equation, self.text_width),
                             (self.below, LEFT + BOX[0])):
            label.setContentsMargins(round(LEFT * k), 0, 0, 0)
            label.setFixedWidth(round(width * k))
            label.fit()

    def show_panel(self, panel):
        self.panel, self.side = panel, panel.side
        self.equation.setText(panel.equation)
        self.hot = None
        self.hovered.emit(None, None)
        self.items, self.legend = plots.draw(self.ax, panel, self.legend_box)
        self.home = (self.ax.get_xlim(), self.ax.get_ylim())
        win = self.canvas.window()
        if isinstance(win, Scaled):     # the text may need more lines
            win.refit()
        self.set_x(self.group.xzoom.get(self.side))
        self.canvas.draw_idle()

    # --------------------------------------------------------------- zoom
    def _scroll(self, event):
        """The wheel zooms around the mouse, 15 % a step, no further out
        than the whole plot; the other plots of the balance follow in x."""
        if event.inaxes is not self.ax or self.home is None:
            return
        gui = event.guiEvent
        steps = gui.angleDelta().y() / 120.0 if hasattr(
            gui, "angleDelta") else event.step
        f = 0.85 ** float(np.clip(steps, -3.0, 3.0))
        x = _zoomed(self.ax.get_xlim(), event.xdata, f, self.home[0])
        y = _zoomed(self.ax.get_ylim(), event.ydata, f, self.home[1])
        self.ax.set_xlim(x)
        self.ax.set_ylim(y)
        self.canvas.draw_idle()
        self.group.zoom(self.side, None if x == self.home[0] else x, self)

    def set_x(self, xlim):
        """The x range of the balance (None: the whole plot); y as is."""
        if self.home is None:
            return
        self.ax.set_xlim(self.home[0] if xlim is None else _zoomed(
            xlim, 0.5 * (xlim[0] + xlim[1]), 1.0, self.home[0]))
        self.canvas.draw_idle()

    def redraw(self):
        if self.panel is not None:
            self.show_panel(self.panel)

    def _hit(self, event):
        """Index of the line (or legend entry) under the mouse, or None."""
        if self.legend is not None:
            texts = self.legend.get_texts()
            handles = self.legend.legend_handles
            for i, (t, h) in enumerate(zip(texts, handles)):
                if t.contains(event)[0] or (h is not None and
                                            h.contains(event)[0]):
                    return i
        if event.inaxes is not self.ax:
            return None
        best, hit = PICK, None
        for i, (art, s) in enumerate(self.items):
            d = _pixels(art, event) - (TIE if s.key is not None else 0.0)
            if d <= best:
                best, hit = d, i
        return hit

    def _motion(self, event):
        if self._drag is not None and self._pan(event):
            return
        i = self._hit(event)
        self._set(i)
        if i is None:
            self.hovered.emit(None, None)
            return
        dpr = getattr(self.canvas, "device_pixel_ratio", 1.0) or 1.0
        at = QtCore.QPoint(round(event.x / dpr),
                           round(self.canvas.height() - event.y / dpr))
        self.hovered.emit(self.items[i][1], self.canvas.mapToGlobal(at))

    def _leave(self, event):
        self._set(None)
        self.hovered.emit(None, None)

    def _set(self, i):
        """Line i glowing and its legend entry highlighted (None: none)."""
        if i == self.hot:
            return
        for j, on in ((self.hot, False), (i, True)):
            if j is None or j >= len(self.items):
                continue
            art, s = self.items[j]
            width = s.width + (HOT if on else 0.0)
            art.set_linewidth(width)
            art.set_path_effects(style.glow(width, s.color) if on else [])
            if self.legend is not None:
                self.legend.get_texts()[j].set_bbox(
                    dict(facecolor=style.line(s.color) if s.color !=
                         "#000000" else "#888888", alpha=0.3,
                         edgecolor="none", pad=0.6) if on else None)
        self.hot = i
        key = self.items[i][1].key if i is not None else None
        self.canvas.setCursor(Qt.PointingHandCursor if key is not None
                              else Qt.ArrowCursor)
        self.canvas.draw_idle()

    def _press(self, event):
        if event.button != 1 or self.home is None:
            return
        self._drag = dict(x=event.x, y=event.y, hit=self._hit(event),
                          inside=event.inaxes is self.ax, moved=False,
                          xlim=self.ax.get_xlim(), ylim=self.ax.get_ylim())

    def _pan(self, event):
        """The view moved with the mouse (left button held); False while
        it has not moved enough to be a drag."""
        d = self._drag
        dx, dy = event.x - d["x"], event.y - d["y"]
        if not d["moved"]:
            if not d["inside"] or np.hypot(dx, dy) < DRAG:
                return False
            d["moved"] = True
            self._set(None)
            self.hovered.emit(None, None)
            self.canvas.setCursor(Qt.ClosedHandCursor)
        box = self.ax.bbox
        (x0, x1), (y0, y1) = d["xlim"], d["ylim"]
        sx, sy = (x1 - x0) / box.width, (y1 - y0) / box.height
        x = (x0 - dx * sx, x1 - dx * sx)
        y = (y0 - dy * sy, y1 - dy * sy)
        x = _zoomed(x, 0.5 * (x[0] + x[1]), 1.0, self.home[0])
        y = _zoomed(y, 0.5 * (y[0] + y[1]), 1.0, self.home[1])
        self.ax.set_xlim(x)
        self.ax.set_ylim(y)
        self.canvas.draw_idle()
        self.group.zoom(self.side, None if x == tuple(self.home[0]) else x,
                        self)
        return True

    def _release(self, event):
        d, self._drag = self._drag, None
        if d is None or event.button != 1:
            return
        if d["moved"]:
            self.canvas.setCursor(Qt.ArrowCursor)
            self._motion(event)
            return
        i = d["hit"]
        if i is not None and self.items[i][1].key is not None:
            self.clicked.emit(self.items[i][1].key)


def _zoomed(lim, at, f, home):
    """Range lim zoomed by f around at, inside home (home if wider)."""
    lo, hi = min(lim), max(lim)
    hlo, hhi = min(home), max(home)
    lo, hi = at - (at - lo) * f, at + (hi - at) * f
    if hi - lo >= hhi - hlo:
        return tuple(home)
    shift = max(hlo - lo, 0.0) - max(hi - hhi, 0.0)
    return (lo + shift, hi + shift)


class _Clicks(QtCore.QObject):
    """A click in a balance window: the system brings it to the front,
    then the windows opened from it go over it again (a window already
    active gets no activation event)."""

    PRESSES = (QtCore.QEvent.MouseButtonPress,
               QtCore.QEvent.NonClientAreaMouseButtonPress)

    def eventFilter(self, obj, event):
        if event.type() in self.PRESSES and isinstance(obj,
                                                       QtWidgets.QWidget):
            win = obj.window()
            if isinstance(win, Scaled):
                QtCore.QTimer.singleShot(0, win, win.raise_opened)
        return False


_CLICKS = []


class Scaled:
    """A window whose content scales with it, as the main window does:
    the aspect ratio of its first size is kept, the fonts follow the
    width and the plots keep their size in inches (their resolution
    follows the width). It stays over its owner window also when another
    program is active, and the windows it opened stay over it."""

    def scaled(self):
        if not _CLICKS:
            app = QtWidgets.QApplication.instance()
            _CLICKS.append(_Clicks(app))
            app.installEventFilter(_CLICKS[0])
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self._aspect = self._width = None
        self._sizing = False
        self._fonts = QtCore.QTimer(self)
        self._fonts.setSingleShot(True)
        self._fonts.setInterval(120)
        self._fonts.timeout.connect(self.restyle)
        self.restyle()

    def views(self):
        """The PlotViews of the window."""
        return []

    def opened(self):
        """The window this one opened (the next level), or None."""
        return None

    def event(self, event):
        if event.type() == QtCore.QEvent.WindowActivate:
            QtCore.QTimer.singleShot(0, self, self.raise_opened)
        return super().event(event)

    def raise_opened(self):
        """The windows opened from this one over it, level by level."""
        w = self.opened()
        if w is not None and w.isVisible():
            w.raise_()
            w.raise_opened()

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
        self.resize(w, h)
        self.setMinimumSize(round(SMALLEST * w), round(SMALLEST * h))
        self._aspect, self._width = w / max(h, 1), w
        for v in self.views():
            v.canvas.freeze()

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


class SpeciesBox(QtWidgets.QToolButton):
    """The species summed, as check boxes in a list under the button, and
    All species last. In a coupled run the species whose equations B2.5
    does not solve (residuals zero everywhere) are greyed out and not in
    All species. changed() after the choice stops changing."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.setStyleSheet("QToolButton::menu-indicator { image: none; "
                           "width: 0px; }")
        self.list = QtWidgets.QMenu(self)
        self.setMenu(self.list)
        self.boxes, self.all, self.default = [], None, []
        self._later = QtCore.QTimer(self)
        self._later.setSingleShot(True)
        self._later.setInterval(350)
        self._later.timeout.connect(self.changed.emit)

    def _add(self, text):
        box = QtWidgets.QCheckBox(text)
        holder = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(holder)
        lay.setContentsMargins(10, 2, 10, 2)
        lay.addWidget(box)
        action = QtWidgets.QWidgetAction(self.list)
        action.setDefaultWidget(holder)
        self.list.addAction(action)
        return box

    def set_file(self, bf):
        self.list.clear()
        self.boxes = []
        solved = bf.solved()
        for i, name in enumerate(bf.species):
            box = self._add(name)
            if bf.eirene and not solved[i]:
                box.setEnabled(False)
                box.setToolTip("Not solved by B2.5 in a coupled run (EIRENE "
                               "neutrals): its terms do not balance")
            box.toggled.connect(lambda on, b=box: self._toggled(b))
            self.boxes.append((box, i))
        self.list.addSeparator()
        self.all = self._add("All species")
        self.all.toggled.connect(self._all)
        self.default = [next((i for b, i in self.boxes if b.isEnabled() and
                              bf.za[i] > 0), 0)]
        self.set_selection(self.default)

    def selection(self):
        return [i for b, i in self.boxes if b.isChecked() and b.isEnabled()]

    def usable(self):
        return [i for b, i in self.boxes if b.isEnabled()]

    def set_selection(self, chosen):
        for b, i in self.boxes:
            b.blockSignals(True)
            b.setChecked(i in chosen and b.isEnabled())
            b.blockSignals(False)
        self._show()

    def _toggled(self, box):
        if not self.selection():        # never none
            box.blockSignals(True)
            box.setChecked(True)
            box.blockSignals(False)
        self._show()
        self._later.start()

    def _all(self, on):
        self.set_selection(self.usable() if on else self.default)
        self._later.start()

    def _show(self):
        sel = self.selection()
        names = [self.boxes[[i for _, i in self.boxes].index(k)][0].text()
                 for k in sel]
        whole = sel == self.usable() and len(sel) > 1
        if self.all is not None:
            self.all.blockSignals(True)
            self.all.setChecked(whole)
            self.all.blockSignals(False)
        self.setText(("All species" if whole else ", ".join(names)
                      if len(names) <= 3 else "%d species" % len(names)) +
                     " \u25be")
        self.setToolTip("Species summed: " + ", ".join(names))


class Output:
    """Save the plots and export the values of a balance window."""

    def panels(self):
        raise NotImplementedError

    def stem(self):
        return "balance"

    def save_plots(self, path=None, options=None):
        """Print figure of the panels of the window (side by side);
        returns the path written or None."""
        panels = self.panels()
        if not panels:
            return None
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), self, "Save plots")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            path = self._ask(self.stem() + "." + fmt, printfig.FILTERS[fmt])
            if path is None:
                return None
        path = printfig.with_suffix(path, fmt)
        dark = theme.is_dark()
        try:
            theme.set_dark(options.get("theme", theme.name().lower())
                           == "dark")
            many = max(len(p.series) for p in panels) > 8
            fig = Figure(figsize=(6.4 * len(panels) + 2.6 * many, 4.6))
            fig.set_layout_engine("constrained")
            for k, p in enumerate(panels):
                plots.draw(fig.add_subplot(1, len(panels), k + 1), p,
                           marks=False)
            note = printfig.save(fig, path, options)
        except (OSError, ValueError, RuntimeError) as err:
            self.status("Cannot save the plots: %s" % err)
            return None
        finally:
            theme.set_dark(dark)
        self.status(("Plots saved to %s. %s" % (path, note)).strip())
        return path

    def export_data(self, path=None):
        """The values of the plots (CSV, text, netCDF, HDF5)."""
        panels = self.panels()
        if not panels:
            return None
        if path is None:
            choice, ok = QtWidgets.QInputDialog.getItem(
                self, "Export data", "Output format",
                list(datafile.FORMATS), 0, False)
            if not ok:
                return None
            ext = datafile.FORMATS[choice]
            path = self._ask(self.stem() + ext, datafile.FILTERS[ext])
            if path is None:
                return None
            if not path.lower().endswith(ext):
                path += ext
        tables = [t for p in panels for t in plots.table(p)]
        xnames = {}
        for p in panels:
            for name, _, _ in plots.table(p):
                xnames[name] = re.sub(r"\$\\rho_\\mathrm\{pol\}\$",
                                      "rho poloidal", p.xlabel)
        try:
            datafile.write(path, self.windowTitle(), tables,
                           lambda n: xnames.get(n, "x"),
                           self.result_unit(), self.meta())
        except (OSError, ValueError) as err:
            self.status("Cannot export the data: %s" % err)
            return None
        self.status("Data written to %s" % path)
        return path

    def _ask(self, name, filters):
        settings = self.controller.settings
        start = os.path.join(settings.value("export_dir", os.getcwd()), name)
        path = QtWidgets.QFileDialog.getSaveFileName(self, "Save", start,
                                                     filters)[0]
        if path:
            settings.setValue("export_dir", os.path.dirname(path))
        return path or None

    def status(self, text):
        self.controller.status(text)
