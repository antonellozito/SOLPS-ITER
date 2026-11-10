"""The field shown with the grid it lives on, for other programs: CSV table,
ASCII text, netCDF or HDF5. The files hold what rebuilds the grid: the
vertices (R, Z and psiN), every cell (or EIRENE triangle) with its vertex
numbers, centre, ix, iy and region, and the values of each species
column. Numbers count from 1, as in b2plot; values are those b2plot
sent."""

import csv

import numpy as np

from ...b2plot import labels
from ..model import split_unit
from ..panels.quantity import column_names

FORMATS = {"CSV table": ".csv", "ASCII text": ".txt", "NetCDF file": ".nc",
           "HDF5 file": ".h5"}
FILTERS = {".csv": "CSV table (*.csv)", ".txt": "ASCII text (*.txt)",
           ".nc": "NetCDF file (*.nc)", ".h5": "HDF5 file (*.h5)"}


def grid(run, data, species=None, name=None):
    """The field and its grid as plain arrays (dict); name: the quantity
    as the GUI calls it (default the b2plot name)."""
    g = run.geometry
    unit = labels.any_to_plain(split_unit(data.label)[1])
    name = name or data.name
    names = [""] if len(data.columns) == 1 and not data.columns[0].strip() \
        else column_names(data.columns, species)
    if data.location == "cells":
        rows = np.flatnonzero(g.visible)
        kind = "%s B2.5 grid" % ("classical" if g.classical else
                                 "unstructured")
        vx, psin = g.vx, g.psin
        corners = [g.corners[r] + 1 for r in rows]
        numbers, idx = g.cells[rows], g.cells[rows] - 1
        centres = g.centres[rows]
        extra = dict(ix=g.ix[rows], iy=g.iy[rows], region=g.region[rows])
    else:
        t = run.trimesh
        kind = "EIRENE triangles"
        vx, psin = np.column_stack((t.x, t.y)), None
        corners = list(t.triangles + 1)
        idx = np.arange(len(corners))
        numbers, centres = idx + 1, vx[t.triangles].mean(axis=1)
        extra = {}
    k = max(len(c) for c in corners)
    table = np.zeros((len(corners), k), int)
    for i, c in enumerate(corners):
        table[i, :len(c)] = c
    def column(*words):
        return " ".join(w for w in words if w)
    if hasattr(data, "vr"):
        values = {column(name, comp, n): np.asarray(a, float)[c][idx]
                  for c, n in enumerate(names)
                  for comp, a in (("R", data.vr), ("Z", data.vz))}
    else:
        values = {column(name, n): np.asarray(data.values, float)[c][idx]
                  for c, n in enumerate(names)}
    return dict(title=labels.any_to_plain(data.label), unit=unit, kind=kind,
                run=run.rundir, quantity=name, vertex=np.asarray(vx),
                psin=None if psin is None else np.asarray(psin),
                number=np.asarray(numbers), corners=table,
                nv=np.array([len(c) for c in corners]),
                centre=np.asarray(centres), values=values, **extra)


def write(path, run, data, species=None, name=None):
    """Write the field in the format of the extension of path."""
    d = grid(run, data, species, name)
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    writer = {".csv": _csv, ".txt": _text, ".nc": _netcdf,
              ".h5": _hdf5}.get(ext)
    if writer is None:
        raise ValueError("unknown format %s (csv, txt, nc, h5)" % ext)
    writer(path, d)


def _header(d):
    return ["b2plot field: %s (%s)" % (d["title"], d["unit"]),
            "run: %s" % d["run"],
            "grid: %s, %d cells, %d vertices; numbers from 1 as in b2plot, "
            "vertex 0: none" % (d["kind"], len(d["number"]),
                                len(d["vertex"]))]


def _cell_columns(d):
    """(names, columns) of the cell table."""
    k = d["corners"].shape[1]
    corners = d["corners"]
    vx = np.vstack((np.full((1, 2), np.nan), d["vertex"]))
    cols = [("cell", d["number"])] + [(n, d[n]) for n in ("ix", "iy",
                                                          "region") if n in d]
    cols += [("R (m)", d["centre"][:, 0]), ("Z (m)", d["centre"][:, 1]),
             ("vertices", d["nv"])]
    cols += [("v%d" % (j + 1), corners[:, j]) for j in range(k)]
    cols += [("R%d (m)" % (j + 1), vx[corners[:, j], 0]) for j in range(k)]
    cols += [("Z%d (m)" % (j + 1), vx[corners[:, j], 1]) for j in range(k)]
    cols += [("%s (%s)" % (n, d["unit"]), v) for n, v in d["values"].items()]
    return cols


def _fmt(v):
    if isinstance(v, (int, np.integer)):
        return "%d" % v
    return "%.8g" % v if np.isfinite(v) else ""


def _csv(path, d):
    cols = _cell_columns(d)
    with open(path, "w", newline="") as f:
        for line in _header(d):
            f.write("# %s\n" % line)
        out = csv.writer(f)
        out.writerow([n for n, _ in cols])
        for i in range(len(d["number"])):
            out.writerow([_fmt(c[i]) for _, c in cols])


def _text(path, d):
    """Two tables: the vertices, then the cells with their values."""
    cols = _cell_columns(d)
    with open(path, "w") as f:
        for line in _header(d):
            f.write("# %s\n" % line)
        f.write("#\n# vertices\n# %-8s %16s %16s%s\n" % (
            "vertex", "R (m)", "Z (m)", "" if d["psin"] is None else
            " %16s" % "psiN"))
        for i, (r, z) in enumerate(d["vertex"]):
            f.write("  %-8d %16.9g %16.9g%s\n" % (i + 1, r, z, "" if d[
                "psin"] is None else " %16.9g" % d["psin"][i]))
        f.write("#\n# cells\n# %s\n" % "  ".join(n.replace(" ", "")
                                                 for n, _ in cols))
        for i in range(len(d["number"])):
            f.write("  %s\n" % "  ".join(_fmt(c[i]) or "nan"
                                         for _, c in cols))


def _variables(nc, d):
    """The grid and the values in a netCDF4 Dataset or group."""
    nc.createDimension("vertex", len(d["vertex"]))
    nc.createDimension("cell", len(d["number"]))
    nc.createDimension("corner", d["corners"].shape[1])
    items = [("vertex_r", d["vertex"][:, 0], ("vertex",), "m"),
             ("vertex_z", d["vertex"][:, 1], ("vertex",), "m")]
    if d["psin"] is not None:
        items.append(("vertex_psin", d["psin"], ("vertex",), "1"))
    items += [("cell_number", d["number"], ("cell",), ""),
              ("cell_vertices", d["corners"], ("cell", "corner"), ""),
              ("cell_r", d["centre"][:, 0], ("cell",), "m"),
              ("cell_z", d["centre"][:, 1], ("cell",), "m")]
    items += [("cell_" + n, d[n], ("cell",), "") for n in ("ix", "iy",
                                                          "region") if n in d]
    for name, vals, dims, unit in items:
        integer = np.issubdtype(np.asarray(vals).dtype, np.integer)
        v = nc.createVariable(name, "i4" if integer else "f8", dims)
        v[:] = vals
        if unit:
            v.units = unit
    nc["cell_vertices"].long_name = "vertex numbers of the cell (0: none)"
    for i, (n, vals) in enumerate(d["values"].items()):
        v = nc.createVariable("value_%d" % (i + 1), "f8", ("cell",))
        v[:] = vals
        v.units = d["unit"]
        v.long_name = "%s, %s" % (d["title"], n)


def _attributes(nc, d):
    nc.title = "b2plot field: " + d["title"]
    nc.quantity = d["quantity"]
    nc.run = d["run"]
    nc.grid = d["kind"]
    nc.numbering = "from 1, as in b2plot"


def _netcdf(path, d):
    netCDF4 = _netcdf4()
    with netCDF4.Dataset(path, "w") as nc:
        _attributes(nc, d)
        _variables(nc, d)


def _hdf5(path, d):
    """An HDF5 file (written with netCDF4, readable by any HDF5 tool):
    groups grid and field."""
    netCDF4 = _netcdf4()
    with netCDF4.Dataset(path, "w", format="NETCDF4") as nc:
        _attributes(nc, d)
        _variables(nc.createGroup("grid"), dict(d, values={}))
        field = nc.createGroup("field")
        field.createDimension("cell", len(d["number"]))
        for i, (n, vals) in enumerate(d["values"].items()):
            v = field.createVariable("value_%d" % (i + 1), "f8", ("cell",))
            v[:] = vals
            v.units = d["unit"]
            v.long_name = "%s, %s" % (d["title"], n)


def _netcdf4():
    try:
        import netCDF4
    except ImportError:
        raise ValueError("netCDF and HDF5 export need the Python module "
                         "netCDF4") from None
    return netCDF4
