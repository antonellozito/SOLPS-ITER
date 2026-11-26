"""Magnetic field lines of a run, for the 2D and 3D views: the unit vector
along B (cvEb of b2fgmtry, else bb of a classical one) on a fine (R, Z)
grid over the B2.5 grid; a field line traced from a point, first
anticlockwise in the 2D plot: one poloidal turn back to the point on a
closed flux surface, else both ways to the boundary of the grid (a target
or its edge), with its connection lengths (kept on its flux surface with
the psi of the B2.5 grid vertices, else the psi map of rzpsi.dat,
against the drift of the interpolation across the surfaces); the
directions of B and of the plasma current.

Toroidal angle: B2.5 and EIRENE count it clockwise seen from above (the
Cartesian Z of cvEb, COCOS 4, solps.tex "Sign conventions"); in the 2D
view (axis on the left) that is towards the viewer. The 3D view uses the
usual anticlockwise angle, the opposite."""

import math

import numpy as np

from ...run_plots.geometry import GEOMETRY
from ..plot.scalar import node_values
from . import cellfiles, inspect

GRID = 900                  # grid points along the longer side
STEP = 0.004                # poloidal step (m)
MAX_DS = 0.05               # largest step along the field line (m)
MAX_STEPS = 400000
MAX_LEN = 5000.0            # longest field line each way (m)


class BField:
    """Unit vector along B (R, Z and toroidal Cartesian components) on a
    regular grid (nan outside the B2.5 grid)."""

    def __init__(self, run, tri, b):
        g = run.geometry
        nodes = [node_values(tri, b[k][g.tri_cell]) for k in range(3)]
        x0, x1, y0, y1 = g.bbox
        w, h = x1 - x0, y1 - y0
        nx = max(int(GRID * w / max(w, h)), 2)
        ny = max(int(GRID * h / max(w, h)), 2)
        self.xs, self.ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
        X, Y = np.meshgrid(self.xs, self.ys)
        it = np.asarray(g.finder(X.ravel(), Y.ravel()))
        psin = getattr(g, "psin", None)
        own = psin is not None and len(psin) == len(g.vx) and \
            np.isfinite(psin).all()
        vals = _barycentric(g.vx, g.triangles, it, X.ravel(), Y.ravel(),
                            nodes + ([np.asarray(psin, float)] if own else []))
        self.f = [v.reshape(X.shape) for v in vals[:3]]
        self.dx = self.xs[1] - self.xs[0]
        self.dy = self.ys[1] - self.ys[0]
        self.size = max(w, h)
        self.psi = None                 # psi on the grid and its gradient
        if own:
            p = vals[3].reshape(X.shape)
            gz, gr = np.gradient(p, self.dy, self.dx)
            self.psi = [p, gr, gz]
        self.psimap = run.psimap        # without vertex psi: rzpsi.dat

    def at(self, r, z):
        """(bR, bZ, bT) at the point, None outside."""
        return self._interp(self.f, r, z)

    def _interp(self, arrays, r, z):
        """Bilinear values of the gridded arrays at the point, from the
        corners inside the grid (None when mostly outside)."""
        fx = (r - self.xs[0]) / self.dx
        fy = (z - self.ys[0]) / self.dy
        if not (0.0 <= fx <= len(self.xs) - 1 and
                0.0 <= fy <= len(self.ys) - 1):
            return None
        i = min(int(fx), len(self.xs) - 2)
        j = min(int(fy), len(self.ys) - 2)
        a, b = fx - i, fy - j
        corners = ((j, i, (1 - a) * (1 - b)), (j, i + 1, a * (1 - b)),
                   (j + 1, i, (1 - a) * b), (j + 1, i + 1, a * b))
        f0 = arrays[0]
        inside = [(jj, ii, w) for jj, ii, w in corners
                  if math.isfinite(f0[jj, ii])]
        wsum = sum(w for _, _, w in inside)
        if wsum < 0.25:                 # mostly outside the grid
            return None
        return [sum(f[jj, ii] * w for jj, ii, w in inside) / wsum
                for f in arrays]

    def psi_at(self, r, z):
        """psi and its gradient at the point (the vertex psi of the grid,
        else psiN of rzpsi.dat), None outside or without either."""
        if self.psi is not None:
            out = self._interp(self.psi, r, z)
            return None if out is None or not all(
                math.isfinite(x) for x in out) else out
        m = self.psimap
        if m is None:
            return None
        rr, zz = m.r, m.z
        i = int(np.searchsorted(rr, r)) - 1
        j = int(np.searchsorted(zz, z)) - 1
        if i < 0 or j < 0 or i >= len(rr) - 1 or j >= len(zz) - 1:
            return None
        hr, hz = rr[i + 1] - rr[i], zz[j + 1] - zz[j]
        u, v = (r - rr[i]) / hr, (z - zz[j]) / hz
        p = m.psin
        a, b = p[j, i], p[j, i + 1]
        c, d = p[j + 1, i], p[j + 1, i + 1]
        f = (1 - u) * (1 - v) * a + u * (1 - v) * b + (1 - u) * v * c + \
            u * v * d
        fr = ((1 - v) * (b - a) + v * (d - c)) / hr
        fz = ((1 - u) * (c - a) + u * (d - b)) / hz
        return f, fr, fz

    def at_many(self, r, z):
        """Arrays (bR, bZ, bT) at the points (nan outside)."""
        from .vector3d import bilinear
        return bilinear(self.xs, self.ys, self.f, np.asarray(r, float),
                        np.asarray(z, float))


def _barycentric(vx, tris, it, x, y, nodes):
    out = [np.full(len(x), np.nan) for _ in nodes]
    ok = it >= 0
    t = tris[it[ok]]
    p0, p1, p2 = vx[t[:, 0]], vx[t[:, 1]], vx[t[:, 2]]
    det = ((p1[:, 1] - p2[:, 1]) * (p0[:, 0] - p2[:, 0]) +
           (p2[:, 0] - p1[:, 0]) * (p0[:, 1] - p2[:, 1]))
    det = np.where(np.abs(det) > 0, det, np.nan)
    xx, yy = x[ok], y[ok]
    l0 = ((p1[:, 1] - p2[:, 1]) * (xx - p2[:, 0]) +
          (p2[:, 0] - p1[:, 0]) * (yy - p2[:, 1])) / det
    l1 = ((p2[:, 1] - p0[:, 1]) * (xx - p2[:, 0]) +
          (p0[:, 0] - p2[:, 0]) * (yy - p2[:, 1])) / det
    l2 = 1.0 - l0 - l1
    for o, v in zip(out, nodes):
        o[ok] = l0 * v[t[:, 0]] + l1 * v[t[:, 1]] + l2 * v[t[:, 2]]
    return out


def cell_field(run):
    """Unit vector along B (bR, bZ, bT: R, Z and toroidal Cartesian
    components) at the cells of the plot (rows of run.geometry): cvEb of
    the unstructured geometry of b2fgmtry, else bb along the x direction
    of the cell corners crx, cry of a classical b2fgmtry (bb x along
    increasing ix); None without either. Read once per run."""
    b = getattr(run, "cell_b", None)
    if b is not None:
        return b if len(b) else None
    g = run.geometry
    geo = inspect.files(run)[0]
    eb = None if geo is None else geo.table(
        "cvEb", len(np.asarray(geo.get("cvX"))))
    if eb is not None:
        b = np.asarray(eb, float)[:, g.cells - 1]
    else:
        b = _classical(run)
    run.cell_b = b if b is not None else ()
    return b


def _classical(run):
    g = run.geometry
    path = next((p for p in (cellfiles.find(run.rundir, n)
                             for n in GEOMETRY) if p), None)
    if path is None or not g.classical:
        return None
    f = cellfiles.GeometryFile(path)
    nx, ny = f.get("nx"), f.get("ny")
    if nx is None or ny is None or not len(nx) or not len(ny):
        return None
    nx, ny = int(nx[0]), int(ny[0])
    n = (nx + 2) * (ny + 2)
    bb, crx, cry = (f.table(k, n) for k in ("bb", "crx", "cry"))
    if bb is None or crx is None or cry is None or len(bb) < 4:
        return None
    ix, iy = np.asarray(g.ix), np.asarray(g.iy)
    ok = (ix >= -1) & (ix <= nx) & (iy >= -1) & (iy <= ny)
    k = np.where(ok, (ix + 1) + (iy + 1) * (nx + 2), 0)
    ex = 0.5 * (crx[1] + crx[3] - crx[0] - crx[2])[k]
    ey = 0.5 * (cry[1] + cry[3] - cry[0] - cry[2])[k]
    e = np.hypot(ex, ey)
    with np.errstate(invalid="ignore", divide="ignore"):
        btot = np.where(ok & (e > 0) & (bb[3][k] > 0), bb[3][k], np.nan)
        bp = bb[0][k] / btot / e
        return np.array([bp * ex, bp * ey, bb[2][k] / btot])


def field_of(run, plot):
    """The BField of the run, built once; None without the field."""
    f = getattr(run, "bfield", None)
    if f is None:
        b = cell_field(run)
        if b is None:
            return None
        f = run.bfield = BField(run, plot.tri, b)
    return f


class FieldLine:
    """A field line traced from (r0, z0): points (R, Z, toroidal angle
    clockwise seen from above, distance along the line from the start,
    negative against B) from its end against B to its end along B; the
    lengths to them, whether each is on the boundary of the grid (a
    target or its edge; else the maximum length stopped it), the names
    of the targets there (None: none); closed: one poloidal turn, from
    the start round to it anticlockwise in the 2D plot (only one half).
    ccw: +1 when the points go anticlockwise in the 2D plot, else -1."""

    def __init__(self, r0, z0, back, fwd, ccw):
        self.start = (r0, z0)
        b = np.asarray(back[::-1], float)
        f = np.asarray(fwd, float)
        self.points = np.vstack((b[:-1], f)) if len(b) > 1 else f
        self.lengths = (abs(float(back[-1][3])), abs(float(fwd[-1][3])))
        self.hits = (back.hit, fwd.hit)
        self.ends = (tuple(back[-1][:2]), tuple(fwd[-1][:2]))
        self.closed = back.closed or fwd.closed
        self.ccw = ccw
        self.names = (None, None)

    def anticlockwise(self):
        """(points, start index) in the anticlockwise order of the 2D
        plot (a closed line from its start)."""
        p = self.points if self.ccw > 0 else self.points[::-1]
        return p, int(np.abs(p[:, 3]).argmin())

    def turns(self, k):
        """Toroidal turns from the start to end k (0 against B)."""
        p = self.points
        i0 = int(np.abs(p[:, 3]).argmin())
        return abs((p[0, 2] if k == 0 else p[-1, 2]) - p[i0, 2]) / \
            (2.0 * math.pi)


class _Half(list):
    hit = False
    closed = False


def _trace(bf, r, z, sign, close=False):
    """One way from (r, z) along sign * B: list of (R, Z, phi, s), its
    attribute hit True when the line left the grid (a target or the edge
    of the grid), closed when (close) it came back round to the start
    (one poloidal turn, ended there)."""
    out = _Half()
    r0, z0 = r, z
    phi, s, spol = 0.0, 0.0, 0.0
    out.append((r, z, phi, s))
    p0 = bf.psi_at(r, z)
    p0 = None if p0 is None else p0[0]
    b0 = bf.at(r, z)
    t0 = (sign * b0[0], sign * b0[1]) if b0 is not None else (0.0, 0.0)
    near = 0.02 * bf.size               # back at the start within this

    def keep(r, z):
        """(r, z) moved back onto the flux surface of the start."""
        if p0 is None:
            return r, z
        q = bf.psi_at(r, z)
        if q is None:
            return r, z
        g2 = q[1] * q[1] + q[2] * q[2]
        if g2 <= 0.0:
            return r, z
        k = (p0 - q[0]) / g2
        return r + k * q[1], z + k * q[2]

    def rhs(r, z):
        b = bf.at(r, z)
        if b is None:
            return None
        bp = math.hypot(b[0], b[1])
        if bp <= 1e-12:
            return None
        return (sign * b[0] / bp, sign * b[1] / bp,
                sign * b[2] / (r * bp), 1.0 / bp)
    for _ in range(MAX_STEPS):
        k1 = rhs(r, z)
        if k1 is None:
            out.hit = True
            break
        dl = min(STEP, MAX_DS / k1[3])
        k2 = rhs(r + 0.5 * dl * k1[0], z + 0.5 * dl * k1[1])
        if k2 is None:                  # leaves the grid: bisect the step
            lo, hi = 0.0, dl
            for _ in range(20):
                m = 0.5 * (lo + hi)
                if bf.at(r + m * k1[0], z + m * k1[1]) is None:
                    hi = m
                else:
                    lo = m
            r, z = r + lo * k1[0], z + lo * k1[1]
            phi, s = phi + lo * k1[2], s + lo * k1[3]
            out.append((r, z, phi, sign * s))
            out.hit = True
            break
        rn, zn = keep(r + dl * k2[0], z + dl * k2[1])
        pn, sn = phi + dl * k2[2], s + dl * k2[3]
        spol += dl
        if close and spol > 2.0 * near:
            d0 = (r - r0) * t0[0] + (z - z0) * t0[1]
            d1 = (rn - r0) * t0[0] + (zn - z0) * t0[1]
            if d0 < 0.0 <= d1 and math.hypot(rn - r0, zn - z0) < near:
                f = -d0 / (d1 - d0) if d1 > d0 else 1.0
                out.append((r0, z0, phi + f * (pn - phi),
                            sign * (s + f * (sn - s))))
                out.closed = True
                break
        r, z, phi, s = rn, zn, pn, sn
        out.append((r, z, phi, sign * s))
        if s >= MAX_LEN:
            break
    return out


def trace(bf, r0, z0, bpol_clockwise, run=None):
    """The FieldLine through (r0, z0), None outside the grid: first
    anticlockwise in the 2D plot (bpol_clockwise: the poloidal field goes
    clockwise), one poloidal turn if it comes back to the start (closed),
    else also the other way; the names of the targets at its ends (run
    given)."""
    if bf.at(r0, z0) is None:
        return None
    ccw = -1.0 if bpol_clockwise else 1.0   # along B: anticlockwise
    first = _trace(bf, r0, z0, ccw, close=True)
    if first.closed:
        other = _Half([(r0, z0, 0.0, 0.0)])
    else:
        other = _trace(bf, r0, z0, -ccw)
    back, fwd = (other, first) if ccw > 0 else (first, other)
    line = FieldLine(r0, z0, back, fwd, ccw)
    if run is not None and not line.closed:
        line.names = tuple(end_name(run, e) if h else None
                           for e, h in zip(line.ends, line.hits))
    return line


def end_name(run, end, tol=0.02):
    """Name of the target nearest to an end of a field line (within tol
    times the size of the grid; IL, OL, IU, OU), else None."""
    from .wallprofile import target_names
    best, name, names = None, None, target_names(run)
    size = max(np.ptp(run.geometry.vx, axis=0))
    for key, seg in run.layers.items():
        if not key.startswith("target: ") or seg is None or not len(seg):
            continue
        seg = np.asarray(seg, float).reshape(-1, 4)
        a, b = seg[:, :2], seg[:, 2:]
        d = b - a
        t = np.clip(((end[0] - a[:, 0]) * d[:, 0] + (end[1] - a[:, 1]) *
                     d[:, 1]) / np.maximum((d * d).sum(1), 1e-30), 0, 1)
        dist = np.hypot(a[:, 0] + t * d[:, 0] - end[0],
                        a[:, 1] + t * d[:, 1] - end[1]).min()
        if dist < tol * size and (best is None or dist < best):
            best, name = dist, names.get(key, key[len("target: "):])
    return name


def directions(run):
    """Directions of the field and the plasma current: the sign of the
    toroidal field (+1: clockwise seen from above, towards the viewer of
    the 2D plot), whether the poloidal field goes clockwise around the
    O-point in the 2D plot, the sign of the toroidal plasma current
    (Ampere: the poloidal field goes around it anticlockwise), the
    O-point (of rzpsi.dat, else the middle of the first volume region),
    the middle of the hole of the grid around it and the radius of the
    circle there inside the hole (hole); None without the field."""
    eb = cell_field(run)
    if eb is None:
        return None
    g = run.geometry
    ok = np.isfinite(eb).all(0) & g.visible
    x, y, eb = g.centres[ok, 0], g.centres[ok, 1], eb[:, ok]
    if run.psimap is not None:
        r0, z0 = (float(v) for v in run.psimap.opoint)
    else:
        core = np.asarray(g.region)[ok] == 1
        core = core if core.any() else np.ones(len(x), bool)
        r0, z0 = float(x[core].mean()), float(y[core].mean())
    dx, dy = x - r0, y - z0
    d2 = np.maximum(dx * dx + dy * dy, 1e-12)
    turn = float(np.sum((dy * eb[0] - dx * eb[1]) / d2))
    clockwise = turn > 0
    return dict(btor=float(np.sign(np.sum(eb[2])) or 1.0),
                bpol_clockwise=clockwise, ip=-1.0 if clockwise else 1.0,
                centre=(r0, z0), hole=_hole(g, r0, z0))


def _hole(g, r0, z0, rays=72, steps=300):
    """Middle of the hole of the grid around (r0, z0) (the centroid of
    where rays from there first meet the grid, twice) and the radius of
    a circle there clear of the grid; (r0, z0) and the
    distance to the grid when the point is on the grid."""
    used = g.vx[g.used]
    near = float(np.hypot(used[:, 0] - r0, used[:, 1] - z0).min())
    if int(np.asarray(g.finder(np.array([r0]), np.array([z0])))[0]) >= 0:
        return (r0, z0), near
    size = float(np.ptp(used, axis=0).max())
    a = np.linspace(0.0, 2.0 * np.pi, rays, endpoint=False)
    t = np.linspace(0.0, size, steps)[1:]
    c = np.array([r0, z0])
    for _ in range(2):
        x = c[0] + np.outer(np.cos(a), t)
        y = c[1] + np.outer(np.sin(a), t)
        hit = np.asarray(g.finder(x.ravel(), y.ravel())).reshape(x.shape)
        first = np.argmax(hit >= 0, axis=1)
        ok = (hit >= 0).any(axis=1)
        if ok.sum() < rays // 2:
            return (r0, z0), near
        edge = np.column_stack((x[ok, first[ok]], y[ok, first[ok]]))
        p, q = edge, np.roll(edge, -1, axis=0)  # polygon centroid
        cross = p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1]
        area = cross.sum() / 2.0
        if abs(area) < 1e-12:
            return (r0, z0), near
        c = np.array([((p[:, 0] + q[:, 0]) * cross).sum(),
                      ((p[:, 1] + q[:, 1]) * cross).sum()]) / (6.0 * area)
    radius = float(np.hypot(used[:, 0] - c[0], used[:, 1] - c[1]).min())
    circle = np.linspace(0.0, 2.0 * np.pi, 360, endpoint=False)
    for _ in range(40):                 # the grid edges inside it
        if (np.asarray(g.finder(c[0] + radius * np.cos(circle),
                                c[1] + radius * np.sin(circle))) < 0).all():
            break
        radius *= 0.98
    return (float(c[0]), float(c[1])), radius


def along(points):
    """From the first of the points (R, Z, phi, s) of a field line: the
    length along it ("parallel"), along its projection on the poloidal
    plane ("poloidal") and the toroidal turns ("turns")."""
    p = np.asarray(points, float)
    pol = np.concatenate(([0.0], np.cumsum(np.hypot(np.diff(p[:, 0]),
                                                    np.diff(p[:, 1])))))
    return dict(parallel=np.abs(p[:, 3] - p[0, 3]), poloidal=pol,
                turns=np.abs(p[:, 2] - p[0, 2]) / (2.0 * math.pi))


def to_3d(points, phi0=0.0):
    """Points (R, Z, phi clockwise, s) of a field line starting at the
    angle phi0 of the 3D view (anticlockwise seen from above) in its x,
    y, z."""
    r, z, phi = points[:, 0], points[:, 1], phi0 - points[:, 2]
    return np.column_stack((r * np.cos(phi), r * np.sin(phi), z))
