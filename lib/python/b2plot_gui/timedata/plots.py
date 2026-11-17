"""The plots of the run tracing, in the small figures of the tools
(FigureView: the options under them, Save plot, Export): a time trace
(alone, with its mean and standard deviation, its rolling or its batch
means), the line sums of a chord with the position of the slider, a
profile at the position (with Show all, those of every position, colours
along them); each with the text of what is shown."""

import re

import numpy as np
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from ..panels.timebox import RANGE
from ..tools.measure import html_unit, math_unit

XLABELS = {"s": "distance along the chord (m)", "R": "R (m)", "Z": "Z (m)",
           "rhop": r"$\rho_p$", "dssep": "distance from the separatrix (m)"}
HEADS = {"s": "s (m)", "R": "R (m)", "Z": "Z (m)", "rhop": "rho_p",
         "dssep": "distance from the separatrix (m)", "phi": "phi (deg)"}
MEANS = {"rolling": "Rolling mean", "batch": "Batch mean"}
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
    middle of each window."""
    w = max(1, min(int(window), len(y)))
    starts = np.arange(0, len(y) - w + 1, 1 if key == "rolling" else w)
    c = np.concatenate(([0.0], np.cumsum(y)))
    return 0.5 * (t[starts] + t[starts + w - 1]), (c[starts + w] -
                                                   c[starts]) / w


def time_trace(t, curves, key, window, title, unit):
    """(draw, header, rows, text) of the time traces curves ([(label, y)]:
    one, or the separatrix and the maximum) at the times t: alone ("trace"),
    with their mean and standard deviation over the whole trace ("mean"),
    with their rolling or batch means."""
    t = np.asarray(t, float)
    curves = [(label, np.asarray(y, float)) for label, y in curves]
    one = len(curves) == 1
    extra = [(label, means(t, y, key, window)) for label, y in curves] \
        if key in MEANS else []

    def name(label, what):
        return what if one else "%s, %s" % (label, what.lower())

    def draw(ax, options):
        ax.set_title(title, fontsize="medium")
        for label, y in curves:
            ax.plot(t, y, label="Time trace" if one else label)
        for label, y in curves if key == "mean" else ():
            m, s = y.mean(), y.std()
            ax.plot(t[[0, -1]], (m, m), label=name(label, "Mean"))
            ax.fill_between(t[[0, -1]], m - s, m + s, color=SPAN,
                            alpha=0.25, linewidth=0, zorder=0.6)
        for label, (x, y) in extra:
            ax.plot(x, y, label=name(label, MEANS[key]))
        if len(t) > 1:
            ax.set_xlim(t[0], t[-1])
        if len(ax.lines) > 1:
            ax.legend(fontsize="small")
        ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 4))
        ax.yaxis.set_major_locator(MaxNLocator("auto",
                                               steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_formatter(ShortLabels())
        ax.set_xlabel("time (s)")
        ax.set_ylabel(math_unit(unit))
    header = ["time (s)"] + ["%s (%s)" % ("value" if one else label.lower(),
                                         unit) for label, _ in curves]
    rows = [list(r) for r in zip(t, *(y for _, y in curves))]
    for label, (x, y) in extra:         # their own times, at the right
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
    k1, k2 = box.frames() if p is None else box.frames_at(p)
    part = a[k1 - 1:k2]
    return part.std(axis=0) if box.key() == "std" else part.mean(axis=0)


def value_text(box, value, unit, what="", f=None):
    """The time (or frames) shown and the value there."""
    return "%s: %s%.5g %s" % (box.time_text(f), what, value, unit)


def trace(t, y, box, title, unit):
    """(draw, header, rows, value) of the time trace y at the times t: every
    frame, the means of the positions (rolling, batch) and the position
    shown, or the mean (standard deviation: and the band around it) over
    the frames of a range."""
    t = np.asarray(t, float)
    y = minus_reference(np.asarray(y, float), box)
    key = box.key()
    k1, k2 = box.frames()
    now = float(at_position(y, box))
    mean = float(y[k1 - 1:k2].mean())
    t_now = 0.5 * (t[k1 - 1] + t[k2 - 1])
    means = None
    if key in MEANS:
        frames = [box.frames_at(p) for p in box.positions()]
        means = (np.array([0.5 * (t[a - 1] + t[b - 1]) for a, b in frames]),
                 np.array([y[a - 1:b].mean() for a, b in frames]))

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
        ax.set_xlabel("t (s)")
        ax.set_ylabel(math_unit(unit))
    if means is not None:
        header = ["t (s)", "%s (%s)" % (MEANS[key].lower(), unit)]
        rows = [list(r) for r in zip(*means)]
    else:
        header, rows = ["t (s)", "value (%s)" % unit], [
            list(r) for r in zip(t, y)]
    return draw, header, rows, now


def profile(xs, a, box, show_all, title, unit, extra=None):
    """(draw, header, rows, kind) of the profiles a (nt, n) against the x
    axes xs ({key: (n,)}, the first at first): at the position shown, with
    show_all those of the other positions too (thin, colours along them);
    extra: more columns of the rows ({key: (n,)})."""
    a = minus_reference(np.asarray(a, float), box)
    positions = box.positions()
    p0 = box.pos.value()
    lo, hi = positions[0], positions[-1]

    def along(p):
        return (p - lo) / float(hi - lo) if hi > lo else 1.0
    now = at_position(a, box)
    others = [(along(p), p, at_position(a, box, p)) for p in positions
              if p != p0] if show_all else []

    def draw(ax, options):
        key = options.xaxis.currentData()
        x = xs[key] if key in xs else next(iter(xs.values()))
        ax.set_title(title, fontsize="medium")
        for f, _, y in others:          # the other positions first, thin
            ln, = ax.plot(x, y, label="_frame")
            ln.frame, ln.curve = (f, False), 0
        ln, = ax.plot(x, now, label="Profile")
        ln.frame, ln.curve = (along(p0), True), 0
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
    return draw, header, rows, "frames" if others else "line"
