"""Colours and glow of the balance plots and of the balance volume on the
2D plot: the colours of the balance scripts (blue upstream flux, red
downstream flux, yellow source, magenta and green residuals) and their
versions for the dark theme."""

import colorsys

import numpy as np
from matplotlib import colors as mcolors
from matplotlib import patheffects

from .. import theme

STRATUM = "#00c8ff"                 # segments of a recycling stratum
# colours of the roles of the total balance plots, shared by both plots and
# the volume on the 2D plot (upstream surface and flux, downstream surface,
# walls and flux, sources with the fill and the sides; residuals); the
# user may change them while a run is open (set_colour)
COLOURS = {"up": "#0072bd", "down": "#d95319", "source": "#edb120",
           "code": "#ff00ff", "post": "#00b000"}
_colours = dict(COLOURS)


def colour(role):
    """The colour of a role ("up", "down", "source", "code", "post")."""
    return _colours[role]


def set_colour(role, c):
    _colours[role] = c


def reset_colours():
    _colours.update(COLOURS)

PALETTE = ("#0072bd", "#d95319", "#edb120", "#7e2f8e", "#77ac30",
           "#4dbeee", "#a2142f", "#1f77b4", "#ff7f0e", "#2ca02c",
           "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
           "#bcbd22", "#17becf")
STYLES = ("-", "--", ":", "-.")


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


def gradient(n, t=None):
    """n colours from the upstream blue to the downstream red, evenly or
    at the fractions t (0 upstream, 1 downstream)."""
    a, b = np.array(mcolors.to_rgb(line(colour("up")))), np.array(
        mcolors.to_rgb(line(colour("down"))))
    t = np.linspace(0.0, 1.0, max(n, 1)) if t is None else np.clip(t, 0, 1)
    return (1 - t[:, None]) * a + t[:, None] * b
