"""Shapes of the poloidal plane turned into 3D over a toroidal sector
[phi0, phi1] (x = R cos phi, y = R sin phi, z = Z): surfaces of revolution
of polylines, polygons cut into triangles, points on the planes of the
sector, toroidal rings of points, the outer boundary loop of a mesh,
segments chained into polylines, loops moved outwards."""

import numpy as np

STEP = np.radians(2.0)          # toroidal step of the surfaces


def nphi(phi0, phi1):
    """Toroidal steps of a sector."""
    return max(int(np.ceil(abs(phi1 - phi0) / STEP)), 2)


def full(phi0, phi1):
    return abs(phi1 - phi0) >= 2.0 * np.pi - 1e-9


def on_plane(rz, phi):
    """Points (R, Z) of the poloidal plane at phi in x, y, z."""
    rz = np.asarray(rz, float).reshape(-1, 2)
    return np.column_stack((rz[:, 0] * np.cos(phi), rz[:, 0] * np.sin(phi),
                            rz[:, 1]))


def surface(poly, phi0, phi1, closed=False):
    """Vertices and quad faces of the surface of revolution of the
    polyline poly (n, 2) (closed: its last point joined to the first)."""
    poly = np.asarray(poly, float)
    n, m = len(poly), nphi(phi0, phi1)
    phis = np.linspace(phi0, phi1, m + 1)
    wrap = full(phi0, phi1)
    if wrap:
        phis = phis[:-1]
    verts = np.vstack([on_plane(poly, p) for p in phis])
    k = len(phis)
    a = np.arange(n - (0 if closed else 1))
    b = (a + 1) % n
    faces = []
    for j in range(m):
        j1 = (j + 1) % k if wrap else j + 1
        faces.append(np.column_stack((j * n + a, j * n + b, j1 * n + b,
                                      j1 * n + a)))
    return verts, np.vstack(faces)


def earclip(poly):
    """Triangles (indices) of the simple polygon poly (n, 2), not closed
    (its last point not the first), either orientation."""
    p = np.asarray(poly, float)
    n = len(p)
    if n < 3:
        return np.zeros((0, 3), int)
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1)
                        - p[:, 1] * np.roll(p[:, 0], -1))
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    guard = 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        m = len(idx)
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = p[i0], p[i1], p[i2]
            if cross(a, b, c) <= 0:             # reflex vertex
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                q = p[j]
                if cross(a, b, q) >= 0 and cross(b, c, q) >= 0 and \
                        cross(c, a, q) >= 0:
                    inside = True
                    break
            if not inside:
                tris.append((i0, i1, i2))
                idx.pop(k)
                break
        else:                                   # degenerate: fan the rest
            break
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
    return np.asarray(tris, int)


def ring(r, z, phi0, phi1):
    """Nodes and edges of the toroidal circle (arc) at (r, z)."""
    m = nphi(phi0, phi1)
    phis = np.linspace(phi0, phi1, m + 1)
    if full(phi0, phi1):
        phis = phis[:-1]
    nodes = np.column_stack((r * np.cos(phis), r * np.sin(phis),
                             np.full(len(phis), z)))
    e = np.column_stack((np.arange(len(phis) - 1), np.arange(1, len(phis))))
    if full(phi0, phi1):
        e = np.vstack((e, [[len(phis) - 1, 0]]))
    return nodes, e


def loops(seg):
    """Closed loops (lists of points) chained from segments (n, 4) whose
    ends meet (the boundary edges of a mesh)."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    if not len(seg):
        return []
    scale = max(np.ptp(seg[:, [0, 2]]), np.ptp(seg[:, [1, 3]]), 1e-9)
    key = lambda x, y: (round(x / scale * 1e7), round(y / scale * 1e7))
    nxt = {}
    for k, s in enumerate(seg):
        nxt.setdefault(key(s[0], s[1]), []).append(k)
        nxt.setdefault(key(s[2], s[3]), []).append(k)
    used = np.zeros(len(seg), bool)
    out = []
    for k0 in range(len(seg)):
        if used[k0]:
            continue
        used[k0] = True
        pts = [seg[k0, :2], seg[k0, 2:]]
        end = key(*pts[-1])
        while True:
            cand = [k for k in nxt.get(end, ()) if not used[k]]
            if not cand:
                break
            k = cand[0]
            used[k] = True
            s = seg[k]
            p = s[2:] if key(s[0], s[1]) == end else s[:2]
            pts.append(p)
            end = key(*p)
        out.append(np.array(pts))
    return out


def outer_loop(seg):
    """The loop of largest area of the segments (the outer boundary)."""
    best, area = None, -1.0
    for p in loops(seg):
        a = abs(0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1)
                             - p[:, 1] * np.roll(p[:, 0], -1)))
        if a > area:
            best, area = p, a
    return best


def boundary_edges(x, y, triangles):
    """Segments (n, 4) of the edges of the triangles belonging to one
    triangle only."""
    t = np.asarray(triangles)
    e = np.sort(np.vstack((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]])), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    u = u[c == 1]
    return np.column_stack((x[u[:, 0]], y[u[:, 0]], x[u[:, 1]], y[u[:, 1]]))


def chains(seg):
    """Polylines chained from segments (n, 4) meeting at their ends, in
    any order and direction: open ones from an end, then closed ones."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    if not len(seg):
        return []
    scale = max(np.ptp(seg[:, [0, 2]]), np.ptp(seg[:, [1, 3]]), 1e-9)

    def key(p):
        return (round(p[0] / scale * 1e7), round(p[1] / scale * 1e7))
    ends = {}
    for k, s in enumerate(seg):
        for j in (0, 2):
            ends.setdefault(key(s[j:j + 2]), []).append(k)
    used = np.zeros(len(seg), bool)
    out = []

    def walk(k, start):
        used[k] = True
        s = seg[k]
        a, b = (s[:2], s[2:]) if key(s[:2]) == start else (s[2:], s[:2])
        pts = [a, b]
        while True:
            cand = [j for j in ends.get(key(pts[-1]), ()) if not used[j]]
            if not cand:
                return np.array(pts)
            j = cand[0]
            used[j] = True
            t = seg[j]
            pts.append(t[2:] if key(t[:2]) == key(pts[-1]) else t[:2])
    for pt, ks in ends.items():             # open: from a free end
        if len(ks) == 1 and not used[ks[0]]:
            out.append(walk(ks[0], pt))
    for k in range(len(seg)):               # closed loops left
        if not used[k]:
            out.append(walk(k, key(seg[k, :2])))
    return out


def distance(points, loop):
    """Distance of each point (n, 2) to the polyline loop (m, 2)."""
    a, b = loop[:-1], loop[1:]
    ab = b - a
    l2 = np.maximum((ab ** 2).sum(1), 1e-30)
    out = np.empty(len(points))
    for i, q in enumerate(np.asarray(points, float)):
        t = np.clip(((q - a) * ab).sum(1) / l2, 0.0, 1.0)
        out[i] = np.min(np.hypot(*(a + t[:, None] * ab - q).T))
    return out


def offset(loop, d):
    """The closed loop moved by d along its normal, away from its inside."""
    p = np.asarray(loop, float)
    if np.allclose(p[0], p[-1]):
        p = p[:-1]
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1)
                        - p[:, 1] * np.roll(p[:, 0], -1))
    t = np.roll(p, -1, 0) - np.roll(p, 1, 0)
    n = np.column_stack((t[:, 1], -t[:, 0]))
    n /= np.maximum(np.hypot(*n.T), 1e-30)[:, None]
    if area < 0:                            # clockwise: outward is left
        n = -n
    return p + d * n
