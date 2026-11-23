"""Vector fields: arrows, streamlines (the field resampled on a regular
grid for streamplot) and the flow texture, alone or arrows over either,
following zoom and pan."""

import inspect

import numpy as np
import matplotlib.tri as mtri
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable

from .scalar import node_values
from .. import theme
from ..tools import births, lic
from .styles import cmap_for, norm_for

STREAM_GRID = 400
NUM_ARROWS = "num_arrows" in inspect.signature(Axes.streamplot).parameters
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
        rows = np.flatnonzero(self.vector_mask)     # its own regions
        u = np.asarray(v.vr[col], float)[g.cells[rows] - 1]
        w = np.asarray(v.vz[col], float)[g.cells[rows] - 1]
        return (g.centres[rows], u, w, self._cell_tri(self.vector_mask),
                np.asarray(v.vxr[col], float), np.asarray(v.vxz[col], float))

    def _quiver(self, pos, u, w, st, box, outline=False):
        """Arrows at pos, the longest (or each) st.arrow_length long;
        outline: edged in black (over the flow texture)."""
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
        if outline:
            kw.update(edgecolor="black", linewidth=0.4)
        if st.color_by_magnitude:
            norm = norm_for(m, st)
            q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                               w[keep] * scale, m, cmap=cmap_for(st, norm),
                               norm=norm, **kw)
        else:
            q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                               w[keep] * scale,
                               color=theme.rgb(st.arrow_color), **kw)
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
        q = None
        if st.kind in ("quiver", "quiverstream", "quivertexture"):
            q = self._quiver(pos, u, w, st, box,
                             outline=st.kind == "quivertexture")
            if q is not None and st.color_by_magnitude:
                self.mappable = q
        if st.kind in ("stream", "quiverstream"):
            self._streamlines(tri, nu, nw, st, box)
        if st.kind in ("texture", "quivertexture"):    # the arrow colours
            self._texture(tri, nu, nw, st, box, None if self.mappable is
                          None else self.mappable.norm)

    def _texture(self, tri, nu, nw, st, box, norm=None):
        """The flow texture over the view: the field resampled on a grid
        of st.tex_detail pixels along its longer side, the noise smeared
        along its lines (LIC), coloured by the magnitude (in norm, default
        its own range) or grey."""
        x0, x1, y0, y1 = box
        w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
        n = int(st.tex_detail)
        nx, ny = max(int(n * w / max(w, h)), 2), max(int(n * h / max(w, h)),
                                                       2)
        xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
        X, Y = np.meshgrid(xs, ys)
        finder = None if tri is self.etri else \
            self.run.geometry.trifinder(tri)
        U = np.ma.filled(mtri.LinearTriInterpolator(
            tri, nu, trifinder=finder)(X, Y).astype(float), np.nan)
        V = np.ma.filled(mtri.LinearTriInterpolator(
            tri, nw, trifinder=finder)(X, Y).astype(float), np.nan)
        img = lic.lic(U, V, lic.noise(ny, nx, st.tex_grain),
                      length=st.tex_length)
        ok = np.isfinite(img)
        if not ok.any():
            return
        img = np.clip(0.5 + (np.where(ok, img, 0.5) - 0.5) *
                      st.tex_contrast, 0.0, 1.0)
        mag = np.hypot(U, V)
        if st.tex_magnitude:
            own = norm is None
            norm = norm_for(mag[ok], st) if own else norm
            cmap = cmap_for(st, norm)
            base = np.asarray(cmap(norm(np.where(ok, mag, 0.0))))[..., :3]
            # the streaks as lighter and darker shades of the colour
            rgb = np.clip(base + 0.55 * (img - 0.5)[..., None], 0.0, 1.0)
            if own:
                sm = ScalarMappable(norm=norm, cmap=cmap)
                sm.set_array(mag[ok])
                self.mappable = sm
        else:
            g = 0.15 + 0.8 * img
            rgb = np.repeat(g[..., None], 3, -1)
        rgba = np.dstack((rgb, np.where(ok, st.tex_alpha, 0.0)))
        view = (self.ax.get_xlim(), self.ax.get_ylim())
        im = self.ax.imshow(rgba, extent=(x0, x1, y0, y1), origin="lower",
                            interpolation="bilinear", zorder=4.0,
                            aspect=self.ax.get_aspect())
        self.ax.set_xlim(*view[0])
        self.ax.set_ylim(*view[1])
        self.field_artists.append(im)

    def _seeds(self, st, xs, ys, speed):
        """Where the streamlines start (st.seed_kind, tools.births): from
        every cell of the density grid of streamplot (st.density, as its
        own seeds), the strongest flow first (in proportion to the
        quantity), a line stopping where it would crowd; or st.seed_count
        of them along a line (in proportion to the quantity, or at random
        along the line drawn), whole. The same for the same view."""
        rng = np.random.default_rng(0)
        if st.seed_kind not in births.LINES:
            n = int(30 * st.density)
            return births.on_cells(xs, ys, speed, n, n, births.weight(
                st.seed_kind), rng)
        n = int(st.seed_count)
        power = births.weight(st.seed_kind)
        pts = births.into_field(xs, ys, speed, births.on_lines(
            births.lines(self.run, st.seed_kind, st.seeds),
            8 * n if power > 0 else n, rng))
        if power > 0 and len(pts):      # in proportion along the line
            m = np.ma.filled(speed, 0.0)
            good = m[m > 0]
            ref = np.percentile(good, 98.0) if good.size else 1.0
            i = np.clip(np.rint((pts[:, 0] - xs[0]) / (xs[1] - xs[0])
                                ).astype(int), 0, len(xs) - 1)
            j = np.clip(np.rint((pts[:, 1] - ys[0]) / (ys[1] - ys[0])
                                ).astype(int), 0, len(ys) - 1)
            keep = rng.random(len(pts)) < (np.minimum(m[j, i], ref) /
                                           ref) ** power
            pts = pts[keep]
        return pts[:n]

    def _streamlines(self, tri, nu, nw, st, box, zorder=4.0):
        x0, x1, y0, y1 = box
        ny = STREAM_GRID
        nx = max(int(STREAM_GRID * (x1 - x0) / max(y1 - y0, 1e-9)), 2)
        xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
        X, Y = np.meshgrid(xs, ys)
        finder = None if tri is self.etri else \
            self.run.geometry.trifinder(tri)
        U = mtri.LinearTriInterpolator(tri, nu, trifinder=finder)(X, Y)
        V = mtri.LinearTriInterpolator(tri, nw, trifinder=finder)(X, Y)
        speed = np.ma.hypot(U, V)
        if speed.count() == 0:
            return
        kw = dict(density=st.density, linewidth=st.stream_width,
                  arrowsize=0.8, zorder=zorder)
        if st.num_arrows != 1 and NUM_ARROWS:
            kw["num_arrows"] = st.num_arrows
        seeds = self._seeds(st, xs, ys, speed)
        if not len(seeds):
            return
        kw["start_points"] = seeds
        kw["integration_direction"] = "both"
        kw["broken_streamlines"] = st.seed_kind not in births.LINES
        if st.seed_markers:
            self.field_artists += self.ax.plot(
                seeds[:, 0], seeds[:, 1], "o", mfc="none",
                mec=theme.rgb("red"), ms=4.0, zorder=zorder + 0.1)
        before = set(self.ax.patches)
        if st.color_by_magnitude and st.kind == "stream":
            norm = norm_for(speed.compressed(), st)
            sp = self.ax.streamplot(xs, ys, U, V, color=speed.filled(0.0),
                                    cmap=cmap_for(st, norm), norm=norm, **kw)
            self.mappable = sp.lines
        else:
            sp = self.ax.streamplot(xs, ys, U, V,
                                    color=theme.rgb(st.stream_color),
                                    **kw)
        sp.lines.set_linestyle(st.stream_style)
        self.field_artists.append(sp.lines)
        self.field_artists += [p for p in self.ax.patches if p not in before]
