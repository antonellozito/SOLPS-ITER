"""Line integral convolution (LIC): a noise image smeared along the flow,
so that its streaks show the flow lines everywhere (the flow texture of
the vector plots)."""

import numpy as np


def noise(ny, nx, grain=1, seed=11):
    """White noise of ny by nx pixels in blocks of grain pixels (coarser
    streaks); the same for the same arguments."""
    g = max(int(grain), 1)
    rng = np.random.default_rng(seed)
    small = rng.random(((ny + g - 1) // g, (nx + g - 1) // g))
    return np.repeat(np.repeat(small, g, 0), g, 1)[:ny, :nx]


def lic(du, dv, image, length=20, step=0.6):
    """Intensity (0 to 1, nan where there is no flow) of the direction
    field (du, dv) in pixel units on the grid of image (rows v, columns
    u): the image averaged along the flow line through each pixel, length
    steps of step pixels each way."""
    ny, nx = image.shape
    valid = np.isfinite(du) & np.isfinite(dv) & ((du != 0) | (dv != 0))
    a, b = np.where(valid, du, 0.0), np.where(valid, dv, 0.0)
    mag = np.hypot(a, b)
    mag = np.where(mag > 0, mag, 1.0)
    ux, uy = a / mag, b / mag
    jj, ii = np.nonzero(valid)
    acc = image[jj, ii].astype(float)
    cnt = np.ones(len(jj))
    for sign in (1.0, -1.0):
        x, y = ii.astype(float), jj.astype(float)
        alive = np.ones(len(jj), bool)
        for _ in range(int(length)):
            ix = np.clip(np.rint(x).astype(int), 0, nx - 1)
            iy = np.clip(np.rint(y).astype(int), 0, ny - 1)
            x = x + sign * step * ux[iy, ix]
            y = y + sign * step * uy[iy, ix]
            ix = np.clip(np.rint(x).astype(int), 0, nx - 1)
            iy = np.clip(np.rint(y).astype(int), 0, ny - 1)
            alive &= (x >= 0) & (x <= nx - 1) & (y >= 0) & (y <= ny - 1) \
                & valid[iy, ix]
            acc += np.where(alive, image[iy, ix], 0.0)
            cnt += alive
    out = np.full((ny, nx), np.nan)
    if not len(jj):
        return out
    v = acc / cnt
    v = (v - v.mean()) / max(v.std(), 1e-12)
    out[jj, ii] = np.clip(0.5 + 0.22 * v, 0.0, 1.0)
    return out
