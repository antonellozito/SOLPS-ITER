"""Overlays of the 2D plot: the layers of the run (structure, grids,
separatrices, flux surfaces, chords, trajectories) and further quantities
over the field (vectors, contour lines, the wall strip)."""

from dataclasses import replace

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.text import Text

from .. import theme
from ..catalog import CHORD_POINTS
from . import shapes
from .scalar import node_values
from .styles import (FILLS, ZORDER, PlotStyle, cmap_for, even_levels,
                     norm_for)

FAR = 1.0e4                     # metres: lines and masks beyond any view


class LayerMixin:
    """Layers and overlay quantities of Plot2D."""

    def _build_layer(self, key):
        run, st = self.run, self.layer_styles[key]
        old = self.layer_artists.pop(key, None)
        for a in old if isinstance(old, list) else (
                [] if old is None else [old]):
            a.remove()
        art = None
        if key in ("structure", "device", "separatrices", "boundary",
                   "targets"):
            seg = run.layers.get(key) if key != "targets" else np.vstack(
                [np.zeros((0, 4))] + [v for k, v in run.layers.items()
                                      if k.startswith("target: ")])
            if seg is not None and len(seg):
                art = LineCollection(seg.reshape(-1, 2, 2))
        elif key == "zero":
            art = LineCollection([[(-FAR, 0.0), (FAR, 0.0)],
                                  [(0.0, -FAR), (0.0, FAR)]])
        elif key == "filled":
            polys = shapes.solid(run.layers.get("device", []),
                                 run.geometry.centres)
            art = PolyCollection(polys) if polys else None
        elif key == "outside" and run.trimesh is not None:
            loop = shapes.outline(run.trimesh)
            box = np.array([[-FAR, -FAR], [-FAR, FAR], [FAR, FAR],
                            [FAR, -FAR], [-FAR, -FAR]])
            art = PathPatch(Path(np.vstack((box, loop)), np.concatenate((
                [Path.MOVETO], [Path.LINETO] * 3, [Path.CLOSEPOLY],
                [Path.MOVETO], [Path.LINETO] * (len(loop) - 2),
                [Path.CLOSEPOLY]))))
            self.ax.add_patch(art)
        elif key == "chords":
            art = self._chords(run.layers)
        elif key == "trajectories" and len(run.layers.get(key, [])):
            seg = run.layers[key]
            art = LineCollection(seg.reshape(-1, 2, 2), colors=theme.rgb_array(
                [run.palette.get(c, (0.5, 0.5, 0.5)) for c in
                 run.layer_colours.get(key, [1] * len(seg))]))
        elif key == "labels":
            art = [self.ax.text(r, z, text, ha="center", va="center",
                                clip_on=True, bbox=dict(
                                    boxstyle="round,pad=0.15", fc="white",
                                    ec="none", alpha=0.6))
                   for text, r, z in shapes.label_points(run)]
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
        elif key == "flux" and st.visible and run.psimap is not None:
            art = self._flux_surfaces(st)
        if isinstance(art, (LineCollection, PolyCollection)):
            self.ax.add_collection(art, autolim=False)
        if art is not None:
            self.layer_artists[key] = art
            self._restyle(key)

    def _wall_strip(self, data, o):
        """A wall field (one value per wall element, WallStyle o) along the
        wall elements, with its own colour scale and colour bar."""
        seg = data.segments if getattr(data, "segments", None) is not None \
            else self.run.layers.get("wall", np.zeros((0, 4)))
        v = np.asarray(data.values[min(o.column, len(data.columns) - 1)],
                       float)[:len(seg)]
        if o.log:
            v = np.where(v > 0, v, np.nan)
        if not len(v) or not np.isfinite(v).any():
            return
        st = replace(PlotStyle(), cmap=o.cmap,
                     scale="log" if o.log else "linear")
        norm = norm_for(v, st)
        strip = LineCollection(seg[:len(v)].reshape(-1, 2, 2),
                               cmap=cmap_for(st, norm), norm=norm,
                               linewidths=o.width, capstyle="butt",
                               zorder=5.2)
        strip.set_array(np.ma.masked_invalid(v))
        self.ax.add_collection(strip, autolim=False)
        self.field_artists.append(strip)
        if o.colorbar:
            self.wall_colorbar(strip, data.label)

    def _chords(self, layers):
        """Chords of every set, each numbered set.chord at its end."""
        art = []
        sets = [k for k in layers if k.startswith("chords: ")]
        for i, key in enumerate(sets, 1):
            seg = layers[key].reshape(-1, CHORD_POINTS - 1, 4)
            if not len(seg):
                continue
            line = LineCollection(seg.reshape(-1, 2, 2))
            self.ax.add_collection(line, autolim=False)
            art.append(line)
            art += [self.ax.text(c[-1, 2], c[-1, 3], "%d.%d" % (i, j),
                                 clip_on=True, ha="left", va="center")
                    for j, c in enumerate(seg, 1)]
        return art or None

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
        if isinstance(art, list):
            for a in art:
                if isinstance(a, Text):
                    a.set(color=theme.rgb(st.color),
                          fontsize=st.width if key == "labels" else 7.0,
                          alpha=st.alpha,
                          visible=st.visible, zorder=ZORDER[key] + 0.01)
                else:
                    a.set(edgecolor=theme.rgb(st.color), linewidth=st.width,
                          linestyle=st.style, alpha=st.alpha,
                          visible=st.visible, zorder=ZORDER[key])
            return
        if key == "trajectories":
            art.set(linewidth=st.width, linestyle=st.style, alpha=st.alpha,
                    visible=st.visible, zorder=ZORDER[key])
            return
        if key == "xpoints":
            art.set(color=theme.rgb(st.color), markersize=st.width,
                    markeredgewidth=max(st.width / 5.0, 1.0),
                    alpha=st.alpha, visible=st.visible)
        elif key in FILLS:
            art.set(facecolor=theme.rgb(st.color), edgecolor="none",
                    alpha=st.alpha,
                    visible=st.visible)
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

    def _overlay(self, role, data, o, st):
        """A vector as arrows or streamlines (VectorStyle o, species column
        o.column) or contour lines of a second quantity (species column of
        the main plot where it exists)."""
        if role == "wall":
            self._wall_strip(data, o)
            return
        col = min(max(st.column, 0), len(data.columns) - 1)
        box = self.vector_box()
        if role.startswith("arrows") and hasattr(data, "vr"):
            col = min(max(o.column, 0), len(data.columns) - 1)
            pos, u, w, tri, nu, nw = self._vector_data(data, col)
            if o.stream:
                self._streamlines(tri, nu, nw, replace(
                    PlotStyle(), kind="stream", stream_width=o.width,
                    stream_color=o.color, color_by_magnitude=False), box,
                    zorder=5.4)
                return
            ast = replace(PlotStyle(), arrow_length=o.length,
                          arrow_width=o.width, every=0, normalize=o.same,
                          color_by_magnitude=False, arrow_color=o.color)
            q = self._quiver(pos, u, w, ast, box)
            if q is not None:
                q.set_zorder(5.5)
        elif role == "lines" and not hasattr(data, "vr"):
            if data.location == "cells":
                tri = self._cell_tri()
                z = np.asarray(data.vertex[col], float)
                used = np.unique(tri.get_masked_triangles())
                zz = z[used]
            elif self.etri is not None:
                tri = self.etri
                z = zz = node_values(self.run.trimesh,
                                     np.asarray(data.values[col], float))
            else:
                return
            lst = replace(PlotStyle(), scale="log" if o.line_log else "linear")
            norm = norm_for(zz, lst)
            lev = even_levels(norm, o.line_levels)
            if o.line_log:
                lev = lev[lev > 0]
                z = np.where(z > 0, z, norm.vmin)
            cs = self.ax.tricontour(tri, z, levels=lev, zorder=4.5,
                                    colors=[theme.rgb(o.line_color)],
                                    linewidths=o.line_width,
                                    linestyles=o.line_style)
            if o.line_labels:
                self.ax.clabel(cs, fontsize="x-small",
                               fmt=lambda v: f"{v:.3g}")
            self.field_artists.append(cs)
