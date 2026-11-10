"""Magnetic equilibrium of a B2.5 cell for the inspector: its flux tube
(the cells from the west target to the east one, or around a closed
tube), the derived quantities (pitch, distances along the tube as DSPOL
and DSPAR of the MDSplus snapshot, poloidal flux expansion, grazing angle
on the wall, safety factor) and the names of the regions of the standard
topologies, identified as B2.5 does (geometryId of b2mod_geometry)."""

import numpy as np

from ..model import Field

# volume regions of the standard topologies, by their number (manual,
# appendix Region definitions)
VOLUME = {
    1: ("plasma",),
    2: ("core", "Scrape-Off Layer"),
    4: ("core", "Scrape-Off Layer", "Western divertor", "Eastern divertor"),
    5: ("core", "Scrape-Off Layer", "inboard divertor", "outboard divertor",
        "island"),
    7: ("core", "Scrape-Off Layer", "inboard divertor",
        "outboard divertor entrance", "outboard divertor leg 1",
        "outboard divertor leg 2", "outboard divertor leg 3"),
    8: ("left core", "left SOL", "left inboard divertor",
        "left outboard divertor", "right core", "right SOL",
        "right inboard divertor", "right outboard divertor")}
TUBES = {1: "Core", 2: "SOL", 3: "PFR"}
# GEOMETRY_ID declared by the grid generator that B2.5 keeps (limiter to
# DDN; any other is the general topology) and its number of regions
DECLARED = {3: 2, 4: 4, 5: 8, 6: 8, 7: 8}


def region_names(run, geo):
    """({volume region: name}, {flux tube region: name}) when the topology
    is a standard one, else (None, None): a declared GEOMETRY_ID (written
    only by grid generators with topological data) must be one B2.5 keeps;
    without it the number of volume regions decides (7 regions: two
    X-points, a snowflake)."""
    reg = geo.get("cvReg")
    if reg is None or not len(reg):
        return None, None
    n = int(reg.max())
    gid = geo.scalar("GEOMETRY_ID")
    if gid is not None and DECLARED.get(gid) != n:
        return None, None
    if n not in VOLUME or (n == 7 and len(run.geometry.xpoints) != 2):
        return None, None
    names = list(VOLUME[n])
    if n == 4:                      # single null: lower or upper
        xp, core = run.geometry.xpoints, reg == 1
        if len(xp) and core.any() and geo.get("cvY") is not None:
            lower = xp[0][1] < np.mean(geo.get("cvY")[core])
            names[2] += ", inboard" if lower else ", outboard"
            names[3] += ", outboard" if lower else ", inboard"
    return dict(enumerate(names, 1)), TUBES


def chain(geo, i, ncv, nfc):
    """The flux tube of cell i (0-based), or None: dict(cells: in order,
    west to east (where most faces of the tube come from) or around a
    closed tube; pol, par: distances of their centres along the tube from
    the west target face (the first face, a guard cell behind it) or from
    the first cell; lpol, lpar: target to target or one turn; closed; q:
    safety factor of a closed tube). Each half cell adds fcHc, times
    |B| / |b_x| along the field, as B2.5."""
    ft, ff, fp = geo.get("cvFt"), geo.get("ftFc"), geo.get("ftFcP")
    cells, hc = geo.table("fcCv", nfc), geo.table("fcHc", nfc)
    bb, r = geo.table("cvBb", ncv), geo.get("cvX")
    if ft is None or ff is None or fp is None or cells is None or \
            hc is None or bb is None or ft[i] < 1:
        return None
    ftp = fp.reshape(2, -1)
    t = ft[i] - 1
    faces = ff[ftp[0][t] - 1:ftp[0][t] - 1 + ftp[1][t]] - 1
    links = {}
    for f in faces:
        a, b = cells[0][f] - 1, cells[1][f] - 1
        links.setdefault(a, []).append((f, b, 0))
        links.setdefault(b, []).append((f, a, 1))
    if i not in links:
        return None
    ends = [c for c, n in links.items() if len(n) == 1]
    start = ends[0] if ends else next(iter(links))
    order, steps, prev = [start], [], None
    while len(order) <= len(links):
        nxt = [(f, c, k) for f, c, k in links[order[-1]] if f != prev]
        if not nxt or (not ends and nxt[0][1] == start):
            if not ends and nxt:
                steps.append(nxt[0])        # closes the tube
            break
        f, c, k = nxt[0]
        steps.append((f, c, k))
        order.append(c)
        prev = f
    seg = [(hc[k][f], hc[1 - k][f]) for f, _, k in steps]   # half cells
    if ends and sum(k == 0 for _, _, k in steps) < 0.5 * len(steps):
        order, seg = order[::-1], [(b, a) for a, b in seg[::-1]]
    with np.errstate(divide="ignore", invalid="ignore"):
        bpol = np.hypot(bb[0], bb[1])
        par = bb[3] / np.abs(bb[0])                 # |B| / |b_x|
        twist = np.abs(bb[2]) / (r * bpol)          # B_tor / (R B_pol)
    cyc = order + [order[0]]
    pol0 = 0.0 if not ends else -seg[0][0]
    pol, dpar = [pol0], [pol0 * par[order[0]]]
    for (a, b), c0, c1 in zip(seg, cyc[:-1], cyc[1:]):
        pol.append(pol[-1] + a + b)
        dpar.append(dpar[-1] + a * par[c0] + b * par[c1])
    out = dict(cells=order, closed=not ends)
    if ends:
        out.update(pol=pol, par=dpar, lpol=pol[-1] - seg[-1][1],
                   lpar=dpar[-1] - seg[-1][1] * par[order[-1]])
    else:
        out.update(pol=pol[:-1], par=dpar[:-1], lpol=pol[-1], lpar=dpar[-1],
                   q=sum(a * twist[c0] + b * twist[c1] for (a, b), c0, c1
                         in zip(seg, cyc[:-1], cyc[1:])) / (2.0 * np.pi))
    return out


def derived_rows(run, geo, i, ncv, nfc):
    """The derived quantities of cell i (0-based): [quantity, "", value,
    unit] rows."""
    bb = geo.table("cvBb", ncv)
    if bb is None:
        return []
    b = bb[:, i]
    bpol = float(np.hypot(b[0], b[1]))
    ch = chain(geo, i, ncv, nfc)
    out = []
    if b[3] > 0:
        out += [["Magnetic pitch", bpol / b[3], ""],
                ["Pitch angle", np.degrees(np.arctan2(bpol, abs(b[2]))),
                 "deg"]]
        if ch is not None and not ch["closed"]:
            out += _grazing(geo, i, ncv, nfc)
        hx = geo.get("cvHx")
        if hx is not None and bpol > 0:
            out.append(["Parallel length of the cell", hx[i] * b[3] / bpol,
                        "m"])
    if ch is not None:
        j = ch["cells"].index(i)
        pol, par = ch["pol"][j], ch["par"][j]
        if ch["closed"]:
            out += [["Poloidal length of the closed flux tube", ch["lpol"],
                     "m"],
                    ["Parallel length of the closed flux tube (one turn)",
                     ch["lpar"], "m"]]
        else:
            out += [["Poloidal distance from the west target", pol, "m"],
                    ["Parallel distance from the west target", par, "m"],
                    ["Poloidal distance to the east target",
                     ch["lpol"] - pol, "m"],
                    ["Parallel distance to the east target",
                     ch["lpar"] - par, "m"],
                    ["Poloidal length of the flux tube, wall to wall",
                     ch["lpol"], "m"],
                    ["Parallel length of the flux tube, wall to wall",
                     ch["lpar"], "m"]]
        out += _expansion(run, geo, ch, i, bb)
        if ch["closed"]:
            out.append(["Safety factor", ch["q"], ""])
    return [[text, "", value, unit] for text, value, unit in out]


def _expansion(run, geo, ch, i, bb):
    """Poloidal flux expansion relative to the midplane (B2.5 inner and
    outer midplane cells, b2plot iimp and iomp) nearest along the tube."""
    r = geo.get("cvX")
    best = None
    for name, side in (("iimp", "inner"), ("iomp", "outer")):
        mask = run.cache.get(("field", name, (), None))
        if mask is None:
            return [["Poloidal flux expansion", "loading…", ""]]
        for k, c in enumerate(ch["cells"]):
            if mask.values[0][c] > 0.5:
                d = abs(ch["pol"][k] - ch["pol"][ch["cells"].index(i)])
                if ch["closed"]:
                    d = min(d, ch["lpol"] - d)
                if best is None or d < best[0]:
                    best = (d, c, side)
    if best is None:
        return []
    m = best[1]
    rb = r * np.hypot(bb[0], bb[1])
    if not rb[i] > 0:
        return []
    return [["Poloidal flux expansion relative to the %s midplane"
             % best[2], rb[m] / rb[i], ""]]


def _grazing(geo, i, ncv, nfc):
    """Grazing angle of the field on the wall and target faces of the cell
    (faces to a guard cell): asin of B_pol / |B| times the cosine of the
    angle between the field and the face normal, at the face."""
    nci, p = geo.scalar("nCi"), geo.table("cvFcP", ncv)
    cells, q, fb = geo.table("fcCv", nfc), geo.table("fcQalf", nfc), \
        geo.table("fcBb", nfc)
    if nci is None or p is None or cells is None or q is None or fb is None:
        return []
    faces = geo.get("cvFc")[p[0][i] - 1:p[0][i] - 1 + p[1][i]] - 1
    found = []
    for f in faces:
        other = cells[1][f] if cells[0][f] == i + 1 else cells[0][f]
        if other > nci and fb[3][f] > 0:
            s = np.hypot(fb[0][f], fb[1][f]) / fb[3][f] * abs(q[0][f])
            found.append("%.6g (face %d)" % (np.degrees(np.arcsin(min(
                s, 1.0))), f + 1))
    return [["Grazing angle on the wall", ", ".join(found), "deg"]] \
        if found else []


# 2D maps of the derived quantities: (name, label as b2plot labels it)
MAPS = (("pitch", "Magnetic pitch"),
        ("pitchangle", "Pitch angle (deg)"),
        ("lparcell", "Parallel length of the cell (m)"),
        ("dspol", "Poloidal distance from the west target (m)"),
        ("dspar", "Parallel distance from the west target (m)"),
        ("dspole", "Poloidal distance to the east target (m)"),
        ("dspare", "Parallel distance to the east target (m)"),
        ("lpol", "Poloidal length of the flux tube, wall to wall or one "
         "turn (m)"),
        ("lpar", "Parallel length of the flux tube, wall to wall or one "
         "turn (m)"),
        ("fexp", "Poloidal flux expansion relative to the nearest midplane"),
        ("qsafety", "Safety factor"))
WALL = ("graze", "Grazing angle on the wall (deg)")     # a wall strip
MIDPLANES = ("iimp", "iomp")    # b2plot masks of the midplane cells


def maps(run, geo):
    """{name: values (nCv)} of every map, NaN where a quantity has no
    meaning (distances on closed tubes, the safety factor on open ones,
    the expansion without a midplane); computed once per run."""
    if getattr(run, "equilibrium_maps", None) is not None:
        return run.equilibrium_maps
    ncv, nfc = len(geo.get("cvX")), len(geo.get("fcS"))
    bb, hx = geo.table("cvBb", ncv), geo.get("cvHx")
    out = {name: np.full(ncv, np.nan) for name, _ in MAPS}
    with np.errstate(divide="ignore", invalid="ignore"):
        bpol = np.hypot(bb[0], bb[1])
        out["pitch"] = bpol / bb[3]
        out["pitchangle"] = np.degrees(np.arctan2(bpol, np.abs(bb[2])))
        out["lparcell"] = hx * bb[3] / bpol
    rb = geo.get("cvX") * bpol
    masks = [run.cache.get(("field", n, (), None)) for n in MIDPLANES]
    ftc = geo.get("ftCvP")
    for first in (ftc.reshape(2, -1)[0] if ftc is not None else []):
        ch = chain(geo, int(geo.get("ftCv")[first - 1]) - 1, ncv, nfc)
        if ch is None:
            continue
        c, pol, par = np.array(ch["cells"]), np.array(ch["pol"]), \
            np.array(ch["par"])
        out["lpol"][c], out["lpar"][c] = ch["lpol"], ch["lpar"]
        if ch["closed"]:
            out["qsafety"][c] = ch["q"]
        else:
            out["dspol"][c], out["dspar"][c] = pol, par
            out["dspole"][c] = ch["lpol"] - pol
            out["dspare"][c] = ch["lpar"] - par
        mids = [k for m in masks if m is not None
                for k in np.flatnonzero(m.values[0][c] > 0.5)]
        if mids:
            d = np.abs(pol[:, None] - pol[None, mids])
            if ch["closed"]:
                d = np.minimum(d, ch["lpol"] - d)
            near = np.array(mids)[np.argmin(d, axis=1)]
            out["fexp"][c] = rb[c[near]] / rb[c]
    if all(m is not None for m in masks):
        run.equilibrium_maps = out
    return out


def vertex_values(geo, values):
    """Values at the vertices: each cell shares its volume equally among
    its vertices, inverse-volume weights (B2.5 vxVol_style 0); NaN cells
    left out."""
    ncv = len(values)
    p, cv = geo.table("vxCvP", len(geo.get("vxX"))), geo.get("cvVxP")
    cells = geo.get("vxCv") - 1
    nv = cv.reshape(2, -1)[1].astype(float)
    w = nv / geo.get("cvVol")
    vid = np.repeat(np.arange(p.shape[1]), p[1])
    idx = np.concatenate([np.arange(s - 1, s - 1 + n)
                          for s, n in zip(p[0], p[1])])
    c = cells[idx]
    ok = np.isfinite(values[c]) & (c < ncv)
    num = np.bincount(vid[ok], weights=w[c[ok]] * values[c[ok]],
                      minlength=p.shape[1])
    den = np.bincount(vid[ok], weights=w[c[ok]], minlength=p.shape[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def field(run, geo, name, ops=()):
    """The map name as a Field of the cells (the scale factor of the
    operations applied, the others do not concern one column)."""
    label = dict(MAPS)[name]
    factor = 1.0
    for op in ops:
        words = op.split()
        if len(words) == 2 and words[1] == "rm*":
            factor *= float(words[0].replace("d", "e").replace("D", "E"))
    values = maps(run, geo)[name] * factor
    return Field(name=name, label=label, location="cells", columns=[""],
                 values=values[None, :],
                 vertex=vertex_values(geo, values)[None, :], ops=tuple(ops))


def wall_faces(geo):
    """The wall and target faces of the B2.5 grid (0-based faces between a
    cell of an open flux tube and a guard cell) with their grazing angle
    (deg) and their segments (n, 4: R, Z of the two vertices)."""
    ncv, nfc = len(geo.get("cvX")), len(geo.get("fcS"))
    nci = geo.scalar("nCi")
    cells, q, fb = geo.table("fcCv", nfc), geo.table("fcQalf", nfc), \
        geo.table("fcBb", nfc)
    fv, ft, ftreg = geo.table("fcVx", nfc), geo.get("cvFt"), geo.get("ftReg")
    if not nci or cells is None or q is None or fb is None or fv is None:
        return np.zeros(0, int), np.zeros(0), np.zeros((0, 4))
    closed = np.zeros(ncv, bool)
    ftp = geo.get("ftFcP")
    if ft is not None and ftp is not None:      # tubes without ends
        for t in range(len(ftp) // 2):
            if chain_closed(geo, t, nfc):
                closed[ft == t + 1] = True
    inner = np.where(cells[0] - 1 < nci, cells[0], cells[1]) - 1
    outer = np.where(cells[0] - 1 < nci, cells[1], cells[0]) - 1
    f = np.flatnonzero((inner < nci) & (outer >= nci) & (fb[3] > 0) &
                       ~closed[np.clip(inner, 0, ncv - 1)])
    angle = np.degrees(np.arcsin(np.minimum(np.hypot(
        fb[0][f], fb[1][f]) / fb[3][f] * np.abs(q[0][f]), 1.0)))
    x, y = geo.get("vxX"), geo.get("vxY")
    a, b = fv[0][f] - 1, fv[1][f] - 1
    return f, angle, np.column_stack((x[a], y[a], x[b], y[b]))


def chain_closed(geo, t, nfc):
    """True if flux tube t (0-based) is closed (no cell with one face of
    the tube)."""
    ftp, ff = geo.get("ftFcP").reshape(2, -1), geo.get("ftFc")
    faces = ff[ftp[0][t] - 1:ftp[0][t] - 1 + ftp[1][t]] - 1
    cells = geo.table("fcCv", nfc)
    ends = np.concatenate((cells[0][faces], cells[1][faces]))
    _, counts = np.unique(ends, return_counts=True)
    return bool(faces.size) and not (counts == 1).any()


def wall_field(geo):
    """The grazing angle on the B2.5 wall and target faces as a wall
    Field, drawn as a strip along those faces."""
    _, angle, seg = wall_faces(geo)
    return Field(name=WALL[0], label=WALL[1], location="wall", columns=[""],
                 values=angle[None, :], segments=seg)
