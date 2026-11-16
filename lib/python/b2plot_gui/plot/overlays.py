"""Overlays of the 2D plot: the layers of the run (structure, grids,
separatrices, flux surfaces, midplanes, targets), the contour lines of a
second quantity and the wall strip."""

from dataclasses import replace

import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection, PolyCollection

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
        seg = data.segments if getattr(data, "segments", None) is not None \
            else self.run.layers.get("wall", np.zeros((0, 4)))
        last = len(data.columns) - 1
        v = sum(np.asarray(data.values[min(max(c, 0), last)], float)
                for c in o.columns or (0,))[:len(seg)]
        if o.scale == "log":
            v = np.where(v > 0, v, np.nan)
        if not len(v) or not np.isfinite(v).any():
            return None
        st = replace(PlotStyle(), cmap=o.cmap, reverse=o.reverse,
                     scale=o.scale, auto=o.auto, vmin=o.vmin, vmax=o.vmax)
        norm = norm_for(v, st)
        strip = LineCollection(seg[:len(v)].reshape(-1, 2, 2),
                               cmap=cmap_for(st, norm), norm=norm,
                               linewidths=o.width, linestyles=o.style,
                               capstyle="butt", zorder=5.2)
        strip.set_array(np.ma.masked_invalid(v))
        self.ax.add_collection(strip, autolim=False)
        if o.colorbar:
            self.wall_colorbar(strip, data.label if label is None else
                               label)
        return strip

    def _flux_surfaces(self, st):
        try:
            lev = sorted(float(v) for v in st.levels.replace(",", " ").split())
        except ValueError:
            lev = []
        if not lev:
            return None
        m = self.run.psimap
        z = np.sqrt(np.clip(m.psin, 0.0, None)) if st.rho else m.psin
        return self.ax.contour(m.r, m.z, z, levels=lev)

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
