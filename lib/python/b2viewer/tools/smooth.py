"""Moderate smoothing of a profile (Smooth of the profile plots and of
the wall strip): on each run of finite points, a discrete smoothing
spline (second differences penalised, Whittaker; the weight for a cut-off
period of a fortieth of the run, at least four points: structures wider
than that, peaks and holes, keep their place and most of their height),
in the logarithm for positive values over more than two decades, drawn
through a monotone cubic (no overshoot) at four points per interval."""

import numpy as np

CUTOFF = 40.0                   # the run over this: the cut-off period
MIN_PERIOD = 4.0                # points
DENSE = 4                       # points drawn per interval
LOG_SPAN = 100.0                # max/min above this: smoothed in log


def _whittaker(y, lam):
    """y smoothed: (I + lam D'D) z = y, D the second differences; the
    banded Cholesky factor of the five diagonals solved in one pass."""
    n = len(y)
    d0 = np.full(n, 6.0)
    d0[[0, -1]], d0[[1, -2]] = 1.0, 5.0
    d1 = np.full(n - 1, -4.0)
    d1[[0, -1]] = -2.0
    a0, a1, a2 = 1.0 + lam * d0, lam * d1, lam * np.ones(n - 2)
    l0, l1, l2 = np.zeros(n), np.zeros(n - 1), np.zeros(n - 2)
    for i in range(n):
        s = a0[i] - (l1[i - 1] ** 2 if i >= 1 else 0.0) - \
            (l2[i - 2] ** 2 if i >= 2 else 0.0)
        l0[i] = np.sqrt(s)
        if i < n - 1:
            l1[i] = (a1[i] - (l2[i - 1] * l1[i - 1] if i >= 1 else 0.0)) \
                / l0[i]
        if i < n - 2:
            l2[i] = a2[i] / l0[i]
    w = np.zeros(n)
    for i in range(n):
        w[i] = (y[i] - (l1[i - 1] * w[i - 1] if i >= 1 else 0.0) -
                (l2[i - 2] * w[i - 2] if i >= 2 else 0.0)) / l0[i]
    z = np.zeros(n)
    for i in range(n - 1, -1, -1):
        z[i] = (w[i] - (l1[i] * z[i + 1] if i < n - 1 else 0.0) -
                (l2[i] * z[i + 2] if i < n - 2 else 0.0)) / l0[i]
    return z


def _pchip(x, y, n):
    """The monotone cubic (Fritsch-Carlson) through (x, y), x increasing,
    at n points per interval."""
    h, d = np.diff(x), np.diff(y) / np.diff(x)
    m = np.zeros(len(x))
    m[0], m[-1] = d[0], d[-1]
    dl, dr = d[:-1], d[1:]
    same = dl * dr > 0                  # a local extremum: flat there
    w1, w2 = 2 * h[1:] + h[:-1], h[1:] + 2 * h[:-1]
    mid = np.zeros(len(x) - 2)
    mid[same] = (w1[same] + w2[same]) / (w1[same] / dl[same] +
                                         w2[same] / dr[same])
    m[1:-1] = mid
    t = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    h0 = h[:, None]
    p0, p1 = y[:-1, None], y[1:, None]
    m0, m1 = m[:-1, None] * h0, m[1:, None] * h0
    yy = (2 * t ** 3 - 3 * t ** 2 + 1) * p0 + (t ** 3 - 2 * t ** 2 + t) * \
        m0 + (-2 * t ** 3 + 3 * t ** 2) * p1 + (t ** 3 - t ** 2) * m1
    xx = x[:-1, None] + t * h0
    return (np.append(xx.ravel(), x[-1]), np.append(yy.ravel(), y[-1]))


def _run(x, y):
    n = len(y)
    if n < 5:
        return x, y
    period = max(MIN_PERIOD, n / CUTOFF)
    lam = (period / (2.0 * np.pi)) ** 4
    pos = (y > 0).all() and y.max() / y.min() > LOG_SPAN
    z = _whittaker(np.log(y) if pos else y, lam)
    if np.all(np.diff(x) > 0):
        x, z = _pchip(x, z, DENSE)
    return x, np.exp(z) if pos else z


def smooth(x, y):
    """(x, y) of the curve smoothed, each run of finite points apart (a nan
    between runs)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if not ok.any():
        return x, y
    cut = np.flatnonzero(np.diff(ok.astype(int)) != 0) + 1
    xs, ys = [], []
    for a, b in zip(np.r_[0, cut], np.r_[cut, len(y)]):
        if ok[a]:
            sx, sy = _run(x[a:b], y[a:b])
            xs += [sx, [np.nan]]
            ys += [sy, [np.nan]]
    return np.concatenate(xs[:-1]), np.concatenate(ys[:-1])
