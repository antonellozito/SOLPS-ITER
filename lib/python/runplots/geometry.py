"""Which divertor target of a single null is the inner one, from the run
itself.

B2.5 stores the target quantities by position: the first target of
b2time.nc (cvlistl: the l profiles, the sepi/mxip/xip traces) and the
first one of blne.trc (il) are the same target. Without the upper single
null reordering of B2.5 they are the outer target of an upper single
null. The inner target is the one at smaller major radius, so the mean R
of the cells of cvlistl and cvlistr (cvX of the geometry) decides it for
any B2.5 version.
"""

import os

import numpy as np

from . import tracefiles

GEOMETRY = ("b2fgmtry_us", "b2fgmtry")
BASERUN = os.path.join(os.pardir, "baserun")


def _field(path, wanted):
    """The values of one field of a geometry file (*cf: format), or None."""
    values, count = None, 0
    for line in tracefiles._text_lines(path):
        if values is None:
            words = line.split()
            if line.startswith("*cf:") and words and words[-1] == wanted:
                count, values = int(words[2]), []
            continue
        if line.startswith("*cf:"):
            break
        values += [tracefiles.number(w) for w in line.split()]
        if len(values) >= count:
            break
    if values is None or len(values) < count:
        return None
    return np.array(values[:count])


def cell_radius():
    """Major radius of the cell centres (cvX of the unstructured geometry:
    b2fgmtry_us, b2fgmtry, also in ../baserun), or None."""
    for name in GEOMETRY:
        paths = [tracefiles.run_file(name), os.path.join(BASERUN, name)]
        for path in paths:
            if path and os.path.isfile(path) and os.path.getsize(path) > 0:
                r = _field(path, "cvX")
                if r is not None:
                    return r
    return None


def first_target_outer(data):
    """True when the first target of b2time.nc is the outer one, False
    when it is the inner one, None when the run cannot tell."""
    if data is None or "cvlistl" not in data.variables \
            or "cvlistr" not in data.variables:
        return None
    r = cell_radius()
    if r is None:
        return None
    sides = []
    for name in ("cvlistl", "cvlistr"):
        cells = np.asarray(data.variables[name][:], dtype=int).ravel()
        cells = cells[(cells >= 1) & (cells <= r.size)]
        if cells.size == 0:
            return None
        sides.append(r[cells - 1].mean())
    return bool(sides[0] > sides[1])
