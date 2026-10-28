"""Pages of 2D plots for export: shapes as b2plot sq, a4p and a4l, and the
nx by ny layout of b2plot page, filled with snapshots (plot2d.Snapshot).

Only matplotlib, no Qt: the page composer of the GUI and the tests use
the same functions.
"""

import math
import os

from matplotlib.figure import Figure

from . import labels
from .plot2d import fit_size, render_snapshot

SHAPES = {                      # inches; None: the size shown on screen
    "shown": ("As shown", None),
    "sq": ("Square (b2plot sq)", (8.0, 8.0)),
    "a4p": ("A4 portrait (b2plot a4p)", (8.27, 11.69)),
    "a4l": ("A4 landscape (b2plot a4l)", (11.69, 8.27)),
}
FORMATS = "PDF (*.pdf);;PNG (*.png);;SVG (*.svg);;EPS (*.eps)"


def layout(n, nx=0, ny=0):
    """Columns and rows of a page for n plots (0: automatic)."""
    if nx > 0 and ny > 0:
        return nx, ny
    if nx > 0:
        return nx, max(1, math.ceil(n / nx))
    if ny > 0:
        return max(1, math.ceil(n / ny)), ny
    nx = max(1, math.ceil(math.sqrt(n)))
    return nx, max(1, math.ceil(n / nx))


def pages(snaps, nx, ny):
    """Snapshots split into pages of nx * ny plots."""
    per = max(1, nx * ny)
    return [snaps[i:i + per] for i in range(0, len(snaps), per)] or [[]]


def draw_page(fig, snaps, nx, ny, header="", values=None, own=False):
    """Plots left to right and top to bottom, as b2plot page, with an
    optional global header over the page; own keeps the header of each
    plot (a figure of one plot)."""
    fig.clear()
    pw, ph = fig.get_size_inches() * 72.0
    top = 1.0 - (2.0 * 12.0 / ph if header.strip() else 0.0)
    if header.strip():
        s = labels.tex_to_mathtext(labels.expand(header, values))
        fig.text(0.5, 1.0 - 0.5 * 12.0 / ph, s, ha="center", va="top",
                 fontsize=fit_size(s, 12.0, 0.98 * pw))
    w, h = 1.0 / nx, top / ny
    for i, snap in enumerate(snaps):
        col, row = i % nx, i // nx
        render_snapshot(fig, snap, (col * w, top - (row + 1) * h, w, h),
                        header=own)


def figure(size):
    return Figure(figsize=size, layout=None)


def save(path, snaps, size, dpi=150, nx=1, ny=1, header="", values=None,
         own=False):
    """Write the snapshots as pages; a PDF holds all pages, other formats
    get one file per page (name_p2.png, ...). Returns the files."""
    groups = pages(snaps, nx, ny)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(path) as pdf:
            for group in groups:
                fig = figure(size)
                draw_page(fig, group, nx, ny, header, values, own)
                pdf.savefig(fig, dpi=dpi)
        return [path]
    out = []
    stem = os.path.splitext(path)[0]
    for i, group in enumerate(groups):
        name = path if i == 0 else "%s_p%d%s" % (stem, i + 1, ext)
        fig = figure(size)
        draw_page(fig, group, nx, ny, header, values, own)
        fig.savefig(name, dpi=dpi)
        out.append(name)
    return out
