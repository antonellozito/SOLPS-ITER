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


def profile(plot, data, p0, p1, n=401, phi=(0.0, 0.0)):
    """Samples along the straight line from (R, Z) p0 at the toroidal angle
    phi[0] to p1 at phi[1] (degrees; the same angle: a line in the poloidal
    plane, else a chord whose projection on it is curved): s along the
    line, R, Z, phi, the values (|v| and the normal component v.n for
    vectors, n to the right of the projection), and the length l along the
    projection; NaN outside the cells shown."""
    t = np.linspace(0.0, 1.0, n)
    a0, a1 = np.radians(np.asarray(phi, float))
    q0 = np.array([p0[0] * np.cos(a0), p0[0] * np.sin(a0), p0[1]], float)
    q1 = np.array([p1[0] * np.cos(a1), p1[0] * np.sin(a1), p1[1]], float)
    q = q0 + t[:, None] * (q1 - q0)
    r, z = np.hypot(q[:, 0], q[:, 1]), q[:, 2]
    ph = np.degrees(np.unwrap(np.arctan2(q[:, 1], q[:, 0])))
    s = t * float(np.linalg.norm(q1 - q0))
    l = np.concatenate(([0.0], np.cumsum(np.hypot(np.diff(r), np.diff(z)))))
    tri, comps = _grid(plot, data)
    vals = [np.ma.filled(mtri.LinearTriInterpolator(tri, c)(r, z), np.nan)
            for c in comps]
    if len(vals) == 1:
        return s, r, z, ph, vals[0], None, l
    dr, dz = np.gradient(r), np.gradient(z)     # along the projection
    norm = np.maximum(np.hypot(dr, dz), 1e-300)
    return (s, r, z, ph, np.hypot(*vals),
            vals[0] * dz / norm - vals[1] * dr / norm, l)


def line_sums(s, r, values, normal, l=None):
    """Integral and average of the values over the part of the line inside
    the cells, and the flux through the surface its projection on the
    poloidal plane (lengths l, default s) sweeps around the axis (2 pi R
    v.n, for vectors)."""
    ok = np.isfinite(values)
    both = ok[1:] & ok[:-1]

    def trapz(f, x):
        return float(np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(x) * both))
    inside = float(np.sum(np.diff(s) * both))
    total = trapz(np.where(ok, values, 0.0), s)
    flux = None if normal is None else trapz(np.where(
        ok, 2 * np.pi * r * normal, 0.0), s if l is None else l)
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
