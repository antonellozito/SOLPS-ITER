"""PyVista meshes of the 3D view, from shapes of the poloidal plane
(tools/revolve): surfaces of revolution over the sector (with values along
them), filled polygons and outlines on planes, the triangles of a poloidal
plane with the values at their nodes, toroidal rings, the strip of the
wall elements with their values; the cut at heights: the part of a mesh
between two heights, flat rings and arcs at a height."""

import numpy as np
import pyvista as pv

from ..tools import revolve


def _faces(f):
    f = np.asarray(f, int).reshape(len(f), -1)
    return np.hstack([np.full((len(f), 1), f.shape[1]), f]).ravel()


def _merge(parts):
    """One PolyData of (vertices, faces) parts, None if empty."""
    parts = [(v, f) for v, f in parts if len(v) and len(f)]
    if not parts:
        return None
    off = np.cumsum([0] + [len(v) for v, _ in parts])
    return pv.PolyData(np.vstack([v for v, _ in parts]),
                       np.concatenate([_faces(f + o) for (_, f), o in
                                       zip(parts, off)]))


def surface(polys, phi0, phi1, closed=False):
    """Surfaces of revolution of the polylines over [phi0, phi1]."""
    return _merge([revolve.surface(p, phi0, phi1, closed=closed)
                   for p in polys if len(p) > 1])


def shell(line, values, phi0, phi1):
    """The surface of revolution of a polyline with the values at its
    points (point data "values", the same all around)."""
    v, f = revolve.surface(line, phi0, phi1)
    m = _merge([(v, f)])
    if m is not None:
        m.point_data["values"] = np.tile(np.asarray(values, float),
                                         len(v) // len(line))
    return m


def plane(points, triangles, values, rho=None, band=None):
    """The triangles of the poloidal plane (x: R, y: Z) with the values at
    their nodes (point data "values"), cut along the flux surfaces to the
    band (lo, hi) of rho_p (rho, at the nodes) if given."""
    m = pv.PolyData(np.column_stack((points, np.zeros(len(points)))),
                    _faces(triangles))
    m.point_data["values"] = np.asarray(values, float)
    if band is not None and rho is not None:
        m.point_data["rho"] = np.asarray(rho, float)
        m = m.clip_scalar(scalars="rho", value=band[1], invert=True)
        if m.n_points:
            m = m.clip_scalar(scalars="rho", value=band[0], invert=False)
        if m.n_points:
            m = m.triangulate()
    return m


def field(plane2d, phi):
    """A plane of the poloidal plane (plane) on the plane at phi."""
    m = plane2d.copy()
    m.points = revolve.on_plane(plane2d.points[:, :2], phi)
    return m


def boundary(plane2d):
    """[(points (n, 2), values (n,))] of the boundary loops of a plane of
    the poloidal plane (plane)."""
    if plane2d.n_points == 0:
        return []
    e = plane2d.extract_feature_edges(boundary_edges=True,
                                      non_manifold_edges=False,
                                      feature_edges=False,
                                      manifold_edges=False)
    if e.n_cells == 0:
        return []
    ends = e.lines.reshape(-1, 3)[:, 1:]
    pts = np.asarray(e.points[:, :2], float)
    at = {tuple(p): v for p, v in zip(np.round(pts, 9),
                                      e.point_data["values"])}
    out = []
    for loop in revolve.loops(np.hstack((pts[ends[:, 0]],
                                         pts[ends[:, 1]]))):
        if len(loop) > 2:
            out.append((loop, np.array([at.get(tuple(p), np.nan)
                                        for p in np.round(loop, 9)])))
    return out


def _open(p):
    p = np.asarray(p, float)
    return p[:-1] if len(p) > 2 and np.allclose(p[0], p[-1]) else p


def caps(polys, phis):
    """The closed polygons filled on the planes at the angles phis."""
    parts = []
    for p in polys:
        p = _open(p)
        t = revolve.earclip(p)
        if len(t):
            parts += [(revolve.on_plane(p, phi), t) for phi in phis]
    return _merge(parts)


def polylines(lines3d):
    """PolyData of polylines (list of (n, 3) arrays)."""
    lines3d = [np.asarray(q, float) for q in lines3d if len(q) > 1]
    if not lines3d:
        return None
    off = np.cumsum([0] + [len(q) for q in lines3d])
    cells = np.concatenate([np.concatenate(([len(q)],
                                            np.arange(len(q)) + o))
                            for q, o in zip(lines3d, off)])
    return pv.PolyData(np.vstack(lines3d), lines=cells)


def outlines(polys, phis, closed=True):
    """The polylines (closed: joined to their start) on the planes at
    the angles phis."""
    out = []
    for p in polys:
        p = _open(p) if closed else np.asarray(p, float)
        q = np.vstack((p, p[:1])) if closed else p
        out += [revolve.on_plane(q, phi) for phi in phis]
    return polylines(out)


def segments(seg, phis):
    """Segments (n, 4) (R1, Z1, R2, Z2) on the planes at phis."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    if not len(seg):
        return None
    pts, cells = [], []
    off = 0
    for phi in phis:
        a, b = revolve.on_plane(seg[:, :2], phi), \
            revolve.on_plane(seg[:, 2:], phi)
        pts += [a, b]
        k = np.arange(len(seg)) + off
        cells.append(np.column_stack((np.full(len(seg), 2), k,
                                      k + len(seg))).ravel())
        off += 2 * len(seg)
    return pv.PolyData(np.vstack(pts), lines=np.concatenate(cells))


def ring(r, z, phi0, phi1):
    n, e = revolve.ring(r, z, phi0, phi1)
    return polylines([n if not revolve.full(phi0, phi1) else
                      np.vstack((n, n[:1]))])


def wall_strip(seg, values, phi0, phi1, normals, lifts):
    """The wall elements (segments (n, 4)) turned around the axis, each
    with its value (cell data "values", none if values is None), moved by
    its lift along its normal (normals (n, 2), towards the plasma)."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    values = np.zeros(len(seg)) if values is None else \
        np.asarray(values, float)
    m = revolve.nphi(phi0, phi1)
    phis = np.linspace(phi0, phi1, m + 1)
    parts, vals = [], []
    for s, v, n, h in zip(seg, values, np.asarray(normals, float),
                          np.asarray(lifts, float)):
        d = n * h
        p = np.vstack((s[:2] + d, s[2:] + d))
        verts = np.vstack([revolve.on_plane(p, f) for f in phis])
        k = np.arange(m) * 2
        quads = np.column_stack((k, k + 1, k + 3, k + 2))
        parts.append((verts, quads))
        vals.append(np.full(m, v))
    mesh = _merge(parts)
    if mesh is not None:
        mesh.cell_data["values"] = np.concatenate(vals)
    return mesh


def zclip(mesh, lo, hi):
    """The part of mesh between the heights lo and hi (None: no limit)."""
    if mesh is not None and hi is not None and mesh.n_points:
        mesh = mesh.clip(normal="z", origin=(0.0, 0.0, hi), invert=True)
    if mesh is not None and lo is not None and mesh.n_points:
        mesh = mesh.clip(normal="z", origin=(0.0, 0.0, lo), invert=False)
    return mesh


def crossings(line, z):
    """Radii where the polyline (n, 2) crosses the height z."""
    line = np.asarray(line, float)
    a, b = line[:-1], line[1:]
    da, db = a[:, 1] - z, b[:, 1] - z
    k = np.flatnonzero((da * db < 0) | ((da == 0) & (db != 0)))
    f = da[k] / (da[k] - db[k])
    return a[k, 0] + f * (b[k, 0] - a[k, 0])


def annuli(rings, z, phi0, phi1):
    """Flat rings at the height z over the sector, each (r0, r1, v0, v1):
    between the radii r0 and r1, the values v0, v1 at them (point data
    "values", linear between)."""
    m = revolve.nphi(phi0, phi1)
    phis = np.linspace(phi0, phi1, m + 1)
    c, s = np.cos(phis), np.sin(phis)
    parts, vals = [], []
    for r0, r1, v0, v1 in rings:
        pts = np.column_stack((np.concatenate((r0 * c, r1 * c)),
                               np.concatenate((r0 * s, r1 * s)),
                               np.full(2 * len(phis), z)))
        k = np.arange(m)
        n = len(phis)
        parts.append((pts, np.column_stack((k, k + 1, n + k + 1, n + k))))
        vals.append(np.concatenate((np.full(n, v0), np.full(n, v1))))
    mesh = _merge(parts)
    if mesh is not None:
        mesh.point_data["values"] = np.concatenate(vals)
    return mesh


def arcs(radii, z, phi0, phi1):
    """Toroidal arcs at the height z over the sector, one per radius."""
    m = revolve.nphi(phi0, phi1)
    phis = np.linspace(phi0, phi1, m + 1)
    return polylines([np.column_stack((r * np.cos(phis), r * np.sin(phis),
                                       np.full(len(phis), z)))
                      for r in radii])
