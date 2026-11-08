"""The field shown with its geometry, for other programs: CSV (one row per
cell or triangle with its centre), VTK (legacy text, polygons in the
poloidal plane x = R, y = 0, z = Z, for ParaView) and netCDF (cell
corners and values; netCDF4 needed). Values are those b2plot sent."""

import csv
import os

import numpy as np

from ...b2plot import labels
from ..model import split_unit
from ..panels.quantity import column_names

FORMATS = "CSV (*.csv);;VTK (*.vtk);;netCDF (*.nc)"


def _cells(run, data):
    """Polygons, centres, numbers and value rows of the cells or
    triangles of the field (only cells with an area)."""
    g = run.geometry
    if data.location == "cells":
        rows = np.flatnonzero(g.visible)
        polys = [g.polygons[r] for r in rows]
        return polys, g.centres[rows], g.cells[rows], g.cells[rows] - 1, rows
    t = run.trimesh
    xy = np.column_stack((t.x, t.y))[t.triangles]
    n = np.arange(len(xy))
    return list(xy), xy.mean(axis=1), n + 1, n, None


def _columns(data, species):
    """(name, values) of each exported column: vectors give R and Z
    components."""
    names = column_names(data.columns, species)
    out = []
    for c, sp in enumerate(names):
        tag = "" if len(names) == 1 else " " + sp
        if hasattr(data, "vr"):
            out += [("%s R%s" % (data.name, tag), data.vr[c]),
                    ("%s Z%s" % (data.name, tag), data.vz[c])]
        else:
            out.append((data.name + tag, data.values[c]))
    return out


def write(path, run, data, species=None):
    """Write the field in the format of the extension of path."""
    ext = os.path.splitext(path)[1].lower()
    writer = {".csv": _csv, ".vtk": _vtk, ".nc": _netcdf}.get(ext)
    if writer is None:
        raise ValueError("unknown format %s (csv, vtk, nc)" % ext)
    writer(path, run, data, species)


def _csv(path, run, data, species):
    polys, centres, numbers, idx, rows = _cells(run, data)
    cols = _columns(data, species)
    g = run.geometry
    unit = labels.any_to_plain(split_unit(data.label)[1])
    with open(path, "w", newline="") as f:
        out = csv.writer(f)
        f.write("# %s, %s, run %s\n" % (labels.any_to_plain(data.label),
                                         unit, run.rundir))
        head = ["cell" if rows is not None else "triangle", "R (m)", "Z (m)"]
        if rows is not None:
            head += ["ix", "iy", "region"]
        out.writerow(head + [n for n, _ in cols])
        for k, (num, c) in enumerate(zip(numbers, centres)):
            row = [int(num), "%.6g" % c[0], "%.6g" % c[1]]
            if rows is not None:
                r = rows[k]
                row += [int(g.ix[r]), int(g.iy[r]), int(g.region[r])]
            out.writerow(row + ["%.7g" % v[idx[k]] for _, v in cols])


def _vtk(path, run, data, species):
    polys, _, numbers, idx, _ = _cells(run, data)
    npts = sum(len(p) for p in polys)
    with open(path, "w") as f:
        f.write("# vtk DataFile Version 3.0\n%s\nASCII\nDATASET POLYDATA\n"
                % labels.any_to_plain(data.label)[:250])
        f.write("POINTS %d float\n" % npts)
        for p in polys:
            for r, z in p:
                f.write("%.7g 0 %.7g\n" % (r, z))
        f.write("POLYGONS %d %d\n" % (len(polys), npts + len(polys)))
        k = 0
        for p in polys:
            f.write("%d %s\n" % (len(p), " ".join(
                str(i) for i in range(k, k + len(p)))))
            k += len(p)
        f.write("CELL_DATA %d\nSCALARS number int 1\nLOOKUP_TABLE default\n"
                % len(polys))
        f.write("\n".join(str(int(n)) for n in numbers) + "\n")
        for name, v in _columns(data, species):
            f.write("SCALARS %s float 1\nLOOKUP_TABLE default\n" % (
                "_".join(name.replace("{", "").replace("}", "").split())))
            f.write("\n".join("%.7g" % x for x in np.asarray(v)[idx]) + "\n")


def _netcdf(path, run, data, species):
    try:
        import netCDF4
    except ImportError:
        raise ValueError("netCDF export needs the Python module netCDF4")
    polys, centres, numbers, idx, rows = _cells(run, data)
    nv = max(len(p) for p in polys)
    corners = np.full((len(polys), nv, 2), np.nan)
    for k, p in enumerate(polys):
        corners[k, :len(p)] = p
    names = column_names(data.columns, species)
    with netCDF4.Dataset(path, "w") as nc:
        nc.title = labels.any_to_plain(data.label)
        nc.run = run.rundir
        nc.createDimension("cell", len(polys))
        nc.createDimension("corner", nv)
        nc.createDimension("column", len(names))
        for name, vals, dims, unit in (
                ("number", numbers, ("cell",), ""),
                ("r", centres[:, 0], ("cell",), "m"),
                ("z", centres[:, 1], ("cell",), "m"),
                ("corner_r", corners[..., 0], ("cell", "corner"), "m"),
                ("corner_z", corners[..., 1], ("cell", "corner"), "m")):
            v = nc.createVariable(name, "i4" if name == "number" else "f8",
                                  dims)
            v[:] = vals
            if unit:
                v.units = unit
        unit = labels.any_to_plain(split_unit(data.label)[1])
        comps = (("value_r", data.vr), ("value_z", data.vz)) if hasattr(
            data, "vr") else (("value", data.values),)
        for name, a in comps:
            v = nc.createVariable(name, "f8", ("column", "cell"))
            v[:] = np.asarray(a, float)[:, idx]
            v.units = unit
            v.long_name = labels.any_to_plain(data.label)
            v.columns = ", ".join(names)
