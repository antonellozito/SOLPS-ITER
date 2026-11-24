"""Line cuts (of the plasma or the vector quantity shown) and statistics
(of the plasma quantity shown), from the values b2plot sent: linear
interpolation of the vertex (or EIRENE node) values as for the contours,
sums weighted with the b2plot volumes (vol, triavol)."""

import re

import numpy as np
import matplotlib.tri as mtri
from matplotlib.path import Path

from ...b2plot import labels
from ..plot.scalar import node_values

PER_M = re.compile(r"(?<![A-Za-z])m\^-(\d)")      # in plain units
M_POWER = re.compile(r"(?<![A-Za-z])m(?:\^(-?\d+))?(?![A-Za-z])")


def times_m(unit, power):
    """Plain unit (m^-3, m.s^-1 ...) of a value times m^power: the power
    of m raised by power (m^-3 times m^3 cancels, m.s^-1 times m gives
    m^2.s^-1), else m^power appended."""
    m = M_POWER.search(unit or "")
    k = power + (int(m.group(1)) if m and m.group(1) else 1 if m else 0)
    new = "" if k == 0 else "m" if k == 1 else "m^%d" % k
    if m:
        out = unit[:m.start()] + new + unit[m.end():]
        return re.sub(r"\.{2,}", ".", out).strip(" .") or "1"
    return ("%s %s" % (unit or "", new)).strip()


# a power: a number (m^2.s^-1: 2, not 2.s) or a name, not one in braces
_POWER = re.compile(r"([\^_])(-?\d+(?:\.\d+)?|-?[A-Za-z]\w*)")


def math_unit(unit):
    """Plain unit (m^-3 s^-1) as matplotlib math text: the powers
    raised."""
    return labels.tex_to_mathtext(_POWER.sub(r"\1{\2}", unit or ""))


def html_unit(unit):
    """Plain unit as rich text of a label: the powers raised."""
    text = (unit or "").replace("&", "&amp;").replace("<", "&lt;")
    return _POWER.sub(lambda m: "<{0}>{1}</{0}>".format(
        "sup" if m.group(1) == "^" else "sub", m.group(2)), text)


def _grid(plot, data, col=None):
    """Triangulation and node values (one array per component) of the
    quantity shown in its column (col, default the one of the plasma
    plot)."""
    col = plot._column(data, plot.style) if col is None else col
    vector = hasattr(data, "vr")
    if data.location == "cells":
        tri = plot._cell_tri(plot.vector_mask if vector else None)
        comps = [data.vxr[col], data.vxz[col]] if vector else \
            [data.vertex[col]]
    else:
        tri = plot.etri
        t = plot.run.trimesh
        comps = [node_values(t, np.asarray(a, float)) for a in (
            (data.vr[col], data.vz[col]) if vector else (data.values[col],))]
    return tri, [np.asarray(z, float) for z in comps]


def profile(plot, data, p0, p1, n=401, phi=(0.0, 0.0), col=None):
    """Samples along the straight line from (R, Z) p0 at the toroidal angle
    phi[0] to p1 at phi[1] (degrees; the same angle: a line in the poloidal
    plane, else a chord whose projection on it is curved): s along the
    line, R, Z, phi, the values (|v| and the normal component v.n for
    vectors, n to the right of the projection), and the length l along the
    projection; NaN outside the cells shown. col: the column of data
    (default: the one of the plasma plot)."""
    t = np.linspace(0.0, 1.0, n)
    a0, a1 = np.radians(np.asarray(phi, float))
    q0 = np.array([p0[0] * np.cos(a0), p0[0] * np.sin(a0), p0[1]], float)
    q1 = np.array([p1[0] * np.cos(a1), p1[0] * np.sin(a1), p1[1]], float)
    q = q0 + t[:, None] * (q1 - q0)
    r, z = np.hypot(q[:, 0], q[:, 1]), q[:, 2]
    ph = np.degrees(np.unwrap(np.arctan2(q[:, 1], q[:, 0])))
    s = t * float(np.linalg.norm(q1 - q0))
    l = np.concatenate(([0.0], np.cumsum(np.hypot(np.diff(r), np.diff(z)))))
    tri, comps = _grid(plot, data, col)
    finder = plot.run.geometry.trifinder(tri) if \
        data.location == "cells" else None
    vals = [np.ma.filled(mtri.LinearTriInterpolator(
        tri, c, trifinder=finder)(r, z), np.nan) for c in comps]
    if len(vals) == 1:
        return s, r, z, ph, vals[0], None, l
    dr, dz = np.gradient(r), np.gradient(z)     # along the projection
    norm = np.maximum(np.hypot(dr, dz), 1e-300)
    return (s, r, z, ph, np.hypot(*vals),
            vals[0] * dz / norm - vals[1] * dr / norm, l)


def at_points(plot, data, r, z, col=None):
    """The quantity at the points (R, Z) as the profiles interpolate it
    (the magnitude of a vector), NaN outside the cells shown."""
    tri, comps = _grid(plot, data, col)
    finder = plot.run.geometry.trifinder(tri) if \
        data.location == "cells" else None
    vals = [np.ma.filled(mtri.LinearTriInterpolator(
        tri, c, trifinder=finder)(np.asarray(r, float),
                                  np.asarray(z, float)), np.nan)
            for c in comps]
    return vals[0] if len(vals) == 1 else np.hypot(*vals)


def chord_ends(r, z):
    """R, Z and toroidal angle (degrees) of the two ends of a straight
    chord in space from its (R, Z) at equal steps along it (as b2plot sends
    the chords of the run): R squared is quadratic in the step, its
    curvature the square of the horizontal length, which with the two radii
    gives the angle between the ends (the first at 0)."""
    t = np.linspace(0.0, 1.0, len(r))
    c = np.polyfit(t, np.asarray(r, float) ** 2, 2)[0]
    r0, r1 = float(r[0]), float(r[-1])
    cos = (r0 ** 2 + r1 ** 2 - c) / max(2.0 * r0 * r1, 1e-300)
    phi = float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
    return (r0, float(z[0]), 0.0, r1, float(z[-1]),
            phi if phi > 0.05 else 0.0)  # below: the precision of the points


def separatrix_distance(s, rho):
    """Distance along the line from where it crosses the separatrix (rho
    poloidal 1), positive outside it; None if rho does not grow or fall
    all along the line or the line does not cross the separatrix."""
    ok = np.isfinite(rho)
    r, d = np.asarray(rho, float)[ok], np.asarray(s, float)[ok]
    if len(r) < 2 or not (np.all(np.diff(r) > 0) or np.all(np.diff(r) < 0)) \
            or not r.min() <= 1.0 <= r.max():
        return None
    k = np.argsort(r)
    at = float(np.interp(1.0, r[k], d[k]))
    return (s - at) if r[-1] > r[0] else (at - s)


def single_valued(x, values):
    """True if x grows or falls all along the samples where both x and the
    values are known (the values a function of x)."""
    ok = np.isfinite(x) & np.isfinite(values)
    d = np.diff(np.asarray(x, float)[ok])
    return len(d) > 0 and (bool(np.all(d > 0)) or bool(np.all(d < 0)))


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
