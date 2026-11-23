"""Vectors of the 2D tab in three dimensions, toroidally symmetric: the
toroidal component of each vector quantity, the field resampled on a
regular (R, Z) grid and interpolated there, points (R, Z, phi) in
Cartesian coordinates.

Toroidal component: EIRENE vectors have it (their z label); B2.5 ones
are reconstructed from their poloidal component, along the field line
(toroidal = poloidal * B_tor / B_pol) or, for drifts and anomalous
transport, perpendicular to it within the flux surface (toroidal =
-poloidal * B_pol / B_tor), the radial component having none. bx and bz
of b2plot are signed (poloidal field along x, toroidal field)."""

import re

import numpy as np
import matplotlib.tri as mtri

ALONG, ACROSS, NONE, DATA = "along", "across", "none", "data"
# poloidal labels of B2.5 vectors perpendicular to the field (drifts,
# anomalous and turbulent transport, perpendicular currents) and without
# a toroidal component (fluid neutrals)
_ACROSS = re.compile(r"ecrb|exb|dia|pnch|nanm|panm|str\b|inrt|vspe|visq|"
                     r"anml|vskt|viskt|fchxn\b|fkt")
_NONE = re.compile(r"^fhn")
GRID = 300                      # resampling points along the longer side


def rule(q):
    """Automatic rule of the toroidal component of vector quantity q."""
    if q.source == "evector":
        return DATA
    p = q.poloidal
    if _NONE.search(p):
        return NONE
    return ACROSS if _ACROSS.search(p) else ALONG


RATIO = "bz bx m/"               # B_tor / B_pol, signed, final state


def component_tokens(q, how):
    """b2plot tokens of the component of vector q asked for its toroidal
    component by rule how: the EIRENE z one (the first x of the label or
    of the movie expression made a z), the poloidal one otherwise (then
    combined with RATIO), None if it is zero."""
    if how == DATA:
        return q.poloidal.replace("x", "z", 1)
    if how in (ALONG, ACROSS):
        return q.poloidal
    return None


def toroidal(how, comp, ratio):
    """Toroidal component from the component asked and B_tor/B_pol."""
    if how == ALONG:
        return comp * ratio
    if how == ACROSS:
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(ratio != 0, -comp / ratio, 0.0)
    return comp


def resample(tri, nodes, box, n=GRID):
    """Node values (list of arrays) of tri linearly interpolated on a
    regular grid over box: xs, ys and the arrays (nan outside)."""
    x0, x1, y0, y1 = box
    w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    nx = max(int(n * w / max(w, h)), 2)
    ny = max(int(n * h / max(w, h)), 2)
    xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    finder = tri.get_trifinder()
    out = [np.ma.filled(mtri.LinearTriInterpolator(tri, v, trifinder=finder)(
        X, Y).astype(float), np.nan) for v in nodes]
    return xs, ys, out


def bilinear(xs, ys, fields, x, y):
    """Values of the gridded fields at the points (x, y), nan outside."""
    fx = (x - xs[0]) / (xs[1] - xs[0])
    fy = (y - ys[0]) / (ys[1] - ys[0])
    fx = np.where(np.isfinite(fx), fx, -1.0)
    fy = np.where(np.isfinite(fy), fy, -1.0)
    inside = (fx >= 0) & (fx <= len(xs) - 1) & (fy >= 0) & \
        (fy <= len(ys) - 1)
    i = np.clip(np.floor(fx).astype(int), 0, len(xs) - 2)
    j = np.clip(np.floor(fy).astype(int), 0, len(ys) - 2)
    a, b = np.clip(fx - i, 0, 1), np.clip(fy - j, 0, 1)
    out = []
    for f in fields:
        v = (f[j, i] * (1 - a) * (1 - b) + f[j, i + 1] * a * (1 - b)
             + f[j + 1, i] * (1 - a) * b + f[j + 1, i + 1] * a * b)
        out.append(np.where(inside, v, np.nan))
    return out


def cartesian(r, z, phi, vr=None, vz=None, vp=None):
    """Points (and vectors) of (R, Z, phi) in Cartesian x, y, z."""
    c, s = np.cos(phi), np.sin(phi)
    pts = (r * c, r * s, z)
    if vr is None:
        return pts
    return pts, (vr * c - vp * s, vr * s + vp * c, vz)
