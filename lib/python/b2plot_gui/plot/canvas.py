"""Matplotlib side of the 2D tab: field, vectors and overlays on one axes.

Overlay artists are built once per run and only restyled; the field and
vector artists are rebuilt when the quantity or the plot type changes,
and only recoloured when the colour options change. All values come from
b2plot (data.py); the choices here (colours, levels, resampling for
streamlines) are presentation only.
"""

from dataclasses import replace

import numpy as np
import matplotlib.tri as mtri

from ...b2plot import labels
from .. import theme
from .overlays import LayerMixin
from .scalar import ScalarMixin
from .styles import LAYERS, LabelStyle, PlotStyle
from .surface import SurfaceMixin
from .texts import TextMixin
from .vector import VectorMixin

TOP = 3.0       # room over a fixed plot: title, header and extra label line


class Plot2D(ScalarMixin, VectorMixin, LayerMixin, SurfaceMixin, TextMixin):
    """One axes (a 3D one for surfaces) with a colour-bar slot at its right
    and a bar under it for the wall strip. fixed: the boxes do not depend
    on the texts (the plot of the GUI), and an empty colour-bar slot shows
    a placeholder."""

    def __init__(self, fig, rect=(0.0, 0.0, 1.0, 1.0), fixed=False):
        self.fig, self.rect, self.fixed = fig, tuple(rect), fixed
        self.label_artists = []
        self.label_style = LabelStyle()
        self._top_pts = 0.0         # header and extra label
        self.bottom_bar = False     # wall strip colour bar under the plot
        self.bbar = None
        self.reference = None       # size (inches) the fixed boxes keep
        self.requested = None       # the view last asked for (R, Z box)
        ax_box, cax_box, bax_box = self._positions()
        self.ax = fig.add_axes(ax_box)
        self.ax3d = None
        self.cax = fig.add_axes(cax_box)
        self.cax.set_visible(False)
        self.bax = fig.add_axes(bax_box)
        self.bax.set_visible(False)
        fig.set_facecolor(theme.figure_bg())
        fig.canvas.mpl_connect("resize_event", self._place)
        self.run = None
        self.layer_styles = {k: replace(s) for k, (_, s) in LAYERS.items()}
        self.layer_artists = {}
        self.field_artists = []
        self.data = None
        self.style = PlotStyle()
        self.mappable = None
        self.cbar = None
        self._cell_pc = None
        self._cell_key = None
        self._tri_pc = None
        self._reset_axes()
        self.ax.set_xticks([])          # an empty frame until a run is set
        self.ax.set_yticks([])

    def _positions(self):
        """Boxes of the axes, of the colour bar at its right and of the
        bar under it, in the rectangle of the figure. Margins in points:
        scaled with the label size, or (fixed) those of the default size
        with one line for the header and the extra label, so that the plot
        box never moves; the bar under the plot takes its room only when
        shown."""
        x, y, w, h = self.rect
        pw, ph = np.maximum(self.inches() * 72.0, 1.0)
        fs = 10.0 if self.fixed else 10.0 * self.label_style.size
        top = (TOP * fs if self.fixed else 3.0 * fs + self._top_pts) / ph
        left, bottom = 6.0 * fs / pw, 4.2 * fs / ph
        under = 3.6 * fs / ph if self.bottom_bar else 0.0
        gap, bar, right = 1.2 * fs / pw, 1.8 * fs / pw, 4.6 * fs / pw
        aw = max(w - left - gap - bar - right, 0.1 * w)
        ah = max(h - bottom - under - top, 0.1 * h)
        ax = [x + left, y + bottom + under, aw, ah]
        return ax, [x + left + aw + gap, y + bottom + under, bar, ah], [
            x + left, y + 1.8 * fs / ph, aw, 1.2 * fs / ph]

    def inches(self):
        """Size of the figure for the boxes: the reference size of a fixed
        plot (its boxes are fractions of the figure from then on)."""
        if self.fixed and self.reference is not None:
            return np.asarray(self.reference, float)
        return self.fig.get_size_inches()

    def freeze(self):
        """The present size becomes the reference of a fixed plot."""
        self.reference = tuple(self.fig.get_size_inches())
        self._place()

    def _place(self, *_):
        """Axes and bars to their boxes (labels, bottom bar or figure size
        changed), keeping the equal aspect."""
        ax_box, cax_box, bax_box = self._positions()
        self.cax.set_position(cax_box)
        self.bax.set_position(bax_box)
        if not np.allclose(self.ax.get_position().bounds, ax_box):
            self.ax.set_position(ax_box)
            self._keep_aspect()
        if self.ax3d is not None:
            self.ax3d.set_position(ax_box)

    def _reset_axes(self):
        self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.set_facecolor(theme.axes_bg())
        self.ax.set_xlabel("R (m)")
        self.ax.set_ylabel("Z (m)")

    def apply_theme(self):
        """Backgrounds and layer colours of the current theme (the field is
        drawn again by show)."""
        self.fig.set_facecolor(theme.figure_bg())
        self.ax.set_facecolor(theme.axes_bg())
        if self.ax3d is not None:
            self.ax3d.set_facecolor(theme.figure_bg())
        if self.run is not None:
            for key in LAYERS:
                self._build_layer(key)

    # --------------------------------------------------------------- run
    def set_run(self, run, hover=True):
        self._drop_colorbar()
        self.field_artists, self.layer_artists = [], {}
        self.label_artists = []
        self.ax.cla()
        self._reset_axes()
        self.cax.set_visible(False)
        self.run, self.data, self.mappable = run, None, None
        self._cell_pc = self._tri_pc = self._cell_key = None
        g = run.geometry
        self.tri = mtri.Triangulation(g.vx[:, 0], g.vx[:, 1], g.triangles)
        self.finder = self.tri.get_trifinder() if hover else None
        self.etri = self.efinder = self.ecentres = None
        if run.trimesh is not None:
            t = run.trimesh
            self.etri = mtri.Triangulation(t.x, t.y, t.triangles)
            self.efinder = self.etri.get_trifinder() if hover else None
            self.ecentres = np.column_stack((t.x, t.y))[t.triangles].mean(1)
        for key in LAYERS:
            self._build_layer(key)
        self.set_view(self.full_box())


    # ------------------------------------------------------------- field
    def clear_field(self):
        self._drop_colorbar()
        self._drop_bottom_bar()
        for a in self.field_artists:
            a.remove()
        self.field_artists = []
        self.mappable = None
        if self._cell_pc is not None:
            self._cell_pc.set_visible(False)
        if self._tri_pc is not None:
            self._tri_pc.set_visible(False)
        self.cax.set_visible(False)

    def show_empty(self):
        """Nothing plotted: the layers, an empty colour-bar slot and no
        title."""
        self.clear_field()
        self._axes3d(False)
        self.data = None
        self._placeholder()
        self.ax.set_title("")

    def show(self, data, style, unit=None, overlays=None):
        """Draw a Field or Vector with a PlotStyle (unit: colour-bar label,
        default the unit in the label b2plot sent). overlays maps "arrows"
        and "lines" to (data, OverlayStyle) drawn over it, "mask" to a cell
        field shown where it is positive."""
        self.clear_field()
        self.data, self.style = data, replace(style)
        self.unit = data.unit if unit is None else unit
        if data is None:
            return
        cond = (overlays or {}).get("mask", (None, None))[0]
        self.mask = self._cell_mask(style, cond)
        self._mask_name = getattr(cond, "name", None)
        self._axes3d(style.kind == "surface" and not hasattr(data, "vr"))
        if hasattr(data, "vr"):
            self._vectors(data, style)
        elif style.kind == "surface":
            self._surface(data, style)
        elif data.location == "cells":
            self._cell_field(data, style)
        else:
            self._tri_field(data, style)
        for role, (odata, ostyle) in (overlays or {}).items():
            if odata is not None:
                self._overlay(role, odata, ostyle, style)
        self._colorbar(data, style)

    # -------------------------------------------------------------- views
    def full_extent(self):
        g = self.run.geometry
        pts = [g.vx[np.unique(g.triangles)]]
        for key in ("structure", "device"):
            seg = self.run.layers.get(key)
            if seg is not None and len(seg):
                pts.append(seg.reshape(-1, 2))
        p = np.vstack(pts)
        return (float(p[:, 0].min()), float(p[:, 0].max()),
                float(p[:, 1].min()), float(p[:, 1].max()))

    def full_box(self):
        """The view limits of the run: grid and device structure with a
        small margin (the start view, Restore, and the most a view may
        show)."""
        x0, x1, y0, y1 = self.full_extent()
        pad = 0.02 * max(x1 - x0, y1 - y0)
        return (x0 - pad, x1 + pad, y0 - pad, y1 + pad)

    def _fit(self, box):
        """The box widened to the equal aspect of the axes."""
        x0, x1, y0, y1 = box
        bb = self.ax.get_window_extent()
        if bb.width > 0 and bb.height > 0 and x1 > x0 and y1 > y0:
            want = bb.height / bb.width
            if (y1 - y0) / (x1 - x0) < want:
                c, h = 0.5 * (y0 + y1), 0.5 * (x1 - x0) * want
                y0, y1 = c - h, c + h
            else:
                c, h = 0.5 * (x0 + x1), 0.5 * (y1 - y0) / want
                x0, x1 = c - h, c + h
        return x0, x1, y0, y1

    def set_view(self, box):
        """Show at least this box, widened to the equal aspect of the axes
        (and again so after a resize), within the limits of the run."""
        self.requested = tuple(box)
        x0, x1, y0, y1 = self._fit(box)
        self.ax.set_xlim(x0, x1)
        self.ax.set_ylim(y0, y1)
        self.clamp()

    def clamp(self):
        """The view inside the limits of the run: no larger than they are,
        moved back inside; True if it changed."""
        if self.run is None:
            return False
        lx0, lx1, ly0, ly1 = self._fit(self.full_box())
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        if x1 - x0 >= lx1 - lx0 - 1e-12 or y1 - y0 >= ly1 - ly0 - 1e-12:
            box = (lx0, lx1, ly0, ly1)
        else:
            dx = max(lx0 - x0, 0.0) - max(x1 - lx1, 0.0)
            dy = max(ly0 - y0, 0.0) - max(y1 - ly1, 0.0)
            box = (x0 + dx, x1 + dx, y0 + dy, y1 + dy)
        if np.allclose(box, (x0, x1, y0, y1), rtol=0.0, atol=1e-12):
            return False
        self.ax.set_xlim(box[0], box[1])
        self.ax.set_ylim(box[2], box[3])
        return True

    def zoom_at(self, x, y, factor):
        """Zoom around (x, y) by factor (below 1: in), within the limits."""
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        self.set_view((x - (x - x0) * factor, x + (x1 - x) * factor,
                       y - (y - y0) * factor, y + (y1 - y) * factor))

    def _keep_aspect(self):
        """Z range for the equal aspect after the axes changed height."""
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        bb = self.ax.get_window_extent()
        if bb.width > 0 and x1 > x0:
            c, h = 0.5 * (y0 + y1), 0.5 * (x1 - x0) * bb.height / bb.width
            self.ax.set_ylim(c - h, c + h)

    def get_view(self):
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        return (x0, x1, y0, y1)

    # -------------------------------------------------------------- hover
    def lookup(self, x, y):
        """Two lines on the cell or triangle at (x, y): the position, then
        the cell and the value; '' without a run."""
        if self.run is None:
            return ""
        out = "R %.4f m  Z %.4f m\n" % (x, y)
        g, d = self.run.geometry, self.data
        it = int(self.finder(x, y))
        if it >= 0:
            row = g.tri_cell[it]
            out += "  cell %d" % g.cells[row]
            if g.classical and g.ix[row] >= 0:
                out += " (ix %d, iy %d)" % (g.ix[row], g.iy[row])
        if d is None:
            return out.strip()
        col = self._column(d, self.style)
        unit = labels.any_to_plain(d.unit)
        if hasattr(d, "vr") and d.location == "cells":
            if it >= 0:
                i = g.cells[g.tri_cell[it]] - 1
                out += "  |v| %.4g %s" % (np.hypot(d.vr[col][i],
                                                   d.vz[col][i]), unit)
        elif hasattr(d, "vr") and self.efinder is not None:
            jt = int(self.efinder(x, y))
            if jt >= 0:
                out += "  triangle %d  |v| %.4g %s" % (
                    jt + 1, np.hypot(d.vr[col][jt], d.vz[col][jt]), unit)
        elif d.location == "cells" and it >= 0:
            out += "  %s %.4g %s" % (d.name, d.values[col][g.cells[
                g.tri_cell[it]] - 1], unit)
        elif d.location == "triangles" and self.efinder is not None:
            jt = int(self.efinder(x, y))
            if jt >= 0:
                out += "  triangle %d  %s %.4g %s" % (
                    jt + 1, d.name, d.values[col][jt], unit)
        return "\n".join(line.strip() for line in out.split("\n"))
