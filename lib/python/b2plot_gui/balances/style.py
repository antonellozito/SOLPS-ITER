"""Colours, glow and smoothing of the balance plots and of the balance
volume on the 2D plot: the colours of the balance scripts (blue upstream
flux, red downstream flux, yellow source, magenta and green residuals),
their versions for the dark theme, and a linear smoothing that keeps the
balances (smoothed terms still add up to the smoothed residual)."""

import colorsys

import numpy as np
from matplotlib import colors as mcolors
from matplotlib import patheffects

from .. import theme

UP = "#0072bd"
DOWN = "#d95319"
SOURCE = "#edb120"
STRATUM = "#00c8ff"                 # segments of a recycling stratum
CODE = "#ff00ff"
POST = "#00b000"
PALETTE = ("#0072bd", "#d95319", "#edb120", "#7e2f8e", "#77ac30",
           "#4dbeee", "#a2142f", "#1f77b4", "#ff7f0e", "#2ca02c",
           "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
           "#bcbd22", "#17becf")
STYLES = ("-", "--", ":", "-.")
SMOOTH = 1                          # passes of the smoothing kernel


def line(color):
    """A line colour in the current theme: as it is on the light
    background, lighter on the dark one (same hue)."""
    if not theme.is_dark():
        return color
    r, g, b = mcolors.to_rgb(color)
    h, lum, s = colorsys.rgb_to_hls(r, g, b)
    return colorsys.hls_to_rgb(h, max(lum, 0.62), min(s, 0.85))


def cycle(i):
    """Colour and line style of the i-th line of a decomposition."""
    return PALETTE[i % len(PALETTE)], STYLES[(i // len(PALETTE)) %
                                            len(STYLES)]


def axes_colors():
    """(figure, axes, text, grid) colours of the plots."""
    if theme.is_dark():
        return theme.figure_bg(), "#2e2e2e", theme.text(), "#4a4a4a"
    return theme.figure_bg(), "#ffffff", theme.text(), "#dddddd"


def glow(width, color, strong=False, on_map=False):
    """Path effects of a glowing line of width (points) and colour; on_map:
    over the 2D plot (light in both themes: a white halo)."""
    c = theme.rgb(color) if on_map else line(color)
    halo = "#000000" if theme.is_dark() and not on_map else "#ffffff"
    out = [patheffects.Stroke(linewidth=width + (10 if strong else 7),
                              foreground=c, alpha=0.18),
           patheffects.Stroke(linewidth=width + (5 if strong else 3.5),
                              foreground=c, alpha=0.35),
           patheffects.Stroke(linewidth=width + 1.6, foreground=halo,
                              alpha=0.9),
           patheffects.Normal()]
    return out


def smooth(y, level, axis=0):
    """y smoothed by level passes of the (1, 2, 1) / 4 kernel, the kernel
    normalised again at the ends (a linear operation)."""
    y = np.asarray(y, float)
    if level <= 0 or y.shape[axis] < 3:
        return y
    y = np.moveaxis(y, axis, 0)
    w = np.ones(y.shape[0])
    for _ in range(level):
        pad = np.concatenate((y[:1] * 0, y, y[:1] * 0))
        wp = np.concatenate(([0.0], w, [0.0]))
        num = 0.25 * pad[:-2] + 0.5 * pad[1:-1] + 0.25 * pad[2:]
        den = 0.25 * wp[:-2] + 0.5 * wp[1:-1] + 0.25 * wp[2:]
        y = num / den.reshape((-1,) + (1,) * (y.ndim - 1))
    return np.moveaxis(y, 0, axis)


def gradient(n, t=None):
    """n colours from the upstream blue to the downstream red, evenly or
    at the fractions t (0 upstream, 1 downstream)."""
    a, b = np.array(mcolors.to_rgb(line(UP))), np.array(mcolors.to_rgb(
        line(DOWN)))
    t = np.linspace(0.0, 1.0, max(n, 1)) if t is None else np.clip(t, 0, 1)
    return (1 - t[:, None]) * a + t[:, None] * b
