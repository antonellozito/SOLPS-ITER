"""Scalar fields on the B2.5 cells or the EIRENE triangles: patches and
contours, restricted to the cells shown."""

import numpy as np
import matplotlib.tri as mtri
from matplotlib.collections import PolyCollection

from ...b2plot.render import HATCHES
from .. import theme
from .styles import cmap_for, levels_for, norm_for

CELL_TEXTS = 400                # most cells with their values written


def node_values(trimesh, values):
    """Triangle values averaged to the nodes with the triangle areas."""
    t = trimesh.triangles
    x, y = trimesh.x[t], trimesh.y[t]
    area = 0.5 * np.abs((x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0])
                        - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0]))
    num = np.zeros(len(trimesh.x))
    den = np.zeros(len(trimesh.x))
    for k in range(3):
        np.add.at(num, t[:, k], area * values)
        np.add.at(den, t[:, k], area)
    return np.divide(num, den, out=np.zeros_like(num), where=den > 0)


class ScalarMixin:
    """Patches and contours of Plot2D."""

    def _cell_mask(self, st, cond=None):
        """Geometry rows shown: cells with an area, inside the index
        intervals (classical grids), in the chosen regions and where the
        cell field cond (a mask) is positive."""
        g = self.run.geometry
        m = g.visible.copy()
        if g.classical and st.ix_range is not None:
            m &= (g.ix >= st.ix_range[0]) & (g.ix <= st.ix_range[1])
        if g.classical and st.iy_range is not None:
            m &= (g.iy >= st.iy_range[0]) & (g.iy <= st.iy_range[1])
        if st.regions is not None:
            m &= np.isin(g.region, st.regions)
        if cond is not None and cond.location == "cells":
            m &= np.asarray(cond.values[0], float)[g.cells - 1] > 0
        return m

    def _cell_tri(self):
        """Triangulation of the vertices restricted to the shown cells."""
        g = self.run.geometry
        hidden = ~self.mask[g.tri_cell]
        if not hidden.any():
            return self.tri
        return mtri.Triangulation(self.tri.x, self.tri.y, self.tri.triangles,
                                  mask=hidden)

    def _column(self, data, style):
        return min(max(style.column, 0), len(data.columns) - 1)

    def _cell_field(self, f, st):
        g = self.run.geometry
        col = self._column(f, st)
        rows = np.flatnonzero(self.mask)
        cell_values = f.values[col][g.cells[rows] - 1]
        norm = norm_for(cell_values, st)
        cmap = cmap_for(st, norm)
        if st.kind == "patch":
            key = (st.ix_range, st.iy_range, st.regions, self._mask_name)
            if self._cell_pc is None or self._cell_key != key:
                if self._cell_pc is not None:
                    self._cell_pc.remove()
                self._cell_pc = PolyCollection([g.polygons[i] for i in rows],
                                               zorder=1.0)
                self._cell_key = key
                self.ax.add_collection(self._cell_pc, autolim=False)
            pc = self._cell_pc
            vals = np.ma.masked_invalid(cell_values)
            if st.scale == "log":
                vals = np.ma.masked_less_equal(vals, 0.0)
            pc.set(array=vals, cmap=cmap, norm=norm, visible=True)
            pc.set_edgecolor(theme.rgb("k") if st.edges else "face")
            pc.set_linewidth(0.15 if st.edges else 0.3)
            self.mappable = pc
        else:
            z = np.asarray(f.vertex[col], float)
            tri = self._cell_tri()
            used = np.unique(tri.get_masked_triangles())
            self._contours(tri, z, norm_for(z[used], st), st, f.levels)
        if st.cell_values:
            self._cell_texts(g.centres[rows], cell_values)

    def _tri_field(self, f, st):
        t = self.run.trimesh
        if t is None:
            return
        col = self._column(f, st)
        values = np.asarray(f.values[col], float)
        norm = norm_for(values, st)
        cmap = cmap_for(st, norm)
        if st.kind == "patch":
            if self._tri_pc is None:
                xy = np.column_stack((t.x, t.y))
                self._tri_pc = PolyCollection(xy[t.triangles], zorder=1.0)
                self.ax.add_collection(self._tri_pc, autolim=False)
            pc = self._tri_pc
            vals = np.ma.masked_invalid(values)
            if st.scale == "log":
                vals = np.ma.masked_less_equal(vals, 0.0)
            pc.set(array=vals, cmap=cmap, norm=norm, visible=True)
            pc.set_edgecolor(theme.rgb("k") if st.edges else "face")
            pc.set_linewidth(0.1 if st.edges else 0.3)
            self.mappable = pc
        else:
            self._contours(self.etri, node_values(t, values), norm, st,
                           f.levels)
        if st.cell_values:
            self._cell_texts(self.ecentres, values)

    def _cell_texts(self, centres, values):
        """Values written at the cell centres when at most CELL_TEXTS cells
        are in the view, with a font size from the cell spacing."""
        x0, x1, y0, y1 = self.get_view()
        inside = np.flatnonzero((centres[:, 0] > x0) & (centres[:, 0] < x1)
                                & (centres[:, 1] > y0) & (centres[:, 1] < y1)
                                & np.isfinite(values))
        if not 0 < inside.size <= CELL_TEXTS:
            return
        bb = self.ax.get_window_extent()
        spacing = np.sqrt(bb.width * bb.height / max(
            inside.size, 1)) * 72.0 / self.fig.dpi
        size = float(np.clip(0.22 * spacing, 4.0, 9.0))
        for i in inside:
            self.field_artists.append(self.ax.text(
                centres[i, 0], centres[i, 1], "%.3g" % values[i],
                fontsize=size, ha="center", va="center", zorder=5.8,
                clip_on=True, color=theme.rgb("black")))

    def _contours(self, tri, z, norm, st, given=None):
        lev = levels_for(st, norm, given)
        cmap = cmap_for(st, norm)
        if st.scale == "log":
            z = np.where(z > 0, z, norm.vmin)
        if st.kind == "contourf" and st.bw:
            cs = self.ax.tricontourf(tri, z, levels=lev, colors="white",
                                     hatches=HATCHES, extend="both",
                                     zorder=1.0)
        elif st.kind == "contourf":
            cs = self.ax.tricontourf(tri, z, levels=lev, cmap=cmap,
                                     norm=norm, extend="both", zorder=1.0)
            if st.fill_lines:
                lines = self.ax.tricontour(tri, z, levels=lev, zorder=2.0,
                                           colors=[theme.rgb(st.line_color)],
                                           linewidths=st.line_width,
                                           linestyles=st.line_style)
                if st.line_labels:
                    self.ax.clabel(lines, fontsize="x-small",
                                   fmt=lambda v: f"{v:.3g}")
                self.field_artists.append(lines)
        else:
            one = theme.rgb("black" if st.bw else st.line_color)
            kw = dict(colors=[one]) if (st.line_mono or st.bw) else dict(
                cmap=cmap, norm=norm)
            cs = self.ax.tricontour(tri, z, levels=lev, zorder=2.0,
                                    linewidths=st.line_width,
                                    linestyles=st.line_style, **kw)
            if st.line_labels:
                self.ax.clabel(cs, fontsize="x-small",
                               fmt=lambda v: f"{v:.3g}")
        self.field_artists.append(cs)
        self.mappable = cs if not (st.kind == "contour" and (
            st.line_mono or st.bw)) else None
