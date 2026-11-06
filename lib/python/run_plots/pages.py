"""Pages of the run plots and their matplotlib drawing.

One page is one gnuplot page of the old scripts: the same curves against
the same abscissa, with the same linear or logarithmic axes. The style is
shared by all run plots: letter landscape, light grid, colour-blind safe
colours (Okabe-Ito) combined with line styles, markers as gnuplot draws
them (at most 200 points). Rules for every page: tab names, legend
entries and axis labels start with a capital letter; the abscissa runs
from the smallest to the largest value plotted; the footer (run folder,
date) is a figure label below the axis label, so the layout never lets
them overlap; a legend does not repeat what the title already says.
"""

import time

import numpy as np
from matplotlib.figure import Figure

PAGE_SIZE = (11.0, 8.5)
COLOURS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00",
           "#56B4E9", "#000000")
STYLES = ("-", "--", ":", "-.")
MARKER_LIMIT = 200


def capital(text):
    """The text with a capital first letter (mathtext left as it is)."""
    if text and text[0].isalpha():
        return text[0].upper() + text[1:]
    return text


class Curve:
    def __init__(self, x, y, label="", style=None):
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.label, self.style = capital(label), style


class Page:
    """Curves on one pair of axes; tab is the short name in the window."""

    def __init__(self, tab, title, xlabel, ylabel, curves, logx=False,
                 logy=False, footer=""):
        self.tab, self.title = capital(tab), capital(title)
        self.xlabel, self.ylabel = capital(xlabel), capital(ylabel)
        self.curves = curves
        self.logx, self.logy = logx, logy
        self.footer = footer

    def xrange(self):
        """Smallest and largest abscissa plotted (positive ones on a
        logarithmic axis); None when there is no range."""
        values = [c.x[np.isfinite(c.x) & np.isfinite(c.y)]
                  for c in self.curves]
        values = np.concatenate(values) if values else np.array([])
        if self.logx:
            values = values[values > 0]
        if values.size == 0 or values.min() == values.max():
            return None
        return float(values.min()), float(values.max())


def stamp():
    """Date and time as the gnuplot time stamp writes them."""
    return time.strftime("%a %b %d %H:%M:%S %Y")


def draw(page):
    """The page as a matplotlib figure."""
    fig = Figure(figsize=PAGE_SIZE, layout="constrained")
    ax = fig.add_subplot()
    points = max((c.x.size for c in page.curves), default=0)
    marker = "o" if 0 < points <= MARKER_LIMIT else None
    labelled = False
    for i, c in enumerate(page.curves):
        style = c.style or STYLES[(i // len(COLOURS)) % len(STYLES)]
        ax.plot(c.x, c.y, linestyle=style, color=COLOURS[i % len(COLOURS)],
                marker=marker, markersize=3, linewidth=1.4,
                label=c.label or None)
        labelled = labelled or bool(c.label)
    if page.logx:
        ax.set_xscale("log", nonpositive="mask")
    if page.logy:
        ax.set_yscale("log", nonpositive="mask")
    if page.xrange():
        ax.set_xlim(*page.xrange())
    ax.set_xlabel(page.xlabel)
    ax.set_ylabel(page.ylabel)
    ax.set_title(page.title, fontsize="large")
    # opaque greys: PostScript has no transparency
    ax.grid(True, which="major", color="0.82", linewidth=0.6)
    ax.grid(True, which="minor", color="0.93", linewidth=0.4)
    ax.set_axisbelow(True)
    if labelled:
        many = len(page.curves) > 8
        ax.legend(loc="upper left" if many else "best", fontsize="small",
                  ncol=1 + (len(page.curves) - 1) // 22,
                  bbox_to_anchor=(1.01, 1.0) if many else None,
                  framealpha=1.0, edgecolor="0.8")
    if page.footer:
        # a figure label: the layout keeps room for it below the axis label
        fig.supxlabel(page.footer, x=0.005, ha="left", fontsize="x-small",
                      color="0.35")
    return fig
