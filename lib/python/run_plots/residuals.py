"""resco, resmo, reshe, reshi and plot_residuals: norms of the residuals of
b2ftrace against the iteration counter, logarithmic.

The records go through resopt with the options of the call (-m, -l, -a)
and the columns are taken as the old scripts take them: after the time
step and iteration counters, ns continuity and ns momentum residuals,
then the total momentum and the electron and ion energy residuals (ns
from SOLPS_FLUIDS).
"""

import os
import sys

from . import helpers, quantities, tracefiles
from .pages import Curve, Page, stamp


def _columns(kind, n):
    """0-based fields of the residuals of kind, after the iteration."""
    if kind == "co":
        return [i + 1 for i in range(1, n + 1)]
    if kind == "mo":
        return [i + n + 1 for i in range(1, n + 1)]
    return [2 * n + 3] if kind == "he" else [2 * n + 4]


def page(kind, resopt_args, name):
    """The page of one residual script, with its messages; None without
    b2ftrace."""
    fluids = helpers.solps_fluids(message=True)
    n = len(fluids)
    print(n, flush=True)
    path = tracefiles.run_file("b2ftrace")
    if path is None:
        sys.stderr.write("%s.py: b2ftrace not found\n" % name)
        return None
    text = helpers.resopt(tracefiles.b2ftrace_records(path), resopt_args)
    columns = _columns(kind, n)
    x, ys = [], [[] for _ in columns]
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        x.append(tracefiles.number(fields[1]) if len(fields) > 1
                 else float("nan"))
        for values, k in zip(ys, columns):
            values.append(tracefiles.number(fields[k]) if len(fields) > k
                          else float("nan"))
    labels = ([quantities.species_label(s) for s in fluids]
              if kind in ("co", "mo") else [""])
    title, ylabel = quantities.RESIDUAL[kind]
    return Page({"co": "continuity", "mo": "momentum",
                 "he": "electron energy", "hi": "ion energy"}[kind],
                title, "iteration", ylabel,
                [Curve(x, y, label) for y, label in zip(ys, labels)],
                logy=True, footer="%s    %s" % (os.getcwd(), stamp()))
