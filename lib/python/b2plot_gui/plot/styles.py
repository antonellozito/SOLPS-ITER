"""Styles of the 2D plot (dataclasses kept by the panels, snapshots and
settings) and the colour scale and contour levels they define."""

from dataclasses import dataclass, field

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import ListedColormap, LogNorm, Normalize, SymLogNorm

from .. import theme

KINDS_FLAT = ("patch", "contourf", "contour")   # on the R, Z axes
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
    "eirene": ("EIRENE grid", LayerStyle(False, "#8c8c8c", 0.1)),
    "separatrices": ("Separatrices", LayerStyle(True, "#d62728", 1.2)),
    "opoints": ("O-points", LayerStyle(False, "#d62728", 8.0)),
    "xpoints": ("X-points", LayerStyle(False, "#d62728", 8.0)),
    "flux": ("Flux surfaces",
             LayerStyle(False, "#2ca02c", 0.6, ":", 1.0,
                        "0.90 0.95 1.00 1.02 1.04 1.06", rho=True)),
    "midplanes": ("Midplanes", LayerStyle(False, "#1f77b4", 1.5, "--")),
    "targets": ("Targets", LayerStyle(False, "#ff7f0e", 2.0)),
}
LAYER_KEYS = tuple(LAYERS)
ZORDER = {"grid": 3.0, "eirene": 3.1, "flux": 3.2,
          "structure": 3.45, "separatrices": 3.5, "midplanes": 3.52,
          "targets": 3.55, "opoints": 3.6, "xpoints": 3.6}
FILL_ZORDER = 3.38              # the filled parts of the structure
HATCH = "////"                  # their pattern
DIVERGING = ("twilight", "Spectral", "coolwarm", "bwr", "seismic", "berlin",
             "vanimo")          # centre colour at zero (centred)


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
class WallStyle:
    """A wall quantity drawn as a strip along the wall elements: the sum
    of its columns (species), a line width (points) and style, a colour
    map (reversed or not), a scale and a range (auto: of the values)."""
    columns: tuple = (0,)
    width: float = 6.0
    style: str = "-"
    cmap: str = "viridis"
    reverse: bool = False
    scale: str = "linear"
    auto: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    colorbar: bool = True


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
    """Colormap of a style: grey in black and white, a diverging map
    centred on zero for the norm; as drawn in the current theme."""
    cmap = colormaps["Greys" if style.bw else style.cmap]
    if style.reverse:
        cmap = cmap.reversed()
    if style.cmap in DIVERGING and norm is not None and not style.bw:
        cmap = centred(cmap, norm)
    return theme.cmap(cmap)


def centred(cmap, norm, n=256):
    """The diverging map cmap with its centre colour at zero, at the same
    colour step per unit on both sides: of each side as much as the range
    covers (all of it for a range symmetric about zero); from the centre
    at the minimum to the positive end when all values are positive, from
    the negative end to the centre at the maximum when all are negative."""
    x = np.linspace(0.0, 1.0, n)
    if norm.vmin < 0.0 < norm.vmax:
        zero = float(norm(0.0))
        t = 0.5 + 0.5 * (x - zero) / max(zero, 1.0 - zero)
    else:
        t = 0.5 * x + (0.5 if norm.vmin >= 0.0 else 0.0)
    return ListedColormap(cmap(np.clip(t, 0.0, 1.0)),
                          name=cmap.name + "_centred")
