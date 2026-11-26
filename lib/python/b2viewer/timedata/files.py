"""The tracing files of a run: those of its latest run, found as the movie
files are (runstate.movies), opened with netCDF4; the quantities they
hold (Item), their values as floats."""

import os
from dataclasses import dataclass

import numpy as np

from .. import runstate
from ..describe import wording

B2TIME = "b2time.nc"
CHORDS = ("b2chords.nc", "eirenechords.nc")
TALLIES = "b2tallies.nc"
NAMES = (B2TIME,) + CHORDS + (TALLIES,)
E_CHARGE = 1.602176634e-19          # J per eV
CACHE = 16                          # arrays kept per file


def netcdf4():
    try:
        import netCDF4
    except ImportError:
        return None
    return netCDF4


def latest(rundir, kind):
    """({name: path} of the tracing files of the latest run of the run
    directory (kind: runstate.state), [why the others are left out])."""
    found = runstate.movies(rundir, kind, NAMES)
    return ({n: p for n, (p, why) in found.items() if not why},
            [why for _, why in found.values() if why])


def unit(var):
    """Plain unit of a variable (m^-3, m^2 s^-1): the dots blanks, no
    question marks, none for 1."""
    u = " ".join(str(getattr(var, "units", "")).replace("?", "").replace(
        ".", " ").split())
    return "" if u == "1" else u


@dataclass
class Item:
    """A quantity of the run tracing: a variable of a tracing file."""
    name: str
    description: str            # what it is (without where)
    group: str
    unit: str
    file: str                   # B2TIME, one of CHORDS or TALLIES
    kind: str                   # "trace", "profile", "chord" or "tally"
    dim: str = ""               # dimension of its species: ns, natm, nmol
    index: int = 0              # divertor of a trace (dimension nc)
    where: str = ""             # where it is, for the titles
    place: str = ""             # its place on the plot
    long: str = ""              # long name in the file
    parts: tuple = ()           # time traces: (variable, curve label)

    def __post_init__(self):
        self.description = wording(self.description)

    @property
    def text(self):
        """What the lists show: the description with its unit (none for a
        pure number)."""
        return "%s (%s)" % (self.description, self.unit) if self.unit \
            else self.description

    @property
    def label(self):
        if len(self.parts) > 1:
            return "/".join(n for n, _ in self.parts)
        return "%s(%d)" % (self.name, self.index + 1) if self.index \
            else self.name

    def title(self, species=""):
        """What it is, its species and where."""
        return self.description + (" [%s]" % species if species else "") + \
            (", " + self.where if self.where else "")


class NcFile:
    """An open netCDF file, its arrays as floats (the last ones read
    kept)."""

    def __init__(self, path):
        self.path, self.name = path, os.path.basename(path)
        self.nc = netcdf4().Dataset(path)
        self.nc.set_auto_mask(False)
        self._cache = {}

    def close(self):
        try:
            self.nc.close()
        except (RuntimeError, OSError):
            pass

    def array(self, var, key=None):
        """The values of a variable as floats; temperatures in eV that
        were written in J (b2time.nc writes some so) in eV."""
        key = key or var.name
        if key in self._cache:
            return self._cache[key]
        a = np.asarray(var[:], float)
        if unit(var) == "eV":
            known = np.abs(a[np.isfinite(a)])
            if known.size and 0 < known.max() < 1e-10:
                a = a / E_CHARGE
        if len(self._cache) >= CACHE:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = a
        return a


def summed(a, axis, cols):
    """a summed over the columns cols of an axis (that axis removed)."""
    return np.take(a, list(cols), axis=axis).sum(axis=axis)
