"""Shapes from the run geometry for the layers and the streamline seeds:
polylines chained from the layer segments, the closed parts of the
structure, points spaced along polylines."""

import numpy as np
from matplotlib.path import Path

SEEDS = (("drawn line", "line"), ("separatrix", "separatrices"),
         ("divertor entrance (X-points)", "xpoints"),
         ("divertor targets", "targets"), ("grid boundary", "boundary"))


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


def along(polys, n):
    """n points evenly spaced along the polylines (by length)."""
    pieces = [(p[:-1], p[1:]) for p in polys if len(p) > 1]
    if not pieces or n < 1:
        return np.zeros((0, 2))
    a = np.vstack([s for s, _ in pieces])
    b = np.vstack([e for _, e in pieces])
    length = np.hypot(*(b - a).T)
    cum = np.concatenate(([0.0], np.cumsum(length)))
    s = (np.arange(n) + 0.5) * cum[-1] / n
    k = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(a) - 1)
    f = ((s - cum[k]) / np.maximum(length[k], 1e-300))[:, None]
    return a[k] + f * (b[k] - a[k])


def targets(layers):
    """Polylines of the divertor targets, by target name."""
    return {k.split(": ", 1)[1]: polylines(v) for k, v in layers.items()
            if k.startswith("target: ")}


def seed_points(run, key, n, inside):
    """Streamline seeds of a preset (SEEDS); inside(points) tells which
    points lie in the B2.5 grid."""
    if key == "targets":
        return along([p for ps in targets(run.layers).values()
                      for p in ps], n)
    if key == "xpoints":
        x0, x1 = run.geometry.bbox[:2]
        lines = [np.array([[x0, z], [x1, z]])
                 for _, z in run.geometry.xpoints]
        dense = along(lines, 40 * n)
        dense = dense[inside(dense)]
        return dense[np.linspace(0, len(dense) - 1, min(n, len(dense)))
                     .astype(int)] if len(dense) else dense
    return along(polylines(run.layers.get(key, [])), n)
