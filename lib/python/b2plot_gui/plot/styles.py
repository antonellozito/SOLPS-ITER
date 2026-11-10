"""Styles of the 2D plot (dataclasses kept by the panels, snapshots and
settings) and the colour scale and contour levels they define."""

from dataclasses import dataclass, field

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import (LinearSegmentedColormap, LogNorm, Normalize,
                               SymLogNorm)

from .. import theme

KINDS_FLAT = ("patch", "contourf", "contour")   # on the R, Z axes
KINDS_SCALAR = KINDS_FLAT + ("surface",)
KINDS_VECTOR = ("quiver", "stream", "quiverstream")


@dataclass
class LayerStyle:
    visible: bool = False
    color: str = "#000000"
    width: float = 0.5
    style: str = "-"
    alpha: float = 1.0
    levels: str = ""            # flux surfaces: psiN or rho levels
    rho: bool = False
    fill_style: str = "empty"   # structure: closed parts "full", hatched
    fill: str = ""              # ("pattern") or not filled, this colour


LAYERS = {
    "structure": ("Structure", LayerStyle(True, "#000000", 1.0,
                                          fill_style="full",
                                          fill="#e0e0e0")),
    "grid": ("B2.5 grid", LayerStyle(True, "#4d4d4d", 0.15)),
    "eirene": ("EIRENE grid", LayerStyle(True, "#8c8c8c", 0.1)),
    "separatrices": ("Separatrices", LayerStyle(True, "#d62728", 1.2)),
    "xpoints": ("X-points", LayerStyle(False, "#d62728", 8.0)),
    "boundary": ("Grid boundary", LayerStyle(False, "#1f3b8c", 0.8)),
    "flux": ("Flux surfaces",
             LayerStyle(False, "#2ca02c", 0.6, ":", 1.0,
                        "0.90 0.95 1.00 1.02 1.04 1.06", rho=True)),
    "midplanes": ("Midplanes", LayerStyle(False, "#1f77b4", 1.5, "--")),
    "targets": ("Divertor targets", LayerStyle(False, "#ff7f0e", 2.0)),
    "chords": ("Chords (*.chords files), numbered",
               LayerStyle(False, "#9467bd", 0.8)),
    "trajectories": ("Trajectories (colours of b2plot)",
                     LayerStyle(False, "#000000", 0.6)),
}
ZORDER = {"grid": 3.0, "eirene": 3.1, "flux": 3.2, "boundary": 3.3,
          "structure": 3.45, "separatrices": 3.5, "midplanes": 3.52,
          "targets": 3.55, "xpoints": 3.6, "chords": 3.7,
          "trajectories": 3.75}
FILL_ZORDER = 3.38              # the filled parts of the structure
HATCH = "////"                  # their pattern
PWN = ((0.15, 0.45, 0.68), (1.0, 1.0, 1.0), (0.72, 0.15, 0.15))


@dataclass
class PlotStyle:
    kind: str = "patch"
    column: int = 0
    mask: str = ""              # cells not zero in this colour, no bar
    cmap: str = "turbo"
    reverse: bool = False
    scale: str = "linear"       # linear, log, symlog
    auto: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    levels: int = 20
    colorbar: bool = True
    edges: bool = False
    line_mono: bool = False     # contour lines in one colour
    line_color: str = "#000000"
    line_width: float = 0.8
    line_style: str = "-"
    line_labels: bool = False
    normalize: bool = False
    arrow_length: float = 0.0   # metres, 0 = automatic
    arrow_width: float = 1.0
    every: int = 0              # one arrow every n cells, 0 = automatic
    color_by_magnitude: bool = True
    arrow_color: str = "#000000"
    bw: bool = False            # black and white (b2plot bw)
    cell_values: bool = False   # values written in the cells when few
    num_arrows: int = 1         # arrows along each streamline
    seed_markers: bool = False
    density: float = 1.5
    stream_width: float = 0.8
    stream_color: str = "#1f77b4"
    stream_style: str = "-"
    seeds: list = field(default_factory=list)
    level_mode: str = "number"  # number, step, list, proportion (b2plot)
    level_step: float = 0.0
    level_list: str = ""
    decades: int = 0            # log scale: decades below the maximum
    fill_lines: bool = False    # contour lines over filled contours
    ix_range: tuple = None      # classical grids: cells shown
    iy_range: tuple = None
    regions: tuple = None       # region numbers shown (None: all)


@dataclass
class LabelStyle:
    """Texts of the plot, as b2plot extl, xlab, ylab, glob, lbsz, bold,
    noax and xcol; empty texts take the automatic ones."""
    title: str = ""
    extra: str = ""
    xlabel: str = ""
    ylabel: str = ""
    header: str = ""
    size: float = 1.0
    bold: bool = False
    axes: bool = True
    color: str = "#000000"


@dataclass
class VectorStyle:
    """A vector quantity drawn over the plot as arrows or streamlines."""
    length: float = 0.0         # arrow length (m), 0 = automatic
    width: float = 1.0
    color: str = "#000000"
    column: int = -1            # species, -1: as the plot
    same: bool = False          # all arrows equally long
    stream: bool = False        # streamlines instead of arrows


@dataclass
class WallStyle:
    """A wall quantity drawn as a strip along the wall elements."""
    column: int = 0
    cmap: str = "viridis"
    log: bool = False
    width: float = 6.0          # points
    colorbar: bool = True


@dataclass
class OverlayStyle:
    """Contour lines of a further quantity over the plot."""
    line_levels: int = 10
    line_log: bool = False
    line_color: str = "#ffffff"
    line_width: float = 0.6
    line_style: str = "-"
    line_labels: bool = False


def norm_for(values, style):
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if style.scale == "log":
        v = v[v > 0]
    if v.size == 0:
        lo, hi = (1.0, 10.0) if style.scale == "log" else (0.0, 1.0)
    else:
        lo, hi = float(v.min()), float(v.max())
    if not style.auto:
        lo, hi = style.vmin, style.vmax
    if style.scale == "log":
        lo = lo if lo > 0 else (hi * 1e-6 if hi > 0 else 1.0)
        hi = hi if hi > lo else lo * 10.0
        decades = getattr(style, "decades", 0)
        if decades > 0:
            lo = max(lo, hi / 10.0 ** decades)
        return LogNorm(vmin=lo, vmax=hi)
    if hi <= lo:
        hi = lo + (abs(lo) if lo else 1.0)
    if style.scale == "symlog":
        top = max(abs(lo), abs(hi))
        return SymLogNorm(linthresh=top * 1e-3, vmin=lo, vmax=hi)
    return Normalize(vmin=lo, vmax=hi)


def even_levels(norm, n):
    t = np.linspace(0.0, 1.0, max(int(n), 1) + 1)
    return np.unique(np.asarray(norm.inverse(t), float))


def _floats(text):
    out = []
    for item in text.replace(",", " ").split():
        try:
            out.append(float(item))
        except ValueError:
            pass
    return np.array(out, float)


def levels_for(st, norm, given=None):
    """Contour levels for the level mode of st: a number of levels over
    the range, a step from the minimum, a list, or the levels b2plot
    computed (clvp, eclvp)."""
    if st.level_mode == "proportion" and given is not None:
        lev = np.unique(np.asarray(given, float))
    elif st.level_mode == "list":
        lev = np.unique(_floats(st.level_list))
    elif st.level_mode == "step" and st.level_step > 0:
        n = min(int((norm.vmax - norm.vmin) / st.level_step), 1000)
        lev = np.unique(norm.vmin + st.level_step * np.arange(n + 1))
    else:
        lev = even_levels(norm, st.levels)
    if isinstance(norm, LogNorm):
        lev = lev[lev > 0]
    return lev if len(lev) >= 2 else even_levels(norm, st.levels)


def cmap_for(style, norm=None):
    """Colormap of a style: grey in black and white, pwn for the norm; as
    drawn in the current theme."""
    if style.cmap == "pwn" and norm is not None and not style.bw:
        return theme.cmap(pwn(norm, style.reverse))
    cmap = colormaps["Greys" if style.bw else style.cmap.replace(
        "pwn", "RdBu_r")]
    return theme.cmap(cmap.reversed() if style.reverse else cmap)


def pwn(norm, reverse=False):
    """Red (positive), white (zero), blue (negative) as MATLAB colorbarpwn
    (reverse: its rev, blue positive): white at the minimum when all values
    are positive, at the maximum when all are negative, else at zero with
    the same colour step per unit on both sides."""
    lo, hi = float(norm(norm.vmin)), float(norm(norm.vmax))
    zero = float(norm(0.0)) if norm.vmin < 0.0 < norm.vmax else None
    blue, white, red = (np.array(c) for c in PWN)
    if reverse:
        blue, red = red, blue
    if zero is None:
        ends = [(0.0, white), (1.0, red)] if norm.vmin >= 0.0 else [
            (0.0, blue), (1.0, white)]
    else:
        span = max(zero - lo, hi - zero)
        ends = [(0.0, white + (blue - white) * (zero - lo) / span),
                (zero, white),
                (1.0, white + (red - white) * (hi - zero) / span)]
    return LinearSegmentedColormap.from_list("pwn", ends)
