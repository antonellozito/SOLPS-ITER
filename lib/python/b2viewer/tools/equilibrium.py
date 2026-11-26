"""Magnetic equilibrium of a B2.5 cell for the inspector: its flux tube
(the cells from the west target to the east one, or around a closed
tube), the derived quantities (pitch, distances along the tube as DSPOL
and DSPAR of the MDSplus snapshot, poloidal flux expansion, grazing angle
on the wall, safety factor) and the 2D maps of them."""

import numpy as np

from ..model import Field

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
            out += [["Safety factor", ch["q"], ""],
                    ["Magnetic shear", maps(run, geo)["shear"][i],
                     "m^-1"]]
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
        ("lpol", "Poloidal length of the flux tube, wall to wall (m)"),
        ("lpar", "Parallel length of the flux tube, wall to wall (m)"),
        ("fexp", "Poloidal flux expansion relative to the nearest midplane"),
        ("qsafety", "Safety factor"),
        ("shear", "Magnetic shear (m^{-1})"))
# wall strips: the grazing angle, the connection lengths of the flux
# tubes that end on each wall face (as the inspector gives them)
WALLS = (("graze", "Field lines grazing angle (deg)"),
         ("lparwall", "Parallel wall to wall connection length (m)"),
         ("lpolwall", "Poloidal wall to wall connection length (m)"))
MIDPLANES = ("iimp", "iomp")    # b2plot masks of the midplane cells


def maps(run, geo):
    """{name: values (nCv)} of every map, NaN where a quantity has no
    meaning (distances on closed tubes, the safety factor and the shear on
    open ones, the expansion without a midplane); computed once per run."""
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
    closed = []
    for first in (ftc.reshape(2, -1)[0] if ftc is not None else []):
        ch = chain(geo, int(geo.get("ftCv")[first - 1]) - 1, ncv, nfc)
        if ch is None:
            continue
        c, pol, par = np.array(ch["cells"]), np.array(ch["pol"]), \
            np.array(ch["par"])
        out["lpol"][c], out["lpar"][c] = ch["lpol"], ch["lpar"]
        if ch["closed"]:
            out["qsafety"][c] = ch["q"]
            closed.append((c, ch["q"]))
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
    _shear(out["shear"], closed, geo, hx)
    if all(m is not None for m in masks):
        run.equilibrium_maps = out
    return out


def _shear(shear, tubes, geo, hx):
    """Magnetic shear dq/dr of the closed flux tubes [(cells, q)] in shear,
    as b2plot computes it (label s): r the mean distance (weights hx) of
    the cells of a tube from the centre of the first closed tube, central
    differences between the tubes next in r, one-sided at the ends."""
    if len(tubes) < 2:
        return
    x, y = geo.get("cvX"), geo.get("cvY")
    c0 = tubes[0][0]
    r0, z0 = (np.sum(hx[c0] * a[c0]) / hx[c0].sum() for a in (x, y))
    r = np.array([np.sum(hx[c] * np.hypot(x[c] - r0, y[c] - z0)) /
                  hx[c].sum() for c, _ in tubes])
    o = np.argsort(r)
    r, q = r[o], np.array([tubes[i][1] for i in o])
    lo = np.concatenate([[0], np.arange(len(q) - 1)])
    hi = np.concatenate([np.arange(1, len(q)), [len(q) - 1]])
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (q[hi] - q[lo]) / (r[hi] - r[lo])
    for k, i in enumerate(o):
        shear[tubes[i][0]] = s[k]


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
    (deg), their segments (n, 4: R, Z of the two vertices) and their
    cells (0-based)."""
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
    order, flip = _chained(a, b)        # in order along the wall
    a, b = np.where(flip, b[order], a[order]), np.where(flip, a[order],
                                                       b[order])
    f, angle = f[order], angle[order]
    return f, angle, np.column_stack((x[a], y[a], x[b], y[b])), inner[f]


def _chained(a, b):
    """Order of the faces (vertices a to b) along the pieces of wall they
    make (each piece from one of its ends, the faces next to each other
    sharing a vertex) and which ones run backwards (flip)."""
    at = {}
    for k, (p, q) in enumerate(zip(a, b)):
        at.setdefault(p, []).append(k)
        at.setdefault(q, []).append(k)
    left, order, flip = set(range(len(a))), [], []
    ends = [k for k, (p, q) in enumerate(zip(a, b))
            if len(at[p]) == 1 or len(at[q]) == 1]
    while left:
        k = next((e for e in ends if e in left), min(left))
        v = a[k] if len(at[a[k]]) == 1 or not len(at[b[k]]) == 1 else b[k]
        while k is not None:
            left.discard(k)
            back = b[k] == v
            order.append(k)
            flip.append(back)
            v = a[k] if back else b[k]          # the far end
            k = next((j for j in at[v] if j in left), None)
    return np.array(order, int), np.array(flip, bool)


def chain_closed(geo, t, nfc):
    """True if flux tube t (0-based) is closed (no cell with one face of
    the tube)."""
    ftp, ff = geo.get("ftFcP").reshape(2, -1), geo.get("ftFc")
    faces = ff[ftp[0][t] - 1:ftp[0][t] - 1 + ftp[1][t]] - 1
    cells = geo.table("fcCv", nfc)
    ends = np.concatenate((cells[0][faces], cells[1][faces]))
    _, counts = np.unique(ends, return_counts=True)
    return bool(faces.size) and not (counts == 1).any()


def wall_field(geo, run, name):
    """The wall quantity name of WALLS on the B2.5 wall and target faces
    as a wall Field, drawn as a strip along those faces: the grazing
    angle, or the wall to wall length of the flux tube of the cell of
    each face (lpar, lpol of maps)."""
    _, angle, seg, cells = wall_faces(geo)
    label = dict(WALLS)[name]
    values = angle if name == "graze" else \
        maps(run, geo)[name[:4]][cells]
    return Field(name=name, label=label, location="wall", columns=[""],
                 values=np.asarray(values, float)[None, :], segments=seg)
