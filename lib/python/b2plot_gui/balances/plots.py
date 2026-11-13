"""What the balance windows draw: panels of lines built from a Result (the
total radial and poloidal balance, the decomposition of one of their
lines, the terms of a group or the strata of an EIRENE term), the
equations shown over them, and the drawing on a matplotlib axes."""

import textwrap
from dataclasses import dataclass, field

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.legend_handler import HandlerLineCollection

from ...b2plot import labels
from .. import theme
from . import style

COORDINATES = (("rhop", "ρ poloidal"),
               ("dssep", "Distance from separatrix"))
XLABELS = {"rhop": r"$\rho_\mathrm{pol}$",
           "dssep": "Distance from the separatrix at the upstream surface "
                    "(cm)"}


@dataclass
class Series:
    """One line: values y at x (the panel x unless given), its colour and
    style, and what a click on it opens (key, None: nothing); gradient:
    coloured from the upstream blue (first point) to the downstream red
    (last point); term: what it is, for its equation ("flux" or "source",
    Term; "group", [Term])."""
    label: str
    y: np.ndarray
    color: str
    style: str = "-"
    width: float = 1.5
    marker: str = None
    key: object = None
    gradient: bool = False
    x: np.ndarray = None
    term: tuple = None
    total: bool = False             # the sum of the other lines


@dataclass
class Panel:
    title: str
    xlabel: str
    ylabel: str
    x: np.ndarray
    series: list = field(default_factory=list)
    equation: str = ""
    reverse_x: bool = False
    side: str = ""                  # "radial" or "poloidal"


def _unit(result):
    return labels.any_to_mathtext("(%s)" % result.unit)


def _nonzero(y):
    return np.any(np.asarray(y) != 0)


def _sym(terms):
    return terms.symbol


# ------------------------------------------------------------- level 2
def radial(result, terms, coord, residuals, level, area_text):
    """Total radial balance: per flux tube, upstream and downstream flux,
    sources, residuals."""
    s = _sym(terms)
    x = result.x
    sm = lambda y: style.smooth(y, level)                  # noqa: E731
    lines = [Series("Upstream flux (into the volume)", sm(result.up.sum(1)),
                    style.UP, marker=".", key=("radial", "up")),
             Series("Downstream flux (out of the volume)",
                    sm(result.down.sum(1)), style.DOWN, marker=".",
                    key=("radial", "down")),
             Series("Sources, poloidally integrated", sm(result.src.sum(1)),
                    style.SOURCE, marker=".", key=("radial", "src"))]
    if residuals:
        lines += [Series("Residual (B2.5)", sm(result.code), style.CODE),
                  Series("Residual (post-processing)", sm(result.post),
                         style.POST, style="--")]
    return Panel("Total radial balance", XLABELS[coord], _unit(result), x,
                 lines, radial_text(s, area_text), side="radial")


def area_text(quantity, areatype, areaend, reverse):
    """What the terms of the level 2 plots are divided by, in words."""
    if quantity == "totpress":
        return ", per face at the %s end" % ("upstream" if reverse else
                                             "downstream")
    if quantity == "force":
        return "; every term per ion, over the ions n<sub>a</sub>V of a " \
            "cell (radial balance: of the first cell of each flux tube; " \
            "poloidal balance: of each cell)"
    if areatype == "none":
        return ""
    return "; all divided by the %s area of the %s surface" % (
        areatype, "upstream" if areaend == "up" else "downstream")


def area_texts(quantity):
    """Every text area_text gives for the quantity."""
    return {area_text(quantity, t, e, r) for t in ("none", "parallel",
                                                   "contact")
            for e in ("up", "down") for r in (False, True)}


def radial_text(s, area):
    """Explanation of the total radial balance (s: symbol of the flux)."""
    return ("%s<sub>up</sub>(x) &minus; %s<sub>down</sub>(x) + S(x) = "
            "R(x), for each flux tube of the volume: %s<sub>up</sub> flows "
            "in through the upstream surface, %s<sub>down</sub> out "
            "through the downstream surface and the walls, S = &int; "
            "sources dV over the tube in the volume (radial transport into "
            "the tube included); R: residual of B2.5, or post-processed as "
            "%s<sub>up</sub> &minus; %s<sub>down</sub> + S%s." % (
                s, s, s, s, s, s, area))


def poloidal_text(s, distance, area):
    """Explanation of the total poloidal balance."""
    return ("%s(s<sub>k</sub>) &minus; %s(s<sub>k+1</sub>) + S<sub>k</sub> "
            "= R<sub>k</sub>, for each slice k of the volume between the "
            "surfaces at s<sub>k</sub> and s<sub>k+1</sub> (s: %s distance "
            "from the downstream surface along the flux tube next to the "
            "separatrix): %s(s) flows through all the tubes of the volume, "
            "S<sub>k</sub> = &int; sources dV over the slice (transport "
            "through its sides and walls included); R: residual of B2.5, "
            "or post-processed%s." % (s, s, distance, s, area))


def all_texts(side):
    """Every explanation a plot of the side ("radial", "poloidal",
    "parts": levels 3 and 4) can show: its label keeps the room of the
    longest, so that the plots keep their size."""
    from .terms import QUANTITIES, SYMBOLS
    from .calc import DISTANCES
    out = set()
    for q, _ in QUANTITIES:
        s = SYMBOLS[q]
        for a in area_texts(q):
            if side == "radial":
                out.add(radial_text(s, a))
            elif side == "poloidal":
                out |= {poloidal_text(s, d, a) for d, _ in DISTANCES}
        if side == "parts":
            out |= {parts_text(s, sub) for sub in ("up", "down", "")}
    if side == "parts":
        out |= {SOURCES_TEXT, members_text(True), members_text(False)}
    return tuple(sorted(out))


def poloidal(result, terms, distance, residuals, level, area_text):
    """Total poloidal balance: flux through the surfaces between the
    slices (coloured from upstream to downstream), sources of the slices,
    residuals."""
    s = _sym(terms)
    sm = lambda y: style.smooth(y, level)                  # noqa: E731
    lines = [Series("Flux through the volume", sm(result.edges.sum(1)),
                    style.UP, gradient=True, key=("poloidal", "flux"),
                    x=result.px_edges, marker="."),
             Series("Sources of the slices", sm(result.psrc.sum(1)),
                    style.SOURCE, marker=".", key=("poloidal", "src"))]
    if residuals:
        lines += [Series("Residual (B2.5)", sm(result.pcode), style.CODE),
                  Series("Residual (post-processing)", sm(result.ppost),
                         style.POST, style="--")]
    return Panel("Total poloidal balance", "%s distance from the "
                 "downstream surface (m)" % distance.capitalize(),
                 _unit(result), result.px, lines,
                 poloidal_text(s, distance, area_text), reverse_x=True,
                 side="poloidal")


# ------------------------------------------------------------- level 3
SOURCES_TEXT = "S = &Sigma;<sub>g</sub> S<sub>g</sub>: the sources by " \
    "group; a group marked ▸ opens its terms (EIRENE: its strata)."


def parts_text(s, sub):
    """Explanation of the parts of a flux (sub: up, down, or "" for the
    poloidal flux)."""
    if sub:
        return "%s<sub>%s</sub> = &Sigma;<sub>k</sub> %s<sub>%s</sub>" \
            "<sub>,k</sub>: the parts of the flux of B2.5." % (s, sub, s, sub)
    return "%s(s) = &Sigma;<sub>k</sub> %s<sub>k</sub>(s): the parts of " \
        "the flux of B2.5." % (s, s)


def members_text(strata):
    """Explanation of the terms (strata) of a group of sources."""
    return "S<sub>g</sub> = &Sigma;<sub>i</sub> S<sub>g,i</sub>: %s" % (
        "the strata of EIRENE (click a recycling stratum: its segments "
        "glow on the 2D plot)." if strata else "the terms of the group.")


def groups(sources, values):
    """[(group name, [column indices])] of the source columns, in order of
    first appearance; terms without a group are their own group."""
    out = []
    for k, t in enumerate(sources):
        g = t.group or t.name
        for name, cols in out:
            if name == g:
                cols.append(k)
                break
        else:
            out.append((g, [k]))
    return out


def _expandable(sources, values, cols):
    live = [k for k in cols if _nonzero(values[:, k])]
    return len(live) > 1 or any(sources[k].parts for k in live)


def decomposition(result, terms, which, coord, distance, level):
    """Level 3: the decomposition of the line which (("radial", "up"),
    ...): flux parts, or the sources by group (a group with several terms
    or with strata opens its own window)."""
    s = _sym(terms)
    sm = lambda y: style.smooth(y, level)                  # noqa: E731
    side, part = which
    if side == "radial":
        x, xlabel = result.x, XLABELS[coord]
    else:
        x, xlabel = result.px, "%s distance from the downstream surface " \
            "(m)" % distance.capitalize()
    edge = side == "poloidal" and part == "flux"
    if edge:
        x = result.px_edges
    lines = []
    if part in ("up", "down", "flux"):
        values = {"up": result.up, "down": result.down,
                  "flux": result.edges}[part]
        for k, t in enumerate(result.fluxes):
            if _nonzero(values[:, k]):
                c, st = style.cycle(len(lines))
                lines.append(Series(t.name, sm(values[:, k]), c, st,
                                    term=("flux", t)))
        title = {"up": "Upstream flux by part", "down": "Downstream flux "
                 "by part", "flux": "Flux through the volume by part"}[part]
        sub = {"up": "up", "down": "down", "flux": ""}[part]
        eq = parts_text(s, sub)
        total = values.sum(1)
    else:
        sources = result.sources if side == "radial" else result.psources
        values = result.src if side == "radial" else result.psrc
        for name, cols in groups(sources, values):
            y = values[:, cols].sum(1)
            if not _nonzero(values[:, cols]):
                continue
            live = [k for k in cols if _nonzero(values[:, k])]
            label = name if len(live) > 1 or sources[live[0]].parts else \
                sources[live[0]].name
            key = (side, "group", name) if _expandable(
                sources, values, cols) else None
            one = len(live) == 1 and not sources[live[0]].parts
            term = ("source", sources[live[0]]) if one else \
                ("group", [sources[k] for k in live])
            c, st = style.cycle(len(lines))
            lines.append(Series(label, sm(y), c, st,
                                width=1.8 if key else 1.5, key=key,
                                term=term))
        title = "Sources by group" + (", poloidally integrated" if
                                      side == "radial" else
                                      " of the slices")
        eq = SOURCES_TEXT
        total = values.sum(1)
    lines.append(Series("Sum", sm(total), "#000000", width=2.4,
                        style="-", total=True))
    return Panel(title, xlabel, _unit(result), x, lines, eq,
                 reverse_x=side == "poloidal", side=side)


# ------------------------------------------------------------- level 4
def members(result, terms, key, coord, distance, level, strata):
    """Level 4: the terms of a group of sources, the strata of its EIRENE
    terms (recycling strata clickable: their segments on the 2D plot)."""
    side, _, name = key
    sm = lambda y: style.smooth(y, level)                  # noqa: E731
    sources = result.sources if side == "radial" else result.psources
    values = result.src if side == "radial" else result.psrc
    cols = dict(groups(sources, values))[name]
    if side == "radial":
        x, xlabel, summed = result.x, XLABELS[coord], result.radial_sum
    else:
        x, xlabel, summed = result.px, "%s distance from the downstream " \
            "surface (m)" % distance.capitalize(), result.poloidal_sum
    lines, strata_lines = [], False
    for k in cols:
        t = sources[k]
        if not _nonzero(values[:, k]):
            continue
        if not t.parts:
            c, st = style.cycle(len(lines))
            lines.append(Series(t.name, sm(values[:, k]), c, st,
                                term=("source", t)))
            continue
        strata_lines = True
        for part, arr in t.parts:
            per = summed(arr)
            for j in range(per.shape[1]):
                if not _nonzero(per[:, j]):
                    continue
                label = strata.label(j) + (", " + part if part else "")
                c, st = style.cycle(len(lines))
                lines.append(Series(label, sm(per[:, j]), c, st, key=(
                    "stratum", j) if strata.recycling(j) else None))
        rest = values[:, k] - sum(summed(arr).sum(1) for _, arr in t.parts)
        if _nonzero(np.round(rest, 12)) and \
                np.max(np.abs(rest)) > 1e-9 * np.max(np.abs(values[:, k])):
            c, st = style.cycle(len(lines))
            lines.append(Series("Not by stratum", sm(rest), c, st))
    lines.append(Series("Sum", sm(values[:, cols].sum(1)), "#000000",
                        width=2.4, total=True))
    return Panel(name, xlabel, _unit(result), x, lines,
                 members_text(strata_lines),
                 reverse_x=side == "poloidal", side=side)


# -------------------------------------------------------------- drawing
class GradientHandler(HandlerLineCollection):
    """Legend entry of a line coloured along x: the same colours."""

    def create_artists(self, legend, orig, xdescent, ydescent, width, height,
                       fontsize, trans):
        n = 12
        x = np.linspace(-xdescent, width - xdescent, n + 1)
        y = np.full(n + 1, height / 2.0 - ydescent)
        seg = np.stack((np.column_stack((x[:-1], y[:-1])),
                        np.column_stack((x[1:], y[1:]))), axis=1)
        lc = LineCollection(seg, colors=style.gradient(n),
                            linewidths=orig.get_linewidths()[0],
                            transform=trans)
        return [lc]


BOX_ASPECT = 0.75                   # every plot box 4 wide, 3 high
LEGEND_FITS = (("small", 1), ("x-small", 1), ("x-small", 2),
               ("xx-small", 2), ("xx-small", 3))


def opens(s):
    """True if a click on the line s opens a window (its parts)."""
    return s.key is not None and s.key[0] != "stratum"


def draw(ax, panel, legend_box=None, marks=True):
    """The panel on ax (cleared, its box 4:3); the legend inside the box
    for few lines, else right of it, or in legend_box (x, top, width,
    height in figure fractions) with the font that fits; marks: ▸ after
    the names of the lines that open a window (on the screen, not in
    saved pictures). Returns [(artist, series)] and the legend."""
    fig_bg, ax_bg, text, grid = style.axes_colors()
    ax.clear()
    ax.set_box_aspect(BOX_ASPECT)
    ax.set_facecolor(ax_bg)
    out = []
    for s in panel.series:
        x = panel.x if s.x is None else s.x
        name = s.label + (" ▸" if marks and opens(s) else "")
        color = style.line(s.color) if s.color != "#000000" else text
        if s.gradient:
            pts = np.column_stack((x, s.y))
            seg = np.stack((pts[:-1], pts[1:]), axis=1)
            span = (x[-1] - x[0]) or 1.0
            t = (np.asarray(x, float) - x[0]) / span     # along the volume
            art = LineCollection(seg, colors=style.gradient(
                len(seg), 0.5 * (t[:-1] + t[1:])), linewidths=s.width,
                label=name, linestyles=s.style)
            ax.add_collection(art)
            if s.marker:
                ax.scatter(x, s.y, s=9, c=style.gradient(len(x), t),
                           zorder=3)
        else:
            art, = ax.plot(x, s.y, color=color, linestyle=s.style,
                           linewidth=s.width, marker=s.marker,
                           markersize=4, label=name)
        out.append((art, s))
    xs = np.concatenate([np.asarray(panel.x if s.x is None else s.x, float)
                         for s in panel.series] or [np.zeros(1)])
    ok = np.isfinite(xs)
    if ok.any() and xs[ok].max() > xs[ok].min():
        ax.set_xlim(xs[ok].min(), xs[ok].max())
    ax.autoscale(axis="y")
    ax.relim()
    ax.autoscale_view(scalex=False)
    ax.set_title(panel.title, color=text, fontsize="medium")
    ax.set_xlabel(panel.xlabel, color=text)
    ax.set_ylabel(panel.ylabel, color=text)
    ax.tick_params(colors=text, labelsize="small")
    for spine in ax.spines.values():
        spine.set_color(text)
    ax.grid(True, color=grid, linewidth=0.6)
    ax.axhline(0.0, color=text, linewidth=0.6, linestyle="--", alpha=0.6,
               zorder=1.5)
    handles = [a for a, _ in out]
    if legend_box is not None:
        legend = _fitted(ax, handles, [a.get_label() for a, _ in out],
                         legend_box)
    else:
        outside = len(out) > 8
        legend = ax.legend(
            handles, [a.get_label() for a, _ in out],
            handler_map={LineCollection: GradientHandler()},
            fontsize="small" if len(out) <= 20 else "x-small",
            loc="upper left" if outside else "best",
            bbox_to_anchor=(1.01, 1.0) if outside else None,
            ncol=1 if len(out) <= 30 else 2, framealpha=0.9)
    legend.get_frame().set_facecolor(fig_bg if theme.is_dark() else
                                     "#ffffff")
    legend.get_frame().set_edgecolor(grid)
    for t in legend.get_texts():
        t.set_color(text)
    ax.figure.set_facecolor(fig_bg)
    return out, legend


def _fitted(ax, handles, labels, box):
    """The legend in its column: long names over two lines, the largest
    font (and fewest columns) whose legend fits the column."""
    x0, top, width, height = box
    fig = ax.figure
    labels = [textwrap.fill(t, 36) for t in labels]
    renderer = fig.canvas.get_renderer()
    for size, ncol in LEGEND_FITS:
        legend = ax.legend(handles, labels, loc="upper left",
                           bbox_to_anchor=(x0, top),
                           bbox_transform=fig.transFigure,
                           handler_map={LineCollection: GradientHandler()},
                           fontsize=size, ncol=ncol, framealpha=0.9,
                           borderaxespad=0.0)
        bb = legend.get_window_extent(renderer).transformed(
            fig.transFigure.inverted())
        if bb.width <= width and bb.height <= height:
            break
    return legend


def table(panel):
    """The values of the panel: [(name, x, [(label, y)])], one table per
    abscissa."""
    tables = {}
    for s in panel.series:
        x = panel.x if s.x is None else s.x
        key = id(x) if s.x is not None else "x"
        tables.setdefault(key, (np.asarray(x), []))[1].append(
            (s.label, np.asarray(s.y)))
    out = []
    for key, (x, cols) in tables.items():
        name = panel.title if key == "x" else panel.title + ", edges"
        out.append((name, x, cols))
    return out
