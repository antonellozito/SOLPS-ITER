"""Scalar fields on the B2.5 cells or the EIRENE triangles: patches and
contours, restricted to the cells shown."""

import numpy as np
import matplotlib.tri as mtri
from matplotlib.collections import PolyCollection

from .styles import cmap_for, levels_for, norm_for


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

    def _cell_mask(self, st):
        """Geometry rows shown: cells with an area, inside the index
        intervals (classical grids) and in the chosen regions."""
        g = self.run.geometry
        m = g.visible.copy()
        if g.classical and st.ix_range is not None:
            m &= (g.ix >= st.ix_range[0]) & (g.ix <= st.ix_range[1])
        if g.classical and st.iy_range is not None:
            m &= (g.iy >= st.iy_range[0]) & (g.iy <= st.iy_range[1])
        if st.regions is not None:
            m &= np.isin(g.region, st.regions)
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
        norm, cmap = norm_for(cell_values, st), cmap_for(st)
        if st.kind == "patch":
            key = (st.ix_range, st.iy_range, st.regions)
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
            pc.set_edgecolor("k" if st.edges else "face")
            pc.set_linewidth(0.15 if st.edges else 0.3)
            self.mappable = pc
            return
        z = np.asarray(f.vertex[col], float)
        tri = self._cell_tri()
        used = np.unique(tri.get_masked_triangles())
        self._contours(tri, z, norm_for(z[used], st), cmap, st, f.levels)

    def _tri_field(self, f, st):
        t = self.run.trimesh
        if t is None:
            return
        col = self._column(f, st)
        values = np.asarray(f.values[col], float)
        norm, cmap = norm_for(values, st), cmap_for(st)
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
            pc.set_edgecolor("k" if st.edges else "face")
            pc.set_linewidth(0.1 if st.edges else 0.3)
            self.mappable = pc
            return
        self._contours(self.etri, node_values(t, values), norm, cmap, st,
                       f.levels)

    def _contours(self, tri, z, norm, cmap, st, given=None):
        lev = levels_for(st, norm, given)
        if st.scale == "log":
            z = np.where(z > 0, z, norm.vmin)
        if st.kind == "contourf":
            cs = self.ax.tricontourf(tri, z, levels=lev, cmap=cmap,
                                     norm=norm, extend="both", zorder=1.0)
            if st.fill_lines:
                lines = self.ax.tricontour(tri, z, levels=lev, zorder=2.0,
                                           colors=st.line_color,
                                           linewidths=st.line_width,
                                           linestyles=st.line_style)
                if st.line_labels:
                    self.ax.clabel(lines, fontsize="x-small",
                                   fmt=lambda v: f"{v:.3g}")
                self.field_artists.append(lines)
        else:
            kw = dict(colors=st.line_color) if st.line_mono else dict(
                cmap=cmap, norm=norm)
            cs = self.ax.tricontour(tri, z, levels=lev, zorder=2.0,
                                    linewidths=st.line_width,
                                    linestyles=st.line_style, **kw)
            if st.line_labels:
                self.ax.clabel(cs, fontsize="x-small",
                               fmt=lambda v: f"{v:.3g}")
        self.field_artists.append(cs)
        self.mappable = cs if not (st.kind == "contour" and st.line_mono) \
            else None
