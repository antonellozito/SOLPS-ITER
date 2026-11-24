"""Magnetic parts of the 2D plot: the field line traced from the plot
(tools/fieldlines) as its projection on the poloidal plane, in one colour
or in a colour map of the parallel or poloidal length or the toroidal
turns from where it starts (anticlockwise), with a halo, a dot at the point clicked and a
square at each end with its length (open lines); the directions of the
toroidal field, the poloidal field and the plasma current in the hole of
the grid around the O-point (a layer)."""

import numpy as np
from matplotlib import colormaps, patheffects
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path

from .. import theme
from ..tools import fieldlines
from .styles import ZORDER

FIELDLINE_Z = 6.3               # over the plot, under the mouse shapes


def _halo(width):
    return [patheffects.Stroke(linewidth=width, foreground=theme.axes_bg()),
            patheffects.Normal()]


def colour_scale(line, by, cmap):
    """(values along the anticlockwise points, Normalize, colormap) of a
    field line coloured by "parallel", "poloidal" or "turns" in the
    colour map cmap."""
    pts, _ = line.anticlockwise()
    v = fieldlines.along(pts)[by]
    top = float(v.max()) if len(v) else 1.0
    return v, Normalize(0.0, top if top > 0 else 1.0), \
        theme.cmap(colormaps[cmap])


def fieldline_artists(ax, line, look, by=None):
    """The field line (look: colour, width, line style, colour map) added
    to ax, coloured by by ("parallel", "poloidal", "turns") or not
    (None): the
    artists and the mappable of its colour scale (None in one colour)."""
    colour, width, style = theme.rgb(look[0]), look[1], look[2]
    pts, _ = line.anticlockwise()
    out, mappable = [], None
    halo = Line2D(pts[:, 0], pts[:, 1], color=theme.axes_bg(),
                  linewidth=width + 2.0, solid_capstyle="round",
                  zorder=FIELDLINE_Z - 0.01)
    ax.add_line(halo)
    out.append(halo)
    if by is None:
        ln = Line2D(pts[:, 0], pts[:, 1], color=colour, linewidth=width,
                    linestyle=style, zorder=FIELDLINE_Z)
        ax.add_line(ln)
        out.append(ln)
    else:
        v, norm, cmap = colour_scale(line, by, look[3])
        seg = np.stack((pts[:-1, :2], pts[1:, :2]), axis=1)
        lc = LineCollection(seg, cmap=cmap, norm=norm, linewidths=width,
                            linestyles=style, zorder=FIELDLINE_Z)
        lc.set_array(0.5 * (v[1:] + v[:-1]))
        ax.add_collection(lc, autolim=False)
        out.append(lc)
        mappable = lc
    size = 4.0 + 1.5 * width
    out += ax.plot([line.start[0]], [line.start[1]], ls="none", marker="o",
                   ms=size, mfc=colour, mec=theme.axes_bg(), mew=0.8,
                   zorder=FIELDLINE_Z + 0.01)
    if not line.closed:
        for k in (0, 1):
            e = line.ends[k]
            out += ax.plot([e[0]], [e[1]], ls="none", marker="s", ms=size,
                           mfc=colour, mec=theme.axes_bg(), mew=0.8,
                           zorder=FIELDLINE_Z + 0.01)
            text = "%.1f m" % line.lengths[k]
            out.append(ax.annotate(
                text if line.hits[k] else "> " + text, e, xytext=(5, 3),
                textcoords="offset points", fontsize="x-small",
                color=colour, zorder=FIELDLINE_Z + 0.02,
                path_effects=_halo(2.5)))
    return out, mappable


def direction_artists(ax, run, st):
    """Symbols of the toroidal field and the plasma current (a dot: out
    of the plot, clockwise seen from above; a cross: into it) and an arc
    arrow of the poloidal field around the O-point, added to ax; []
    without the field."""
    d = fieldlines.directions(run)
    if d is None or not st.visible:
        return []
    colour = theme.rgb(st.color)
    z = ZORDER["directions"]
    (r0, z0), rr = d["hole"]
    rr = rr if rr > 0 else 0.1
    out = []
    size = 8.0 + 5.0 * st.width
    for dx, sign, label in ((-0.3, d["btor"], r"$B_\phi$"),
                            (0.3, d["ip"], r"$I_p$")):
        x = r0 + dx * rr
        out += ax.plot([x], [z0], ls="none", marker="o", ms=size,
                       mfc="none", mec=colour, mew=st.width, alpha=st.alpha,
                       zorder=z)
        out += ax.plot([x], [z0], ls="none", marker="o" if sign > 0 else "x",
                       ms=size * (0.25 if sign > 0 else 0.55), mfc=colour,
                       mec=colour, mew=st.width, alpha=st.alpha, zorder=z)
        out.append(ax.annotate(label, (x, z0), xytext=(0, -size),
                               textcoords="offset points", ha="center",
                               va="top", color=colour, alpha=st.alpha,
                               zorder=z, path_effects=_halo(2.5)))
    a = np.radians(np.linspace(110.0, 430.0, 60))
    if d["bpol_clockwise"]:
        a = a[::-1]
    arc = np.column_stack((r0 + 0.65 * rr * np.cos(a),
                           z0 + 0.65 * rr * np.sin(a)))
    arrow = FancyArrowPatch(path=Path(arc), arrowstyle="-|>",
                            mutation_scale=6.0 + 4.0 * st.width,
                            color=colour, linewidth=st.width,
                            linestyle=st.style, alpha=st.alpha, zorder=z)
    ax.add_patch(arrow)
    out.append(arrow)
    out.append(ax.annotate(r"$B_\theta$", (r0, z0 + 0.65 * rr),
                           xytext=(0, 4), textcoords="offset points",
                           ha="center", va="bottom", color=colour,
                           alpha=st.alpha, zorder=z,
                           path_effects=_halo(2.5)))
    return out
