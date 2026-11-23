"""Overlays of the 2D plot: the layers of the run (structure, grids,
separatrices, flux surfaces, midplanes, targets), the contour lines of a
second quantity and the wall strip."""

from dataclasses import replace

import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection, PathCollection, \
    PolyCollection
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform

from .. import theme
from . import shapes
from .scalar import node_values
from .styles import FILL_ZORDER, HATCH, ZORDER, PlotStyle, cmap_for, \
    norm_for


def structure(run):
    """Segments of the structure: structure.dat, else mesh.extra."""
    for key in ("structure", "vessel"):
        seg = run.layers.get(key)
        if seg is not None and len(seg):
            return seg
    return np.zeros((0, 4))


def wall_segments(run, data):
    """Segments of a wall field: its own, else the wall elements."""
    seg = getattr(data, "segments", None)
    return seg if seg is not None else run.layers.get("wall",
                                                      np.zeros((0, 4)))


def wall_values(data, columns):
    """The values of a wall field drawn: the sum of its columns chosen
    (default the first)."""
    last = len(data.columns) - 1
    return sum(np.asarray(data.values[min(max(c, 0), last)], float)
               for c in columns or (0,))


def _wall_joints(ax, seg, v, norm, cmap, width):
    """Round dots under a solid wall strip where an element starts at the
    end of the one before it, as wide as the strip, in the colour of the
    mean of their values: the square ends of the elements cover them but
    for the notch at a bend (no element drawn over its neighbours)."""
    seg = np.asarray(seg, float)
    if len(seg) < 2:
        return None
    length = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    gap = np.hypot(seg[1:, 0] - seg[:-1, 2], seg[1:, 1] - seg[:-1, 3])
    joined = gap <= 1e-4 * max(float(length.max()), 1e-12)
    a, b = np.ma.masked_invalid(v[:-1]), np.ma.masked_invalid(v[1:])
    with np.errstate(invalid="ignore"):
        na, nb = np.ma.filled(norm(a), np.nan), np.ma.filled(norm(b), np.nan)
    mean = np.where(np.isfinite(na) & np.isfinite(nb), 0.5 * (na + nb),
                    np.where(np.isfinite(na), na, nb))
    keep = joined & np.isfinite(mean)
    if not keep.any():
        return None
    dot = MarkerStyle("o")
    joints = PathCollection(
        [dot.get_path().transformed(dot.get_transform())],
        sizes=[float(width) ** 2], offsets=seg[:-1, 2:4][keep],
        offset_transform=ax.transData, cmap=cmap, norm=norm,
        linewidths=0.0, zorder=5.19)
    joints.set_transform(IdentityTransform())     # sizes in points
    joints.set_array(np.asarray(norm.inverse(mean[keep]), float))
    return joints


class LayerMixin:
    """Layers and overlay quantities of Plot2D."""

    def _build_layer(self, key):
        run, st = self.run, self.layer_styles[key]
        old = self.layer_artists.pop(key, None)
        for a in old if isinstance(old, list) else (
                [] if old is None else [old]):
            a.remove()
        art = None
        if key == "structure":
            seg = structure(run)
            if len(seg):
                polys = shapes.solid(seg, run.geometry.centres)
                art = [LineCollection(seg.reshape(-1, 2, 2))] + (
                    [PolyCollection(polys)] if polys else [])
        elif key in ("separatrices", "targets", "midplanes"):
            seg = run.layers.get(key) if key != "targets" else np.vstack(
                [np.zeros((0, 4))] + [v for k, v in run.layers.items()
                                      if k.startswith("target: ")])
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
        elif key == "opoints" and run.psimap is not None:
            r, z = run.psimap.opoint        # of rzpsi.dat
            art, = self.ax.plot([r], [z], ls="none", marker="o")
        elif key == "flux" and st.visible and run.psimap is not None:
            art = self._flux_surfaces(st)
        if isinstance(art, (LineCollection, PolyCollection)):
            self.ax.add_collection(art, autolim=False)
        elif key == "structure" and art is not None:    # lines and fill
            for a in art:
                self.ax.add_collection(a, autolim=False)
        if art is not None:
            self.layer_artists[key] = art
            self._restyle(key)

    def _wall_strip(self, data, o, label=None):
        """A wall field (one value per wall element, WallStyle o) along the
        wall elements, with its own colour scale and colour bar (label,
        default the label of data)."""
        seg = wall_segments(self.run, data)
        v = wall_values(data, o.columns)[:len(seg)]
        if o.scale == "log":
            v = np.where(v > 0, v, np.nan)
        if not len(v) or not np.isfinite(v).any():
            return None
        st = replace(PlotStyle(), cmap=o.cmap, reverse=o.reverse,
                     scale=o.scale, auto=o.auto, vmin=o.vmin, vmax=o.vmax)
        norm = norm_for(v, st)
        cmap = cmap_for(st, norm)
        strip = LineCollection(seg[:len(v)].reshape(-1, 2, 2), cmap=cmap,
                               norm=norm, linewidths=o.width,
                               linestyles=o.style, capstyle="butt",
                               zorder=5.2)
        strip.set_array(np.ma.masked_invalid(v))
        self.ax.add_collection(strip, autolim=False)
        out = [strip]
        if o.style == "-":
            joints = _wall_joints(self.ax, seg[:len(v)], v, norm, cmap,
                                  o.width)
            if joints is not None:
                self.ax.add_collection(joints, autolim=False)
                out.append(joints)
        if o.colorbar:
            self.wall_colorbar(strip, data.label if label is None else
                               label)
        return out

    def _flux_surfaces(self, st):
        """The flux surfaces at the levels of st, on the B2.5 grid only."""
        lines = shapes.flux_lines(self.run, st)
        return LineCollection([ln for _, ln in lines]) if lines else None

    def _restyle(self, key):
        art, st = self.layer_artists.get(key), self.layer_styles[key]
        if art is None:
            return
        if key == "structure":
            art[0].set(edgecolor=theme.rgb(st.color), facecolor="none",
                       linewidth=st.width, linestyle=st.style,
                       alpha=st.alpha, visible=st.visible,
                       zorder=ZORDER[key])
            fill = theme.rgb(st.fill or "#e0e0e0")
            hatched = st.fill_style == "pattern"
            for a in art[1:]:
                a.set(facecolor="none" if hatched else fill,
                      edgecolor=fill if hatched else "none", linewidth=0.0,
                      hatch=HATCH if hatched else None, alpha=st.alpha,
                      visible=st.visible and st.fill_style != "empty",
                      zorder=FILL_ZORDER)
                if hasattr(a, "set_hatchcolor"):    # matplotlib 3.10
                    a.set_hatchcolor(fill)
            return
        if key in ("xpoints", "opoints"):
            art.set(color=theme.rgb(st.color), markersize=st.width,
                    markeredgewidth=max(st.width / 5.0, 1.0) if key ==
                    "xpoints" else 0.0, alpha=st.alpha, visible=st.visible)
        else:
            art.set(edgecolor=theme.rgb(st.color), facecolor="none",
                    linewidth=st.width,
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

    def _overlay_lines(self, data, st, label=None):
        """Contour lines of the overlay quantity (PlotStyle st: levels,
        lines, colour scale, its own volume regions) over the plasma plot;
        coloured ones with a horizontal colour bar inside the plot box, at
        its bottom, with the name of the quantity (label, default the
        label of data)."""
        col = self._column(data, st)
        field, self.mappable = self.mappable, None
        if data.location == "cells":
            tri, z = self._finite_tri(np.asarray(data.vertex[col], float),
                                      self._cell_mask(st, None))
            used = np.unique(tri.get_masked_triangles())
            self._contours(tri, z, norm_for(z[used], st), st, data.levels)
        elif self.etri is not None:
            values = np.asarray(data.values[col], float)
            self._contours(self.etri, node_values(self.run.trimesh, values),
                           norm_for(values, st), st, data.levels)
        self.overlay_mappable, self.mappable = self.mappable, field
        if self.overlay_mappable is not None and st.colorbar:
            cs = self.overlay_mappable      # a continuous scale: readable
            self.overlay_colorbar(ScalarMappable(norm=cs.norm, cmap=cs.cmap),
                                  data.label if label is None else label)
