"""Cell inspector: the cell and EIRENE triangle at a point and the values
there of every quantity the GUI has loaded (b2plot values, no
interpolation)."""

import numpy as np

from ...b2plot import labels
from ..model import split_unit
from ..panels.quantity import column_names

DEFAULTS = ("ne", "te", "ti", "na", "po", "ua", "vol", "triavol")
HEADER = ["Quantity", "Species", "Value", "Unit"]


def at(plot, x, y):
    """(geometry row, triangle) at (x, y), -1 where there is none."""
    it = int(plot.finder(x, y))
    row = int(plot.run.geometry.tri_cell[it]) if it >= 0 else -1
    jt = int(plot.efinder(x, y)) if plot.efinder is not None else -1
    return row, jt


def _name(name, ops, source, names):
    text = names.get(name, name)
    if ops:
        text += "  [%s]" % " ".join(ops)
    if source:
        text += "  (frames %d to %d of file %d)" % (source[1], source[2],
                                                    source[0])
    return text


def rows(run, plot, x, y, names, species):
    """Table rows [quantity, species, value, unit] at (x, y): position,
    cell, triangle, then each loaded field (all its species); names maps
    quantity names to the labels shown in the GUI."""
    g = run.geometry
    row, jt = at(plot, x, y)
    out = [["R, Z", "", "%.5g, %.5g" % (x, y), "m"]]
    if row >= 0:
        icv = int(g.cells[row])
        text = "%d" % icv
        if g.classical and g.ix[row] >= 0:
            text += " (ix %d, iy %d)" % (g.ix[row], g.iy[row])
        out += [["cell", "", text, ""],
                ["region", "", "%d" % g.region[row], ""],
                ["cell centre R, Z", "", "%.5g, %.5g" % tuple(g.centres[row]),
                 "m"]]
    if jt >= 0:
        out.append(["EIRENE triangle", "", "%d" % (jt + 1), ""])
    found = []
    for (kind, name, ops, source), d in run.cache.items():
        if kind in ("field", "vector") and row >= 0:
            i = int(g.cells[row]) - 1
        elif kind in ("efield", "evector") and jt >= 0:
            i = jt
        else:
            continue
        unit = labels.any_to_plain(split_unit(d.label)[1])
        cols = column_names(d.columns, species)
        for c, sp in enumerate(cols):
            if hasattr(d, "vr"):
                v = np.hypot(d.vr[c][i], d.vz[c][i])
                text = "|v| %.7g" % v
            else:
                text = "%.7g" % d.values[c][i]
            found.append([_name(name, ops, source, names),
                          sp if len(cols) > 1 else "", text, unit])
    return out + sorted(found, key=lambda r: r[0].lower())
