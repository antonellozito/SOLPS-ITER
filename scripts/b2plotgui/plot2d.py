"""Matplotlib side of the 2D tab: field, vectors and overlays on one axes.

Overlay artists are built once per run and only restyled; the field and
vector artists are rebuilt when the quantity or the plot type changes,
and only recoloured when the colour options change. All values come from
b2plot (data.py); the choices here (colours, levels, resampling for
streamlines) are presentation only.
"""

from dataclasses import dataclass, field, replace

import numpy as np
import matplotlib.tri as mtri
from matplotlib import colormaps
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import LogNorm, Normalize, SymLogNorm

from . import labels

KINDS_SCALAR = ("patch", "contourf", "contour")
KINDS_VECTOR = ("quiver", "stream", "quiverstream")
STREAM_GRID = 400


@dataclass
class LayerStyle:
    visible: bool = False
    color: str = "#000000"
    width: float = 0.5
    style: str = "-"
    alpha: float = 1.0
    levels: str = ""            # flux surfaces: psiN or rho levels
    rho: bool = False


LAYERS = {
    "structure": ("Device structure",
                  LayerStyle(True, "#000000", 1.0)),
    "separatrices": ("Separatrices", LayerStyle(True, "#d62728", 1.2)),
    "xpoints": ("X-points", LayerStyle(False, "#d62728", 8.0)),
    "boundary": ("Grid boundary", LayerStyle(False, "#1f3b8c", 0.8)),
    "grid": ("B2.5 grid", LayerStyle(False, "#4d4d4d", 0.15)),
    "eirene": ("EIRENE grid", LayerStyle(False, "#8c8c8c", 0.1)),
    "flux": ("Flux surfaces",
             LayerStyle(False, "#2ca02c", 0.6, ":", 1.0,
                        "0.90 0.95 1.00 1.02 1.04 1.06")),
}
ZORDER = {"grid": 3.0, "eirene": 3.1, "flux": 3.2, "boundary": 3.3,
          "structure": 3.4, "separatrices": 3.5, "xpoints": 3.6}


@dataclass
class PlotStyle:
    kind: str = "patch"
    column: int = 0
    cmap: str = "turbo"
    reverse: bool = False
    scale: str = "linear"       # linear, log, symlog
    auto: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    levels: int = 20
    colorbar: bool = True
    edges: bool = False
    line_mono: bool = False     # contour lines in one colour
    line_color: str = "#000000"
    line_width: float = 0.8
    line_style: str = "-"
    line_labels: bool = False
    normalize: bool = False
    arrow_length: float = 0.0   # metres, 0 = automatic
    arrow_width: float = 1.0
    every: int = 1
    color_by_magnitude: bool = True
    arrow_color: str = "#000000"
    density: float = 1.5
    stream_width: float = 0.8
    stream_color: str = "#1f77b4"
    stream_style: str = "-"
    seeds: list = field(default_factory=list)


def _norm(values, style):
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if style.scale == "log":
        v = v[v > 0]
    if v.size == 0:
        lo, hi = (1.0, 10.0) if style.scale == "log" else (0.0, 1.0)
    else:
        lo, hi = float(v.min()), float(v.max())
    if not style.auto:
        lo, hi = style.vmin, style.vmax
    if style.scale == "log":
        lo = lo if lo > 0 else (hi * 1e-6 if hi > 0 else 1.0)
        hi = hi if hi > lo else lo * 10.0
        return LogNorm(vmin=lo, vmax=hi)
    if hi <= lo:
        hi = lo + (abs(lo) if lo else 1.0)
    if style.scale == "symlog":
        top = max(abs(lo), abs(hi))
        return SymLogNorm(linthresh=top * 1e-3, vmin=lo, vmax=hi)
    return Normalize(vmin=lo, vmax=hi)


def _levels(norm, n):
    t = np.linspace(0.0, 1.0, max(int(n), 1) + 1)
    return np.unique(np.asarray(norm.inverse(t), float))


def _cmap(style):
    cmap = colormaps[style.cmap]
    return cmap.reversed() if style.reverse else cmap


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


class Plot2D:
    """One fixed axes with a fixed colour-bar slot."""

    def __init__(self, fig):
        self.fig = fig
        self.ax = fig.add_axes([0.09, 0.08, 0.72, 0.86])
        self.cax = fig.add_axes([0.85, 0.12, 0.025, 0.78])
        self.cax.set_visible(False)
        self.run = None
        self.layer_styles = {k: replace(s) for k, (_, s) in LAYERS.items()}
        self.layer_artists = {}
        self.field_artists = []
        self.data = None
        self.style = PlotStyle()
        self.mappable = None
        self.cbar = None
        self._cell_pc = None
        self._tri_pc = None
        self._reset_axes()

    def _reset_axes(self):
        self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.set_xlabel("R (m)")
        self.ax.set_ylabel("Z (m)")

    # --------------------------------------------------------------- run
    def set_run(self, run):
        self._drop_colorbar()
        self.field_artists, self.layer_artists = [], {}
        self.ax.cla()
        self._reset_axes()
        self.cax.set_visible(False)
        self.run, self.data, self.mappable = run, None, None
        self._cell_pc = self._tri_pc = None
        g = run.geometry
        self.tri = mtri.Triangulation(g.vx[:, 0], g.vx[:, 1], g.triangles)
        self.finder = self.tri.get_trifinder()
        self.etri = self.efinder = None
        if run.trimesh is not None:
            t = run.trimesh
            self.etri = mtri.Triangulation(t.x, t.y, t.triangles)
            self.efinder = self.etri.get_trifinder()
        for key in LAYERS:
            self._build_layer(key)
        self.set_view(self.views()["Full"])

    # ------------------------------------------------------------ layers
    def _build_layer(self, key):
        run, st = self.run, self.layer_styles[key]
        old = self.layer_artists.pop(key, None)
        if old is not None:
            old.remove()
        art = None
        if key in ("structure", "separatrices", "boundary"):
            seg = run.layers.get(key)
            if seg is not None and len(seg):
                art = LineCollection(seg.reshape(-1, 2, 2))
        elif key == "grid":
            art = LineCollection([np.vstack((p, p[:1]))
                                  for p in run.geometry.polygons])
        elif key == "eirene" and run.trimesh is not None:
            t = run.trimesh.triangles
            e = np.sort(np.vstack((t[:, [0, 1]], t[:, [1, 2]],
                                   t[:, [2, 0]])), axis=1)
            e = np.unique(e, axis=0)
            xy = np.column_stack((run.trimesh.x, run.trimesh.y))
            art = LineCollection(np.stack((xy[e[:, 0]], xy[e[:, 1]]), 1))
        elif key == "xpoints" and len(run.geometry.xpoints):
            xp = run.geometry.xpoints
            art, = self.ax.plot(xp[:, 0], xp[:, 1], ls="none", marker="x")
        elif key == "flux" and st.visible and run.geometry.psin is not None:
            art = self._flux_surfaces(st)
        if isinstance(art, LineCollection):
            self.ax.add_collection(art, autolim=False)
        if art is not None:
            self.layer_artists[key] = art
            self._restyle(key)

    def _flux_surfaces(self, st):
        try:
            lev = sorted(float(v) for v in st.levels.replace(",", " ").split())
        except ValueError:
            lev = []
        if not lev:
            return None
        psin = self.run.geometry.psin
        z = np.sqrt(np.clip(psin, 0.0, None)) if st.rho else psin
        cs = self.ax.tricontour(self.tri, z, levels=lev)
        return cs

    def _restyle(self, key):
        art, st = self.layer_artists.get(key), self.layer_styles[key]
        if art is None:
            return
        if key == "xpoints":
            art.set(color=st.color, markersize=st.width,
                    markeredgewidth=max(st.width / 5.0, 1.0),
                    alpha=st.alpha, visible=st.visible)
        else:
            art.set(edgecolor=st.color, facecolor="none", linewidth=st.width,
                    linestyle=st.style, alpha=st.alpha, visible=st.visible)
        art.set_zorder(ZORDER[key])

    def set_layer(self, key, style):
        old = self.layer_styles[key]
        self.layer_styles[key] = replace(style)
        if self.run is None:
            return
        rebuild = key == "flux" and (
            style.visible != old.visible or style.levels != old.levels
            or style.rho != old.rho or key not in self.layer_artists)
        if rebuild:
            self._build_layer(key)
        else:
            self._restyle(key)

    # ------------------------------------------------------------- field
    def clear_field(self):
        self._drop_colorbar()
        for a in self.field_artists:
            a.remove()
        self.field_artists = []
        self.mappable = None
        if self._cell_pc is not None:
            self._cell_pc.set_visible(False)
        if self._tri_pc is not None:
            self._tri_pc.set_visible(False)
        self.cax.set_visible(False)

    def show(self, data, style):
        """Draw a Field or Vector with a PlotStyle."""
        self.clear_field()
        self.data, self.style = data, replace(style)
        if data is None:
            return
        if hasattr(data, "vr"):
            self._vectors(data, style)
        elif data.location == "cells":
            self._cell_field(data, style)
        else:
            self._tri_field(data, style)
        self._colorbar(data, style)

    def _column(self, data, style):
        return min(max(style.column, 0), len(data.columns) - 1)

    def _cell_field(self, f, st):
        g = self.run.geometry
        col = self._column(f, st)
        cell_values = f.values[col][g.cells - 1]
        norm, cmap = _norm(cell_values, st), _cmap(st)
        if st.kind == "patch":
            if self._cell_pc is None:
                self._cell_pc = PolyCollection(g.polygons, zorder=1.0)
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
        self._contours(self.tri, z, norm, cmap, st)

    def _tri_field(self, f, st):
        t = self.run.trimesh
        if t is None:
            return
        col = self._column(f, st)
        values = np.asarray(f.values[col], float)
        norm, cmap = _norm(values, st), _cmap(st)
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
        self._contours(self.etri, node_values(t, values), norm, cmap, st)

    def _contours(self, tri, z, norm, cmap, st):
        lev = _levels(norm, st.levels)
        if st.scale == "log":
            z = np.where(z > 0, z, norm.vmin)
        if st.kind == "contourf":
            cs = self.ax.tricontourf(tri, z, levels=lev, cmap=cmap,
                                     norm=norm, extend="both", zorder=1.0)
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

    def _vectors(self, v, st):
        g = self.run.geometry
        col = self._column(v, st)
        u = np.asarray(v.vr[col], float)[g.cells - 1]
        w = np.asarray(v.vz[col], float)[g.cells - 1]
        mag = np.hypot(u, w)
        x0, x1, y0, y1 = self.full_extent()
        cmap = _cmap(st)
        if st.kind in ("quiver", "quiverstream"):
            keep = np.flatnonzero(mag > 0)[::max(int(st.every), 1)]
            if keep.size:
                length = st.arrow_length or 0.025 * (x1 - x0)
                m = mag[keep]
                scale = length / m if st.normalize else length / m.max()
                c = g.centres[keep]
                kw = dict(angles="xy", scale_units="xy", scale=1.0,
                          width=0.0022 * st.arrow_width, zorder=5.0)
                if st.color_by_magnitude:
                    norm = _norm(m, st)
                    q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                                       w[keep] * scale, m, cmap=cmap,
                                       norm=norm, **kw)
                    self.mappable = q
                else:
                    q = self.ax.quiver(c[:, 0], c[:, 1], u[keep] * scale,
                                       w[keep] * scale, color=st.arrow_color,
                                       **kw)
                self.field_artists.append(q)
        if st.kind in ("stream", "quiverstream"):
            self._streamlines(v, col, st, cmap, (x0, x1, y0, y1))

    def _streamlines(self, v, col, st, cmap, box):
        x0, x1, y0, y1 = box
        ny = STREAM_GRID
        nx = max(int(STREAM_GRID * (x1 - x0) / max(y1 - y0, 1e-9)), 2)
        xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
        X, Y = np.meshgrid(xs, ys)
        U = mtri.LinearTriInterpolator(self.tri, v.vxr[col])(X, Y)
        V = mtri.LinearTriInterpolator(self.tri, v.vxz[col])(X, Y)
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
            norm = _norm(speed.compressed(), st)
            sp = self.ax.streamplot(xs, ys, U, V, color=speed.filled(0.0),
                                    cmap=cmap, norm=norm, **kw)
            self.mappable = sp.lines
        else:
            sp = self.ax.streamplot(xs, ys, U, V, color=st.stream_color,
                                    **kw)
        sp.lines.set_linestyle(st.stream_style)
        self.field_artists.append(sp.lines)
        self.field_artists += [p for p in self.ax.patches if p not in before]

    def _drop_colorbar(self):
        """Detach the colour bar from its (possibly reused) mappable."""
        cb, self.cbar = self.cbar, None
        if cb is not None:
            cid = getattr(cb.mappable, "colorbar_cid", None)
            if cid is not None:
                cb.mappable.callbacks.disconnect(cid)
            cb.mappable.colorbar = None
        self.cax.cla()

    def _colorbar(self, data, st):
        self._drop_colorbar()
        if self.mappable is None or not st.colorbar:
            self.cax.set_visible(False)
            return
        self.cax.set_visible(True)
        self.cbar = self.fig.colorbar(self.mappable, cax=self.cax)
        self.cbar.set_label(labels.tex_to_mathtext(data.unit))

    def title(self, text):
        self.ax.set_title(labels.tex_to_mathtext(text), fontsize="medium")

    # -------------------------------------------------------------- views
    def full_extent(self):
        g = self.run.geometry
        pts = [g.vx[np.unique(g.triangles)]]
        seg = self.run.layers.get("structure")
        if seg is not None and len(seg):
            pts.append(seg.reshape(-1, 2))
        p = np.vstack(pts)
        return (float(p[:, 0].min()), float(p[:, 0].max()),
                float(p[:, 1].min()), float(p[:, 1].max()))

    def views(self):
        """View presets from the grid, X-points and separatrices."""
        x0, x1, y0, y1 = self.full_extent()
        w, h = x1 - x0, y1 - y0
        pad = 0.02 * max(w, h)
        out = {"Full": (x0 - pad, x1 + pad, y0 - pad, y1 + pad)}
        zmid = 0.5 * (y0 + y1)
        sep = self.run.layers.get("separatrices")
        if sep is not None and len(sep):
            p = sep.reshape(-1, 2)
            omp = p[np.argmax(p[:, 0])]
            zmid = float(omp[1])
            out["Outer midplane"] = (omp[0] - 0.12 * w, x1 + pad,
                                     omp[1] - 0.12 * h, omp[1] + 0.12 * h)
        for xr, xz in self.run.geometry.xpoints:
            if xz < zmid and "Lower divertor" not in out:
                out["Lower divertor"] = (xr - 0.3 * w, xr + 0.3 * w,
                                         y0 - pad, xz + 0.2 * h)
            elif xz >= zmid and "Upper divertor" not in out:
                out["Upper divertor"] = (xr - 0.3 * w, xr + 0.3 * w,
                                         xz - 0.2 * h, y1 + pad)
        return out

    def set_view(self, box):
        """Show at least this box, widened to the equal aspect of the axes."""
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
        self.ax.set_xlim(x0, x1)
        self.ax.set_ylim(y0, y1)

    def get_view(self):
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        return (x0, x1, y0, y1)

    # -------------------------------------------------------------- hover
    def lookup(self, x, y):
        """Text describing the cell or triangle at (x, y), or ''."""
        if self.run is None:
            return ""
        out = "R %.4f m  Z %.4f m" % (x, y)
        g, d = self.run.geometry, self.data
        it = int(self.finder(x, y))
        if it >= 0:
            row = g.tri_cell[it]
            out += "  cell %d" % g.cells[row]
            if g.classical and g.ix[row] >= 0:
                out += " (ix %d, iy %d)" % (g.ix[row], g.iy[row])
        if d is None:
            return out
        col = self._column(d, self.style)
        unit = d.unit
        if hasattr(d, "vr"):
            if it >= 0:
                i = g.cells[g.tri_cell[it]] - 1
                out += "  |v| %.4g %s" % (np.hypot(d.vr[col][i],
                                                   d.vz[col][i]), unit)
        elif d.location == "cells" and it >= 0:
            out += "  %s %.4g %s" % (d.name, d.values[col][g.cells[
                g.tri_cell[it]] - 1], unit)
        elif d.location == "triangles" and self.efinder is not None:
            jt = int(self.efinder(x, y))
            if jt >= 0:
                out += "  triangle %d  %s %.4g %s" % (
                    jt + 1, d.name, d.values[col][jt], unit)
        return out
