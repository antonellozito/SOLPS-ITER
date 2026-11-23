"""Where the streamlines of the 2D plot start and the tracers of the 3D
view are born: in proportion to the magnitude of the vector quantity (to
the power WEIGHT), over the field or along a line of the run (the main
separatrix, the midplanes, the targets); or at random along the line
drawn in 2D."""

import numpy as np

from . import revolve

KINDS = (("proportional to the quantity", "quantity"),
         ("on the main separatrix", "separatrix"),
         ("on the midplanes", "midplanes"),
         ("on the targets", "targets"),
         ("random on the line drawn in 2D", "line"))
WEIGHT = 0.5            # "proportional": density as the magnitude to it
LINES = ("separatrix", "midplanes", "targets", "line")


def weight(kind):
    """The power of the magnitude of the density of births of kind."""
    return 0.0 if kind == "line" else WEIGHT


def lines(run, kind, drawn=()):
    """Polylines (R, Z) of a line kind; drawn: the ends of the line drawn
    in 2D."""
    if kind == "line":
        d = np.asarray(drawn, float).reshape(-1, 2)
        return [d] if len(d) > 1 else []
    if kind == "targets":
        seg = [v for k, v in run.layers.items() if k.startswith("target: ")]
        return revolve.chains(np.vstack(seg)) if seg else []
    seg = run.layers.get("separatrices" if kind == "separatrix" else
                         "midplanes")
    if seg is None or not len(seg):
        return []
    chains = revolve.chains(seg)
    if kind != "separatrix" or len(chains) < 2:
        return chains
    m = run.psimap                      # the main one: rho_p nearest 1
    if m is not None:
        def off(c):
            rho = np.asarray(m.rhop(c[:, 0], c[:, 1]), float)
            rho = rho[np.isfinite(rho)]
            return abs(np.median(rho) - 1.0) if rho.size else np.inf
        return [min(chains, key=off)]
    return [max(chains, key=lambda c: np.hypot(*np.diff(c, axis=0).T).sum())]


def on_lines(polys, n, rng):
    """n random points (R, Z) along the polylines, evenly by length."""
    pieces = [(p[:-1], p[1:]) for p in polys if len(p) > 1]
    if not pieces or n < 1:
        return np.zeros((0, 2))
    a = np.vstack([s for s, _ in pieces])
    b = np.vstack([e for _, e in pieces])
    cum = np.concatenate(([0.0], np.cumsum(np.hypot(*(b - a).T))))
    if not cum[-1] > 0:
        return np.zeros((0, 2))
    s = rng.uniform(0.0, cum[-1], n)
    k = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(a) - 1)
    f = ((s - cum[k]) / np.maximum(cum[k + 1] - cum[k], 1e-300))[:, None]
    return a[k] + f * (b[k] - a[k])


def into_field(xs, ys, mag, pts, k=3):
    """The points (n, 2) in a cell of the grid xs, ys where the magnitude
    mag (ny, nx) is positive at its four corners, kept; the others moved to
    the middle of the nearest such cell within k cells (a line on the edge
    of the grid, as the targets), else dropped."""
    m = np.ma.filled(np.ma.masked_invalid(mag), 0.0) > 0
    cell = m[:-1, :-1] & m[1:, :-1] & m[:-1, 1:] & m[1:, 1:]
    ny, nx = cell.shape
    dx = (xs[-1] - xs[0]) / max(len(xs) - 1, 1)
    dy = (ys[-1] - ys[0]) / max(len(ys) - 1, 1)
    pts = np.asarray(pts, float).reshape(-1, 2)
    i = np.floor((pts[:, 0] - xs[0]) / dx).astype(int)
    j = np.floor((pts[:, 1] - ys[0]) / dy).astype(int)
    best = np.full(len(pts), np.inf)
    bi, bj = i.copy(), j.copy()
    for di in range(-k, k + 1):
        for dj in range(-k, k + 1):
            ii, jj = i + di, j + dj
            ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
            ok[ok] = cell[jj[ok], ii[ok]]
            d = di * di + dj * dj
            better = ok & (d < best)
            best[better], bi[better], bj[better] = d, ii[better], jj[better]
    moved = np.column_stack((xs[0] + (bi + 0.5) * dx, ys[0] + (bj + 0.5) * dy))
    out = np.where((best == 0)[:, None], pts, moved)
    return out[np.isfinite(best)]


def on_cells(xs, ys, mag, nx, ny, power, rng):
    """The middles of the nx by ny cells over the grid xs, ys where the
    magnitude mag (ny', nx'; masked or nan: no field) is positive, all of
    them, in a random order weighted by it to the power (0: even): the
    strongest first, most likely."""
    m = np.ma.filled(np.ma.masked_invalid(mag), 0.0)
    cx = xs[0] + (np.arange(nx) + 0.5) * (xs[-1] - xs[0]) / nx
    cy = ys[0] + (np.arange(ny) + 0.5) * (ys[-1] - ys[0]) / ny
    X, Y = np.meshgrid(cx, cy)
    i = np.clip(np.rint((X - xs[0]) / (xs[1] - xs[0])).astype(int), 0,
                len(xs) - 1)
    j = np.clip(np.rint((Y - ys[0]) / (ys[1] - ys[0])).astype(int), 0,
                len(ys) - 1)
    w = m[j, i].ravel()
    ok = w > 0
    pts = np.column_stack((X.ravel()[ok], Y.ravel()[ok]))
    if not len(pts):
        return pts
    key = rng.random(len(pts))          # weighted order: u^(1/w), largest
    if power > 0:                       # first
        key = key ** (1.0 / w[ok] ** power)
    return pts[np.argsort(-key)]
