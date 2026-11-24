"""Mouse modes of the 2D plot: inspect a cell (its button here), draw a
chord, a box or a polygon (started from the sections of the chords and
the statistics) or the seed line of the streamlines (from the streamline
options), the start of a field line (from the Field line section). The
shape drawn goes out with the signal done;
Escape drops the points clicked so far; a polygon closes with a click
near its first corner."""

import numpy as np
from matplotlib.lines import Line2D

from .. import theme
from ..balances.style import glow
from ...qt import QtWidgets, Signal

MODES = (
    ("Inspect\ncell", "inspect", "Click a B2.5 cell or an EIRENE triangle: "
     "the value shown there and the geometry of the cell and the "
     "triangle"),
    )
HIDDEN = ("seeds", "line", "box", "polygon", "fieldline")  # no button
CLICKED = ("fieldline",)        # a click, a drag pans the plot
POINTS = {"inspect": 1, "line": 2, "box": 2, "seeds": 2, "fieldline": 1}
GOLD = "#e8b500"                    # the cell under the mouse (Inspect)
HINTS = {"inspect": "Click a cell", "line": "Click the two ends of the line",
         "box": "Click two corners of the box", "polygon": "Click the "
         "corners of the polygon, then the first one again",
         "seeds": "Click the start and the end of the seed line",
         "fieldline": "Click a point of the B2.5 grid: the field line "
         "through it"}


class MouseTools(QtWidgets.QWidget):
    """Mode buttons of a Plot2D canvas, one under the other (pan and zoom
    of the navigation bar go off when a mode goes on, and a mode waits
    while they are on)."""

    done = Signal(str, object)      # mode, (n, 2) array of R, Z
    hint = Signal(str)
    changed = Signal()              # a mode went on or off

    def __init__(self, canvas, plot, toolbar, parent=None):
        super().__init__(parent)
        self.canvas, self.plot, self.toolbar = canvas, plot, toolbar
        self.mode, self.points, self.shape = None, [], None
        self.down = None                # field line: the press (a click)
        self.hot, self.hot_key = None, None     # cell outline (Inspect)
        row = QtWidgets.QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)
        self.buttons = {}
        for text, key, tip in MODES:
            b = QtWidgets.QPushButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.toggled.connect(lambda on, k=key: self._toggled(k, on))
            row.addWidget(b)
            self.buttons[key] = b
        canvas.mpl_connect("button_press_event", self._press)
        canvas.mpl_connect("button_release_event", self._release)
        canvas.mpl_connect("motion_notify_event", self._move)
        canvas.mpl_connect("key_press_event", self._key)

    def set_mode(self, mode):
        """Mode on, or all off with None."""
        for key, b in self.buttons.items():
            b.setChecked(key == mode)
        if mode in HIDDEN:
            self._toggled(mode, True)
        elif self.mode in HIDDEN:
            self._toggled(self.mode, False)

    def _toggled(self, key, on):
        if on:
            for k, b in self.buttons.items():
                if k != key:
                    b.setChecked(False)
            nav = str(self.toolbar.mode)
            if nav == "pan/zoom":
                self.toolbar.pan()
            elif nav == "zoom rect":
                self.toolbar.zoom()
            self.mode = key
            self.hint.emit(HINTS[key])
        elif self.mode == key:
            self.mode = None
        self.points = []
        self._draw([])
        if self.mode != "inspect":
            self._outline(None)
        self.changed.emit()

    def _press(self, event):
        if self.mode is None or event.inaxes is not self.plot.ax or \
                event.button != 1 or str(self.toolbar.mode):
            return
        if self.mode in CLICKED:        # on the release, if not dragged
            self.down = (event.x, event.y, event.xdata, event.ydata)
            return
        if self.mode == "polygon" and (event.dblclick or self._near_first(
                event)):
            if len(self.points) >= 3:
                self._finish(np.array(self.points))
            return
        self.points.append((event.xdata, event.ydata))
        if len(self.points) == POINTS.get(self.mode):
            self._finish(np.array(self.points))
        else:
            self._draw(self.points)

    def _release(self, event):
        """A click (not a drag, which pans the plot) of a mode of
        CLICKED: its point."""
        down, self.down = self.down, None
        if down is None or self.mode not in CLICKED or event.button != 1:
            return
        if np.hypot(event.x - down[0], event.y - down[1]) <= \
                4.0 * self.canvas.device_pixel_ratio:
            self._finish(np.array([down[2:]]))

    def _move(self, event):
        if self.mode == "inspect" and not str(self.toolbar.mode):
            self._outline(self._cell_at(event))
        if self.points and event.inaxes is self.plot.ax:
            if self.mode == "polygon" and self._near_first(event):
                self._draw(self.points, closed=True)
            else:
                self._draw(self.points + [(event.xdata, event.ydata)])

    def _cell_at(self, event):
        """(key, polygon) of the B2.5 cell under the mouse, else of the
        EIRENE triangle, else None."""
        run, plot = self.plot.run, self.plot
        if run is None or event.inaxes is not plot.ax or event.xdata is None:
            return None
        g = run.geometry
        it = int(plot.finder(event.xdata, event.ydata)) if \
            plot.finder is not None else -1
        if it >= 0 and g.visible[g.tri_cell[it]]:
            row = g.tri_cell[it]
            return ("cell", row), g.polygons[row]
        it = int(plot.efinder(event.xdata, event.ydata)) if \
            plot.efinder is not None else -1
        if it >= 0:
            t = run.trimesh
            k = t.triangles[it]
            return ("triangle", it), np.column_stack((t.x[k], t.y[k]))
        return None

    def _outline(self, found):
        """The cell (key, polygon) with a golden glowing outline; None:
        none. Drawn again only when the cell changes."""
        key = found[0] if found is not None else None
        if key == self.hot_key and (self.hot is None or
                                    self.hot in self.plot.ax.lines):
            return
        self.hot_key = key
        if self.hot is None or self.hot not in self.plot.ax.lines:
            self.hot = Line2D([], [], linewidth=1.6, zorder=6.4)
            self.plot.ax.add_line(self.hot)
            self.apply_theme()
        if found is None:
            self.hot.set_visible(False)
        else:
            p = np.vstack((found[1], found[1][:1]))
            self.hot.set_data(p[:, 0], p[:, 1])
            self.hot.set_visible(True)
        self.canvas.draw_idle()

    def _near_first(self, event):
        """The mouse within 10 screen pixels of the first corner of a
        polygon of at least three corners."""
        if self.mode != "polygon" or len(self.points) < 3:
            return False
        x, y = self.plot.ax.transData.transform(self.points[0])
        return np.hypot(event.x - x, event.y - y) <= \
            10.0 * self.canvas.device_pixel_ratio

    def _key(self, event):
        if event.key == "escape" and self.points:
            self.points = []
            self._draw([])

    def _finish(self, pts):
        mode, self.points = self.mode, []
        self._draw(pts, closed=mode == "polygon")
        if mode == "seeds":
            self.set_mode(None)
        self.done.emit(mode, pts)

    def _draw(self, pts, closed=False):
        """The shape (a box from two corners, a closed polygon) as one
        dashed line over the plot."""
        ax = self.plot.ax
        if self.shape is None or self.shape not in ax.lines:
            self.shape = Line2D([], [], color=theme.rgb("red"),
                                linestyle="--", linewidth=1.2, marker="+",
                                zorder=6.5)
            ax.add_line(self.shape)
        self.shape.set_markevery(None)
        p = np.asarray(pts, float).reshape(-1, 2)
        if self.mode == "box" and len(p) == 2:
            (x0, y0), (x1, y1) = p
            p = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
        elif closed and len(p):
            p = np.vstack((p, p[:1]))
        self.shape.set_data(p[:, 0], p[:, 1])
        self.canvas.draw_idle()

    def show_shape(self, mode, pts):
        """A box (two corners) or a polygon drawn as the shape."""
        p = np.asarray(pts, float).reshape(-1, 2)
        if mode == "box" and len(p) == 2:
            (x0, y0), (x1, y1) = p
            p = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        self._draw(np.vstack((p, p[:1])) if len(p) else p)

    def curve(self, r, z):
        """The line drawn as its projection (r, z) on the poloidal plane,
        its ends marked."""
        self._draw(np.column_stack((r, z)))
        self.shape.set_markevery([0, len(r) - 1])
        self.canvas.draw_idle()

    def apply_theme(self):
        """The shape drawn in the red of the theme, the cell outline in
        its gold."""
        if self.shape is not None:
            self.shape.set_color(theme.rgb("red"))
        if self.hot is not None:
            self.hot.set_color(theme.rgb(GOLD))
            self.hot.set_path_effects(glow(1.6, GOLD, strong=True,
                                           on_map=True))
