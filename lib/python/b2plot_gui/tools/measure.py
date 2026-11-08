"""Line cuts and statistics of the quantity shown, from the values b2plot
sent: linear interpolation of the vertex (or EIRENE node) values as for
the contours, sums weighted with the b2plot volumes (vol, triavol)."""

import re

import numpy as np
import matplotlib.tri as mtri
from matplotlib.path import Path

from ..plot.scalar import node_values

PER_M = re.compile(r"(?<![A-Za-z])m\^-(\d)")      # in plain units


def times_m(unit, power):
    """Plain unit (m^-3 ...) of a value times m^power: the power of m
    raised by power (m^-3 times m^3 cancels), else m^power appended."""
    m = PER_M.search(unit or "")
    k = power - int(m.group(1)) if m else power
    new = "" if k == 0 else "m" if k == 1 else "m^%d" % k
    if m:
        return (unit[:m.start()] + new + unit[m.end():]).strip(" .") or "1"
    return ("%s %s" % (unit or "", new)).strip()


def _grid(plot, data):
    """Triangulation and node values (one array per component) of the
    quantity shown in its column."""
    col = plot._column(data, plot.style)
    vector = hasattr(data, "vr")
    if data.location == "cells":
        tri = plot._cell_tri()
        comps = [data.vxr[col], data.vxz[col]] if vector else \
            [data.vertex[col]]
    else:
        tri = plot.etri
        t = plot.run.trimesh
        comps = [node_values(t, np.asarray(a, float)) for a in (
            (data.vr[col], data.vz[col]) if vector else (data.values[col],))]
    return tri, [np.asarray(z, float) for z in comps]


def profile(plot, data, p0, p1, n=401):
    """Samples along the line p0-p1: s, R, Z and the values (|v| and the
    normal component v.n for vectors, n to the right of the line), NaN
    outside the cells shown."""
    t = np.linspace(0.0, 1.0, n)
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    r = p0[0] + t * (p1[0] - p0[0])
    z = p0[1] + t * (p1[1] - p0[1])
    length = float(np.hypot(*(p1 - p0)))
    tri, comps = _grid(plot, data)
    vals = [np.ma.filled(mtri.LinearTriInterpolator(tri, c)(r, z), np.nan)
            for c in comps]
    if len(vals) == 1:
        return t * length, r, z, vals[0], None
    nr, nz = (p1[1] - p0[1]) / length, -(p1[0] - p0[0]) / length
    return t * length, r, z, np.hypot(*vals), vals[0] * nr + vals[1] * nz


def line_sums(s, r, values, normal):
    """Integral and average of the values over the part of the line inside
    the cells, and the flux through the surface the line sweeps around
    the axis (2 pi R v.n, for vectors)."""
    ok = np.isfinite(values)
    seg = np.diff(s)
    both = ok[1:] & ok[:-1]

    def trapz(f):
        return float(np.sum(0.5 * (f[1:] + f[:-1]) * seg * both))
    inside = float(np.sum(seg * both))
    total = trapz(np.where(ok, values, 0.0))
    flux = None if normal is None else trapz(np.where(
        ok, 2 * np.pi * r * normal, 0.0))
    return inside, total, total / inside if inside > 0 else np.nan, flux


def chosen(plot, data, shape=None):
    """Indices of the cells (geometry rows) or triangles whose centres lie
    in the shape ((n, 2) corners; two corners: a box), of the cells shown;
    all of them without a shape."""
    if data.location == "cells":
        g = plot.run.geometry
        idx, centres = np.flatnonzero(plot.mask), g.centres
    else:
        idx, centres = np.arange(len(plot.ecentres)), plot.ecentres
    if shape is None:
        return idx
    p = np.asarray(shape, float)
    if len(p) == 2:
        (x0, y0), (x1, y1) = p
        p = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return idx[Path(p).contains_points(centres[idx])]


def values_at(plot, data, idx):
    """Values of the quantity shown (|v| for vectors) at the cells or
    triangles idx."""
    col = plot._column(data, plot.style)
    i = plot.run.geometry.cells[idx] - 1 if data.location == "cells" \
        else idx
    if hasattr(data, "vr"):
        return np.hypot(data.vr[col][i], data.vz[col][i])
    return np.asarray(data.values[col], float)[i]


def statistics(values, volumes):
    """Cells, volume, volume integral, volume average, min and max of the
    finite values."""
    ok = np.isfinite(values) & np.isfinite(volumes)
    v, w = values[ok], volumes[ok]
    vol = float(w.sum())
    total = float(np.sum(v * w))
    return dict(n=int(ok.sum()), volume=vol, integral=total,
                average=total / vol if vol > 0 else np.nan,
                min=float(v.min()) if v.size else np.nan,
                max=float(v.max()) if v.size else np.nan)
