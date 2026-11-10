"""3D surface of a scalar field over R, Z (MATLAB surfplot): the values as
heights, clipped to the colour range and coloured with the same scale (a
log scale gives log10 heights); the 3D axes takes the place of the map."""

import numpy as np
from matplotlib.colors import LogNorm

from .. import theme
from .scalar import node_values
from .styles import cmap_for, norm_for


class SurfaceMixin:
    """3D surface plot type of Plot2D."""

    def _axes3d(self, on):
        """Show the 3D axes (made on first use) or the map."""
        if on and self.ax3d is None:
            self.ax3d = self.fig.add_axes(self.ax.get_position(),
                                          projection="3d")
            self.ax3d.set_facecolor(theme.figure_bg())
        if self.ax3d is not None:
            self.ax3d.set_visible(on)
        self.ax.set_visible(not on)

    def _surface(self, f, st):
        col = self._column(f, st)
        if f.location == "cells":
            tri = self._cell_tri()
            x, y, t = tri.x, tri.y, tri.get_masked_triangles()
            z = np.asarray(f.vertex[col], float)
        elif self.run.trimesh is not None:
            m = self.run.trimesh
            x, y, t = m.x, m.y, m.triangles
            z = node_values(m, np.asarray(f.values[col], float))
        else:
            return
        used, t = np.unique(t, return_inverse=True)
        x, y, t = x[used], y[used], t.reshape(-1, 3)
        norm = norm_for(z[used], st)
        z = np.clip(z[used], norm.vmin, norm.vmax)
        log = isinstance(norm, LogNorm)
        surf = self.ax3d.plot_trisurf(x, y, t, np.log10(z) if log else z,
                                      cmap=cmap_for(st, norm),
                                      linewidth=0.0, antialiased=False)
        surf.set_array(z[t].mean(axis=1))
        surf.set_norm(norm)
        w, h = np.ptp(x), np.ptp(y)
        self.ax3d.set_box_aspect((w, h, 0.7 * max(w, h)))
        self.ax3d.set_zlabel("log10" if log else "")
        self.field_artists.append(surf)
        self.mappable = surf
