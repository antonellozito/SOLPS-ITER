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
from .masks import MaskMixin
from .styles import LAYER_KEYS, LAYERS, LabelStyle, PlotStyle
from .texts import TextMixin
from .vector import VectorMixin
from .fast import FastMixin

TOP = 3.0       # room over a fixed plot: title, header and extra label line
READOUT = 0.6   # room under a fixed plot for the cursor readout (font sizes)


class Plot2D(ScalarMixin, VectorMixin, LayerMixin, TextMixin, MaskMixin,
             FastMixin):
    """One axes with the colour-bar slot of the plasma quantity at its
    right, then the slots of the vector quantity and of the wall
    quantity. fixed: the boxes do not depend on the texts and all three
    slots are always there, empty ones with a placeholder (the plot of the
    GUI); otherwise the vector and wall slots take their room only while
    their bar is shown."""

    def __init__(self, fig, rect=(0.0, 0.0, 1.0, 1.0), fixed=False):
        self.fig, self.rect, self.fixed = fig, tuple(rect), fixed
        self.label_artists = []
        self.label_style = LabelStyle()
        self._top_pts = 0.0         # header and extra label
        self.wall_bar = False       # wall strip colour bar shown
        self.wbar = None
        self.vector_bar = False     # vector colour bar shown
        self.vbar = None
        self.obar = self.oax = None     # overlay bar, inside the plot box
        self.placeholders = set()   # slots (vax, wax) with their placeholder
        self.overlay_mappable = None
        self.reference = None       # size (inches) the fixed boxes keep
        self.requested = None       # the view last asked for (R, Z box)
        ax_box, cax_box, vax_box, wax_box = self._positions()
        self.ax = fig.add_axes(ax_box)
        self.cax = fig.add_axes(cax_box)
        self.cax.set_visible(False)
        self.vax = fig.add_axes(vax_box)
        self.vax.set_visible(False)
        self.wax = fig.add_axes(wax_box)
        self.wax.set_visible(False)
        fig.set_facecolor(theme.figure_bg())
        fig.canvas.mpl_connect("resize_event", self._place)
        self.run = None
        self.layer_styles = {k: replace(s) for k, (_, s) in LAYERS.items()}
        self.layer_artists = {}
        self.field_artists = []
        self.wall_artists = []      # the wall strip, apart from the field
        self.wall_mappable = None
        self.wall_data = None       # the wall data of the strip
        self.vector_artists = []    # the vector plot, apart from the field
        self.vector_mappable = None
        self.vectors = None         # (data, style) of the vector plot
        self.vector_mask = None     # its cells shown (its own regions)
        self.tracers2d = None       # its tracers (kept on zoom and pan)
        self.mask = None            # the cells shown of the plasma plot
        self.data = None
        self.style = PlotStyle()
        self.masks, self.mask_artists = [], []
        self.mappable = None
        self.drawn = None
        self.cbar = None
        self._cell_pc = None
        self._cell_key = None
        self._tri_pc = None
        self._reset_axes()
        self.ax.set_xticks([])          # an empty frame until a run is set
        self.ax.set_yticks([])

    def _positions(self):
        """Boxes of the axes, of the colour bar at its right, of the vector
        bar and of the wall bar right of that, in the rectangle of the
        figure. Margins in points: scaled with the label size, or (fixed)
        those of the default size with one line for the header and the
        extra label and all three bar slots, and a line under the axis
        label for the readout of the cursor (the box a little lower, as
        wide), so that the plot box never moves."""
        x, y, w, h = self.rect
        pw, ph = np.maximum(self.inches() * 72.0, 1.0)
        fs = 10.0 if self.fixed else 10.0 * self.label_style.size
        top = (TOP * fs if self.fixed else 3.0 * fs + self._top_pts) / ph
        left, bottom = 6.0 * fs / pw, 4.2 * fs / ph
        gap, bar, right = 1.2 * fs / pw, 1.8 * fs / pw, 3.7 * fs / pw
        wall = bar + right if self.fixed or self.wall_bar else 0.0
        vec = bar + right if self.fixed or self.vector_bar else 0.0
        aw = max(w - left - gap - bar - right - vec - wall, 0.1 * w)
        ah = max(h - bottom - top, 0.1 * h)
        if self.fixed:                  # the box lower, as wide
            room = min(READOUT * fs / ph, ah - 0.1 * h)
            ah, bottom = ah - room, bottom + room
        x0 = x + left + aw + gap
        return ([x + left, y + bottom, aw, ah], [x0, y + bottom, bar, ah],
                [x0 + bar + right, y + bottom, bar, ah],
                [x0 + bar + right + vec, y + bottom, bar, ah])

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
        """Axes and bars to their boxes (labels, wall bar or figure size
        changed), keeping the equal aspect."""
        ax_box, cax_box, vax_box, wax_box = self._positions()
        self.cax.set_position(cax_box)
        self.vax.set_position(vax_box)
        self.wax.set_position(wax_box)
        if not np.allclose(self.ax.get_position().bounds, ax_box):
            self.ax.set_position(ax_box)
            self._keep_aspect()

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
        self.placeholders.clear()       # in the colours of the theme
        if self.run is not None:
            for key in LAYER_KEYS:
                self._build_layer(key)
            self.draw_masks()

    # --------------------------------------------------------------- run
    def set_run(self, run, hover=True):
        self.placeholders.clear()
        self.fast = None            # the kept parts of the fast frames
        self._drop_overlay_bar()
        self._drop_colorbar()
        self._drop_vector_bar()
        self._drop_wall_bar()
        self.field_artists, self.layer_artists = [], {}
        self.wall_artists, self.wall_mappable = [], None
        self.vector_artists, self.vector_mappable = [], None
        self.vectors = self.wall_data = None
        if self.tracers2d is not None:
            self.tracers2d.detach()
        self.tracers2d = None
        self.label_artists = []
        self.ax.cla()
        self._reset_axes()
        self.cax.set_visible(False)
        self.run, self.data, self.mappable = run, None, None
        self.mask = self.vector_mask = None
        self._cell_pc = self._tri_pc = self._cell_key = None
        g = run.geometry
        self.tri = mtri.Triangulation(g.vx[:, 0], g.vx[:, 1], g.triangles)
        self.finder = g.finder if hover else None
        self.etri = self.efinder = self.ecentres = None
        if run.trimesh is not None:
            t = run.trimesh
            self.etri = mtri.Triangulation(t.x, t.y, t.triangles)
            self.efinder = self.etri.get_trifinder() if hover else None
            self.ecentres = np.column_stack((t.x, t.y))[t.triangles].mean(1)
        for key in LAYER_KEYS:
            self._build_layer(key)
        self.masks, self.mask_artists = [], []  # of the run: set again
        self.set_view(self.full_box())


    # ------------------------------------------------------------- field
    def clear_field(self):
        """The plasma field and its overlay away (the wall strip and the
        vectors stay)."""
        self._drop_colorbar()
        self._drop_overlay_bar()
        self.overlay_mappable = None
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
        self.data = None
        self._placeholder()
        self._empty_slots()
        self.ax.set_title("")

    def clear_wall(self):
        for a in self.wall_artists:
            a.remove()
        self.wall_artists, self.wall_mappable = [], None
        self.wall_data = None
        self._drop_wall_bar()

    def set_wall(self, data, style, label=None):
        """The wall quantity data (WallStyle style) as a strip along the
        wall elements, with its colour bar (label, default the label of
        data); None: no wall plot. Apart from the plasma field: either may
        be shown alone."""
        self.clear_wall()
        if data is None or self.run is None:
            return
        arts = self._wall_strip(data, style, label)    # strip, joints
        if arts is not None:
            self.wall_artists, self.wall_mappable = arts, arts[0]
            self.wall_data = data
            self.wall_artists += self._wall_marks(data, style.width)

    def clear_vectors(self):
        if self.tracers2d is not None:  # attached again if still plotted
            self.tracers2d.detach()
        for a in self.vector_artists:
            try:
                a.remove()
            except (ValueError, AttributeError):
                pass
        self.vector_artists, self.vector_mappable = [], None
        self.vectors = None
        self._drop_vector_bar()

    def set_vectors(self, data, style, unit=None, parts=None):
        """A vector quantity (PlotStyle style: kind, arrows, streamlines,
        colour by magnitude with its own colour bar) over the plasma
        field, or alone, or its parts (tools/splits.combine) as arrows of
        their own; None: no vector plot."""
        self.clear_vectors()
        if data is None or self.run is None:
            return
        self.vector_mask = self._cell_mask(style, None)
        n0, field = len(self.field_artists), self.mappable
        self.mappable = None
        self._vectors(data, style, parts)
        self.vector_artists = self.field_artists[n0:]
        self.vectors = (data, style)
        del self.field_artists[n0:]
        self.vector_mappable, self.mappable = self.mappable, field
        if self.vector_mappable is not None and style.colorbar:
            self.vector_colorbar(self.vector_mappable,
                                 data.unit if unit is None else unit)

    def show(self, data, style, unit=None, overlays=None):
        """Draw a Field with a PlotStyle (unit: colour-bar label, default
        the unit in the label b2plot sent). overlays maps "lines" to
        (data, PlotStyle, label) of the contour lines drawn over it,
        "mask" to a cell field shown where it is positive, "wall" to (wall
        data, WallStyle, label) drawn whatever data is (None: the wall
        alone), "vectors" to (vector data, PlotStyle, label) drawn over it
        or alone."""
        self.clear_field()
        wall = (overlays or {}).get("wall")
        if wall is not None:
            self.set_wall(*wall)
        vectors = (overlays or {}).get("vectors")
        self.drawn = None       # mask and guard labels: cells or faces drawn
        self.data, self.style = data, replace(style)
        if data is None:
            self._placeholder()
            if vectors is not None:
                self.set_vectors(*vectors)
            return
        self.unit = data.unit if unit is None else unit
        cond = (overlays or {}).get("mask", (None, None))[0]
        self.mask = self._cell_mask(style, cond)
        self._mask_name = getattr(cond, "name", None)
        if data.location == "cells":
            self._cell_field(data, style)
        else:
            self._tri_field(data, style)
        lines = (overlays or {}).get("lines")
        if lines is not None and lines[0] is not None:
            self._overlay_lines(*lines)
        self._colorbar(data, style)
        if vectors is not None:
            self.set_vectors(*vectors)

    # -------------------------------------------------------------- views
    def full_extent(self):
        g = self.run.geometry
        pts = [g.vx[np.unique(g.triangles)]]
        for key in ("structure", "vessel"):
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

    def pan_to(self, box):
        """The view moved to box (same size), stopped at the limits of the
        run before it is drawn."""
        self.ax.set_xlim(box[0], box[1])
        self.ax.set_ylim(box[2], box[3])
        self.clamp()

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
        """One line on the point (x, y): R, Z, rhop (rho poloidal, with a
        psi map) and the value of each quantity plotted where it is drawn
        under the cursor (the plasma quantity, |v| of the vector quantity,
        the wall quantity on the strip element under the cursor; "--":
        none there, an empty place in the readout); '' without a run."""
        if self.run is None:
            return ""
        parts = ["R = %.4f m" % x, "Z = %.4f m" % y]
        if self.run.psimap is not None:
            rho = self.run.psimap.rhop(x, y)
            parts.append("rhop = " + ("%.4f" % rho if np.isfinite(rho)
                                      else "--"))
        for name, data, value in self.readings(x, y, every=True):
            parts.append(("%s = %s %s" % (name, "--" if value is None else
                                          "%.4g" % value,
                                          labels.any_to_plain(data.unit))
                          ).strip())
        return "   ".join(parts)

    def readings(self, x, y, every=False):
        """[(name, data, value)] at (x, y) of the plasma quantity, of |v|
        of the vector quantity and of the wall quantity (on its strip),
        each where it is plotted and has a value there (every: also where
        it has none, value None)."""
        vector = self.vectors or (None, None)
        out = [("Plasma quantity", self.data,
                self._value(self.data, self.style, x, y, self.mask)),
               ("Vector quantity", vector[0],
                self._value(*vector, x, y, self.vector_mask)),
               ("Wall quantity", self.wall_data, self._wall_value(x, y))]
        return [r for r in out if r[2] is not None or every and
                r[1] is not None]

    def value_at(self, x, y):
        """The value of the plasma quantity shown (else |v| of the vector
        quantity shown) at the cell or triangle under (x, y), or None."""
        values = [v for n, _, v in self.readings(x, y)
                  if n != "Wall quantity"]
        return values[0] if values else None

    def _value(self, d, st, x, y, shown=None):
        """The value of field d (|v| of a vector) in its column of style st
        at the cell or triangle under (x, y) where it is drawn (cells:
        those of shown, the geometry rows drawn), or None (no cell, not
        drawn there, not a number)."""
        if d is None or self.run is None:
            return None
        col = self._column(d, st)
        g = self.run.geometry
        if d.location == "cells":
            it = int(self.finder(x, y))
            row = int(g.tri_cell[it]) if it >= 0 else -1
            if row < 0 or shown is not None and not shown[row]:
                return None
            i = g.cells[row] - 1
        else:
            i = int(self.efinder(x, y)) if self.efinder is not None else -1
            if i < 0:
                return None
        v = float(np.hypot(d.vr[col][i], d.vz[col][i])) if hasattr(
            d, "vr") else float(d.values[col][i])
        return v if np.isfinite(v) else None

    def _wall_value(self, x, y):
        """The wall quantity on the strip element under (x, y): within
        half the width of the strip and 3 pixels, or None."""
        if not self.wall_artists:
            return None
        strip = self.wall_artists[0]
        seg = np.asarray(strip.get_segments(), float)
        if not len(seg):
            return None
        tr = self.ax.transData
        p = tr.transform([(x, y)])[0]
        a, b = tr.transform(seg[:, 0]), tr.transform(seg[:, 1])
        d = b - a
        t = np.clip(np.sum((p - a) * d, axis=1) / np.maximum(
            np.sum(d * d, axis=1), 1e-12), 0.0, 1.0)
        dist = np.hypot(*(a + t[:, None] * d - p).T)
        k = int(np.argmin(dist))
        half = 0.5 * float(np.max(strip.get_linewidth())) * self.fig.dpi / 72
        value = np.ma.masked_invalid(strip.get_array())[k]
        if dist[k] > half + 3.0 or value is np.ma.masked:
            return None
        return float(value)
