"""Cell inspector: at a point inside a B2.5 cell or an EIRENE triangle,
groups of rows [quantity, name, value, unit]: the value of the quantity
shown; the grid of the B2.5 cell and its magnetic equilibrium, basic
quantities (the variables of b2fgmtry documented in b2cdcv, rhop and
psiN of rzpsi.dat, the connection length of b2plot) and derived ones
(equilibrium.derived_rows, no name); the EIRENE triangle (fort.33,
fort.34, fort.35, area and volume of b2plot)."""

import numpy as np

from ...b2plot import labels
from . import cellfiles, equilibrium

HEADER = ["Quantity", "Name", "Value", "Unit"]
REQUESTS = ("triarea", "triavol", "conn", "iimp", "iomp")  # from b2plot
KINDS = {0: "undefined", 1: "internal", 3: "boundary", 9: "guard"}


def at(plot, x, y):
    """(geometry row, triangle) at (x, y), -1 where there is none."""
    it = int(plot.finder(x, y))
    row = int(plot.run.geometry.tri_cell[it]) if it >= 0 else -1
    jt = int(plot.efinder(x, y)) if plot.efinder is not None else -1
    return row, jt


def files(run):
    """Geometry and triangles of the run files, read once per run."""
    if getattr(run, "cell_files", None) is None:
        run.cell_files = (cellfiles.geometry(run.rundir),
                          cellfiles.triangles(run.rundir)
                          if run.trimesh is not None else None)
    return run.cell_files


def _num(v):
    return "%d" % v if isinstance(v, (int, np.integer)) else "%.7g" % v


def _list(values):
    return ", ".join(_num(v) for v in values)


def groups(tab, x, y):
    """[(title, rows)] at (x, y); [] outside every cell and triangle."""
    plot, run = tab.plot, tab.run
    row, jt = at(plot, x, y)
    if row < 0 and jt < 0:
        return []
    out = []
    shown = _shown(tab, row, jt)
    if shown:
        out.append(("Quantity shown", shown))
    rho = run.psimap.rhop if run.psimap is not None else None
    geo, tri = files(run)
    if row >= 0:
        icv = int(run.geometry.cells[row])
        grid, basic, derived = cell_rows(run, row, geo, rho)
        out.append(("B2.5 cell %d: grid" % icv, grid))
        for rows, text in ((basic, "basic"), (derived, "derived")):
            if rows:
                out.append(("B2.5 cell %d: magnetic equilibrium (%s "
                            "quantities)" % (icv, text), rows))
    if jt >= 0:
        out.append(("EIRENE triangle %d" % (jt + 1),
                    triangle_rows(run, jt, tri, rho)))
    return out


def _shown(tab, row, jt):
    """The quantity shown (|v| and its components for vectors) there."""
    d, plot = tab.data, tab.plot
    if d is None or not tab._current():
        return []
    if d.location == "cells":
        if row < 0:
            return []
        i = int(tab.run.geometry.cells[row]) - 1
    elif jt < 0:
        return []
    else:
        i = jt
    col = plot._column(d, plot.style)
    text = labels.tex_to_plain(tab.wanted.description) if hasattr(
        tab.wanted, "description") else tab.wanted.label
    if tab.quantity.species.count() > 1:
        text += " (%s)" % tab.quantity.species.currentText()
    unit = labels.any_to_plain(d.unit)
    if hasattr(d, "vr"):
        vr, vz = float(d.vr[col][i]), float(d.vz[col][i])
        return [[text + ", magnitude", d.name, _num(np.hypot(vr, vz)),
                 unit],
                [text + ", R component", d.name, _num(vr), unit],
                [text + ", Z component", d.name, _num(vz), unit]]
    return [[text, d.name, _num(float(d.values[col][i])), unit]]


def cell_rows(run, row, geo, rho=None):
    """The B2.5 cell of geometry row row: (grid rows, magnetic
    equilibrium rows of basic and of derived quantities)."""
    g = run.geometry
    icv = int(g.cells[row])
    grid, eq = [["Cell number", "iCv", "%d" % icv, ""]], []
    if geo is None:
        cx, cy = g.centres[row]
        grid += [["Cell centre R", "cvX", _num(cx), "m"],
                 ["Cell centre Z", "cvY", _num(cy), "m"],
                 ["Region", "cvReg", "%d" % g.region[row], ""]]
        if g.classical and g.ix[row] >= 0:
            grid.append(["Structured grid indices ix, iy", "imapCv",
                         "%d, %d" % (g.ix[row], g.iy[row]), ""])
        grid.append(["Geometry file", "b2fgmtry",
                     "not found or not unstructured", ""])
        if rho is not None and np.isfinite(rho(cx, cy)):
            eq.append(["Rho poloidal at the centre", "rhop (rzpsi.dat)",
                       _num(rho(cx, cy)), ""])
        return grid, eq, []
    i = icv - 1
    ncv = len(geo.get("cvX"))
    nfc, nvx = len(geo.get("fcS")), len(geo.get("vxX"))

    def val(name):
        a = geo.get(name)
        return None if a is None else a[i]

    def add(out, text, name, value, unit=""):
        if value is not None:
            out.append([text, name, value if isinstance(value, str) else
                        _num(value), unit])
    # the grid
    cx, cy = val("cvX"), val("cvY")
    add(grid, "Cell centre R", "cvX", cx, "m")
    add(grid, "Cell centre Z", "cvY", cy, "m")
    imap = geo.get("imapCv")
    nx, ny = geo.scalar("nx"), geo.scalar("ny")
    if imap is not None and nx and ny and len(imap) == (nx + 2) * (ny + 2):
        hit = np.argwhere(imap.reshape(ny + 2, nx + 2) == icv)
        if len(hit):
            add(grid, "Structured grid indices ix, iy", "imapCv",
                "%d, %d" % (hit[0][1] - 1, hit[0][0] - 1))
    volume, tubes = equilibrium.region_names(run, geo)
    reg = val("cvReg")
    if reg is not None:
        add(grid, "Region", "cvReg", "%d (%s)" % (reg, volume[int(reg)])
            if volume and int(reg) in volume else "%d" % reg)
    kind = val("cvLbl")
    if kind is not None:
        add(grid, "Cell kind", "cvLbl", "%d (%s)" % (
            kind, KINDS.get(int(kind), "other")))
    ift = val("cvFt")
    if ift is not None and ift > 0:
        add(grid, "Flux tube", "cvFt", ift)
        for name, text in (("ftReg", "Region of the flux tube"),
                           ("ftLbl", "Label of the flux tube")):
            a = geo.get(name)
            if a is not None and ift <= len(a):
                v = int(a[ift - 1])
                add(grid, text, name, "%d (%s)" % (v, tubes[v])
                    if name == "ftReg" and tubes and v in tubes else
                    "%d" % v)
    add(grid, "Volume", "cvVol", val("cvVol"), "m^3")
    add(grid, "Area in the poloidal plane", "cvSz", val("cvSz"), "m^2")
    add(grid, "Poloidal length", "cvHx", val("cvHx"), "m")
    add(grid, "Toroidal length at the centre", "cvHz", val("cvHz"), "m")
    faces, face_eq = _faces(geo, i, icv, ncv, nfc)
    vertices, vertex_eq = _vertices(geo, i, ncv, nvx)
    grid += faces + vertices
    # the magnetic equilibrium
    if rho is not None and cx is not None and np.isfinite(rho(cx, cy)):
        add(eq, "Rho poloidal at the centre", "rhop (rzpsi.dat)",
            rho(cx, cy))
        add(eq, "Normalised poloidal flux at the centre", "psiN (rzpsi.dat)",
            rho(cx, cy) ** 2)
    bb = geo.table("cvBb", ncv)
    if bb is not None:
        for k, text in enumerate(("Magnetic field b_x (poloidal)",
                                  "Magnetic field b_y (radial)",
                                  "Magnetic field b_z (toroidal)",
                                  "Magnetic field strength |B|")):
            add(eq, text, "cvBb(:,%d)" % k, bb[k][i], "T")
    eb = geo.table("cvEb", ncv)
    if eb is not None:
        add(eq, "Field direction (unit vector R, Z, toroidal)", "cvEb",
            _list(eb[:, i]))
    conn = run.cache.get(("field", "conn", (), None))
    add(eq, "Connection length, to the nearer target (closed tube: the "
        "tube)", "cvConn", float(conn.values[0][i]) if conn is not None
        else val("cvConn"), "m")
    eq += face_eq + vertex_eq
    derived = [[q, n, v if isinstance(v, str) else _num(v), u]
               for q, n, v, u in equilibrium.derived_rows(run, geo, i, ncv,
                                                          nfc)]
    return grid, eq, derived


def _pointed(geo, pointer, items, i, ncv):
    """Entries of items for cell i through the pointer array (cvFcP,
    cvVxP), or []."""
    p, a = geo.table(pointer, ncv), geo.get(items)
    if p is None or a is None:
        return []
    return list(a[p[0][i] - 1:p[0][i] - 1 + p[1][i]])


def _faces(geo, i, icv, ncv, nfc):
    """The faces of the cell, in the order of cvFc: (grid rows, magnetic
    equilibrium rows)."""
    faces = _pointed(geo, "cvFcP", "cvFc", i, ncv)
    if not faces:
        return [], []
    f = np.asarray(faces) - 1
    grid, eq = [["Faces (%d)" % len(faces), "cvFc", _list(faces), ""]], []
    cells = geo.table("fcCv", nfc)
    side = None
    if cells is not None:
        side = np.where(cells[0][f] == icv, 0, 1)
        grid.append(["Cells across the faces", "fcCv",
                     _list(cells[1 - side, f]), ""])

    def per_face(out, text, name, unit="", k=None):
        a = geo.get(name) if k is None else geo.table(name, nfc)
        if a is not None:
            out.append([text, name, _list(a[f] if k is None else a[k][f]),
                        unit])

    def angle(out, name, text):
        q = geo.table(name, nfc)
        if q is not None:
            out.append([text, name, _list(np.degrees(np.arctan2(
                q[1][f], q[0][f]))), "deg"])
    per_face(grid, "Face areas", "fcS", "m^2")
    per_face(grid, "Face lengths", "fcHt", "m")
    hc = geo.table("fcHc", nfc)
    if hc is not None and side is not None:
        grid.append(["Distances from the cell centre to the face centres",
                     "fcHc", _list(hc[side, f]), "m"])
    per_face(grid, "Regions of the faces", "fcReg")
    per_face(grid, "Labels of the faces", "fcLbl")
    angle(grid, "fcQgam", "Angle between cell connector and face normal")
    per_face(eq, "Parallel contact areas of the faces", "fcPbs", "m^2")
    angle(eq, "fcQalf", "Angle between magnetic field and face normal")
    angle(eq, "fcQbet", "Angle between cell connector and magnetic field")
    bb = geo.table("fcBb", nfc)
    if bb is not None:
        for k, text in enumerate(("Magnetic field b_x (poloidal) at the faces",
                                  "Magnetic field b_y (radial) at the faces",
                                  "Magnetic field b_z (toroidal) at the faces",
                                  "Magnetic field strength |B| at the faces")):
            eq.append([text, "fcBb(:,%d)" % k, _list(bb[k][f]), "T"])
    return grid, eq


def _vertices(geo, i, ncv, nvx):
    """The vertices of the cell, in the order of cvVx: (grid rows,
    magnetic equilibrium rows)."""
    vx = _pointed(geo, "cvVxP", "cvVx", i, ncv)
    if not vx:
        return [], []
    v = np.asarray(vx) - 1
    grid, eq = [["Vertices (%d)" % len(vx), "cvVx", _list(vx), ""]], []
    for out, name, text, unit in (
            (grid, "vxX", "Vertex R", "m"), (grid, "vxY", "Vertex Z", "m"),
            (eq, "vxFpsi", "Poloidal flux at the vertices", "Wb"),
            (eq, "vxFfbz", "Toroidal field function at the vertices",
             "T m")):
        a = geo.get(name)
        if a is not None and len(a) == nvx:
            out.append([text, name, _list(a[v]), unit])
    return grid, eq


def triangle_rows(run, jt, tri, rho=None):
    """The EIRENE triangle jt (0-based): corners, neighbours, its B2.5
    cell and faces, centroid, area and volume."""
    t = run.trimesh
    nodes = t.triangles[jt] + 1
    r, z = t.x[nodes - 1], t.y[nodes - 1]
    out = [["Triangle number", "", "%d" % (jt + 1), ""],
           ["Nodes", "NECKE (fort.34)", _list(nodes), ""],
           ["Node R", "XTRIAN (fort.33)", _list(r), "m"],
           ["Node Z", "YTRIAN (fort.33)", _list(z), "m"]]
    if tri is not None and jt < len(tri.neighbours):
        out += [["Neighbour triangles of sides 1, 2, 3 (0: none)",
                 "NCHBAR (fort.35)", _list(tri.neighbours[jt]), ""],
                ["Side of each neighbour facing this triangle",
                 "NSEITE (fort.35)", _list(tri.sides[jt]), ""],
                ["Additional surface on sides 1, 2, 3 (0: none)",
                 "INMTI (fort.35)", _list(tri.surfaces[jt]), ""]]
        extra = tri.extra[jt]
        if len(extra) == 4:
            out += [["B2.5 cell of the triangle (-1: none)",
                     "iCv (fort.35)", "%d" % extra[0], ""],
                    ["B2.5 faces on sides 1, 2, 3 (0: none)",
                     "iFc (fort.35)", _list(extra[1:]), ""]]
        elif len(extra) == 2:
            out.append(["B2.5 cell ix, iy of the triangle",
                        "IXTRI, IYTRI (fort.35)", _list(extra), ""])
    cr, cz = float(r.mean()), float(z.mean())
    out += [["Centroid R", "tr", _num(cr), "m"],
            ["Centroid Z", "tz", _num(cz), "m"]]
    if rho is not None and np.isfinite(rho(cr, cz)):
        out.append(["Rho poloidal at the centroid", "rhop (rzpsi.dat)",
                    _num(rho(cr, cz)), ""])
    for name, text, unit in (("triarea", "Triangle area", "m^2"),
                             ("triavol", "Triangle volume", "m^3")):
        d = run.cache.get(("efield", name, (), None))
        out.append([text, name, _num(float(d.values[0][jt])) if d is not None
                    else "loading…", unit])
    return out
