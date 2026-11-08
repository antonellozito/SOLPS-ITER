"""Overlays of the 2D plot: the layers of the run (structure, grids,
separatrices, flux surfaces) and further quantities over the field
(arrows, contour lines)."""

from dataclasses import replace

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path

from . import shapes
from .scalar import node_values
from .styles import FILLS, ZORDER, PlotStyle, even_levels, norm_for

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
        if key == "labels":
            for a in art:
                a.set(color=st.color, fontsize=st.width, alpha=st.alpha,
                      visible=st.visible, zorder=ZORDER[key])
            return
        if key == "xpoints":
            art.set(color=st.color, markersize=st.width,
                    markeredgewidth=max(st.width / 5.0, 1.0),
                    alpha=st.alpha, visible=st.visible)
        elif key in FILLS:
            art.set(facecolor=st.color, edgecolor="none", alpha=st.alpha,
                    visible=st.visible)
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

    def _overlay(self, role, data, o, st):
        """A vector as arrows or streamlines (VectorStyle o, species column
        o.column) or contour lines of a second quantity (species column of
        the main plot where it exists)."""
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
                                    colors=o.line_color,
                                    linewidths=o.line_width,
                                    linestyles=o.line_style)
            if o.line_labels:
                self.ax.clabel(cs, fontsize="x-small",
                               fmt=lambda v: f"{v:.3g}")
            self.field_artists.append(cs)
