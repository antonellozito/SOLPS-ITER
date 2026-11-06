"""Overlays of the 2D plot: the layers of the run (structure, grids,
separatrices, flux surfaces) and further quantities over the field
(arrows, contour lines)."""

from dataclasses import replace

import numpy as np
from matplotlib.collections import LineCollection

from .scalar import node_values
from .styles import ZORDER, PlotStyle, even_levels, norm_for


class LayerMixin:
    """Layers and overlay quantities of Plot2D."""

    def _build_layer(self, key):
        run, st = self.run, self.layer_styles[key]
        old = self.layer_artists.pop(key, None)
        if old is not None:
            old.remove()
        art = None
        if key in ("structure", "device", "separatrices", "boundary"):
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
        elif key == "flux" and st.visible and run.psimap is not None:
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
        m = self.run.psimap
        z = np.sqrt(np.clip(m.psin, 0.0, None)) if st.rho else m.psin
        return self.ax.contour(m.r, m.z, z, levels=lev)

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

    def _overlay(self, role, data, o, st):
        """Arrows of a vector or contour lines of a second quantity, for
        the species column of the main plot where it exists."""
        col = min(max(st.column, 0), len(data.columns) - 1)
        box = self.vector_box()
        if role == "arrows" and hasattr(data, "vr"):
            pos, u, w = self._vector_data(data, col)[:3]
            ast = replace(PlotStyle(), arrow_length=o.arrow_length,
                          arrow_width=o.arrow_width, every=0,
                          color_by_magnitude=False, arrow_color=o.arrow_color)
            q = self._quiver(pos, u, w, ast, None, box)
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
