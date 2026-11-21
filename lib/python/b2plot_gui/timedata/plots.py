"""The plots of the run tracing, in the small figures of the tools
(FigureView: the options under them, Save plot, Export): a time trace
(alone, with its mean and standard deviation, its rolling, batch or
phase means), the line sums of a chord with the position of the slider, a
profile at the position (with Show all, those of every position, colours
along them); each with the text of what is shown."""

import re

import numpy as np
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from ..panels.timebox import RANGE
from ..tools.figure import frame_lines
from ..tools.measure import html_unit, math_unit

XLABELS = {"s": "distance along the chord (m)", "R": "R (m)", "Z": "Z (m)",
           "rhop": r"$\rho_p$", "dssep": "distance from the separatrix (m)"}
HEADS = {"s": "s (m)", "R": "R (m)", "Z": "Z (m)", "rhop": "rho_p",
         "dssep": "distance from the separatrix (m)", "phi": "phi (deg)"}
MEANS = {"rolling": "Rolling mean", "batch": "Batch mean",
         "phase": "Phase mean"}
SPAN = "#888888"                    # the frames of a mean, the time shown
DECIMALS = 3                        # at most in the labels of a trace


class ShortLabels(ScalarFormatter):
    """Tick labels with at most DECIMALS decimals beside the power of ten;
    where they would need more, the leading digits they share go to the
    offset over the axis."""

    _need = 0                       # decimals the labels would need

    def set_locs(self, locs):
        self._offset_threshold = rcParams["axes.formatter.offset_threshold"]
        super().set_locs(locs)
        if self._need > DECIMALS:
            self._offset_threshold = 2
            super().set_locs(locs)

    def _set_format(self):
        super()._set_format()
        for name in ("_format", "format"):  # matplotlib 3.10 on, before
            text = self.__dict__.get(name)
            if isinstance(text, str):
                m = re.search(r"%1\.(\d+)f", text)
                self._need = int(m.group(1)) if m else 0
                self.__dict__[name] = re.sub(
                    r"%1\.(\d+)f", lambda m: "%%1.%df" % min(
                        int(m.group(1)), DECIMALS), text)


def means(t, y, key, window):
    """(times, means) of a trace over windows of frames: rolling (every
    window of consecutive frames) or batch (consecutive blocks), at the
    middle of each window; phase (the frames one window apart: 1, 1 + w,
    ..., then 2, 2 + w, ...), at the times of the first window."""
    w = max(1, min(int(window), len(y)))
    if key == "phase":
        return t[:w], np.array([y[i::w].mean() for i in range(w)])
    starts = np.arange(0, len(y) - w + 1, 1 if key == "rolling" else w)
    c = np.concatenate(([0.0], np.cumsum(y)))
    return 0.5 * (t[starts] + t[starts + w - 1]), (c[starts + w] -
                                                   c[starts]) / w


def time_trace(t, curves, key, window, title, unit):
    """(draw, header, rows, text) of the time traces curves ([(label, y)]:
    one, or the separatrix and the maximum) at the times t: alone ("trace"),
    with their mean and standard deviation over the whole trace ("mean"),
    with their rolling or batch means, or their phase means alone (over
    the first window)."""
    t = np.asarray(t, float)
    curves = [(label, np.asarray(y, float)) for label, y in curves]
    one = len(curves) == 1
    extra = [(label, means(t, y, key, window)) for label, y in curves] \
        if key in MEANS else []
    phase = key == "phase"
    span = extra[0][1][0] if phase else t

    def name(label, what):
        return what if one else "%s, %s" % (label, what.lower())

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        for label, y in () if phase else curves:
            ax.plot(t, y, label="Time trace" if one else label)
        for label, y in curves if key == "mean" else ():
            m, s = y.mean(), y.std()
            ax.plot(t[[0, -1]], (m, m), label=name(label, "Mean"))
            ax.fill_between(t[[0, -1]], m - s, m + s, color=SPAN,
                            alpha=0.25, linewidth=0, zorder=0.6)
        for label, (x, y) in extra:
            ax.plot(x, y, label=name(label, MEANS[key]))
        if len(span) > 1:
            ax.set_xlim(span[0], span[-1])
        if len(ax.lines) > 1:
            ax.legend(fontsize="small")
        ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 4))
        ax.yaxis.set_major_locator(MaxNLocator("auto",
                                               steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_formatter(ShortLabels())
        ax.set_xlabel("time (s)")
        ax.set_ylabel(math_unit(unit))
    if phase:
        header = ["time (s)"] + ["%s (%s)" % (name(label, MEANS[key]).lower(),
                                             unit) for label, _ in extra]
        rows = [list(r) for r in zip(span, *(y for _, (_, y) in extra))]
    else:
        header = ["time (s)"] + ["%s (%s)" % (
            "value" if one else label.lower(), unit) for label, _ in curves]
        rows = [list(r) for r in zip(t, *(y for _, y in curves))]
    for label, (x, y) in () if phase else extra:    # their own times
        header += ["time of the %s (s)" % name(label, MEANS[key]).lower(),
                   "%s (%s)" % (name(label, MEANS[key]).lower(), unit)]
        for i, row in enumerate(rows):
            row += [x[i], y[i]] if i < len(x) else ["", ""]
    u = " " + html_unit(unit) if unit else ""
    text = "%s (mean \u00b1 standard deviation)" % ", ".join(
        "%s%.5g \u00b1 %.5g%s" % ("" if one else label.lower() + " ",
                                  y.mean(), y.std(), u)
        for label, y in curves)
    return draw, header, rows, text[:1].upper() + text[1:]


def minus_reference(a, box):
    """a (nt, ...) minus the reference of the frame box (the mean of its
    frames)."""
    ref = box.reference()
    if ref is None or ref == "final":
        return a
    return a - a[ref[0] - 1:ref[1]].mean(axis=0)


def at_position(a, box, p=None):
    """a (nt, ...) at slider position p (default the one shown): its
    frame, the mean or the standard deviation of its frames."""
    part = a[np.asarray(box.frame_list(p)) - 1]
    return part.std(axis=0) if box.key() == "std" else part.mean(axis=0)


def value_text(box, value, unit, what="", f=None):
    """The time (or frames) shown and the value there."""
    return "%s: %s%.5g %s" % (box.time_text(f), what, value, unit)


def trace(t, y, box, title, unit):
    """(draw, header, rows, value) of the time trace y at the times t: every
    frame, the means of the positions (rolling, batch, phase) and the position
    shown, or the mean (standard deviation: and the band around it) over
    the frames of a range."""
    t = np.asarray(t, float)
    y = minus_reference(np.asarray(y, float), box)
    key = box.key()
    k1, k2 = box.frames()
    now = float(at_position(y, box))
    mean = float(y[k1 - 1:k2].mean())
    t_now = box.time_value()
    means = None
    if key in MEANS:
        ps = box.positions()
        means = (np.array([box.time_at(p) for p in ps]),
                 np.array([float(at_position(y, box, p)) for p in ps]))

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        ax.plot(t, y, label="Every frame")
        if means is not None:
            ax.plot(*means, label=MEANS[key])
        if key in RANGE:
            span = (t[k1 - 1], t[k2 - 1])
            ax.plot(span, (mean, mean), label="Mean")
            ax.axvspan(*span, color=SPAN, alpha=0.15, linewidth=0,
                       zorder=0.5)
            if key == "std":
                ax.fill_between(span, mean - now, mean + now, color=SPAN,
                                alpha=0.3, linewidth=0, zorder=0.6)
        else:
            ax.plot([t_now], [now], linestyle="None", marker="o",
                    markersize=8, label="Shown")
            ln = ax.axvline(t_now, color=SPAN, linestyle="--",
                            linewidth=0.8)
            ln.frame = (1.0, False)     # no options of its own
        if len(t) > 1:
            ax.set_xlim(t[0], t[-1])
        ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 4))
        if means is not None or key in RANGE:
            ax.legend(fontsize="small")
        ax.set_xlabel("time (s)")
        ax.set_ylabel(math_unit(unit))
    if means is not None:
        header = ["time (s)", "%s (%s)" % (MEANS[key].lower(), unit)]
        rows = [list(r) for r in zip(*means)]
    else:
        header, rows = ["time (s)", "value (%s)" % unit], [
            list(r) for r in zip(t, y)]
    return draw, header, rows, now


def profile(xs, a, box, show_all, title, unit, extra=None):
    """(draw, header, rows, kind) of the profiles a (nt, n) against the x
    axes xs ({key: (n,)}, the first at first): at the position shown, with
    show_all those of all the positions too (one collection, colours along
    them; draw.key and draw.current: a move of the slider only moves the
    profile shown); extra: more columns of the rows ({key: (n,)}). a a
    list [(species, (nt, n))]: a curve per species (no show_all)."""
    if isinstance(a, list):
        return species_profiles(xs, a, box, title, unit, extra)
    a = minus_reference(np.asarray(a, float), box)
    positions = box.positions()
    p0 = box.pos.value()
    lo, hi = positions[0], positions[-1]

    def along(p):
        return (p - lo) / float(hi - lo) if hi > lo else 1.0
    now = at_position(a, box)
    every = [(along(p), p, at_position(a, box, p)) for p in positions] \
        if show_all and len(positions) > 1 else []
    others = [e for e in every if e[1] != p0]   # in more columns of the rows

    def x_of(options):
        key = options.xaxis.currentData()
        return xs[key] if key in xs else next(iter(xs.values()))

    def draw(ax, options):
        key = options.xaxis.currentData()
        x = x_of(options)
        ax.set_title(title, fontsize="medium")
        if every:                       # all the positions under it
            frame_lines(ax, x, [y for _, _, y in every],
                        [f for f, _, _ in every])
        ln, = ax.plot(x, now, label="Profile")
        ln.frame, ln.curve = (along(p0), True), 0
        ln.moves = bool(every)          # over all the positions: moved only
        known = np.isfinite(x) & np.isfinite(now)
        if known.any() and np.ptp(x[known]) > 0:    # from end to end
            ax.set_xlim(x[known].min(), x[known].max())
        ax.set_xlabel(XLABELS.get(key if key in xs else next(iter(xs)), ""))
        ax.set_ylabel(math_unit(unit))
    cols = dict(xs, **(extra or {}))
    prefix = box.pos.prefix().strip() or "frame"
    header = [HEADS.get(k, k) for k in cols] + ["value (%s), %s" % (
        unit, box.time_text())] + ["value (%s), %s %d" % (unit, prefix, p)
                                   for _, p, _ in others]
    rows = [list(r) for r in zip(*(list(cols.values()) + [now] +
                                   [y for _, _, y in others]))]
    if every:
        draw.current = lambda options: [(x_of(options), now)]
        draw.key = (title, unit, tuple(xs), tuple(p for _, p, _ in every),
                    hash(np.array([y for _, _, y in every]).tobytes()),
                    hash(np.concatenate([np.ravel(np.asarray(v, float))
                                         for v in xs.values()]).tobytes()))
    return draw, header, rows, "frames" if every else "line"


def species_profiles(xs, series, box, title, unit, extra=None):
    """(draw, header, rows, kind) of the profiles of several species at the
    position shown (series [(species, (nt, n))]), a curve each with its
    own options."""
    nows = [(label, at_position(minus_reference(np.asarray(y, float), box),
                                box)) for label, y in series]

    def draw(ax, options):
        key = options.xaxis.currentData()
        x = xs[key] if key in xs else next(iter(xs.values()))
        ax.set_title(title, fontsize="medium")
        known = np.zeros(len(x), bool)
        for label, now in nows:
            ax.plot(x, now, label=label)
            known |= np.isfinite(x) & np.isfinite(now)
        if known.any() and np.ptp(x[known]) > 0:
            ax.set_xlim(x[known].min(), x[known].max())
        if len(nows) > 1:
            ax.legend(fontsize="small")
        ax.set_xlabel(XLABELS.get(key if key in xs else next(iter(xs)), ""))
        ax.set_ylabel(math_unit(unit))
    cols = dict(xs, **(extra or {}))
    header = [HEADS.get(k, k) for k in cols] + [
        "%s (%s), %s" % (label, unit, box.time_text()) for label, _ in nows]
    rows = [list(r) for r in zip(*(list(cols.values()) +
                                   [now for _, now in nows]))]
    return draw, header, rows, "line"
