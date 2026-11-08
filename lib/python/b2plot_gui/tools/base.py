"""Mouse modes of the 2D plot: inspect a cell, draw a line, a box or a
polygon, or the seed line of the streamlines. The shape drawn goes out
with the signal done and stays drawn until the next one; Escape drops
the points clicked so far."""

import numpy as np
from matplotlib.lines import Line2D

from ...qt import QtWidgets, Signal

MODES = (
    ("Inspect", "inspect", "Click a cell or triangle: index, position, "
     "volume and the values of the quantities loaded"),
    ("Line", "line", "Click the two ends of a line: profile of the "
     "quantity shown, integral, average; flux through the line for flux "
     "densities"),
    ("Box", "box", "Click two corners: statistics of the cells shown "
     "inside"),
    ("Polygon", "polygon", "Click the corners, double-click the last one: "
     "statistics of the cells shown inside"),
    ("Seeds", "seeds", "Click the two ends of the seed line of the "
     "streamlines"))
POINTS = {"inspect": 1, "line": 2, "box": 2, "seeds": 2}
HINTS = {"inspect": "Click a cell", "line": "Click the two ends of the line",
         "box": "Click two corners of the box", "polygon": "Click the "
         "corners of the polygon, double-click the last one",
         "seeds": "Click the start and the end of the seed line"}


class MouseTools(QtWidgets.QWidget):
    """Mode buttons over a Plot2D canvas (pan and zoom of the tool bar go
    off when a mode goes on, and a mode waits while they are on)."""

    done = Signal(str, object)      # mode, (n, 2) array of R, Z
    shown = Signal()                # statistics of the cells shown
    hint = Signal(str)

    def __init__(self, canvas, plot, toolbar, parent=None):
        super().__init__(parent)
        self.canvas, self.plot, self.toolbar = canvas, plot, toolbar
        self.mode, self.points, self.shape = None, [], None
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QtWidgets.QLabel("Mouse"))
        self.buttons = {}
        for text, key, tip in MODES:
            b = QtWidgets.QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.toggled.connect(lambda on, k=key: self._toggled(k, on))
            row.addWidget(b)
            self.buttons[key] = b
        stats = QtWidgets.QToolButton()
        stats.setText("Statistics of the cells shown")
        stats.setToolTip("Volume integral, average, minimum, maximum and "
                         "histogram of the quantity over the cells shown "
                         "(Cells shown: index ranges, regions, Only where)")
        stats.clicked.connect(lambda *_: self.shown.emit())
        row.addWidget(stats)
        row.addStretch(1)
        canvas.mpl_connect("button_press_event", self._press)
        canvas.mpl_connect("motion_notify_event", self._move)
        canvas.mpl_connect("key_press_event", self._key)

    def set_mode(self, mode):
        """Mode on, or all off with None."""
        for key, b in self.buttons.items():
            b.setChecked(key == mode)

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

    def _press(self, event):
        if self.mode is None or event.inaxes is not self.plot.ax or \
                event.button != 1 or str(self.toolbar.mode):
            return
        if self.mode == "polygon" and event.dblclick:
            if len(self.points) >= 3:
                self._finish(np.array(self.points))
            return
        self.points.append((event.xdata, event.ydata))
        if len(self.points) == POINTS.get(self.mode):
            self._finish(np.array(self.points))
        else:
            self._draw(self.points)

    def _move(self, event):
        if self.points and event.inaxes is self.plot.ax:
            self._draw(self.points + [(event.xdata, event.ydata)])

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
            self.shape = Line2D([], [], color="red", linestyle="--",
                                linewidth=1.2, marker="+", zorder=6.5)
            ax.add_line(self.shape)
        p = np.asarray(pts, float).reshape(-1, 2)
        if self.mode == "box" and len(p) == 2:
            (x0, y0), (x1, y1) = p
            p = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
        elif closed and len(p):
            p = np.vstack((p, p[:1]))
        self.shape.set_data(p[:, 0], p[:, 1])
        self.canvas.draw_idle()
