"""Realistic views of a camera image of the light: the lines of a light
quantity weighted by a filter (a wavelength range or an interference
filter), seen as the eye sees them (CIE 1931 colour matching functions,
sRGB), or as the counts of a camera (aperture, exposure, quantum
efficiency, photon noise, full well).

Brightness L of a pixel: per steradian (photons or W m^-2 s^-1 sr^-1, the
line integral over 4 pi); the light on a pixel: L x the aperture area x
the solid angle of the pixel (pinhole camera)."""

import numpy as np

HC = 6.62607015e-34 * 299792458.0       # J m
# filters: name, kind ("filter": centre and full width at half maximum,
# "range": from, to), the two values in nm
FILTERS = (("D-alpha 656.1 nm", "filter", 656.1, 1.0),
           ("D-beta 486.0 nm", "filter", 486.0, 1.0),
           ("D-gamma 433.9 nm", "filter", 433.9, 1.0),
           ("D-delta 410.1 nm", "filter", 410.1, 1.0),
           ("He I 587.6 nm", "filter", 587.6, 1.0),
           ("He I 667.8 nm", "filter", 667.8, 1.0),
           ("He II 468.6 nm", "filter", 468.6, 1.0),
           ("C III 465.0 nm", "filter", 465.0, 1.0),
           ("N II 399.5 nm", "filter", 399.5, 1.0),
           ("N II 500.5 nm", "filter", 500.5, 1.0),
           ("Ne I 640.2 nm", "filter", 640.2, 1.0),
           ("Ar II 434.8 nm", "filter", 434.8, 1.0),
           ("Visible 380 to 750 nm", "range", 380.0, 750.0))
SRGB = np.array([[3.2406, -1.5372, -0.4986],
                 [-0.9689, 1.8758, 0.0415],
                 [0.0557, -0.2040, 1.0570]])     # linear sRGB from XYZ


def _lobe(lam, mu, s1, s2):
    s = np.where(lam < mu, s1, s2)
    return np.exp(-0.5 * ((lam - mu) / s) ** 2)


def cmf(lam_nm):
    """CIE 1931 2 degree colour matching functions x, y, z at the
    wavelengths (nm): the multi-lobe fit of Wyman, Sloan and Shirley
    (2013), within 1 % of the tables."""
    lam = np.asarray(lam_nm, float)
    x = 1.056 * _lobe(lam, 599.8, 37.9, 31.0) + \
        0.362 * _lobe(lam, 442.0, 16.0, 26.7) - \
        0.065 * _lobe(lam, 501.1, 20.4, 26.2)
    y = 0.821 * _lobe(lam, 568.8, 46.9, 40.5) + \
        0.286 * _lobe(lam, 530.9, 16.3, 31.1)
    z = 1.217 * _lobe(lam, 437.0, 11.8, 36.0) + \
        0.681 * _lobe(lam, 459.0, 26.0, 13.8)
    return np.stack((x, y, z))


def transmission(lam_nm, kind, a, b):
    """Transmission of the filter at the wavelengths (nm): kind "all" 1,
    "range" 1 from a to b, "filter" a Gaussian of centre a and full width
    at half maximum b (an interference filter)."""
    lam = np.asarray(lam_nm, float)
    if kind == "range":
        return ((lam >= min(a, b)) & (lam <= max(a, b))).astype(float)
    if kind == "filter":
        return np.exp(-4.0 * np.log(2.0) * ((lam - a) / max(b, 1e-6)) ** 2)
    return np.ones_like(lam)


def gamma(rgb):
    """Linear sRGB (0 to 1) to the sRGB of a screen."""
    c = np.clip(rgb, 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c,
                    1.055 * c ** (1.0 / 2.4) - 0.055)


def to_srgb(xyz):
    """(..., 3) XYZ to linear sRGB, the negative parts of colours outside
    the gamut (single lines) cut (a line keeps the hue of its primary:
    Balmer alpha deep red, not mixed with white made pink by the screen
    gamma)."""
    rgb = np.einsum("ij,...j->...i", SRGB, np.asarray(xyz, float))
    return np.maximum(rgb, 0.0)


def line_colour(lam_nm):
    """sRGB of a line seen alone (its brightest form), grey outside the
    visible."""
    xyz = cmf(np.atleast_1d(lam_nm)).T
    rgb = to_srgb(xyz)
    top = rgb.max(axis=-1, keepdims=True)
    out = np.where(top > 1e-3, gamma(rgb / np.maximum(top, 1e-30)), 0.6)
    return out[0] if np.ndim(lam_nm) == 0 else out


def solid_angles(cam):
    """(ny, nx) solid angle of each pixel of a pinhole camera (sr)."""
    w = np.tan(np.radians(cam.fov) / 2.0)
    h = w * cam.ny / cam.nx
    u = (2.0 * (np.arange(cam.nx) + 0.5) / cam.nx - 1.0) * w
    v = (1.0 - 2.0 * (np.arange(cam.ny) + 0.5) / cam.ny) * h
    du, dv = 2.0 * w / cam.nx, 2.0 * h / cam.ny
    uu, vv = np.meshgrid(u, v)
    return du * dv / (1.0 + uu * uu + vv * vv) ** 1.5


def etendue(cam, aperture_mm):
    """(ny, nx) aperture area x solid angle of each pixel (m^2 sr)."""
    return np.pi * (0.5e-3 * aperture_mm) ** 2 * solid_angles(cam)


def counts(photons, cam, aperture_mm, exposure_ms, qe, full_well, rng):
    """Photoelectrons of each pixel: brightness (photons m^-2 s^-1 sr^-1)
    x etendue x exposure x quantum efficiency (0 to 1), with photon noise
    (Poisson), at most full_well; and the mean before the noise."""
    mean = np.maximum(np.nan_to_num(photons), 0.0) * etendue(
        cam, aperture_mm) * exposure_ms * 1e-3 * qe
    n = rng.poisson(np.minimum(mean, 1e15)).astype(float)
    return np.minimum(n, full_well), mean


def line_weights(lam_A, photons, kind, a, b):
    """Per line (wavelengths in A, the line images in photons if photons
    else in W): the weights giving the photons through the filter, and
    the X, Y, Z weights (energy, the colour matching functions) of the
    light through it."""
    lam_A = np.asarray(lam_A, float)
    t = transmission(0.1 * lam_A, kind, a, b)
    energy = HC / (lam_A * 1e-10)       # J per photon
    to_ph = t if photons else t / energy
    to_w = t * energy if photons else t
    return to_ph, cmf(0.1 * lam_A) * to_w[None, :]


def true_colour(xyz, brightness=1.0, scale=None):
    """(ny, nx, 3) screen sRGB of an image in X, Y, Z (ny, nx, 3): exposed
    so that the brightest 0.5 % of the pixels saturate (scale: the factor
    to use instead), times brightness; and the factor used."""
    rgb = to_srgb(np.maximum(np.nan_to_num(xyz), 0.0))
    if scale is None:
        top = np.percentile(rgb.max(axis=-1), 99.5)
        scale = 1.0 / top if top > 0 else 1.0
    return gamma(rgb * scale * brightness), scale
