"""Tracers of the 3D view: points moving with the flow of a vector
quantity (toroidally symmetric, gridded in (R, Z)), each with a fading tail
of its last positions; the speed shown true or log-compressed."""

import numpy as np

from . import births, vector3d as v3

TAIL_FADE = 0.85        # tail colour at its end, towards the background
LIFE = (2.0, 6.0)       # lifetime of a tracer (s), at random between
FRAME = 0.033           # a frame of the animation (s)
AGING_MAX = 20.0        # where the magnitude is small: at most this faster
FADE = 0.5              # faster as 1/level to this power (fading on)
UP_STEP = 0.2           # steps back up the flow, placing a tracer (s)


class Field:
    """(vR, vZ, vphi) on the grid xs, ys (nan outside), with the 98th
    percentile v98 and the lowest magnitude shown vmin of the speed;
    valid: not zero everywhere."""

    def __init__(self, xs, ys, fields):
        self.xs, self.ys, self.f = xs, ys, fields
        with np.errstate(over="ignore", invalid="ignore"):
            mag = np.sqrt(sum(f * f for f in fields))
        good = mag[np.isfinite(mag) & (mag > 0)]
        self.valid = bool(good.size)
        self._mag = mag
        self.v98 = float(np.percentile(good, 98.0)) if good.size else 1.0
        self.vmin = max(float(good.min()) if good.size else 1.0,
                        1e-3 * self.v98)
        self.size = max(xs[-1] - xs[0], ys[-1] - ys[0])

    def at(self, r, z):
        return v3.bilinear(self.xs, self.ys, self.f, r, z)

    def shown(self, mag, log):
        """Speed shown per unit of the reference speed: the magnitude over
        v98 (true), or its logarithm between vmin and v98 (log), at most
        1.5."""
        mag = np.where(np.isfinite(mag), mag, 0.0)
        if log:                         # one magnitude: all at full speed
            span = np.log(self.v98 / self.vmin) if self.v98 > self.vmin \
                else 0.0
            if not span > 0:
                return np.where(mag > 0, 1.0, 0.05)
            return np.clip(np.log(np.maximum(mag, self.vmin) / self.vmin)
                           / span, 0.05, 1.5)
        return np.clip(mag / self.v98, 0.0, 1.5)

    def level(self, mag, low=None):
        """Place of the magnitude on the colour scale, 0 to 1 (1 from v98
        up): |v|/v98 on a linear scale (low None), log(|v|/low)/
        log(v98/low) on a log one, low the bottom of the colour bar."""
        mag = np.where(np.isfinite(mag), mag, 0.0)
        if low is None:
            return np.clip(mag / self.v98, 0.0, 1.0)
        if not 0 < low < self.v98:
            return np.where(mag >= low, 1.0, 0.0)
        return np.clip(np.log(np.maximum(mag, low) / low) /
                       np.log(self.v98 / low), 0.0, 1.0)

    def at_least(self, r, z, floor):
        """Where the magnitude at the points is at least floor."""
        if not floor > 0:
            return np.ones(np.shape(r), bool)
        vr, vz, vp = self.at(r, z)
        with np.errstate(invalid="ignore"):
            return np.sqrt(vr * vr + vz * vz + vp * vp) >= floor

    def sample(self, n, rng, zlim=(None, None), weight=0.0, lines=None,
               floor=0.0, low=None, volume=False):
        """n random points (R, Z) where the field is defined and its
        magnitude is at least floor (between the heights zlim, None: no
        limit): along the polylines lines if given, else over the field,
        their density as the level of the magnitude on the colour scale
        (low, see level) to the power weight (0: even, 1: in proportion
        to it); with volume even over the volume turned around the axis
        (as R)."""
        out = np.zeros((0, 2))
        z0 = self.ys[0] if zlim[0] is None else max(self.ys[0], zlim[0])
        z1 = self.ys[-1] if zlim[1] is None else min(self.ys[-1], zlim[1])
        if z1 <= z0:
            return out
        for _ in range(200):
            if lines:                   # moved into the field if on its edge
                r, z = births.into_field(self.xs, self.ys, self._mag,
                                         births.on_lines(lines, 4 * n + 16,
                                                         rng)).T
                inz = (z >= z0) & (z <= z1)
                r, z = r[inz], z[inz]
            else:
                r = rng.uniform(self.xs[0], self.xs[-1], 4 * n + 16)
                z = rng.uniform(z0, z1, 4 * n + 16)
            vr, vz, vp = self.at(r, z)
            m = np.sqrt(vr * vr + vz * vz + vp * vp)
            ok = np.isfinite(m) & (m > 0) & (m >= floor)
            if weight > 0:              # kept as likely as level^weight
                w = self.level(np.where(ok, m, 0.0), low) ** weight
                ok &= rng.random(len(m)) < w
            if volume and not lines:    # as likely as R: even in volume
                ok &= rng.random(len(m)) * self.xs[-1] < r
            out = np.vstack((out, np.column_stack((r[ok], z[ok]))))
            if len(out) >= n:
                break
        return out[:n]


def colour_range(f, given, log):
    """Colour range of the tracers of Field f: given, else up to the 98th
    percentile of the speed, from its lowest shown (log) or zero."""
    lo, hi = given if given is not None else (
        f.vmin if log else 0.0, f.v98)
    if log:
        hi = hi if hi > 0 else 1.0
        lo = lo if 0 < lo < hi else hi * 1e-3
    return (float(lo), float(hi) if hi > lo else float(lo) + 1.0)


class Tracers:
    """Points moving with the flow over the sector [phi0, phi1] (between
    the heights zlim), each with a tail of its last positions, born more
    where the magnitude is larger (weight) or along lines, and ageing
    faster where it is smaller (fade), both by its level on the colour
    scale (low: log from there, None: linear; Field.level); a point leaving the field, the
    sector or the heights, entering where the magnitude is below floor,
    or at the end of its life, starts again at a random place (never
    where the magnitude is below floor; hidden while there is no such
    place)."""

    def __init__(self, field, n, tail, phi0, phi1, rng=None,
                 zlim=(None, None), weight=0.0, fade=0.0, lines=None,
                 vref=1.0, log=True, floor=0.0, low=None, volume=False):
        self.field, self.n, self.tail = field, n, max(int(tail), 2)
        self.phi0, self.phi1 = phi0, phi1
        self.zlim = zlim                # heights kept (vertical cut)
        self.weight = weight            # born more where |v| is larger
        self.fade = fade                # die sooner where |v| is smaller
        self.lines = lines              # flowing through these polylines
        self.vref, self.log = vref, log  # the speeds shown (step)
        self.floor = floor or 0.0       # no tracer where |v| is below it
        self.low = low                  # the colour scale: log from low
        self.volume = volume            # births even over the volume
        self.wrap = abs(phi1 - phi0) >= 2.0 * np.pi - 1e-9
        self.rng = rng or np.random.default_rng(1)
        self.r, self.z = np.zeros(n), np.zeros(n)
        self.phi, self.age, self.life = np.zeros(n), np.zeros(n), \
            np.ones(n)
        self.mag = np.zeros(n)
        self.hist = np.zeros((self.tail, n, 3))
        self.respawn(np.arange(n), spread_age=True)

    def respawn(self, idx, spread_age=False):
        if not len(idx):
            return
        p = self.field.sample(len(idx), self.rng, self.zlim, self.weight,
                              self.lines, self.floor, self.low,
                              self.volume)
        if len(p) < len(idx):           # nowhere to go: hidden, tried again
            lost = idx[len(p):]
            self.r[lost] = self.z[lost] = np.nan
            self.hist[:, lost, :] = np.nan
            idx = idx[:len(p)]
        self.r[idx], self.z[idx] = p[:, 0], p[:, 1]
        self.phi[idx] = self.rng.uniform(self.phi0, self.phi1, len(idx))
        self.life[idx] = self.rng.uniform(*LIFE, len(idx))
        self.age[idx] = self.rng.uniform(0.0, self.life[idx]) \
            if spread_age else 0.0
        if self.lines:                  # through the line in their life
            self._upstream(idx, self.rng.uniform(0.0, self.life[idx] -
                                                 self.age[idx]))
        self.hist[:, idx, :] = np.column_stack(v3.cartesian(
            self.r[idx], self.z[idx], self.phi[idx]))[None]

    def _dir(self, r, z):
        vr, vz, vp = self.field.at(r, z)
        mag = np.sqrt(vr * vr + vz * vz + vp * vp)
        ok = np.isfinite(mag) & (mag > 0) & (r > 0)
        m = np.where(ok, mag, 1.0)
        return vr / m, vz / m, vp / m, np.where(ok, mag, 0.0), ok

    def _aging(self, mag):
        """How much faster a tracer ages: one over the level of |v| on the
        colour scale to the power fade, from 1 (|v| at least v98) to
        AGING_MAX."""
        if self.fade <= 0:
            return 1.0
        s = np.maximum(self.field.level(mag, self.low), 1e-12)
        return np.clip(s ** -self.fade, 1.0, AGING_MAX)

    def warm_up(self, vref, log):
        """Moved frame by frame for the longest lifetime: shown from the
        start as they are later on (tails grown, spread by the flow)."""
        for _ in range(int(np.ceil(LIFE[1] / FRAME))):
            self.step(FRAME, vref, log)

    def _move(self, r, z, phi, dt):
        """Positions after dt seconds (negative: back up the flow), the
        magnitude on the way, where the field is."""
        dr, dz, dp, mag, ok = self._dir(r, z)
        s = self.field.shown(mag, self.log) * self.vref * dt
        dr2, dz2, dp2, mag2, ok2 = self._dir(r + 0.5 * s * dr,
                                             z + 0.5 * s * dz)
        ok &= ok2
        s2 = self.field.shown(mag2, self.log) * self.vref * dt
        return (np.where(ok, r + s2 * dr2, r), np.where(ok, z + s2 * dz2, z),
                np.where(ok, phi + s2 * dp2 / np.maximum(r, 1e-9), phi),
                mag2, ok)

    def _upstream(self, idx, tau):
        """The tracers idx moved back up the flow by tau seconds each (in
        steps of UP_STEP), as far as the field and the heights go and, in
        a sector, as far round the axis as the sector is wide; then turned
        round the axis (the flow is the same all round) so that they
        start in the sector and pass the line they were placed on in it,
        tau seconds later."""
        r, z = self.r[idx], self.z[idx]
        turn = np.zeros(len(idx))       # toroidal angle gone back
        left = np.asarray(tau, float).copy()
        width = self.phi1 - self.phi0
        lo, hi = self.zlim
        while (left > 0).any():
            h = np.minimum(left, UP_STEP)
            nr, nz, nturn, _, ok = self._move(r, z, turn, -h)
            if not self.wrap:
                ok &= np.abs(nturn) <= width
            ok &= self.field.at_least(nr, nz, self.floor)
            if lo is not None:
                ok &= nz >= lo
            if hi is not None:
                ok &= nz <= hi
            go = ok & (left > 0)
            r, z, turn = (np.where(go, nr, r), np.where(go, nz, z),
                          np.where(go, nturn, turn))
            left = np.where(go, left - h, 0.0)
        if self.wrap:
            cross = self.rng.uniform(self.phi0, self.phi1, len(idx))
        else:                           # start and crossing in the sector
            cross = self.rng.uniform(self.phi0 + np.maximum(0.0, -turn),
                                     self.phi1 - np.maximum(0.0, turn))
        self.r[idx], self.z[idx], self.phi[idx] = r, z, cross + turn

    def step(self, dt, vref, log):
        """Move them by dt seconds (reference speed vref in m/s)."""
        self.vref, self.log = vref, log
        self.r, self.z, self.phi, mag2, ok = self._move(self.r, self.z,
                                                        self.phi, dt)
        self.mag = mag2
        self.age += dt * self._aging(mag2)
        if self.wrap:
            self.phi = np.mod(self.phi - self.phi0, 2 * np.pi) + self.phi0
            out = ~ok
        else:
            out = ~ok | (self.phi < self.phi0) | (self.phi > self.phi1)
        out |= self.age > self.life
        if self.floor > 0:              # entered where |v| is too small
            out |= ~self.field.at_least(self.r, self.z, self.floor)
        lo, hi = self.zlim
        if lo is not None:
            out |= self.z < lo
        if hi is not None:
            out |= self.z > hi
        self.hist[1:] = self.hist[:-1]
        self.hist[0] = np.column_stack(v3.cartesian(self.r, self.z,
                                                    self.phi))
        self.respawn(np.flatnonzero(out))

    def edges(self):
        """Edges of the tails (nodes ordered as hist, newest first)."""
        n, t = self.n, self.tail
        k = np.arange(t - 1)[:, None] * n + np.arange(n)[None, :]
        return np.column_stack((k.ravel(), (k + n).ravel()))

    def colors(self, base, background):
        """Node colours of the tails: base (n, k) at the head (k colour
        components, or one: the opacity), fading towards the background
        along the tail."""
        f = (np.arange(self.tail) / max(self.tail - 1, 1) * TAIL_FADE)[
            :, None, None]
        c = (1.0 - f) * base[None] + f * np.asarray(background)[None, None]
        return c.reshape(-1, c.shape[-1])
