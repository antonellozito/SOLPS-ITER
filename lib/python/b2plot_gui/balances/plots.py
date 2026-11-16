"""What the balance section and its extensions draw: panels of lines
built from a Result (the total balance of each of its two parts: along
the radial coordinate and along the flux tubes; the decomposition of one
of their lines, the terms
of a group or the strata of an EIRENE term), the equations shown over
them, and the drawing on a matplotlib axes."""

import textwrap
from dataclasses import dataclass, field

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.legend_handler import HandlerLineCollection

from ...b2plot import labels
from .. import theme
from ..tools.figure import LogLabels
from . import style
from .kinds import KINDS

COORDINATES = (("rhop", "ρ poloidal"),
               ("dssep", "Distance from separatrix"))
XLABELS = {"rhop": r"$\rho_\mathrm{pol}$"}


@dataclass
class Series:
    """One line: values y at x (the panel x unless given), its colour and
    style, and what a click on it opens (key, None: nothing); gradient:
    coloured from blue (first point: upstream, inner) to red (last point:
    downstream, outer); term: what it is, for its equation ("flux",
    "radial" or "source", Term; "group", [Term])."""
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
    role: str = None                # its colour shared (style.colour)


@dataclass
class Panel:
    title: str
    xlabel: str
    ylabel: str
    x: np.ndarray
    series: list = field(default_factory=list)
    equation: str = ""
    side: str = ""                  # the part of the result: "ends", "cut"


def _unit(result):
    return labels.any_to_mathtext("(%s)" % result.unit)


def _nonzero(y):
    return np.any(np.asarray(y) != 0)


# ------------------------------------------------------------- level 2
WORDS = {   # of the plots of each kind: where the coordinates start,
    #         the subscripts of the flux in and out, the variable of the
    #         flux across, the names of the lines of the level 2 plots
    "parallel": dict(
        coord_at="upstream", distance_from="downstream", sub=("up", "down"),
        var="s", inflow="Upstream flux (into the volume)",
        outflow="Downstream flux (out of the volume)",
        ends="Sources, poloidally integrated",
        across="Flux through the volume", cut="Sources of the slices"),
    "radial": dict(
        coord_at="start", distance_from="start", sub=("in", "out"),
        var="r", inflow="Inner flux (into the volume)",
        outflow="Outer flux (out of the volume)",
        ends="Sources, radially integrated",
        across="Flux across the volume", cut="Sources of the flux tubes")}


def _xlabel(kind, coord):
    if coord == "dssep":
        return "Distance from the separatrix at the %s surface (cm)" % \
            WORDS[kind]["coord_at"]
    return XLABELS[coord]


def _dlabel(kind, distance):
    return "%s distance from the %s surface (m)" % (
        distance.capitalize(), WORDS[kind]["distance_from"])


def axis(result, part, coord, distance):
    """x and x label of part ("ends" or "cut") of result: the radial
    coordinate coord or the distance along the flux tubes."""
    p = result.part(part)
    return p.x, (_xlabel(result.kind, coord) if p.axis == "radial" else
                 _dlabel(result.kind, distance))


def total(result, terms, axis_, coord, residuals, area_text, distance):
    """Total radial (axis_ "radial") or poloidal balance: the part of the
    result along axis_, per unit with ends the flux in and out and the
    sources, or the flux across the boundaries of the units cut (coloured
    from the first to the last) and their sources; residuals."""
    kind = KINDS[result.kind]
    w = WORDS[kind.key]
    part = kind.part(axis_)
    p = result.part(part)
    _, xlabel = axis(result, part, coord, distance)
    c = style.colour
    if part == "ends":
        lines = [Series(w["inflow"], p.inflow.sum(1), c("up"),
                        key=("ends", "in"), role="up"),
                 Series(w["outflow"], p.outflow.sum(1), c("down"),
                        key=("ends", "out"), role="down")]
    else:                               # from the up to the down colour
        lines = [Series(w["across"], p.across.sum(1), c("up"),
                        gradient=True, key=("cut", "across"), x=p.edges,
                        role="across")]
    lines.append(Series(w[part], p.src.sum(1), c("source"),
                        key=(part, "src"), role="source"))
    if residuals:
        lines += [Series("Residual (B2.5)", p.code, c("code"), role="code"),
                  Series("Residual (post-processing)", p.post, c("post"),
                         style="--", role="post")]
    text = TEXTS[(kind.key, part)](terms.symbol, distance, area_text)
    return Panel("Total %s balance" % axis_, xlabel, _unit(result), p.x,
                 lines, text, side=part)


FIXED_AREAS = {     # quantities with their own areas
    "totpress": lambda reverse: ", per face at the %s end" % (
        "upstream" if reverse else "downstream"),
    "force": lambda reverse: "; every term per ion, over the ions "
    "n<sub>a</sub>V of a cell (radial balance: of the first cell of each "
    "flux tube; poloidal balance: of each cell)"}


def area_text(quantity, areatype, areaend, reverse, kind="parallel"):
    """What the terms of the level 2 plots are divided by, in words."""
    k = KINDS[kind]
    if quantity in FIXED_AREAS and quantity not in k.left_out:
        return FIXED_AREAS[quantity](reverse)
    if areatype == "none":
        return ""
    return "; all divided by the %s area of the %s surface" % (
        areatype, dict(k.area_ends)[areaend].lower())


def tubes_text(s, distance, area):
    """Explanation of the flux tubes between their ends (parallel
    balance; s: symbol of the flux)."""
    return ("%s<sub>up</sub>(x) &minus; %s<sub>down</sub>(x) + S(x) = "
            "R(x), for each flux tube of the volume: %s<sub>up</sub> flows "
            "in through the upstream surface, %s<sub>down</sub> out "
            "through the downstream surface and the walls, S = &int; "
            "sources dV over the tube in the volume (radial transport into "
            "the tube included); R: residual of B2.5, or post-processed as "
            "%s<sub>up</sub> &minus; %s<sub>down</sub> + S%s." % (
                s, s, s, s, s, s, area))


def slices_text(s, distance, area):
    """Explanation of the slices cut (parallel balance)."""
    return ("%s(s<sub>k</sub>) &minus; %s(s<sub>k+1</sub>) + S<sub>k</sub> "
            "= R<sub>k</sub>, for each slice k of the volume between the "
            "surfaces at s<sub>k</sub> and s<sub>k+1</sub> (s: %s distance "
            "from the downstream surface along the flux tube next to the "
            "separatrix): %s(s) flows through all the tubes of the volume, "
            "S<sub>k</sub> = &int; sources dV over the slice (transport "
            "through its sides and walls included); R: residual of B2.5, "
            "or post-processed%s." % (s, s, distance, s, area))


def columns_text(s, distance, area):
    """Explanation of the slices between their ends (radial balance)."""
    return ("%s<sub>in</sub>(s) &minus; %s<sub>out</sub>(s) + S(s) = R(s), "
            "for each slice of the volume (s: %s distance from the start "
            "surface along the flux tube next to the separatrix): "
            "%s<sub>in</sub> flows in through the inner surface, "
            "%s<sub>out</sub> out through the outer surface, S = &int; "
            "sources dV over the slice (poloidal transport into the slice "
            "included); R: residual of B2.5, or post-processed as "
            "%s<sub>in</sub> &minus; %s<sub>out</sub> + S%s." % (
                s, s, distance, s, s, s, s, area))


def rings_text(s, distance, area):
    """Explanation of the flux tubes cut (radial balance)."""
    return ("%s(r<sub>k</sub>) &minus; %s(r<sub>k+1</sub>) + S<sub>k</sub> "
            "= R<sub>k</sub>, for each flux tube k of the volume between the "
            "flux surfaces at r<sub>k</sub> and r<sub>k+1</sub>: %s(r) flows "
            "across the flux surfaces through the whole volume, S<sub>k</sub>"
            " = &int; sources dV over the tube (transport through its ends "
            "included); R: residual of B2.5, or post-processed%s." % (
                s, s, s, area))


TEXTS = {("parallel", "ends"): tubes_text, ("parallel", "cut"): slices_text,
         ("radial", "ends"): columns_text, ("radial", "cut"): rings_text}


# ------------------------------------------------------------- level 3
SOURCES_TEXT = "S = &Sigma;<sub>g</sub> S<sub>g</sub>: the sources by " \
    "group; a group marked ▸ opens its terms (EIRENE: its strata)."


def parts_text(s, sub, var="s"):
    """Explanation of the parts of a flux (sub: of the flux in or out, or
    "" for the flux across, function of var)."""
    if sub:
        return "%s<sub>%s</sub> = &Sigma;<sub>k</sub> %s<sub>%s</sub>" \
            "<sub>,k</sub>: the parts of the flux of B2.5." % (s, sub, s, sub)
    return "%s(%s) = &Sigma;<sub>k</sub> %s<sub>k</sub>(%s): the parts of " \
        "the flux of B2.5." % (s, var, s, var)


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


def decomposition(result, terms, which, coord, distance):
    """Level 3: the decomposition of the line which ((part, "in"), (part,
    "out"), (part, "across"), (part, "src")): flux parts, or the sources
    by group (a group with several terms or with strata opens its own
    plot)."""
    kind = KINDS[result.kind]
    w = WORDS[kind.key]
    s = terms.symbol
    part, what = which
    p = result.part(part)
    x, xlabel = axis(result, part, coord, distance)
    lines = []
    if what in ("in", "out", "across"):
        values = {"in": p.inflow, "out": p.outflow, "across": p.across}[what]
        if what == "across":
            x = p.edges
        for k, t in enumerate(result.fluxes):
            if _nonzero(values[:, k]):
                c, st = style.cycle(len(lines))
                lines.append(Series(t.name, values[:, k], c, st,
                                    term=(kind.flux_role, t)))
        name = {"in": "inflow", "out": "outflow", "across": "across"}[what]
        title = w[name].split(" (")[0] + " by part"
        sub = {"in": w["sub"][0], "out": w["sub"][1], "across": ""}[what]
        eq = parts_text(s, sub, w["var"])
    else:
        values = p.src
        for name, cols in groups(p.sources, values):
            y = values[:, cols].sum(1)
            if not _nonzero(values[:, cols]):
                continue
            live = [k for k in cols if _nonzero(values[:, k])]
            one = len(live) == 1 and not p.sources[live[0]].parts
            label = p.sources[live[0]].name if one else name
            key = (part, "group", name) if _expandable(
                p.sources, values, cols) else None
            term = ("source", p.sources[live[0]]) if one else \
                ("group", [p.sources[k] for k in live])
            c, st = style.cycle(len(lines))
            lines.append(Series(label, y, c, st,
                                width=1.8 if key else 1.5, key=key,
                                term=term))
        title = "Sources by group" + w[part][len("Sources"):]
        eq = SOURCES_TEXT
    return Panel(title, xlabel, _unit(result), x, lines, eq, side=part)


# ------------------------------------------------------------- level 4
def members(result, terms, key, coord, distance, strata):
    """Level 4: the terms of a group of sources, the strata of its EIRENE
    terms (recycling strata clickable: their segments on the 2D plot)."""
    part, _, name = key
    p = result.part(part)
    sources, values = p.sources, p.src
    cols = dict(groups(sources, values))[name]
    x, xlabel = axis(result, part, coord, distance)
    lines, strata_lines = [], False
    for k in cols:
        t = sources[k]
        if not _nonzero(values[:, k]):
            continue
        if not t.parts:
            c, st = style.cycle(len(lines))
            lines.append(Series(t.name, values[:, k], c, st,
                                term=("source", t)))
            continue
        strata_lines = True
        for sub, arr in t.parts:
            per = p.sum(arr)
            for j in range(per.shape[1]):
                if not _nonzero(per[:, j]):
                    continue
                label = strata.label(j) + (", " + sub if sub else "")
                c, st = style.cycle(len(lines))
                lines.append(Series(label, per[:, j], c, st, key=(
                    "stratum", j) if strata.recycling(j) else None))
        rest = values[:, k] - sum(p.sum(arr).sum(1) for _, arr in t.parts)
        if _nonzero(np.round(rest, 12)) and \
                np.max(np.abs(rest)) > 1e-9 * np.max(np.abs(values[:, k])):
            c, st = style.cycle(len(lines))
            lines.append(Series("Not by stratum", rest, c, st))
    return Panel(name, xlabel, _unit(result), x, lines,
                 members_text(strata_lines), side=part)


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
    """True if a click on the line s opens its parts."""
    return s.key is not None and s.key[0] != "stratum"


def draw(ax, panel, legend_box=None, marks=True, grid=True, logy=False):
    """The panel on ax (cleared, its box 4:3); the legend inside the box
    for few lines, else right of it, or in legend_box (x, top, width,
    height in figure fractions) with the font that fits; marks: ▸ after
    the names of the lines that open their parts (on the screen, not in
    saved pictures); grid: the grid lines; logy: a logarithmic y axis
    (values not positive left out). Returns [(artist, series)] and the
    legend."""
    fig_bg, ax_bg, text, grid_colour = style.axes_colors()
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
    if logy:                            # its labels as narrow as linear ones
        ax.set_yscale("log", nonpositive="mask")
        ax.yaxis.set_major_formatter(LogLabels())
        ax.yaxis.set_minor_formatter(LogLabels())
    ax.autoscale(axis="y")
    ax.relim()
    ax.autoscale_view(scalex=False)
    ax.set_title(panel.title, color=text, fontsize="medium")
    ax.set_xlabel(panel.xlabel, color=text)
    ax.set_ylabel(panel.ylabel, color=text)
    ax.tick_params(colors=text, labelsize="small")
    for spine in ax.spines.values():
        spine.set_color(text)
    if grid:
        ax.grid(True, color=grid_colour, linewidth=0.6)
    else:
        ax.grid(False)
    if not logy:
        ax.axhline(0.0, color=text, linewidth=0.6, linestyle="--",
                   alpha=0.6, zorder=1.5)
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
    legend.get_frame().set_edgecolor(grid_colour)
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
