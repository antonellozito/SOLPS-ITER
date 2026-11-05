"""b2time.nc and b2batch.nc: one netCDF4 open per run, variables read as
the old scripts read them with nc2text, without starting nc2text.

Time traces come as rows: a variable (time, nc) gives nc rows, a species
name such as nasepm1 or dabsepm0 gives the nc rows of that species (index
after the name, from 0). The text of 2da is the text
nc2text_simple and awk.transpose write (Fortran order, 1-based
subscripts, negative ones from the end, values as 1pe18.10).
"""

import math
import os
import re
import sys

import numpy as np

from . import tracefiles

# Species variables over (time, nc, species): the others are (time, ns)
_NC_SPECIES = re.compile(r"^(namx.*|.*bsep.*|nasep.*)$")
_SUBSCRIPT = re.compile(r"^([A-Za-z_0-9]+)\((.*)\)$")


def open_file(name):
    """b2mn.exe.dir/name, else name (netCDF4); None if neither is there."""
    import netCDF4
    path = tracefiles.run_file(name)
    return netCDF4.Dataset(path) if path else None


def species_name(name, data):
    """(base, index) for a species name such as nasepm1 (base in data,
    the full name not); None otherwise."""
    m = re.match(r"^(.*?[^0-9])([0-9]+)$", name)
    if m and name not in data.variables and m.group(1) in data.variables:
        return m.group(1), int(m.group(2))
    return None


def rows(data, name):
    """The time rows of a variable or species name, as 2dt reads them."""
    found = species_name(name, data)
    if found:
        base, index = found
        a = np.asarray(data.variables[base][:], dtype=float)
        if a.ndim == 3 and _NC_SPECIES.match(base):
            return [a[:, r, index] for r in range(a.shape[1])]
        if a.ndim == 2:
            return [a[:, index]]
        if a.ndim == 3:
            return [a[:, index, r] for r in range(a.shape[2])]
        raise ValueError("%s: no species index for %s" % (name, base))
    a = np.asarray(data.variables[name][:], dtype=float)
    if a.ndim == 1:
        return [a]
    if a.ndim == 2:
        return [a[:, r] for r in range(a.shape[1])]
    raise ValueError("%s has more than two dimensions: give a species "
                     "index (%s0, %s1, ...)" % (name, name, name))


def fortran_e(value):
    """A value as Fortran 1pe18.10 writes it, without the blanks."""
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    text = "%.10E" % value
    mantissa, exponent = text.split("E")
    if len(exponent) > 3:
        return mantissa + exponent
    return text


def _bounds(part, low, high):
    """a, a:b, :b, a: of an nc2text subscript (missing ends keep the
    defaults 1 and 0, 0 meaning the end)."""
    part = part.strip()
    if ":" not in part:
        if part:
            low = high = int(part)
        return low, high
    a, b = part.split(":", 1)
    return (int(a) if a.strip() else low), (int(b) if b.strip() else high)


def nc2text(data, expression):
    """The lines nc2text_simple prints for a variable or name(subscripts)."""
    m = _SUBSCRIPT.match(expression)
    name, subscripts = (m.group(1), m.group(2)) if m else (expression, None)
    if name not in data.variables:
        raise KeyError(name)
    a = np.asarray(data.variables[name][:], dtype=float)
    f = a.T.reshape(a.T.shape + (1,) * (3 - a.ndim)) if a.ndim else \
        a.reshape(1, 1, 1)
    b = [1, 0, 1, 0, 1, 0]
    if subscripts is not None:
        parts = subscripts.split(",")
        if len(parts) == 1:
            b[2], b[3] = _bounds(parts[0], 1, 0)
        else:
            for n, part in enumerate(parts[:3]):
                b[2 * n], b[2 * n + 1] = _bounds(part, 1, 0)
    if a.ndim == 0:
        b = [1, 1, 1, 1, 1, 1]
    elif a.ndim == 1:
        b = [b[2], b[3], b[0], b[1], 1, 1]
    elif a.ndim == 2:
        b[4], b[5] = 1, 1
    for n in range(6):
        if b[n] <= 0:
            b[n] += f.shape[n // 2]
    i1, i2 = sorted(b[0:2])
    j1, j2 = sorted(b[2:4])
    k1, k2 = sorted(b[4:6])
    if (i2 > f.shape[0] or j2 > f.shape[1] or k2 > f.shape[2]
            or min(i1, j1, k1) <= 0):
        raise IndexError("index out of bounds")
    return ["".join("%18s" % fortran_e(f[i, j, k]) for i in range(i1 - 1, i2))
            for k in range(k1 - 1, k2) for j in range(j1 - 1, j2)]


def transpose(lines):
    """awk.transpose: fields split on blanks, as many output lines as the
    last input line has fields, a blank after every value."""
    fields = [line.split() for line in lines]
    if not fields:
        return []
    width = len(fields[-1])
    return ["".join((f[i] if i < len(f) else "") + " " for f in fields)
            for i in range(width)]


def warn(name, text):
    sys.stderr.write("%s: %s\n" % (name, text))


def source(name, batch=False):
    """(dataset, time variable): b2batch.nc (batchsa) for the averaged
    traces when present, else b2time.nc (timesa)."""
    if batch:
        data = open_file("b2batch.nc")
        if data is not None:
            return data, "batchsa"
    return open_file("b2time.nc"), "timesa"


def batch_name(data, name):
    """name in b2batch.nc: the _av variable when the plain one is absent."""
    if name in data.variables or species_name(name, data):
        return name
    found = re.match(r"^(.*?[^0-9])([0-9]*)$", name)
    base, index = found.groups()
    if base + "_av" in data.variables:
        return base + "_av" + index
    return name


def folder():
    return os.getcwd()
