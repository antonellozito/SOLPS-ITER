"""What the chords of Run movies (tools.control) and of Run tracing
(timedata.tracing) draw alike: a chord on the 2D plot (its line as its tab
says, a dot at its start, an arrow at its end, its number), its line
integrals or averages against the chord number, and in time (a curve per
chord, each with its own options)."""

import numpy as np
from matplotlib.ticker import FixedLocator, FormatStrFormatter, \
    MaxNLocator

from .. import theme
from . import measure

SPAN = "#7f7f7f"                    # the line at the time shown


def draw_chord(ax, number, parts, look, zorder=6.5):
    """Artists of a chord: parts, its [(n, 2)] pieces in order; look,
    (colour, width, line style, number shown)."""
    colour, width, style, shown = look
    colour = theme.rgb(colour)
    out = []
    for xy in parts:
        line, = ax.plot(xy[:, 0], xy[:, 1], color=colour, linestyle=style,
                        linewidth=width, zorder=zorder)
        out.append(line)
    first, last = parts[0], parts[-1]
    start, = ax.plot(first[:1, 0], first[:1, 1], color=colour,
                     linestyle="None", marker="o",
                     markersize=3.0 + 1.5 * width, zorder=zorder + 0.1)
    out.append(start)
    if len(last) < 2:
        return out
    d = last[-1] - last[-2]
    if not np.hypot(*d) > 0:
        return out
    d = d / np.hypot(*d)
    out.append(ax.annotate(
        "", xy=tuple(last[-1]), xytext=tuple(last[-1] - 1e-6 * d),
        arrowprops=dict(arrowstyle="-|>", color=colour, lw=width,
                        shrinkA=0, shrinkB=0,
                        mutation_scale=8.0 + 2.0 * width),
        zorder=zorder + 0.1))
    if shown:
        out.append(ax.annotate(
            "%d" % number, xy=tuple(last[-1]), xytext=tuple(
                (9.0 + width) * d), textcoords="offset points",
            color=colour, fontsize=9, fontweight="bold", ha="center",
            va="center", zorder=zorder + 0.1, annotation_clip=True))
    return out


def sums_draw(title, y, key, unit, others=(), now=1.0):
    """draw(ax, options) of the line integrals or averages (key) y of the
    chords 1 to n against the chord number; others: [(position along the
    frames, values)] drawn first, small (all the frames of a movie; then
    another frame only moves the markers of the one shown). y
    [(species, values)]: markers per species on each chord."""
    if len(y) and isinstance(y[0], tuple):
        return species_sums_draw(title, y, key, unit)
    n = np.arange(1, len(y) + 1)

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        for t, v in others:
            ln, = ax.plot(n, v, linestyle="None", marker="o",
                          label="_frame")
            ln.frame = (t, False)
        ln, = ax.plot(n, y, linestyle="None", marker="o")
        ln.frame, ln.moves = (now, True), bool(others)
        ax.xaxis.set_major_locator(FixedLocator(n) if len(n) <= 20
                                   else MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
        ax.set_xlim(0.5, len(n) + 0.5)
        ax.set_xlabel("chord")
        ax.set_ylabel("line %s (%s)" % (key, measure.math_unit(unit)))
    if others:
        draw.key = ("sums", title, key, unit, len(y), hash(np.array(
            [np.ravel(np.asarray(v, float)) for _, v in others]).tobytes()))
        draw.current = lambda options: [(n, y)]
    return draw


def species_sums_draw(title, series, key, unit):
    """draw(ax, options) of the line integrals or averages (key) of several
    species (series [(species, values of the chords 1 to n)]): markers of
    each species on the line of each chord, with its own options."""
    n = np.arange(1, len(series[0][1]) + 1) if series else np.arange(1, 2)

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        for label, y in series:
            ax.plot(n, y, linestyle="None", marker="o", label=label)
        ax.xaxis.set_major_locator(FixedLocator(n) if len(n) <= 20
                                   else MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
        ax.set_xlim(0.5, len(n) + 0.5)
        if len(series) > 1:
            ax.legend(fontsize="small")
        ax.set_xlabel("chord")
        ax.set_ylabel("line %s (%s)" % (key, measure.math_unit(unit)))
    return draw


def traces_draw(title, t, curves, t_now, key, unit, xlabel="time (s)"):
    """draw(ax, options) of the line integrals or averages (key) of the
    chords in time: curves [(label, values at t)], a curve each, the time
    shown dashed (another time only moves it)."""
    t = np.asarray(t, float)

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        for label, y in curves:
            ax.plot(t, y, label=label)
        if t_now is not None:
            ln = ax.axvline(t_now, color=SPAN, linestyle="--",
                            linewidth=0.8)
            ln.frame, ln.moves = (1.0, False), True     # no options
        if len(t) > 1:
            ax.set_xlim(t[0], t[-1])
        ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 4))
        if len(curves) > 1:
            ax.legend(fontsize="small")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("line %s (%s)" % (key, measure.math_unit(unit)))
    if t_now is not None:
        draw.key = ("traces", title, key, unit, xlabel, tuple(
            label for label, _ in curves), hash(t.tobytes()), hash(np.array(
                [np.ravel(np.asarray(y, float)) for _, y in curves]
            ).tobytes()) if curves else 0)
        draw.current = lambda options: [([t_now, t_now], [0.0, 1.0])]
    return draw


def traces_rows(t, sums, units, tname="time (s)", names=None):
    """Header and rows of the time traces: per chord (or per species of
    names) its integral and average (sums: [(integrals, averages)] of the
    chords 1 to n, or of the species)."""
    header = [tname]
    for k in range(len(sums)):
        name = names[k] if names else "chord %d" % (k + 1)
        header += ["%s integral (%s)" % (name, units[0]),
                   "%s average (%s)" % (name, units[1])]
    rows = [[ti] + [float(v[j]) for s in sums for v in s]
            for j, ti in enumerate(t)]
    return header, rows


def fresh_limits(view, key):
    """The y limits of a plot of the sums automatic again after the other
    sums (key) were chosen."""
    if key != getattr(view, "shown", key):
        for e in view.options.limits[2:]:
            e.clear()
    view.shown = key


def two_rows(integral, average, units):
    """The text of a chord tab: its line integral and line average (lists
    [(species, value)]: those of each species)."""
    html = measure.html_unit
    if isinstance(integral, list):
        return "Integral along the line (%s): %s<br>Average along the " \
            "line (%s): %s" % (html(units[0]), ", ".join(
                "%s %.4g" % kv for kv in integral), html(units[1]),
                ", ".join("%s %.4g" % kv for kv in average))
    return "Integral along the line: %.5g %s<br>Average along the line: " \
        "%.5g %s" % (integral, html(units[0]), average, html(units[1]))
