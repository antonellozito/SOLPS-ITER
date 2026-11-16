"""Parts of the balance section and of its extensions: a plot with its
equation (the line under the mouse glows, a click on a line opens what it
is made of), the species check boxes, and save and export of the
plots."""

import os
import re

import matplotlib
import numpy as np
from matplotlib.figure import Figure

from .. import scaling, theme
from ..output import printfig
from ..panels.plotarea import ScaledCanvas
from ..tools.figure import BOTTOM, LEFT, PLOT_ASPECT, RIGHT, TOP
from ...qt import QtCore, QtGui, QtWidgets, Qt, Signal
from . import datafile, look, plots, style

LEGEND = 22.0                       # legend column of a decomposition
#                                     (font sizes, as the room around the box)
HOT = 2.2                           # points added to a line under the mouse
PICK = 6.0                          # pixels from a line that take it
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
    lines (and no taller)."""

    def __init__(self):
        super().__init__()
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def fit(self):
        self.setMinimumHeight(0)        # else it bounds the height below
        self.setMinimumHeight(self.need(self.maximumWidth()))

    def need(self, w):
        """Height at width w."""
        return self.heightForWidth(w) if self.text() else 0

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
    by their owner; emits clicked(key) for a click on a line (or its
    legend entry) that opens something, hovered(series or None, global
    point) for the line under the mouse. The plot box is 4:3 with the room
    around it in font sizes (the texts as large as the font of the
    window), as the figures of the chords and statistics; a decomposition
    has the column of its legend at the right. follow: the height follows
    the width (the column), else set_box gives the size. The layout is
    fixed, so that nothing moves when a line glows. The mouse wheel zooms
    in and out (never out of the view of the whole plot), dragging with
    the left button moves the view (inside the whole plot; a press without
    moving is a click); group.zoom passes the x range to the other plots of
    the same part of the balance with the same x axis."""

    clicked = Signal(object)
    hovered = Signal(object, object)

    def __init__(self, group, column=False, follow=False, parent=None):
        super().__init__(parent)
        self.group, self.side, self.home = group, "", None
        self.column, self.follow = column, follow
        self.equation = Text()
        self.equation.setTextFormat(Qt.RichText)
        self.equation.setProperty("muted", True)
        self.below = Text()                 # a text under the plot box
        self.below.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.figure = Figure(figsize=(5.0, 4.0))
        self.canvas = ScaledCanvas(self.figure, self._resized)
        if follow:                          # never wider than the column
            self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                      QtWidgets.QSizePolicy.Fixed)
            self.canvas.setMinimumWidth(0)
        self.ax = self.figure.add_axes([0.15, 0.15, 0.7, 0.7])
        self.legend_box = None
        self.panel, self.items, self.legend, self.hot = None, [], None, None
        self.pinned = None              # key of the line kept glowing
        self._drag = None
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self.canvas.mpl_connect("button_press_event", self._press)
        self.canvas.mpl_connect("button_release_event", self._release)
        self.canvas.mpl_connect("figure_leave_event", self._leave)
        self.canvas.mpl_connect("scroll_event", self._scroll)

    # ------------------------------------------------------------- size
    def px(self):
        """Pixels of the font of the window."""
        return max(QtGui.QFontInfo(self.canvas.font()).pixelSize(), 1)

    def margins(self):
        """Room left, right (with the legend column), top, bottom of the
        plot box in pixels."""
        px = self.px()
        return (LEFT * px, (RIGHT + (LEGEND if self.column else 0.0)) * px,
                TOP * px, BOTTOM * px)

    def size_for(self, box):
        """Canvas size (pixels) of a plot box box pixels wide."""
        left, right, top, bottom = self.margins()
        return (round(left + box + right),
                round(top + bottom + PLOT_ASPECT * box))

    def box_for(self, width, height=None):
        """Width of the plot box in a canvas of this size (or width)."""
        left, right, top, bottom = self.margins()
        box = width - left - right
        if height is not None:
            box = min(box, (height - top - bottom) / PLOT_ASPECT)
        return max(box, 40.0)

    def set_box(self, box):
        """The canvas for a plot box box pixels wide."""
        self.canvas.setFixedSize(*self.size_for(box))

    def _resized(self):
        """The plot for the size of the canvas: its height from the width
        (follow), the texts as large as the font of the window, the box
        and the legend column at their place, the texts as wide as the
        box."""
        w, h = self.canvas.width(), self.canvas.height()
        if w <= 0:
            return
        if self.follow:
            need = self.size_for(self.box_for(w))[1]
            if h != need:
                self.canvas.setFixedHeight(need)    # resized again
                return
        px = self.px()
        dpi = 72.0 * px / matplotlib.rcParams["font.size"]
        fig = self.figure
        fig._original_dpi = dpi
        fig._set_dpi(dpi * self.canvas.device_pixel_ratio, forward=False)
        fig.set_size_inches(max(w, 1) / dpi, max(h, 1) / dpi, forward=False)
        left, right, top, bottom = self.margins()
        box = self.box_for(w, h)
        self.ax.set_position([left / w, bottom / h, box / w,
                              PLOT_ASPECT * box / h])
        if self.column:
            x0 = (left + box + RIGHT * px) / w
            self.legend_box = (x0, (h - top) / h,
                               (LEGEND - RIGHT) * px / w, (h - top) / h)
        if self.follow:                 # the texts from the left edge of
            for label in (self.equation, self.below):   # the canvas
                label.setContentsMargins(0, 0, 0, 0)
                label.setMaximumWidth(w)
                label.fit()
        if self.panel is not None:
            self.redraw()

    def show_panel(self, panel):
        panel = look.apply(panel, self.group.looks)    # the looks chosen
        self.panel, self.side = panel, panel.side
        self.equation.setText(panel.equation)
        self.hot = None
        self.hovered.emit(None, None)
        self.items, self.legend = plots.draw(
            self.ax, panel, self.legend_box, **self.group.axes_options())
        for j in range(len(self.items)):
            if self._pinned(j):
                self._glow(j, True)
        self.home = (self.ax.get_xlim(), self.ax.get_ylim())
        self.set_x(self.group.xzoom.get((self.side, panel.xlabel)))
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
        x = scaling.zoomed(self.ax.get_xlim(), event.xdata, f,
                           self.home[0])
        y = scaling.zoomed(self.ax.get_ylim(), event.ydata, f,
                           self.home[1])
        self.ax.set_xlim(x)
        self.ax.set_ylim(y)
        self.canvas.draw_idle()
        self.group.zoom(self.side, None if x == self.home[0] else x, self)

    def set_x(self, xlim):
        """The x range of the balance (None: the whole plot); y as is."""
        if self.home is None:
            return
        self.ax.set_xlim(self.home[0] if xlim is None else scaling.zoomed(
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

    def _glow(self, j, on):
        """Line j glowing and its legend entry highlighted, or not."""
        art, s = self.items[j]
        width = s.width + (HOT if on else 0.0)
        art.set_linewidth(width)
        art.set_path_effects(style.glow(width, s.color) if on else [])
        if self.legend is not None:
            self.legend.get_texts()[j].set_bbox(
                dict(facecolor=style.line(s.color) if s.color !=
                     "#000000" else "#888888", alpha=0.3,
                     edgecolor="none", pad=0.6) if on else None)

    def _pinned(self, j):
        return self.pinned is not None and self.items[j][1].key == \
            self.pinned

    def pin(self, key):
        """The line of key glows while what it opened is shown (None:
        none)."""
        old, self.pinned = self.pinned, key
        for j, (_, s) in enumerate(self.items):
            if s.key is not None and s.key in (old, key):
                self._glow(j, j == self.hot or self._pinned(j))
        self.canvas.draw_idle()

    def _set(self, i):
        """Line i glowing and its legend entry highlighted (None: none);
        the pinned line glows anyway."""
        if i == self.hot:
            return
        for j, on in ((self.hot, False), (i, True)):
            if j is None or j >= len(self.items):
                continue
            self._glow(j, on or self._pinned(j))
        self.hot = i
        key = self.items[i][1].key if i is not None else None
        self.canvas.setCursor(Qt.PointingHandCursor if key is not None
                              else Qt.ArrowCursor)
        self.canvas.draw_idle()

    def _press(self, event):
        if event.button == 3 and self.home is not None:
            self._look(event)
            return
        if event.button != 1 or self.home is None:
            return
        self._drag = dict(x=event.x, y=event.y, hit=self._hit(event),
                          inside=event.inaxes is self.ax, moved=False,
                          xlim=self.ax.get_xlim(), ylim=self.ax.get_ylim())

    def _look(self, event):
        """Right click on a line or its legend entry: its colour, width,
        style and marker in a small window at the mouse."""
        i = self._hit(event)
        if i is None:
            return
        s = self.items[i][1]
        key = (self.panel.title, s.label)

        def changed(fields):
            self.group.looks[key] = fields
            self.redraw()
        self._set(None)
        self.hovered.emit(None, None)
        dpr = getattr(self.canvas, "device_pixel_ratio", 1.0) or 1.0
        at = self.canvas.mapToGlobal(QtCore.QPoint(
            round(event.x / dpr), round(self.canvas.height() - event.y / dpr)))
        self._popup = look.LinePopup(s, changed, self.group.recolour,
                                     self.group.end_names(), self.canvas)
        self._popup.show_at(at)

    def _pan(self, event):
        """The view moved with the mouse (left button held); False while
        it has not moved enough to be a drag."""
        d = self._drag
        dx, dy = event.x - d["x"], event.y - d["y"]
        if not d["moved"]:
            if not d["inside"] or np.hypot(dx, dy) < scaling.DRAG:
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
        x = scaling.zoomed(x, 0.5 * (x[0] + x[1]), 1.0, self.home[0])
        y = scaling.zoomed(y, 0.5 * (y[0] + y[1]), 1.0, self.home[1])
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
    """Save the plots and export the values of the balance section or of
    one of its extensions."""

    def panels(self):
        raise NotImplementedError

    def stem(self):
        return "balance"

    def title(self):
        return self.controller.name

    def save_plots(self, path=None, options=None):
        """Save plot of the panels (side by side);
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
                           marks=False, **self.controller.axes_options())
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
            choice, ok = scaling.choose(self, "Export data",
                                        "Output format",
                                        list(datafile.FORMATS))
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
            datafile.write(path, self.title(), tables,
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
