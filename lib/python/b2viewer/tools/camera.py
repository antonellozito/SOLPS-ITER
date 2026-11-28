"""A pinhole camera looking at the plasma of the run, toroidally symmetric:
the rays of its pixels in x, y, z (x = R cos phi, y = R sin phi, z = Z),
the first wall each ray meets and the line integral of a quantity along
the ray up to it.

The wall is the EIRENE wall of the run (b2plot wall label ewsurf: the
EIRENE surface of each element, fort.44 isrftype: its type ILIIN) turned
around the axis, each element a cone, a cylinder or a plane annulus. Rays
stop at the real walls (ILIIN 1, reflecting, and the absorbing surfaces,
ILIIN 2, but the core boundary: the absorbing surface closed around the
plasma) and cross the transparent ones (ILIIN 0 or below: the faces of the
B2.5 grid facing the void, tally surfaces); a real wall made
semi-transparent by EIRENE (TRANSP of its surface model or card, from
either side) lets the rays through with that fraction. Outside the B2.5
cells the quantity is zero (no plasma).

A pixel can take several rays spread evenly over it (samples x samples),
their integrals averaged. The image of a field linear in the triangles of
a triangulation is a linear map of its node values: matrix() gives its
weights, and the length of the rays of each pixel in each triangle."""

from dataclasses import dataclass

import numpy as np

STEP = 2e-3                     # m between the samples along a ray
CHUNK = 512                     # rays per block of the wall search


@dataclass
class Camera:
    """position and target (R, Z in m, phi in degrees): the pinhole and the
    point seen at the centre of the image; roll (degrees) turns the image
    about the line of sight; fov the horizontal field of view (degrees);
    nx, ny the pixels."""
    position: tuple = (2.5, 0.0, 0.0)
    target: tuple = (1.6, -1.0, 0.0)
    roll: float = 0.0
    fov: float = 60.0
    nx: int = 160
    ny: int = 120


def xyz(r, z, phi):
    """x, y, z of points (R, Z, phi in degrees)."""
    p = np.radians(np.asarray(phi, float))
    r = np.asarray(r, float)
    return np.stack(np.broadcast_arrays(r * np.cos(p), r * np.sin(p),
                                        np.asarray(z, float)), axis=-1)


def frame(cam):
    """Origin and the unit vectors forward, right, up of the camera."""
    o = xyz(*cam.position)
    f = xyz(*cam.target) - o
    norm = np.linalg.norm(f)
    if norm == 0:
        raise ValueError("the camera looks at its own position")
    f = f / norm
    ref = np.array([0.0, 0.0, 1.0]) if abs(f[2]) < 0.999 else \
        np.array([1.0, 0.0, 0.0])
    right = np.cross(f, ref)
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    a = np.radians(cam.roll)
    right, up = (np.cos(a) * right + np.sin(a) * up,
                 -np.sin(a) * right + np.cos(a) * up)
    return o, f, right, up


def rays(cam, samples=1):
    """(ny * nx * samples^2, 3) unit vectors of the rays of the pixels,
    samples x samples spread evenly over each pixel, those of a pixel
    together, the pixels row by row from the top."""
    o, f, right, up = frame(cam)
    w = np.tan(np.radians(cam.fov) / 2.0)
    h = w * cam.ny / cam.nx
    off = (np.arange(samples) + 0.5) / samples
    u = (2.0 * (np.arange(cam.nx)[:, None] + off) / cam.nx - 1.0) * w
    v = (1.0 - 2.0 * (np.arange(cam.ny)[:, None] + off) / cam.ny) * h
    d = f + u[None, :, None, :, None] * right + \
        v[:, None, :, None, None] * up      # (ny, nx, s, s, 3)
    d = d.reshape(-1, 3)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def directions(cam):
    """(ny, nx, 3) unit vectors of the rays of the pixel centres (row 0 at
    the top)."""
    return rays(cam).reshape(cam.ny, cam.nx, 3)


def classify(surface, types, segments):
    """Stopping mask of the wall elements: surface (element -> EIRENE
    surface, 1-based, 0 none), types (ILIIN of the surfaces, fort.44
    isrftype), segments (n, 4) R1, Z1, R2, Z2. Real walls stop the rays;
    transparent surfaces and the core boundary (an absorbing surface whose
    elements close on themselves) do not."""
    surface = np.asarray(surface, int)
    types = np.asarray(types, int)
    seg = np.asarray(segments, float).reshape(-1, 4)
    kind = np.where((surface > 0) & (surface <= len(types)),
                    types[np.clip(surface - 1, 0, max(len(types) - 1, 0))],
                    1)          # no surface: a wall element of B2.5
    stop = kind >= 1
    for s in np.unique(surface[kind == 2]):
        on = surface == s
        ends = np.round(np.vstack((seg[on, :2], seg[on, 2:])), 6)
        _, count = np.unique(ends, axis=0, return_counts=True)
        if np.all(count == 2):              # closed: the core boundary
            stop[on] = False
    return stop, kind


def _crossings(origin, d, seg):
    """(n, m, 3) distances along the rays d (n, 3) from origin to their
    crossings of the surfaces of revolution of seg (m, 4): the two of the
    cone (or cylinder) and the one of the plane annulus; inf where
    none."""
    r1, z1, r2, z2 = seg.T
    dz, dr = z2 - z1, r2 - r1
    ox, oy, oz = origin
    flat = np.abs(dz) <= 1e-12 * np.maximum(np.abs(dr), 1e-300)
    k = np.where(flat, 0.0, dr / np.where(flat, 1.0, dz))
    r0 = r1 - k * z1                        # cone: R = r0 + k z
    eps = 1e-9
    dx, dy, dzr = d[:, 0:1], d[:, 1:2], d[:, 2:3]
    rr = r0[None, :] + k[None, :] * oz
    a = dx ** 2 + dy ** 2 - (k ** 2)[None, :] * dzr ** 2
    b = 2.0 * (ox * dx + oy * dy - k[None, :] * dzr * rr)
    c = ox ** 2 + oy ** 2 - rr ** 2
    out = np.full(a.shape + (3,), np.inf)
    with np.errstate(invalid="ignore", divide="ignore"):
        disc = b * b - 4.0 * a * c
        sq = np.sqrt(np.where(disc >= 0, disc, np.nan))
        lin = np.abs(a) < 1e-14
        for n, sign in enumerate((-1.0, 1.0)):
            tt = np.where(lin, -c / b, (-b + sign * sq) / (2.0 * a))
            zt = oz + tt * dzr
            s = (zt - z1[None, :]) / np.where(flat, 1.0, dz)[None, :]
            rcone = r0[None, :] + k[None, :] * zt
            ok = (tt > eps) & (s >= 0) & (s <= 1) & (rcone >= 0) & \
                ~flat[None, :] & np.isfinite(tt)
            out[..., n] = np.where(ok, tt, np.inf)
        tp = (z1[None, :] - oz) / dzr                    # planes z = z1
        rp = np.hypot(ox + tp * dx, oy + tp * dy)
        lo, hi = np.minimum(r1, r2)[None, :], np.maximum(r1, r2)[None, :]
        ok = flat[None, :] & (tp > eps) & (rp >= lo) & (rp <= hi) & \
            np.isfinite(tp)
        out[..., 2] = np.where(ok, tp, np.inf)
    return out


def hits(origin, dirs, segments):
    """Distance along each ray (dirs (n, 3), unit) from origin to its first
    crossing of the surfaces of revolution of segments (m, 4), and the
    element crossed (-1: none, distance inf)."""
    seg = np.asarray(segments, float).reshape(-1, 4)
    n = len(dirs)
    best = np.full(n, np.inf)
    which = np.full(n, -1)
    if not len(seg):
        return best, which
    for a0 in range(0, n, CHUNK):
        t = _crossings(origin, dirs[a0:a0 + CHUNK], seg).min(axis=2)
        j = np.argmin(t, axis=1)
        tmin = t[np.arange(len(t)), j]
        best[a0:a0 + CHUNK] = tmin
        which[a0:a0 + CHUNK] = np.where(np.isfinite(tmin), j, -1)
    return best, which


def passes(origin, dirs, segments, trans, limit):
    """The crossings of the semi-transparent elements (segments (m, 4),
    trans (m, 2): EIRENE's TRANSP of their surface, from the side of the
    normal (Z2 - Z1, R1 - R2) and from the other) before limit along each
    ray: a list per ray of (distances, transmissions), sorted."""
    seg = np.asarray(segments, float).reshape(-1, 4)
    out = [None] * len(dirs)
    if not len(seg):
        return out
    nr, nz = seg[:, 3] - seg[:, 1], seg[:, 0] - seg[:, 2]
    for a0 in range(0, len(dirs), CHUNK):
        d = dirs[a0:a0 + CHUNK]
        t = _crossings(origin, d, seg)
        for i in np.flatnonzero(np.any(t < limit[a0:a0 + len(d), None, None],
                                       axis=(1, 2))):
            m, kk = np.nonzero(t[i] < limit[a0 + i])
            ti = t[i][m, kk]
            p = origin + ti[:, None] * d[i]
            rad = np.hypot(p[:, 0], p[:, 1])
            vr = (p[:, 0] * d[i, 0] + p[:, 1] * d[i, 1]) / np.maximum(rad,
                                                                      1e-300)
            side = nr[m] * vr + nz[m] * d[i, 2]
            f = np.where(side > 0, trans[m, 0], trans[m, 1])
            o = np.argsort(ti)
            out[a0 + i] = (ti[o], f[o])
    return out


def _samples(origin, dirs, length, step=STEP, box=None, cuts=None):
    """Blocks of the samples along the rays (dirs from origin, over length:
    finite, inf counts as 0): midpoints every step (m), the last of each ray
    in the middle of its remainder; (ray, R, Z, weight) of those inside box
    (rmin, rmax, zmin, zmax), weight the length of the sample times the
    transmission of the semi-transparent surfaces crossed before it (cuts:
    per ray None or (distances, transmissions))."""
    n = len(dirs)
    length = np.where(np.isfinite(length), length, 0.0)
    counts = np.ceil(length / step).astype(int)
    for a0 in range(0, n, 256):
        sl = slice(a0, min(n, a0 + 256))
        m = counts[sl].max(initial=0)
        if m == 0:
            continue
        k = np.arange(m)[None, :]
        t = (k + 0.5) * step
        ds = np.full(t.shape, step)
        last = counts[sl][:, None] - 1
        t = np.where(k == last, last * step + 0.5 * (length[sl][:, None] -
                                                       last * step), t)
        ds = np.where(k == last, length[sl][:, None] - last * step, ds)
        use = k <= last
        p = origin[None, None, :] + t[..., None] * dirs[sl][:, None, :]
        r, z = np.hypot(p[..., 0], p[..., 1]), p[..., 2]
        if box is not None:
            use &= (r >= box[0]) & (r <= box[1]) & (z >= box[2]) & \
                (z <= box[3])
        if cuts is not None:
            for i in range(sl.start, sl.stop):
                if cuts[i] is not None:
                    tc, fc = cuts[i]
                    w = np.concatenate(([1.0], np.cumprod(fc)))
                    ds[i - sl.start] *= w[np.searchsorted(tc,
                                                          t[i - sl.start])]
        ray = np.nonzero(use)[0]
        yield a0 + ray, r[use], z[use], ds[use]


def integrate(origin, dirs, length, values_at, step=STEP, box=None,
              cuts=None):
    """Line integral of a field along each ray (the samples of _samples),
    the field given by values_at(r, z) (NaN outside the cells: 0)."""
    out = np.zeros(len(dirs))
    for ray, r, z, w in _samples(origin, dirs, length, step, box, cuts):
        vals = np.asarray(values_at(r, z), float)
        out += np.bincount(ray, np.where(np.isfinite(vals), vals, 0.0) * w,
                           minlength=len(dirs))
    return out


def _trace(cam, segments, stop, trans, samples):
    """The rays of the camera up to the first opaque wall: origin, the
    rays (as rays()), their lengths, the semi-transparent surfaces they
    cross, and for the pixel centres the distance to the wall and the
    element seen (-1: none)."""
    origin = xyz(*cam.position)
    d = rays(cam, samples)
    seg = np.asarray(segments, float).reshape(-1, 4)
    trans = np.zeros((len(seg), 2)) if trans is None else \
        np.asarray(trans, float)
    semi = np.asarray(stop, bool) & (trans.max(axis=1) > 0)
    idx = np.flatnonzero(np.asarray(stop, bool) & ~semi)
    t, j = hits(origin, d, seg[idx])
    cuts = passes(origin, d, seg[semi], trans[semi], t) if semi.any() \
        else None
    if samples > 1:
        tc, j = hits(origin, rays(cam), seg[idx])
    else:
        tc = t
    elem = np.where(j >= 0, idx[np.maximum(j, 0)], -1)
    return origin, d, t, cuts, tc, elem


def image(cam, segments, stop, values_at, per_sr=True, step=STEP,
          box=None, trans=None, samples=1):
    """The camera image of a field: (ny, nx) line integrals up to the first
    opaque wall (divided by 4 pi with per_sr; the mean of samples x samples
    rays per pixel), the distance to it and the wall element seen at the
    pixel centre (-1: none). trans (n, 2): EIRENE's TRANSP of the surface
    of each element (semi-transparent where not 0: the rays go on through
    it, weighted)."""
    origin, d, t, cuts, tc, elem = _trace(cam, segments, stop, trans,
                                          samples)
    val = integrate(origin, d, t, values_at, step, box, cuts)
    val = val.reshape(-1, samples * samples).mean(axis=1)
    if per_sr:
        val = val / (4.0 * np.pi)
    shape = (cam.ny, cam.nx)
    return val.reshape(shape), tc.reshape(shape), elem.reshape(shape)


def _summed(rows, cols, vals, ncols):
    """(rows, cols, sums of vals) of the distinct pairs."""
    key, inv = np.unique(rows.astype(np.int64) * ncols + cols,
                         return_inverse=True)
    return key // ncols, key % ncols, np.bincount(inv.ravel(), vals.ravel())


def matrix(cam, segments, stop, tri, finder, per_sr=True, step=STEP,
           box=None, trans=None, samples=1, groups=None):
    """The image as a linear map of a field linear in the triangles of tri
    (a matplotlib Triangulation; finder its TriFinder, -1 in the triangles
    left out), as LinearTriInterpolator and image() take it: pixel (row
    by row from the top), node, weight, the image the sum of weight x
    node value per pixel; and pixel, group, length of the rays in the
    triangles of the group (groups: the group of each triangle, default
    the triangle). Both the mean over the rays of a pixel, divided by 4 pi
    with per_sr."""
    origin, d, t, cuts, _, _ = _trace(cam, segments, stop, trans, samples)
    ns = samples * samples
    x, y, corner = np.asarray(tri.x), np.asarray(tri.y), tri.triangles
    groups = np.arange(len(corner)) if groups is None else \
        np.asarray(groups, int)
    ng = int(groups.max(initial=0)) + 1
    nodes, cells = [], []
    for ray, r, z, w in _samples(origin, d, t, step, box, cuts):
        it = np.asarray(finder(r, z))
        ok = it >= 0
        ray, r, z, w, it = ray[ok], r[ok], z[ok], w[ok], it[ok]
        v = corner[it]
        x0, x1, x2 = x[v[:, 0]], x[v[:, 1]], x[v[:, 2]]
        y0, y1, y2 = y[v[:, 0]], y[v[:, 1]], y[v[:, 2]]
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        l0 = ((y1 - y2) * (r - x2) + (x2 - x1) * (z - y2)) / det
        l1 = ((y2 - y0) * (r - x2) + (x0 - x2) * (z - y2)) / det
        lam = np.stack((l0, l1, 1.0 - l0 - l1), axis=1)
        pix = ray // ns
        nodes.append(_summed(np.repeat(pix, 3), v.ravel(),
                             (lam * w[:, None]).ravel(), len(x)))
        cells.append(_summed(pix, groups[it], w, ng))
    scale = 1.0 / ns / (4.0 * np.pi if per_sr else 1.0)
    out = []
    for parts, n in ((nodes, len(x)), (cells, ng)):
        if not parts:
            out.append((np.zeros(0, int), np.zeros(0, int), np.zeros(0)))
            continue
        rows, cols, vals = (np.concatenate(a) for a in zip(*parts))
        rows, cols, vals = _summed(rows, cols, vals, n)
        out.append((rows, cols, vals * scale))
    return out[0], out[1]


def apply(weights, values, npix):
    """The image (npix values) of node values by the weights of matrix()
    (non-finite values counted as 0)."""
    rows, cols, vals = weights
    v = np.asarray(values, float)[cols]
    return np.bincount(rows, vals * np.where(np.isfinite(v), v, 0.0),
                       minlength=npix)
