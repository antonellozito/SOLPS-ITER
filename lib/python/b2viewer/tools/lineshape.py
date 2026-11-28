"""Spectra with the shapes of the lines and the continua along a line of
sight (a chord, the central ray of a camera pixel), from the plasma at
points along it.

Each line of the quantity shown (an npec window, a hydrogen line of
Eirene's model) is split by its emitters (emission.RunEmission: zparts,
hparts), each with a profile at every point:
- Doppler: a Gaussian of the emitter temperature and mass: the excitation
  of the atoms at the Eirene atom temperature of the element, the
  excitation of the ions and every recombination and charge exchange (the
  emitter born from the ion above) at the ion temperature; the hydrogen
  atoms made by the molecules at assumed fragment energies (FRAGMENT);
- shift by the flow along the sight: the parallel velocity of the ion
  (none for the atoms and fragments);
- Zeeman: the normal triplet (pi unshifted, sigma at +- e B lambda^2 / (4
  pi m_e c)), its weights by the angle between the sight and B;
- Stark: a Lorentzian of the electron density for Balmer alpha and beta
  (STARK);
- the instrument: a Gaussian of the full width given;
the Gaussians combined, the Lorentzian with them as a pseudo-Voigt. Each
line keeps its integral (the stick of the spectrum without shapes).

The continua: bremsstrahlung (free-free, all ions, Gaunt factor of the Born
approximation, at least 1) and recombination (free-bound onto each level
of the hydrogenic ion of the charge of the recombining ion: its edges, the
Balmer edge at 364.6 nm), from the electron density and temperature and
the ion densities."""

import numpy as np

C = 299792458.0
QE = 1.602176634e-19
AMU = 1.66053906660e-27
HC_EVA = 12398.41984            # h c (eV A)
HC = 6.62607015e-34 * C         # J m
RY = 13.605693                  # eV
ZEEMAN = 4.6686e-9              # A per T and A^2: e / (4 pi m_e c)
# bremsstrahlung per unit frequency over 4 pi: 6.8e-51 W m^3 Hz^-1 K^0.5
# Z^2 ne ni Te^-1/2 g exp(-h nu / kTe), Te in eV here
FF = 6.8e-51 / np.sqrt(QE / 1.380649e-23)
# Stark full widths (A) of the hydrogen Balmer lines at 1e23 m^-3 and
# their powers of the density (Gigosos, Gonzalez and Cardenoso 2003: Balmer
# alpha, full width at half area, used as the Lorentzian width; Gigosos
# and Cardenoso 1996: Balmer beta)
STARK = {"alpha": (6562.0, 5.49, 0.67965), "beta": (4861.0, 48.0, 0.68116)}
FRAGMENT = {"molecule": 0.3, "molecular ion": 2.0}  # eV per atom
MASSES = {"H": 1.008, "D": 2.014, "T": 3.016, "He": 4.003, "Li": 6.94,
          "Be": 9.012, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999,
          "F": 18.998, "Ne": 20.18, "Ar": 39.95, "Fe": 55.85, "Kr": 83.8,
          "Mo": 95.95, "Xe": 131.29, "W": 183.84}
HYDROGEN = ("H", "D", "T")
COARSE = 2000                   # points of the continua over the range
FINE = 8                        # points per full width of a line at least
WIDE = 10.0                     # a line drawn over +- WIDE full widths
LORENTZ = 40.0                  # +- this many Lorentzian widths


def mass(element, neutrals=()):
    """Atomic mass (amu) of an element: that of the Eirene atom of the
    run, else of the table."""
    for n in neutrals:
        if n.stack == "a" and n.name == element and n.mass > 0:
            return float(n.mass)
    return MASSES.get(element, 2.0 * max(1, len(element)))


def segment(q0, q1, n=401):
    """Points (n, 3) from q0 to q1 (x, y, z) and the unit sight from q0."""
    q0, q1 = np.asarray(q0, float), np.asarray(q1, float)
    t = np.linspace(0.0, 1.0, n)
    d = q1 - q0
    length = float(np.linalg.norm(d))
    return q0 + t[:, None] * d, d / max(length, 1e-300), t * length


def weights(s, inside):
    """Trapezoid weights along s, only over the steps with both ends
    inside (as measure.chord_weights)."""
    ds = np.diff(s) * (inside[1:] & inside[:-1])
    w = np.zeros(len(s))
    w[1:] += 0.5 * ds
    w[:-1] += 0.5 * ds
    return w


def sight_parts(points, d):
    """The sight d in the local R, Z, toroidal unit vectors at points."""
    phi = np.arctan2(points[:, 1], points[:, 0])
    c, s = np.cos(phi), np.sin(phi)
    return d[0] * c + d[1] * s, np.full(len(points), d[2]), \
        -d[0] * s + d[1] * c


def stark_fwhm(element, wl, ne):
    """Lorentzian full width (A) of a hydrogen Balmer alpha or beta line
    at the electron densities ne (m^-3), else 0."""
    if element not in HYDROGEN:
        return np.zeros_like(ne)
    for lam, w, p in STARK.values():
        if abs(wl - lam) < 3.0:
            return w * (np.maximum(np.nan_to_num(ne), 0.0) / 1e23) ** p
    return np.zeros_like(ne)


def pseudo_voigt(x, fg, fl):
    """Normalised Voigt profile (pseudo-Voigt of Thompson, Cox and
    Hastings 1987, within 1 %) at offsets x of Gaussian and Lorentzian full
    widths fg, fl (same units)."""
    f = (fg ** 5 + 2.69269 * fg ** 4 * fl + 2.42843 * fg ** 3 * fl ** 2 +
         4.47163 * fg ** 2 * fl ** 3 + 0.07842 * fg * fl ** 4 +
         fl ** 5) ** 0.2
    r = fl / np.maximum(f, 1e-300)
    eta = 1.36603 * r - 0.47719 * r ** 2 + 0.11116 * r ** 3
    h = 0.5 * f
    lor = h / (np.pi * (x * x + h * h))
    gau = np.sqrt(np.log(2.0) / np.pi) / h * np.exp(-np.log(2.0) *
                                                     (x / h) ** 2)
    return eta * lor + (1.0 - eta) * gau


def _i0(x):
    t = (x / 3.75) ** 2
    return 1.0 + t * (3.5156229 + t * (3.0899424 + t * (1.2067492 + t * (
        0.2659732 + t * (0.0360768 + t * 0.0045813)))))


def k0_scaled(x):
    """exp(x) K0(x) (Abramowitz and Stegun 9.8.5, 9.8.6)."""
    x = np.asarray(x, float)
    small = np.minimum(x, 2.0)
    t = (small / 2.0) ** 2
    k_small = -np.log(small / 2.0) * _i0(small) + (-0.57721566 + t * (
        0.42278420 + t * (0.23069756 + t * (0.03488590 + t * (
            0.00262698 + t * (0.00010750 + t * 0.00000740))))))
    big = np.maximum(x, 2.0)
    t = 2.0 / big
    k_big = (1.25331414 + t * (-0.07832358 + t * (0.02189568 + t * (
        -0.01062446 + t * (0.00587872 + t * (-0.00251540 + t *
                                              0.00053208)))))) / np.sqrt(big)
    return np.where(x <= 2.0, np.exp(small) * k_small, k_big)


def gaunt_ff(hnu, te):
    """Free-free Gaunt factor: the Born approximation (sqrt 3 / pi) e^x
    K0(x), x = h nu / 2 Te, at least 1 (it fails in cold plasmas)."""
    x = np.maximum(hnu / (2.0 * np.maximum(te, 1e-3)), 1e-8)
    return np.maximum(np.sqrt(3.0) / np.pi * k0_scaled(x), 1.0)


def continua(lam, ne, te, ions, w):
    """Bremsstrahlung and recombination (W m^-2 A^-1 over 4 pi: the
    emissivity integrated with the weights w along the sight) at the
    wavelengths lam (A); ions: {charge: densities (m^-3)} at the points
    (ne, te in m^-3, eV)."""
    keep = (w > 0) & np.isfinite(ne) & np.isfinite(te) & (te > 0)
    ne, te, w = ne[keep], te[keep], w[keep]
    ions = {z: np.nan_to_num(n[keep]) for z, n in ions.items() if z > 0}
    hnu = HC_EVA / lam                                  # (G,)
    per_a = C / (lam * 1e-10) ** 2 * 1e-10              # per Hz -> per A
    base = FF * ne / np.sqrt(te)                        # (S,)
    boltz = np.exp(-hnu[None, :] / te[:, None])         # (S, G)
    zsum = sum(z * z * n for z, n in ions.items()) if ions else 0.0 * ne
    ff = ((w * base * zsum) @ (gaunt_ff(hnu[None, :], te[:, None]) * boltz))
    fb = np.zeros(len(lam))
    for z, n in ions.items():
        if not np.any(n > 0):
            continue
        amp = w * base * n * z * z                      # (S,)
        nmin = np.maximum(np.ceil(z * np.sqrt(RY / hnu)), 1.0)  # (G,)
        top = int(min(nmin.max(), 400)) + 30
        tot = np.zeros((len(ne), len(lam)))
        for k in range(1, top + 1):
            chi = z * z * RY / k ** 2
            ok = hnu >= chi
            if not ok.any():
                continue
            tot[:, ok] += 2.0 * chi / (k * te[:, None]) * np.exp(
                (chi - hnu[None, ok]) / te[:, None])
        tail = top + 0.5                                # the levels above
        tot += z * z * RY / (te[:, None] * tail ** 2) * boltz
        fb += amp @ tot
    return ff * per_a, fb * per_a


def edges(charges, lo, hi):
    """Wavelengths (A) of the recombination edges within lo to hi."""
    out = []
    for z in charges:
        for k in range(1, 60):
            lam = HC_EVA / (z * z * RY / k ** 2)
            if lam > hi:
                break
            if lam >= lo:
                out.append(lam)
    return np.array(out)


def profiles(rows, b, cos, instrument):
    """Per line: (centre, Gaussian full widths, Lorentzian full widths,
    shifts and the weights at the points of each emitter); rows: (lambda
    A, element, [(emission x weight at the points, T eV, mass amu, line
    of sight velocity m/s, ne)])."""
    sig_i = instrument / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    zw = np.stack(((1.0 + cos ** 2) / 4.0, (1.0 - cos ** 2) / 2.0,
                   (1.0 + cos ** 2) / 4.0), axis=1)           # (S, 3)
    out = []
    for lam, element, parts in rows:
        comps = []
        for e, t, m, v, ne in parts:
            keep = np.flatnonzero(np.nan_to_num(e) != 0.0)
            if not len(keep):
                continue
            sig = lam * np.sqrt(np.maximum(np.nan_to_num(t[keep]), 0.0) *
                                QE / (m * AMU * C * C))
            fg = 2.0 * np.sqrt(2.0 * np.log(2.0)) * np.sqrt(
                sig ** 2 + sig_i ** 2)
            fl = stark_fwhm(element, lam, ne[keep])
            dz = ZEEMAN * np.nan_to_num(b[keep]) * lam ** 2
            centre = lam * (1.0 + np.nan_to_num(v[keep]) / C)
            cen = centre[:, None] + dz[:, None] * np.array([-1.0, 0.0, 1.0])
            comps.append((e[keep], zw[keep], cen, np.maximum(fg, 1e-6),
                          fl))
        out.append(comps)
    return out


def grid(lines, lo, hi, extra=()):
    """Wavelengths: COARSE over lo to hi, FINE per width near each line
    (lines: profiles()), and both sides of the edges extra."""
    pts = [np.geomspace(lo, hi, COARSE)]
    for comps in lines:
        for e, zw, cen, fg, fl in comps:
            f = np.maximum(fg, fl)
            a = cen.min() - WIDE * f.max() - LORENTZ * fl.max()
            b = cen.max() + WIDE * f.max() + LORENTZ * fl.max()
            step = max(min(f.min() / FINE, (b - a) / 40.0), (b - a) / 1500.0)
            pts.append(np.arange(a, b + step, step))
    for x in extra:
        pts.append(x * np.array([1.0 - 1e-6, 1.0 + 1e-6]))
    g = np.unique(np.concatenate(pts))
    return g[(g > 0)]


def line_curves(lines, lam):
    """The profiles of the lines summed on lam, and the integral of each
    line (trapezoid on lam: each profile normalised there, so that a line
    keeps its integral)."""
    tw = np.zeros(len(lam))
    dl = np.diff(lam)
    tw[1:] += 0.5 * dl
    tw[:-1] += 0.5 * dl
    curve = np.zeros(len(lam))
    for comps in lines:
        for e, zw, cen, fg, fl in comps:
            f = np.maximum(fg, fl)
            a = np.searchsorted(lam, cen.min() - WIDE * f.max() -
                                LORENTZ * fl.max())
            b = np.searchsorted(lam, cen.max() + WIDE * f.max() +
                                LORENTZ * fl.max(), "right")
            x = lam[None, None, a:b] - cen[:, :, None]          # (S, 3, G)
            p = pseudo_voigt(x, fg[:, None, None], fl[:, None, None])
            norm = p @ tw[a:b]
            p = p / np.where(norm > 0, norm, 1.0)[:, :, None]
            curve[a:b] += np.einsum("s,sk,skg->g", e, zw, p)
    return curve
