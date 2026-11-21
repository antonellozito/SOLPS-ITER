"""A small figure of the tools (line profiles, chord sums, histograms) in
the colours of the theme, with its options under it (colour, style,
width and markers of each curve, bins, x axis of a profile, axis limits,
logarithmic axes, grid): a 4:3 plot box, wheel zoom and drag, Save plot
and Export (CSV) of the rows behind it; and the ends of a chord (R, Z and
the toroidal angle)."""

import csv
import math
import os
import re

import matplotlib
import numpy as np
from matplotlib import colormaps, colors as mcolors
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterSciNotation

from .. import theme
from ..output import printfig
from ..panels.glyphs import CmapChooser, LineStyleChooser, MarkerChooser, \
    WidthChooser
from ..panels.layers import ColorButton
from ..panels.plotarea import ScaledCanvas
from ..scaling import Navigator, Number, squeezable
from ...qt import QtCore, QtGui, QtWidgets

PLOT_ASPECT = 0.75                  # height / width of the plot box (4:3)
# room around the plot box in font sizes (the texts of the figure are as
# large as the font of the window): the widest tick labels (-0.03, -5000,
# 10^-12) with the axis label at its left, the title above, the tick labels
# and the axis label under it
LEFT, RIGHT, TOP, BOTTOM = 5.6, 1.5, 1.9, 3.25
XAXES = (("distance along the line", "s"), ("R", "R"), ("Z", "Z"),
         ("ρₚ", "rhop"),
         ("distance from the separatrix", "dssep"))
HIST = "#4c72b0"                    # bars of a histogram at first
FAMILY = {"frames": "line", "sumframes": "sums"}   # of all the frames
FRAMES_CMAP = "viridis"             # colours along the frames at first
OTHER = 0.2                         # width, marker size: frames not shown
OTHER_ALPHA = 0.6                   # opacity of their lines
ALL_WIDTH = 0.5                     # profiles of all the frames at first
NOW_COLOURS = ("#000000", "#000000")    # the profile shown at first (|v|,
NOW_STYLES = ("-", "--")                # v·n), thick
NOW_WIDTH = 2.5


def main_lines(lines):
    """The lines of the frame shown (all, without the frames)."""
    return [ln for ln in lines if getattr(ln, "frame", (0, True))[1]]


class BarColorButton(ColorButton):
    """The colour of the profile shown, as long and high as the colour bar
    of the row All above it (bar: its CmapChooser), rounded as it."""

    def __init__(self, color, bar, parent=None):
        super().__init__(color, parent)
        self.bar = bar
        bar.installEventFilter(self)
        self._swatch()

    def _swatch(self):
        bar = getattr(self, "bar", None)
        if bar is None:
            return super()._swatch()
        opt = QtWidgets.QStyleOptionComboBox()
        bar.initStyleOption(opt)
        rect = bar.style().subControlRect(
            QtWidgets.QStyle.CC_ComboBox, opt,
            QtWidgets.QStyle.SC_ComboBoxEditField, bar).adjusted(3, 3, -3, -3)
        if rect.width() <= 4:
            return super()._swatch()
        dpr = self.devicePixelRatioF()
        pix = QtGui.QPixmap(round(rect.width() * dpr),
                            round(rect.height() * dpr))
        pix.setDevicePixelRatio(dpr)
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(bar.palette().color(QtGui.QPalette.Mid),
                                  1.0))
        painter.setBrush(QtGui.QColor(mcolors.to_hex(theme.rgb(
            self.color()))))
        painter.drawRoundedRect(QtCore.QRectF(
            0.5, 0.5, rect.width() - 1.0, rect.height() - 1.0), 3.0, 3.0)
        painter.end()
        self.setIconSize(rect.size())
        self.setIcon(QtGui.QIcon(pix))

    def eventFilter(self, obj, event):
        if obj is getattr(self, "bar", None) and \
                event.type() == QtCore.QEvent.Resize:
            self._swatch()
        return False


def frame_lines(ax, x, ys, ts, curve=0):
    """The profiles ys (against x) of all the frames, at the positions ts
    along them (0 to 1), as one collection (hundreds drawn and zoomed
    fast; the row All of the options styles them); curve: the curve of the
    profile shown they belong to."""
    x = np.asarray(x, float)
    ys = [np.asarray(y, float) for y in ys if y is not None and
          len(y) == len(x)]
    if not ys:
        return None
    lc = LineCollection([np.column_stack((x, y)) for y in ys],
                        label="_frames")
    lc.frames, lc.curve = np.asarray(ts, float)[:len(ys)], curve
    ax.add_collection(lc, autolim=False)
    pts = np.column_stack((np.tile(x, len(ys)), np.concatenate(ys)))
    pts = pts[np.isfinite(pts).all(axis=1)]
    if len(pts):
        ax.update_datalim(pts)
        ax.autoscale_view()
    return lc


def _number(edit):
    try:
        return float(edit.text())
    except ValueError:
        return None


class LogLabels(LogFormatterSciNotation):
    """Labels of a logarithmic axis as narrow as those of a linear one: the
    decades as powers of ten, the other ticks labelled by their digits;
    within one decade its power over the axis (as the offset of a linear
    axis)."""

    def __call__(self, x, pos=None):
        label = super().__call__(x, pos)
        if not label or x <= 0:
            return label
        e = math.floor(math.log10(x) + 1e-9)
        m = x / 10.0 ** e
        return label if abs(m - 1.0) < 1e-6 else "%g" % round(m, 3)

    def get_offset(self):
        lo, hi = sorted(self.axis.get_view_interval())
        if lo <= 0:
            return ""
        e0 = math.floor(math.log10(lo) + 1e-9)
        e1 = math.floor(math.log10(hi) - 1e-9)
        return r"$\times\mathdefault{10^{%d}}$" % e0 if e0 == e1 else ""


class FigureOptions(QtWidgets.QGroupBox):
    """Options of the small figure: a row per curve (colour, style, width,
    markers) or the bars of a histogram (colour, bins), then the axes
    (limits, empty: automatic; logarithmic; grid); for values against the
    chord number ("sums") only the colour and symbol of the markers and
    the y axis; with all the frames of a movie ("sumframes") a colour map
    along the frames instead of a colour, the markers of the frames not
    shown a fifth as large; with the profiles of all the frames ("frames")
    per curve a row All (colour map along the frames, line style and
    width, 60 percent opaque) and a row Current (the profile shown, black
    and thick at first); changed() after each choice."""

    def __init__(self, changed, parent=None):
        super().__init__("Plot options", parent)
        self.changed = changed
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.grid = QtWidgets.QGridLayout()     # the curves or the bars
        self.grid.setColumnStretch(5, 1)
        axes = QtWidgets.QGridLayout()          # the axes, compact
        axes.setColumnStretch(6, 1)
        lay.addLayout(self.grid)
        lay.addLayout(axes)
        self.curves = []                # (name, colour, style, width, marker)
        self.bars = ColorButton(HIST)
        self.bars.changed.connect(lambda *_: changed())
        self.bins = QtWidgets.QSpinBox()
        self.bins.setRange(5, 500)
        self.bins.setValue(30)
        self.bins.setKeyboardTracking(False)
        self.bins.setToolTip("Bins of the histogram")
        self.bins.valueChanged.connect(lambda *_: changed())
        self.limits = []
        for _ in range(4):
            e = QtWidgets.QLineEdit()
            e.setValidator(Number())        # empty: automatic
            e.setPlaceholderText("auto")
            e.editingFinished.connect(lambda: changed())
            self.limits.append(e)
        self.logx, self.logy = (QtWidgets.QCheckBox("log x"),
                                QtWidgets.QCheckBox("log y"))
        self.show_grid = QtWidgets.QCheckBox("grid")
        self.show_grid.setChecked(True)
        for w in (self.logx, self.logy, self.show_grid):
            w.toggled.connect(lambda *_: changed())
        self.xrow = []                  # the widgets of the x axis row
        for i, axis in enumerate("xy"):
            lo, hi = self.limits[2 * i:2 * i + 2]
            row = (QtWidgets.QLabel(axis + " from"), lo,
                   QtWidgets.QLabel("to"), hi, (self.logx, self.logy)[i])
            for c, w in enumerate(row):
                axes.addWidget(w, i, c)
            if axis == "x":
                self.xrow = list(row)
        axes.addWidget(self.show_grid, 1, 5)
        self.xaxis = QtWidgets.QComboBox()      # of a line profile
        for text, key in XAXES:
            self.xaxis.addItem(text, key)
        self.xaxis.setToolTip("The profile as a function of the distance "
                              "along the line, of R, of Z, of ρₚ "
                              "or of the distance along it from the "
                              "separatrix (the last two only where the "
                              "profile is a function of them)")
        self.xaxis.currentIndexChanged.connect(self._xaxis)
        self.xaxis_label = QtWidgets.QLabel("x axis")
        axes.addWidget(self.xaxis_label, 2, 0)
        axes.addWidget(self.xaxis, 2, 1, 1, 3)
        self.kind = None
        self.xaxes = True               # the x axis menu with the lines

    def allow(self, keys):
        """The x axes offered for this line (the others greyed out; one
        chosen and no longer offered: the first offered, the distance
        along the line for a chord)."""
        model = self.xaxis.model()
        for i, (_, key) in enumerate(XAXES):
            model.item(i).setEnabled(key in keys)
        if self.xaxis.currentData() not in keys:
            self.xaxis.blockSignals(True)
            self.xaxis.setCurrentIndex(next((i for i, (_, k) in enumerate(
                XAXES) if k in keys), 0))
            self.xaxis.blockSignals(False)

    def _xaxis(self, *_):
        """Another x axis: its limits automatic again."""
        for e in self.limits[:2]:
            e.clear()
        self.changed()

    def set_curves(self, kind, lines):
        """The rows of a figure of this kind ("line", "frames": its lines,
        Line2D; "hist"; "sums", "sumframes"), kept when the curves are the
        same; the limits kept between one frame and all frames."""
        base = FAMILY.get(kind, kind)
        lines = main_lines(lines)
        names = [ln.get_label() if not ln.get_label().startswith("_") else
                 "Profile" for ln in lines] if base == "line" else \
            ([ln.get_label() for ln in lines] if len(lines) > 1 and
             kind == "sums" else ["Markers"] * len(lines[:1])) \
            if base == "sums" else []       # markers of each species
        if kind == "frames":            # all the profiles, the one shown
            one = len(names) == 1
            names = [n for name in names for n in (
                "All profiles" if one else "All " + name,
                "Current profile" if one else "Current " + name)]
            lines = [ln for ln in lines for _ in (0, 1)]
        if kind == self.kind and names == [c[0] for c in self.curves]:
            return
        keep = FAMILY.get(self.kind, self.kind) == base and names == [
            c[0] for c in self.curves]
        self.kind = kind
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                if w not in (self.bars, self.bins):
                    w.deleteLater()
        self.curves = []
        line = base == "line"           # sums: markers only
        for r, (name, ln) in enumerate(zip(names, lines)):
            every = kind == "sumframes" or kind == "frames" and r % 2 == 0
            now = kind == "frames" and r % 2 == 1
            if every:                   # all the frames: a colour map
                colour = CmapChooser(FRAMES_CMAP, diverging=False)
                colour.setToolTip("Colours along the frames")
                colour.currentIndexChanged.connect(
                    lambda *_: self.changed())
            else:
                colour = BarColorButton(NOW_COLOURS[min(r // 2, 1)],
                                        self.curves[-1][1]) if now else \
                    ColorButton(mcolors.to_hex(ln.get_color()))
                colour.changed.connect(lambda *_: self.changed())
            style = NOW_STYLES[min(r // 2, 1)] if now else "-" if \
                kind == "frames" else ln.get_linestyle()
            width = NOW_WIDTH if now else ALL_WIDTH if every and \
                kind == "frames" else ln.get_linewidth()
            row = (name, colour,
                   LineStyleChooser(style, with_none=True) if line else None,
                   WidthChooser(width) if line else None,
                   None if every and kind == "frames" else
                   MarkerChooser(str(ln.get_marker())))
            for w in row[2:]:
                if w is not None:
                    w.currentIndexChanged.connect(lambda *_: self.changed())
            self.grid.addWidget(QtWidgets.QLabel(name), r, 0)
            for c, w in enumerate([w for w in row[1:] if w is not None], 1):
                self.grid.addWidget(w, r, c)
            self.curves.append(row)
        if kind == "hist":
            for c, w in enumerate((QtWidgets.QLabel("Bars"), self.bars,
                                   QtWidgets.QLabel("bins"), self.bins)):
                self.grid.addWidget(w, 0, c)
        for i in range(self.grid.count()):
            self.grid.itemAt(i).widget().show()
        squeezable(self)                # new rows never widen the column
        for e in self.limits if not keep else ():
            e.clear()
        for w in (self.xaxis_label, self.xaxis):
            w.setVisible(base == "line" and self.xaxes)
        for w in self.xrow + [self.show_grid]:  # sums: the y axis only
            w.setVisible(base != "sums")

    def apply(self, ax):
        """The choices on the axes drawn (the curves in order)."""
        lines = list(ax.lines)
        if self.kind == "frames":       # rows All and Current per curve
            for lc in ax.collections:
                ts = getattr(lc, "frames", None)
                if ts is None:
                    continue
                _, cmap, style, width, _ = self.curves[min(
                    2 * lc.curve, len(self.curves) - 2)]
                lc.set_color(colormaps[cmap.name()](ts))
                lc.set_alpha(OTHER_ALPHA)
                lc.set_visible(style.currentData() != "None")
                if style.currentData() != "None":
                    lc.set_linestyle(style.currentData())
                lc.set_linewidth(width.value())
                lc.set_zorder(2.0)
            for ln in main_lines(lines):
                _, colour, style, width, marker = self.curves[min(
                    2 * getattr(ln, "curve", 0) + 1, len(self.curves) - 1)]
                ln.set_gid(colour.color())
                ln.set_linestyle(style.currentData())
                ln.set_linewidth(width.value())
                ln.set_marker(marker.currentData())
                ln.set_alpha(None)
                ln.set_zorder(2.5)
            lines = []
        if self.kind == "sumframes":    # all the frames
            size = matplotlib.rcParams["lines.markersize"]
            for ln in lines:
                t, shown = getattr(ln, "frame", (1.0, True))
                row = self.curves[min(getattr(ln, "curve", 0),
                                      len(self.curves) - 1)]
                _, cmap, style, width, marker = row
                f = 1.0 if shown else OTHER
                ln.set_gid(mcolors.to_hex(colormaps[cmap.name()](t)))
                if style is not None:
                    ln.set_linestyle(style.currentData())
                    ln.set_linewidth(width.value() * f)
                ln.set_marker(marker.currentData())
                ln.set_markersize(size * f)
                ln.set_alpha(None if shown or self.kind != "frames" else
                             OTHER_ALPHA)
                ln.set_zorder(2.5 if shown else 2.0)
            lines = []
        for (_, colour, style, width, marker), ln in zip(self.curves, lines):
            ln.set_gid(colour.color())
            if style is not None:
                ln.set_linestyle(style.currentData())
                ln.set_linewidth(width.value())
            ln.set_marker(marker.currentData())
        if self.kind == "hist":
            for p in ax.patches:
                p.set_gid(self.bars.color())
        sums = self.kind == "sums"
        x = "log" if self.logx.isChecked() and not sums else "linear"
        y = "log" if self.logy.isChecked() else "linear"
        if ax.get_xscale() != x:        # else the ticks drawn are kept
            ax.set_xscale(x)
        if ax.get_yscale() != y:
            ax.set_yscale(y)
        for axis, scale in ((ax.xaxis, x), (ax.yaxis, y)):
            if scale == "log":          # labels as narrow as linear ones
                axis.set_major_formatter(LogLabels())
                axis.set_minor_formatter(LogLabels())
        if y == "linear":               # plain from 0.01 to 9999
            ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 4))
        x0, x1, y0, y1 = (_number(e) for e in self.limits)
        if not sums:
            ax.set_xlim(left=x0, right=x1)
        ax.set_ylim(bottom=y0, top=y1)
        if sums or self.show_grid.isChecked():
            ax.grid(True, alpha=0.3)
        else:
            ax.grid(False)


class LineEnds(QtWidgets.QGroupBox):
    """R, Z and the toroidal angle phi (degrees) of the two ends of a line
    cut; moved(coords) when one is changed."""

    def __init__(self, parent=None):
        super().__init__("Start/End coordinates", parent)
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setColumnStretch(7, 1)
        self.moved = None
        self.edits = []
        for r, end in enumerate(("Start", "End")):
            grid.addWidget(QtWidgets.QLabel(end), r, 0)
            for c, name in enumerate(("R (m)", "Z (m)", "phi (°)")):
                e = QtWidgets.QLineEdit()
                e.setValidator(QtGui.QDoubleValidator())
                e.setToolTip("%s of the %s of the line" % (name, end.lower()))
                e.editingFinished.connect(self._changed)
                grid.addWidget(QtWidgets.QLabel(name), r, 2 * c + 1)
                grid.addWidget(e, r, 2 * c + 2)
                self.edits.append(e)

    FORMATS = ("%.4f", "%.4f", "%g") * 2

    def set_editable(self, on):
        for e in self.edits:
            e.setReadOnly(not on)

    def set(self, coords, moved):
        """coords: R0, Z0, phi0, R1, Z1, phi1."""
        self.moved = moved
        for e, v, fmt in zip(self.edits, coords, self.FORMATS):
            e.blockSignals(True)
            e.setText(fmt % v)
            e.blockSignals(False)
        self._coords = tuple(float(v) for v in coords)

    def _changed(self):
        """The values typed; a field not changed keeps its value (not the
        rounded text)."""
        values = [old if e.text() == fmt % old else _number(e) for e, old,
                  fmt in zip(self.edits, self._coords, self.FORMATS)]
        if None in values or self.moved is None:
            return
        if any(abs(a - b) > 1e-12 for a, b in zip(values, self._coords)):
            self._coords = tuple(values)
            self.moved(self._coords)



class FigureView(QtWidgets.QWidget):
    """The figure (a 4:3 plot box at a fixed place, the room around it
    and the texts as large as the font of the window) and its options;
    set_figure(draw, ...) shows draw(ax, options)."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.draw, self.header, self.rows, self.name = None, [], [], "plot"
        self.figure = Figure(figsize=(5.0, 4.0))
        self.canvas = ScaledCanvas(self.figure)
        self.canvas.resized = self._resized     # the box placed again
        self.ax = self.figure.add_subplot(111)
        self.nav = Navigator(self.canvas, self.ax)
        self.background = None  # all but the profile shown (blitted over)
        self.drawn = None       # key of the draw on the axes
        self.stale = False      # set while hidden: drawn once shown
        self.logx = False
        self.canvas.mpl_connect("draw_event", self._drawn)
        self.options = FigureOptions(self.redraw)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)               # the options right under the plot
        lay.addWidget(self.canvas)
        lay.addWidget(self.options)
        lay.addStretch(1)               # the options never stretched

    def resizeEvent(self, event):
        super().resizeEvent(event)
        px = max(QtGui.QFontInfo(self.font()).pixelSize(), 1)
        box = self.width() - (LEFT + RIGHT) * px
        self.canvas.setFixedHeight(max(round(
            (TOP + BOTTOM) * px + PLOT_ASPECT * box), 120))
        self._fit_dpi()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self._fit_dpi()

    def _fit_dpi(self):
        """The texts of the figure as large as those of the window (they
        follow its font when the window scales), whatever its width."""
        px = QtGui.QFontInfo(self.font()).pixelSize()
        dpi = 72.0 * px / matplotlib.rcParams["font.size"]
        fig, c = self.figure, self.canvas
        if px <= 0 or abs(fig._original_dpi - dpi) < 0.01:
            return
        fig._original_dpi = dpi
        fig._set_dpi(dpi * c.device_pixel_ratio, forward=False)
        fig.set_size_inches(max(c.width(), 1) / dpi,
                            max(c.height(), 1) / dpi, forward=False)
        if self.draw is not None:       # the zoom kept
            self.apply_theme()

    def set_figure(self, draw, header, rows, kind="line", logx=False,
                   name="plot"):
        """draw(ax, options) makes the figure (kind "line": curves,
        "hist": a histogram, at first on a logarithmic axis with logx);
        rows are what Export writes, name the file name offered. Not drawn
        while its section is not painted (a frame of a movie drawn into
        an image) or hidden (another tab): only kept, drawn when it is
        shown. A draw with a key (draw.key) equal to the one drawn and
        draw.current(options) only moves its moving lines (moves True,
        e.g. the profile shown over all the frames, the time line): their
        [(x, y)] set, blitted over the rest."""
        same = kind == getattr(self, "kind", None) and getattr(
            draw, "key", None) is not None and self.drawn == draw.key and \
            not self.stale
        self.draw, self.header, self.rows, self.name = draw, list(header), \
            list(rows), name
        self.kind, self.logx = kind, logx
        if not self.updatesEnabled():
            return
        if not self.isVisible():
            self.stale = True
            return
        self.stale = False
        if same and self._move(draw.current(self.options)):
            return
        self.ax.clear()
        draw(self.ax, self.options)
        new = FAMILY.get(kind, kind) != FAMILY.get(self.options.kind,
                                                   self.options.kind)
        self.options.set_curves(kind, list(self.ax.lines))
        if kind == "hist" and new:
            self.options.logx.blockSignals(True)
            self.options.logx.setChecked(logx)
            self.options.logx.blockSignals(False)
        self.redraw()

    def showEvent(self, event):
        super().showEvent(event)
        if self.stale:                  # once shown (a tab switched off
            QtCore.QTimer.singleShot(0, self._fresh)    # the updates)

    def _fresh(self):
        """The figure kept while hidden, drawn now that it is shown."""
        if self.stale and self.draw is not None and self.isVisible() and \
                self.updatesEnabled():
            self.stale = False
            self.set_figure(self.draw, self.header, self.rows, self.kind,
                            self.logx, self.name)

    def _move(self, curves):
        """The moving lines moved to curves ([(x, y)]): only they are
        drawn again, over the rest kept (False: drawn as a whole)."""
        lines = [ln for ln in self.ax.lines if getattr(ln, "moves", False)]
        if not lines or len(lines) != len(curves):
            return False
        for ln, (x, y) in zip(lines, curves):
            ln.set_data(x, y)
        if self.background is None:
            self.canvas.draw_idle()
            return True
        self.canvas.restore_region(self.background)
        for ln in lines:
            self.ax.draw_artist(ln)
        self.canvas.blit(self.ax.bbox)
        return True

    def _drawn(self, event):
        """After each drawing of the canvas: the plot without its moving
        lines kept, the lines drawn over it."""
        self.background = None
        lines = [ln for ln in self.ax.lines if ln.get_animated()]
        if event.canvas is not self.canvas or not lines or \
                self.canvas.is_saving():
            return
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        for ln in lines:
            self.ax.draw_artist(ln)

    def redraw(self):
        """The figure again with the options, its whole view the home of
        the mouse zoom."""
        if self.draw is None:
            return
        self.ax.clear()
        self.draw(self.ax, self.options)
        self.drawn = getattr(self.draw, "key", None)
        self.options.apply(self.ax)
        for ln in self.ax.lines:        # drawn over the background
            ln.set_animated(getattr(ln, "moves", False))
        self.ax.set_box_aspect(PLOT_ASPECT)
        self.apply_theme()
        self.nav.set_home()

    def apply_theme(self):
        """The figure in the colours of the theme (each curve and bar in
        the colour chosen, its gid)."""
        ax, color = self.ax, theme.text()
        self.figure.set_facecolor(theme.figure_bg())
        ax.set_facecolor("#424242" if theme.is_dark() else "#ffffff")
        ax.tick_params(colors=color, which="both")
        for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
            item.set_color(color)
        for spine in ax.spines.values():
            spine.set_color(color)
        lines = list(ax.lines)
        for a in lines + list(ax.patches):     # gid: the colour chosen
            line = a in lines
            if a.get_gid() is None:
                a.set_gid(mcolors.to_hex(a.get_color() if line else
                                         a.get_facecolor()))
            (a.set_color if line else a.set_facecolor)(theme.rgb(a.get_gid()))
        legend = ax.get_legend()
        if legend is not None:           # again, with the new line colours
            legend = ax.legend(fontsize="small")
            legend.get_frame().set_facecolor(theme.figure_bg())
            for t in legend.get_texts():
                t.set_color(color)
        self._place()
        self.canvas.draw_idle()

    def _resized(self):
        """The plot box for the new size of the figure (a figure drawn
        before its tab had its size kept the box of the first size)."""
        if self.draw is not None:
            self._place()
            self.canvas.draw_idle()

    def _place(self):
        """The plot box at the same place whatever the labels (4:3, the
        room around it in font sizes)."""
        font = matplotlib.rcParams["font.size"] / 72.0     # inches
        w, h = self.figure.get_size_inches()
        w, h = max(w, 1e-6), max(h, 1e-6)
        width = max(1.0 - (LEFT + RIGHT) * font / w, 0.1)
        bottom = BOTTOM * font / h
        height = min(PLOT_ASPECT * width * w / h, 1.0 - bottom - 0.02)
        self.ax.set_position([LEFT * font / w, bottom, width, height])

    def save(self, path=None, options=None):
        """Save plot: the figure as Save plot of the main window does
        (options dialog and file dialog unless given); the path or None."""
        if self.draw is None:
            return None
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), self, "Save plot")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            path = self._ask("Save plot", fmt, printfig.FILTERS[fmt])
            if path is None:
                return None
        path = printfig.with_suffix(path, fmt)
        dark = theme.is_dark()
        try:
            theme.set_dark(options.get("theme", theme.name().lower())
                           == "dark")
            self.apply_theme()
            printfig.save(self.figure, path, options)
        except (OSError, ValueError, RuntimeError):
            return None
        finally:                # the figure in the theme of the GUI again
            theme.set_dark(dark)
            self.apply_theme()
        return path

    def export(self, path=None):
        """The rows as CSV (dialog unless path is given); the path or
        None."""
        if not self.rows:
            return None
        if path is None:
            path = self._ask("Export values", "csv", "CSV (*.csv)")
            if path is None:
                return None
        with open(path, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(self.header)
            out.writerows(self.rows)
        return path

    def _ask(self, title, ext, filters):
        folder = self.settings.value("export_dir", os.getcwd())
        name = re.sub(r"[^A-Za-z0-9_.+-]+", "_", self.name) or "plot"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, title, os.path.join(folder, name + "." + ext), filters)
        if path:
            self.settings.setValue("export_dir", os.path.dirname(path))
        return path or None
