"""The values of the balance plots for other programs: CSV table, ASCII
text, netCDF or HDF5 (the formats of Export field), one table per abscissa
of the plots."""

import csv
import re

import numpy as np

from ..output.fieldfile import FORMATS, FILTERS, _netcdf4  # noqa: F401


def _name(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower() or "value"


def write(path, title, tables, xname, unit, meta):
    """tables: [(name, x, [(label, y)])]; xname: the abscissa of each
    table; meta: [(key, value)] written as header lines or attributes."""
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "csv":
        _csv(path, title, tables, xname, unit, meta)
    elif ext == "txt":
        _text(path, title, tables, xname, unit, meta)
    else:
        _nc(path, title, tables, xname, unit, meta, ext == "h5")


def _header(f, title, unit, meta):
    f.write("# %s\n" % title)
    for k, v in meta:
        f.write("# %s: %s\n" % (k, v))
    f.write("# unit of the values: %s\n" % unit)


def _csv(path, title, tables, xname, unit, meta):
    with open(path, "w", newline="") as f:
        _header(f, title, unit, meta)
        out = csv.writer(f)
        for k, (name, x, cols) in enumerate(tables):
            if k:
                f.write("\n")
            f.write("# %s\n" % name)
            out.writerow([xname(name)] + [label for label, _ in cols])
            for i in range(len(x)):
                out.writerow(["%.9g" % x[i]] + ["%.9g" % y[i]
                                                for _, y in cols])


def _text(path, title, tables, xname, unit, meta):
    with open(path, "w") as f:
        _header(f, title, unit, meta)
        for name, x, cols in tables:
            f.write("#\n# %s\n# columns: %s\n" % (name, "; ".join(
                [xname(name)] + [label for label, _ in cols])))
            for i in range(len(x)):
                f.write(" ".join("%16.9e" % v for v in
                                 [x[i]] + [y[i] for _, y in cols]) + "\n")


def _nc(path, title, tables, xname, unit, meta, hdf5):
    netCDF4 = _netcdf4()
    with netCDF4.Dataset(path, "w", format="NETCDF4") as nc:
        nc.title = title
        for k, v in meta:
            nc.setncattr(_name(k), str(v))
        for name, x, cols in tables:
            g = nc.createGroup(_name(name)) if hdf5 or len(tables) > 1 \
                else nc
            g.createDimension("point", len(x))
            v = g.createVariable("x", "f8", ("point",))
            v[:] = x
            v.long_name = xname(name)
            used = set()
            for label, y in cols:
                key = _name(label)
                while key in used:
                    key += "_"
                used.add(key)
                v = g.createVariable(key, "f8", ("point",))
                v[:] = np.asarray(y, float)
                v.long_name = label
                v.units = unit
