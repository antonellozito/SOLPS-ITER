"""Shapes from the run geometry for the layers: polylines chained from
the layer segments, the closed parts of the structure, the flux surfaces
on the B2.5 grid."""

import numpy as np
from matplotlib.path import Path



def polylines(seg):
    """Segments (n, 4) chained into polylines where one starts at the end
    of the previous one."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    if not len(seg):
        return []
    tol = 1e-6 * max(np.ptp(seg[:, [0, 2]]), np.ptp(seg[:, [1, 3]]), 1e-9)
    out, cur = [], [seg[0, :2], seg[0, 2:]]
    for s in seg[1:]:
        if np.hypot(*(s[:2] - cur[-1])) <= tol:
            cur.append(s[2:])
        else:
            out.append(np.array(cur))
            cur = [s[:2], s[2:]]
    out.append(np.array(cur))
    return out


def closed(p):
    return len(p) > 3 and np.hypot(*(p[0] - p[-1])) <= 1e-6 * max(
        np.ptp(p, axis=0).max(), 1e-9)


def solid(seg, centres):
    """Closed polylines of the segments that are not around the plasma
    (most cell centres outside): the parts of the structure to fill."""
    return [p for p in polylines(seg) if closed(p) and
            Path(p).contains_points(centres).mean() < 0.5]


def area(p):
    return 0.5 * (np.dot(p[:, 0], np.roll(p[:, 1], -1))
                  - np.dot(p[:, 1], np.roll(p[:, 0], -1)))


def _edge(a, b, inside, steps=14):
    """The point between a (inside) and b (outside) where the line leaves
    the region, by bisection."""
    for _ in range(steps):
        m = 0.5 * (a + b)
        if inside(m[None])[0]:
            a = m
        else:
            b = m
    return a


def clipped(lines, inside):
    """The parts of the polylines where inside (points (n, 2) -> bool)
    holds, cut where they leave the region."""
    out = []
    for ln in lines:
        ok = inside(ln)
        if ok.all():
            out.append(ln)
            continue
        edges = np.flatnonzero(np.diff(np.concatenate(([0], ok.astype(
            np.int8), [0]))))
        for a, b in zip(edges[::2], edges[1::2]):     # ln[a:b] inside
            piece = [ln[a:b]]
            if a > 0:
                piece.insert(0, _edge(ln[a], ln[a - 1], inside)[None])
            if b < len(ln):
                piece.append(_edge(ln[b - 1], ln[b], inside)[None])
            piece = np.vstack(piece)
            if len(piece) > 1:
                out.append(piece)
    return out


def flux_lines(run, st):
    """[(level, polyline)] of the flux surfaces of rzpsi.dat at the levels
    of the layer style st (psiN, or rho with st.rho), only on the B2.5
    grid."""
    try:
        lev = sorted(float(v) for v in st.levels.replace(",", " ").split())
    except ValueError:
        return []
    m = run.psimap
    if not lev or m is None:
        return []
    import contourpy
    z = np.sqrt(np.clip(m.psin, 0.0, None)) if st.rho else m.psin
    r, zz = np.asarray(m.r, float), np.asarray(m.z, float)
    if r.ndim == 1:
        r, zz = np.meshgrid(r, zz)
    gen = contourpy.contour_generator(r, zz, np.asarray(z, float))
    find = run.geometry.finder

    def inside(p):
        return np.asarray(find(p[:, 0], p[:, 1])) >= 0
    return [(lv, ln) for lv in lev for ln in clipped(
        [np.asarray(x, float) for x in gen.lines(lv) if len(x) > 1],
        inside)]
