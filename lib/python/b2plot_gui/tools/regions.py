"""Regions and labels of the B2.5 grid for the masks of the 2D plot and
the inspector: the topology as B2.5 identifies it (geometryId of
b2mod_geometry), the names of its volume, face and flux tube regions (the
manual appendix Region definitions, inner/outer for single nulls), and
the masks: cells by volume region (cvReg) or by the region of their flux
tube (ftReg), faces by face region (fcReg), boundary labels (fcLbl) and
the recycling strata of b2.neutrals.parameters on them (numbers only, no
device names)."""

import matplotlib
import numpy as np
from matplotlib import colors as mcolors

from . import cellfiles

# GEOMETRY_ID declared by the grid generator that B2.5 keeps (limiter to
# DDN; any other is the general topology) and its number of regions
DECLARED = {3: 2, 4: 4, 5: 8, 6: 8, 7: 8}
TUBES = {1: "Core", 2: "SOL", 3: "PFR"}
TOPOLOGICAL = {0: ("(no tube)", "0.8"), 1: ("core", "#d62728"),
               2: ("SOL", "#1f77b4"), 3: ("PFR", "#2ca02c")}
# high-contrast qualitative colours, darker on each further round
PALETTE = ("#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
           "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080",
           "#e6beff", "#9a6324", "#800000", "#aaffc3", "#808000",
           "#000075", "#a9a9a9", "#ffd8b1", "#00a5ff", "#00ced1",
           "#ff1493", "#7cfc00")


def _names(*words):
    return {i: w for i, w in enumerate(words, 1) if w}


def _single_null(upper):
    w, e = ("outer", "inner") if upper else ("inner", "outer")
    W, E = w.capitalize(), e.capitalize()
    return (_names("Core", "SOL", W + " divertor", E + " divertor"),
            _names(W + " target", "Entrance to %s divertor" % w,
                   "Entrance to %s divertor" % e, E + " target",
                   "Connection between core sides",
                   "Connection between divertor sides",
                   W + " PFR wall boundary", "Core boundary",
                   E + " PFR wall boundary", "Separatrix",
                   W + " divertor wall boundary",
                   "Main chamber wall boundary",
                   E + " divertor wall boundary"), (1, 4))


def _double_null(ddn):
    face = _names("Lower inner divertor target",
                  "Entrance to lower inner divertor",
                  "Entrance to upper inner divertor",
                  "Upper inner divertor target",
                  "Upper outer divertor target",
                  "Entrance to upper outer divertor",
                  "Entrance to lower outer divertor",
                  "Lower outer divertor target",
                  "Connection between lower inner and lower outer core",
                  "Connection between upper inner and upper outer PFR",
                  "Connection between upper outer and upper inner core",
                  "Connection between lower outer and lower inner PFR")
    off = 0
    if ddn:
        face[13], off = "Connection between right and left SOL", 1
    for k, w in enumerate(("Lower inner PFR wall boundary",
                           "Left core boundary",
                           "Upper inner PFR wall boundary",
                           "Left separatrix",
                           "Lower inner divertor main wall boundary",
                           "Left SOL main wall boundary",
                           "Upper inner divertor main wall boundary",
                           "Upper outer PFR wall boundary",
                           "Right core boundary",
                           "Lower outer PFR wall boundary",
                           "Right separatrix",
                           "Upper outer divertor main wall boundary",
                           "Right SOL main wall boundary",
                           "Lower outer divertor main wall boundary")):
        face[13 + off + k] = w
    return (_names("Left core", "Left SOL", "Lower inner divertor",
                   "Upper inner divertor", "Right core", "Right SOL",
                   "Upper outer divertor", "Lower outer divertor"),
            face, (1, 4, 5, 8))


TABLES = {
    "linear": (_names("Plasma"),
               _names("Western edge", "Eastern edge", "Core boundary",
                      "SOL boundary"), (1, 2)),
    "limiter": (_names("Core", "SOL"),
                _names("Left target", "Right target", "Core connection",
                       "Core boundary", "Separatrix", "Wall boundary"),
                (1, 2)),
    "island": (_names("Core", "SOL", "Inboard divertor", "Outboard divertor",
                      "Island"),
               _names("Inboard target", "Entrance to inboard divertor",
                      "Entrance to outboard divertor", "Outboard target",
                      "Connection between core sides",
                      "Connection between PFR sides",
                      "Connection between island sides",
                      "Inboard PFR wall boundary", "Core boundary",
                      "Outboard PFR wall boundary", "Separatrix",
                      "Entrance to inboard PFR", "Island centre",
                      "Entrance to outboard PFR", "Island boundary"),
               (1, 4)),
    "snowflake": (_names("Core", "SOL", "Inboard divertor",
                         "Outboard divertor entrance",
                         "Outboard divertor leg 1", "Outboard divertor leg 2",
                         "Outboard divertor leg 3"),
                  _names("Inboard divertor target",
                         "Entrance to inboard divertor",
                         "Entrance to outboard divertor",
                         "First outboard divertor target",
                         "Second outboard divertor target",
                         "Entrance to first outer divertor leg",
                         "Connection between 2nd and 3rd outer legs",
                         "Third outboard divertor target",
                         "Connection between core sides",
                         "Connection between primary PFR sides",
                         "Connection between 1st and 2nd outer legs",
                         "Connection between primary PFR and 3rd leg",
                         "Connection between primary CFR and 3rd leg",
                         "Inboard divertor PFR wall boundary",
                         "Core boundary",
                         "Outboard divertor entrance PFR wall boundary",
                         "Primary separatrix",
                         "Inboard divertor main chamber wall boundary",
                         "SOL main chamber wall boundary",
                         "Outboard divertor entrance main chamber wall "
                         "boundary",
                         "First outboard leg PFR wall boundary",
                         "Second outboard leg PFR wall boundary",
                         "Third outboard leg PFR wall boundary",
                         "First outboard leg main chamber wall boundary",
                         "Second outboard leg main chamber wall boundary",
                         "Third outboard leg main chamber wall boundary"),
                  (1, 4, 5, 8)),
}


def topology(run, geo):
    """(volume names, face names, target face regions) of the topology
    when it is a standard one, else None: a declared GEOMETRY_ID (written
    only by grid generators with topological data) must be one B2.5
    keeps; without it the number of volume regions decides (7 regions:
    two X-points, a snowflake; 8: 27 face regions, a disconnected double
    null)."""
    reg = geo.get("cvReg")
    if reg is None or not len(reg):
        return None
    n = int(reg.max())
    gid = geo.scalar("GEOMETRY_ID")
    if gid is not None and DECLARED.get(gid) != n:
        return None
    nx = len(run.geometry.xpoints)
    if n == 4:
        core = reg == 1
        upper = bool(nx and core.any() and geo.get("cvY") is not None and
                     run.geometry.xpoints[0][1] > np.mean(
                         geo.get("cvY")[core]))
        return _single_null(upper)
    if n == 8:
        freg = geo.get("fcReg")
        return _double_null(gid in (6, 7) or (
            gid is None and freg is not None and int(freg.max()) >= 27))
    if n == 7 and nx != 2:
        return None
    key = {1: "linear", 2: "limiter", 5: "island", 7: "snowflake"}.get(n)
    return TABLES[key] if key else None


def region_names(run, geo):
    """({volume region: name}, {flux tube region: name}) of a standard
    topology, else (None, None)."""
    top = topology(run, geo)
    return (top[0], TUBES) if top else (None, None)


def palette(keys):
    """{key: colour} in the order of keys."""
    out = {}
    for i, k in enumerate(keys):
        base = mcolors.to_rgb(PALETTE[i % len(PALETTE)])
        shade = 1.0 - 0.28 * (i // len(PALETTE))
        out[k] = tuple(max(0.0, c * shade) for c in base)
    return out


def boundary_labels(geo):
    """The boundary labels (fcLbl not zero), the negative ones first, and
    their colours: black for those next to the core, the others in turn
    from tab20."""
    lbl = geo.get("fcLbl")
    faces = np.flatnonzero(lbl)
    used = set(lbl[faces].tolist())
    keys = sorted(k for k in used if k < 0) + sorted(k for k in used if k > 0)
    nci = geo.scalar("nCi")
    cv = geo.table("fcCv", len(lbl))
    ft, ftreg = geo.get("cvFt"), geo.get("ftReg")
    core = set()
    if cv is not None and ft is not None and ftreg is not None and nci:
        inner = np.where(cv[0][faces] <= nci, cv[0][faces], cv[1][faces]) - 1
        tube = ft[inner]
        ok = (inner < nci) & (tube >= 1)
        core = set(lbl[faces][ok][ftreg[tube[ok] - 1] == 1].tolist())
    tab = matplotlib.colormaps["tab20"]
    others = [k for k in keys if k not in core]
    col = {k: (0.0, 0.0, 0.0) for k in core}
    col.update({k: tab(i % 20)[:3] for i, k in enumerate(others)})
    return keys, col


# ---------------------------------------------------------------- masks
def cell_mask(run, geo, kind):
    """("cells", rows, colours, legend) of the internal cells (rows of the
    plotted geometry): kind "volume" by cvReg, "topological" by the
    region of their flux tube; legend [(text, colour)]."""
    g = run.geometry
    nci = geo.scalar("nCi") or len(g.cells)
    rows = np.flatnonzero(g.cells <= nci)
    i = g.cells[rows] - 1
    if kind == "volume":
        value = np.asarray(geo.get("cvReg"))[i]
        keys = sorted(set(value.tolist()))
        names, _ = region_names(run, geo)
        col = palette(keys)
        legend = [("cvReg %d: %s" % (k, (names or {}).get(k) or
                                     _macro(geo, k)), col[k]) for k in keys]
    else:
        ft, ftreg = geo.get("cvFt"), geo.get("ftReg")
        value = np.where(ft[i] >= 1, ftreg[np.maximum(ft[i], 1) - 1], 0)
        keys = sorted(set(value.tolist()))
        extra = palette([k for k in keys if k not in TOPOLOGICAL])
        col = {k: (mcolors.to_rgb(TOPOLOGICAL[k][1]) if k in TOPOLOGICAL
                   else extra[k]) for k in keys}
        legend = [("ftReg %d: %s" % (k, TOPOLOGICAL[k][0]) if k in
                   TOPOLOGICAL else "ftReg %d" % k, col[k]) for k in keys]
    return "cells", rows, [col[v] for v in value], legend


def _macro(geo, reg):
    """Core, SOL or PFR: the region of the flux tubes of most cells of
    volume region reg."""
    nci = geo.scalar("nCi")
    cv, ft, ftreg = geo.get("cvReg")[:nci], geo.get("cvFt")[:nci], \
        geo.get("ftReg")
    t = ft[(cv == reg) & (ft >= 1)]
    if not len(t):
        return "?"
    vals, counts = np.unique(ftreg[t - 1], return_counts=True)
    return TUBES.get(int(vals[np.argmax(counts)]), "?")


def _segments(geo, faces):
    fv = geo.table("fcVx", len(geo.get("fcS")))
    x, y = geo.get("vxX"), geo.get("vxY")
    a, b = fv[0][faces] - 1, fv[1][faces] - 1
    return np.stack((np.column_stack((x[a], y[a])),
                     np.column_stack((x[b], y[b]))), axis=1)


def face_mask(run, geo, kind):
    """("faces", segments, colours, legend) of kind "face" (fcReg),
    "labels" (fcLbl) or "strata" (recycling strata on fcLbl)."""
    if kind == "face":
        freg = geo.get("fcReg")
        faces = np.flatnonzero(freg)
        keys = sorted(set(freg[faces].tolist()))
        top = topology(run, geo)
        col = palette(keys)
        legend = [("fcReg %d: %s" % (k, top[1][k]) if top and k in top[1]
                   else "fcReg %d" % k, col[k]) for k in keys]
        return "faces", _segments(geo, faces), [col[v] for v in
                                                freg[faces]], legend
    lbl = geo.get("fcLbl")
    faces = np.flatnonzero(lbl)
    keys, col = boundary_labels(geo)
    if kind == "strata":
        strata = recycling_strata(run)
        keys = [k for k in keys if k in strata]
        faces = faces[np.isin(lbl[faces], keys)]
        legend = [("[%s]: fcLbl %d" % (",".join(str(n) for n in strata[k]),
                                       k), col[k]) for k in keys]
    else:
        legend = [("fcLbl %d" % k, col[k]) for k in keys]
    return "faces", _segments(geo, faces), [col[v] for v in lbl[faces]], \
        legend


def recycling_strata(run):
    """{fcLbl: [stratum numbers]}: the recycling strata of
    b2.neutrals.parameters on each boundary label, those of all species of
    one label together; a stratum of kind 'A' (crcstra) holds the
    boundary faces with rcstart <= fcLbl <= rcend, as B2.5 reads it."""
    nl = cellfiles.namelist(cellfiles.find(run.rundir,
                                           "b2.neutrals.parameters"))
    kinds = [v.strip("'\" ").upper() for v in nl.get("crcstra", [])]
    start, end = nl.get("rcstart", []), nl.get("rcend", [])
    out = {}
    for i, k in enumerate(kinds):
        if k != "A" or i >= min(len(start), len(end)):
            continue
        for v in range(int(start[i]), int(end[i]) + 1):
            if v:
                out.setdefault(v, []).append(i + 1)
    return out
