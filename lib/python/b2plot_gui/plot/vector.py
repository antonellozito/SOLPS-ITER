"""Vector fields: arrows and streamlines (the field resampled on a
regular grid for streamplot), following zoom and pan."""

import numpy as np
import matplotlib.tri as mtri

from .scalar import node_values
from .styles import cmap_for, norm_for

STREAM_GRID = 400
AUTO_ARROWS = 2000              # arrows shown when the spacing is automatic
ARROW_PERCENTILE = 98.0         # magnitude drawn with the arrow length
ARROW_CAP = 1.5                 # longest arrow, in arrow lengths


def _spread(pos, index, box):
    """About AUTO_ARROWS of index, one per bin of a regular grid over box,
    the element nearest to the bin centre (even density on any mesh)."""
    x0, x1, y0, y1 = box
    w, h = max(x1 - x0, 1e-12), max(y1 - y0, 1e-12)
    d = np.sqrt(w * h / AUTO_ARROWS)
    ix = np.floor((pos[:, 0] - x0) / d).astype(int)
    iy = np.floor((pos[:, 1] - y0) / d).astype(int)
    cx, cy = x0 + (ix + 0.5) * d, y0 + (iy + 0.5) * d
    dist = np.hypot(pos[:, 0] - cx, pos[:, 1] - cy)
    order = np.lexsort((dist, iy, ix))
    key = ix[order] * 1000003 + iy[order]
    first = np.concatenate(([True], key[1:] != key[:-1]))
    return np.sort(index[order[first]])


class VectorMixin:
    """Arrows and streamlines of Plot2D."""

    def _vector_data(self, v, col):
        """Positions and components, and the mesh and node values used
        for streamlines (B2.5 cells or EIRENE triangles)."""
        if v.location == "triangles":
            t = self.run.trimesh
            u = np.asarray(v.vr[col], float)
            w = np.asarray(v.vz[col], float)
            return (self.ecentres, u, w, self.etri, node_values(t, u),
                    node_values(t, w))
        g = self.run.geometry
        rows = np.flatnonzero(self.mask)
        u = np.asarray(v.vr[col], float)[g.cells[rows] - 1]
        w = np.asarray(v.vz[col], float)[g.cells[rows] - 1]
        return (g.centres[rows], u, w, self._cell_tri(),
                np.asarray(v.vxr[col], float), np.asarray(v.vxz[col], float))

    def _quiver(self, pos, u, w, st, cmap, box):
        """Arrows at pos, the longest (or each) st.arrow_length long."""
        mag = np.hypot(u, w)
        x0, x1, y0, y1 = box
        keep = np.flatnonzero((mag > 0) & (pos[:, 0] >= x0) & (pos[:, 0] <= x1)
                              & (pos[:, 1] >= y0) & (pos[:, 1] <= y1))
        if int(st.every) > 0:
            keep = keep[::int(st.every)]
        else:
            keep = _spread(pos[keep], keep, box)
        if not keep.size:
            return None
        x0, x1 = box[0], box[1]
        length = st.arrow_length or 0.025 * (x1 - x0)
        m = mag[keep]
        if st.normalize:
            scale = length / m
        else:
            # reference: 98th percentile, longer arrows capped at 1.5 times
            ref = max(float(np.percentile(m, ARROW_PERCENTILE)), 1e-300)
            scale = length / ref * np.minimum(m, ARROW_CAP * ref) / m
        c = pos[keep]
        kw = dict(angles="xy", scale_units="xy", scale=1.0,
                  width=0.0022 * st.arrow_width, zorder=5.0)
        if st.color_by_magnitude:
            q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                               w[keep] * scale, m, cmap=cmap,
                               norm=norm_for(m, st), **kw)
        else:
            q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                               w[keep] * scale, color=st.arrow_color, **kw)
        self.field_artists.append(q)
        return q

    def vector_box(self):
        """Current view, limited to the extent of the data (arrows and
        streamlines follow zoom and pan)."""
        f = self.full_extent()
        x0, x1, y0, y1 = self.get_view()
        box = (max(x0, f[0]), min(x1, f[1]), max(y0, f[2]), min(y1, f[3]))
        return box if box[1] > box[0] and box[3] > box[2] else f

    def _vectors(self, v, st):
        col = self._column(v, st)
        pos, u, w, tri, nu, nw = self._vector_data(v, col)
        box = self.vector_box()
        cmap = cmap_for(st)
        if st.kind in ("quiver", "quiverstream"):
            q = self._quiver(pos, u, w, st, cmap, box)
            if q is not None and st.color_by_magnitude:
                self.mappable = q
        if st.kind in ("stream", "quiverstream"):
            self._streamlines(tri, nu, nw, st, cmap, box)

    def _streamlines(self, tri, nu, nw, st, cmap, box):
        x0, x1, y0, y1 = box
        ny = STREAM_GRID
        nx = max(int(STREAM_GRID * (x1 - x0) / max(y1 - y0, 1e-9)), 2)
        xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
        X, Y = np.meshgrid(xs, ys)
        U = mtri.LinearTriInterpolator(tri, nu)(X, Y)
        V = mtri.LinearTriInterpolator(tri, nw)(X, Y)
        speed = np.ma.hypot(U, V)
        if speed.count() == 0:
            return
        kw = dict(density=st.density, linewidth=st.stream_width,
                  arrowsize=0.8, zorder=4.0)
        seeds = np.asarray(st.seeds, float).reshape(-1, 2)
        if len(seeds):
            inside = ((seeds[:, 0] > x0) & (seeds[:, 0] < x1)
                      & (seeds[:, 1] > y0) & (seeds[:, 1] < y1))
            if inside.any():
                kw["start_points"] = seeds[inside]
                kw["integration_direction"] = "both"
                kw["broken_streamlines"] = False
        before = set(self.ax.patches)
        if st.color_by_magnitude and st.kind == "stream":
            norm = norm_for(speed.compressed(), st)
            sp = self.ax.streamplot(xs, ys, U, V, color=speed.filled(0.0),
                                    cmap=cmap, norm=norm, **kw)
            self.mappable = sp.lines
        else:
            sp = self.ax.streamplot(xs, ys, U, V, color=st.stream_color,
                                    **kw)
        sp.lines.set_linestyle(st.stream_style)
        self.field_artists.append(sp.lines)
        self.field_artists += [p for p in self.ax.patches if p not in before]
