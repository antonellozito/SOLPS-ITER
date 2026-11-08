"""Shapes from the run geometry for the layers and the streamline seeds:
polylines chained from the layer segments, the outline of the EIRENE
mesh, points spaced along polylines, positions of the text labels."""

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


def outline(trimesh):
    """Outer boundary of a triangle mesh (closed, counter-clockwise)."""
    t = trimesh.triangles
    e = np.sort(np.vstack((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]])), 1)
    edges, count = np.unique(e, axis=0, return_counts=True)
    near = {}
    for a, b in edges[count == 1]:
        near.setdefault(a, []).append(b)
        near.setdefault(b, []).append(a)
    xy = np.column_stack((trimesh.x, trimesh.y))
    loops, seen = [], set()
    for start in near:
        if start in seen:
            continue
        loop, prev, cur = [start], -1, start
        seen.add(start)
        nxt = [n for n in near[cur] if n != prev and n not in seen]
        while nxt:
            prev, cur = cur, nxt[0]
            loop.append(cur)
            seen.add(cur)
            nxt = [n for n in near[cur] if n != prev and n not in seen]
        loops.append(xy[loop + loop[:1]])
    best = max(loops, key=lambda p: abs(area(p)), default=None)
    return best if best is None or area(best) > 0 else best[::-1]


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


def label_points(run):
    """(text, R, Z) of the labels: regions at a central cell, X-points,
    the O-point of the psi map, midplanes (run.marks), targets at their
    middle."""
    g, out = run.geometry, []
    for r in np.unique(g.region[g.visible]):
        rows = np.flatnonzero(g.visible & (g.region == r))
        c = g.centres[rows]
        i = np.argmin(np.hypot(*(c - c.mean(axis=0)).T))
        out.append((str(r), c[i, 0], c[i, 1]))
    for k, (r, z) in enumerate(g.xpoints):
        out.append(("X%s" % (k + 1 if len(g.xpoints) > 1 else ""), r, z))
    if run.psimap is not None:
        out.append(("O",) + tuple(run.psimap.opoint))
    for name, (r, z) in getattr(run, "marks", {}).items():
        out.append((name, r, z))
    for name, polys in targets(run.layers).items():
        mid = along(polys, 1)
        if len(mid):
            out.append(("T" + name, mid[0, 0], mid[0, 1]))
    return out
