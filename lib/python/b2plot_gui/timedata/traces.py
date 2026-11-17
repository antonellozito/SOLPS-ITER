"""The time traces of b2time.nc by place of the plot, in categories: the
outer midplane separatrix (its state variables), each target (its state
variables at the separatrix with their maxima along it, its integrated
poloidal fluxes), the wall and private flux region boundaries (the
integrated radial fluxes over the main chamber and over the divertor
region) and anywhere else in the plasma (its totals); the shapes of the
places on the plot and where their names go."""

import numpy as np

from .files import B2TIME, Item, summed, unit

STATE = ("ne", "te", "ti", "po", "kt", "na", "dab", "tab", "dmb", "tmb")
FLUXES = ("fni", "fee", "fei", "fet", "fch")    # integrated
TOTALS = ("tmne", "tmte", "tmti")
GROUPS = ("State variables", "Fluxes", "Integrated quantities")
# the places always on the plot with their names (anywhere else in the
# grid: "plasma", no name)
PLACES = {"omp": "Outer midplane separatrix", "target_w": "{W} target",
          "target_e": "{E} target", "wall": "Wall boundary",
          "pfr": "Private flux region boundary"}
SHOWN = tuple(PLACES)
# ends of the names at a target: separatrix, maximum, integral
TARGETS = {"target_w": ("sepi", "mxip", "xip"),
           "target_e": ("sepa", "mxap", "xap")}
RADIAL = ("yip", "yap")             # integrals over the main chamber and
#                                     the divertor region
# face regions of a single null as B2.5 integrates over them: the wall,
# the private flux region boundaries, the main chamber, the divertor region
REGIONS = {"wall": (11, 12, 13), "pfr": (7, 9), "yip": (12,),
           "yap": (7, 9, 11, 13)}
SINGLE_NULL = {1, 4, 7, 9, 12}      # face regions there (none above 13)


def _what(long, where=True, state=False):
    """What a long name says, without where (after its last comma) and,
    for a state variable, without separatrix or maximum."""
    text = long.rsplit(", ", 1)[0] if where and ", " in long else long
    for word in ("separatrix ", "maximum ") if state else ():
        if text.startswith(word):
            text = text[len(word):]
    return text[:1].upper() + text[1:]


def items(b2t, place):
    """The time traces of a place (PLACES, "plasma") in their categories,
    in order."""
    v = b2t.nc.variables

    def item(parts, group, where, mark, state=False, whole=False):
        parts = tuple((n, label) for n, label in parts if n in v)
        if not parts:
            return []
        var = v[parts[0][0]]
        long = str(getattr(var, "long_name", var.name)).strip()
        dim = next((d for d in var.dimensions if d in
                    ("ns", "natm", "nmol")), "")
        return [Item(var.name, _what(long, not whole, state), group,
                     unit(var), B2TIME, "trace", dim, 0,
                     b2t.side_text(where), mark, b2t.side_text(long),
                     parts)]
    out = []
    if place == "omp":
        for k in STATE:
            out += item(((k + "sepm", ""),), GROUPS[0],
                        "outer midplane separatrix", "omp", True)
    elif place in TARGETS:
        sep, top, total = TARGETS[place]
        where = "{%s} target" % place[-1]
        for k in STATE:
            out += item(((k + sep, "Separatrix"), (k + top, "Maximum")),
                        GROUPS[0], where, place, True)
        for k in FLUXES:
            out += item(((k + total, ""),), GROUPS[1], where, place)
        out += item((("pw" + top, ""),), GROUPS[1], where, place)
    elif place in ("wall", "pfr"):
        for end in RADIAL:
            for k in FLUXES:
                out += item(((k + end, ""),), GROUPS[1], "", end,
                            whole=True)
    elif place == "plasma":
        for k in TOTALS:
            out += item(((k, ""),), GROUPS[2], "", "plasma", whole=True)
    return out


def curves(b2t, item, cols=(0,)):
    """[(label, trace (nt,))] of the item (separatrix and maximum: two),
    of its first divertor, its species columns cols summed."""
    out = []
    for name, label in item.parts:
        a = b2t.array(b2t.nc[name])
        if a.ndim >= 2:
            a = a[:, 0]
        out.append((label, summed(a, 1, cols) if a.ndim == 2 else a))
    return out


def key(item):
    """What the item is whatever its place (the same at another place)."""
    end = 4 if item.parts[0][0].endswith(("sepm", "sepi", "sepa")) else 3
    return item.group, item.name[:-end] if item.place != "plasma" else \
        item.name


def _faces(geo):
    """(face regions, face segments (n, 2, 2)) of the geometry file."""
    reg = geo.get("fcReg")
    vx, x, y = geo.table("fcVx", len(reg)), geo.get("vxX"), geo.get("vxY")
    if vx is None or x is None or y is None:
        return None, None
    a, b = vx[0] - 1, vx[1] - 1
    return reg, np.stack((np.column_stack((x[a], y[a])),
                          np.column_stack((x[b], y[b]))), axis=1)


def _at_separatrix(points, ds):
    """Where the line of the points crosses the separatrix (ds = 0)."""
    ok = np.isfinite(points).all(axis=1) & np.isfinite(ds)
    if ok.sum() < 2:
        return None
    k = np.argsort(ds[ok])
    return np.array([[np.interp(0.0, ds[ok][k], points[ok][k][:, c])
                      for c in (0, 1)]])


def shapes(b2t, geometry, geo):
    """{key: (kind, data)} on the plot: "omp", "sep_w", "sep_e" points
    (1, 2) (where the separatrix crosses the outer midplane and the
    targets); "target_w", "target_e", "wall", "pfr", "yip", "yap" face
    segments (n, 2, 2) (with the geometry file geo; the targets else from
    the cell centres, the wall and private flux region boundaries only in
    a single null); "plasma" the cell polygons of the grid."""
    out = {}
    nc = b2t.nc.variables
    line = b2t.lines.get("mid_a")
    if line is not None and "dsa" in nc:
        p = _at_separatrix(line, b2t.array(nc["dsa"]).ravel())
        if p is not None:
            out["omp"] = ("point", p)
    reg, seg = _faces(geo) if geo is not None and "fcReg" in geo else \
        (None, None)
    for place, faces, ds, sep in (("target_w", "fclistl", "dsl", "sep_w"),
                                  ("target_e", "fclistr", "dsr", "sep_e")):
        if seg is not None and faces in nc:
            f = b2t.array(nc[faces]).astype(int).ravel() - 1
            s = seg[f[(f >= 0) & (f < len(seg))]]
            mid = s.mean(axis=1)
        elif place in b2t.lines:
            mid = b2t.lines[place]
            s = np.stack((mid[:-1], mid[1:]), axis=1)
        else:
            continue
        out[place] = ("lines", s)
        if ds in nc and len(mid) == len(b2t.array(nc[ds]).ravel()):
            p = _at_separatrix(mid, b2t.array(nc[ds]).ravel())
            if p is not None:
                out[sep] = ("point", p)
    if reg is not None and SINGLE_NULL <= set(reg.tolist()) and \
            reg.max() <= 13:
        for k, regions in REGIONS.items():
            out[k] = ("lines", seg[np.isin(reg, regions)])
    vis = geometry.visible if geometry.visible is not None else \
        np.ones(len(geometry.polygons), bool)
    out["plasma"] = ("area", [p for p, v in zip(geometry.polygons, vis)
                              if v])
    return out


def anchors(shapes):
    """(centre, {place: (point (2,), away)}): the middle of the grid and
    where the names of the places of SHOWN go, away from the middle or
    toward it: the separatrix point (toward), the middle of a target and
    the private flux region boundary nearest the middle (away), the main
    chamber wall farthest from the targets (toward)."""
    cells = [np.asarray(p, float).reshape(-1, 2) for p in
             shapes.get("plasma", (None, []))[1]]
    xy = np.concatenate(cells) if cells else np.empty((0, 2))
    xy = xy[np.isfinite(xy).all(axis=1)]
    if not len(xy):
        return None, {}
    centre = 0.5 * (xy.min(axis=0) + xy.max(axis=0))
    out = {}
    if "omp" in shapes:
        out["omp"] = (shapes["omp"][1][0], False)
    ends = []
    for k in ("target_w", "target_e"):
        if k in shapes and len(shapes[k][1]):
            s = shapes[k][1]
            ends.append(s[len(s) // 2].mean(axis=0))
            out[k] = (ends[-1], True)
    for k, near, away in (("pfr", centre, True),
                          ("wall", np.mean(ends, axis=0) if ends else
                           centre, False)):
        seg = shapes.get("yip" if k == "wall" else k, shapes.get(k))
        if seg is not None and len(seg[1]):
            v = seg[1].reshape(-1, 2)
            d = np.hypot(*(v - near).T)
            out[k] = (v[np.argmin(d) if k == "pfr" else np.argmax(d)], away)
    return centre, out


def mark(item):
    """The shapes glowing for the item: its place, with the separatrix
    point of a state variable at a target."""
    if item.place in TARGETS and item.group == GROUPS[0]:
        return (item.place, "sep" + item.place[-2:])
    return (item.place,)
