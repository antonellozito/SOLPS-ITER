"""balance.nc of a run: whether it belongs to the present state of the run
(written with b2fstate and b2fplasma at the end of the same run), its grid,
and its fields in the order of the balance scripts (cells or faces first,
then components, species, strata)."""

import os

import numpy as np

NAME = "balance.nc"
STATE = ("b2fstate", "b2fplasma")
SLACK = 300.0               # seconds between balance.nc and the state files
# fields of older balance.nc files under their old names
OLD_NAMES = {"eirene_mc_mppl_smo_bal": "eirene_mc_cppv_smo_bal"}


def _netcdf4():
    try:
        import netCDF4
    except ImportError:
        return None
    return netCDF4


def status(rundir):
    """(path, "") of a balance.nc of the present state of the run, or
    (None, reason)."""
    if _netcdf4() is None:
        return None, "The balances need the Python module netCDF4"
    path = os.path.join(rundir, NAME)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return None, "No balance.nc in the run directory (balance_netcdf " \
            "set in b2mn.dat writes it)"
    times = [os.path.getmtime(p) for p in (os.path.join(rundir, n)
                                           for n in STATE)
             if os.path.isfile(p)]
    if not times:
        return None, "No b2fstate or b2fplasma next to balance.nc"
    gap = abs(os.path.getmtime(path) - max(times))
    if gap > SLACK:
        return None, "balance.nc is %s older or newer than b2fstate and " \
            "b2fplasma: it is not from the run of this state" % _age(gap)
    return path, ""


def _age(seconds):
    for unit, size in (("days", 86400.0), ("hours", 3600.0),
                       ("minutes", 60.0)):
        if seconds >= 2 * size:
            return "%.0f %s" % (seconds / size, unit)
    return "%.0f seconds" % seconds


class BalanceFile:
    """One open balance.nc. Fields come back transposed (the order of the
    balance scripts), species summed over isplot when asked."""

    def __init__(self, path):
        self.path = path
        self.nc = _netcdf4().Dataset(path)
        self.nc.set_auto_mask(False)
        self.dims = {k: len(v) for k, v in self.nc.dimensions.items()}
        self.missing = []           # optional fields not in the file
        self.ns = self.dims["ns"]
        self.nstra = self.dims.get("nstra", 0)
        self.za = self.raw("za").astype(int)
        self.am = self.raw("am").astype(float)
        self.mp = float(self.raw("mp").ravel()[0])
        self.ev = float(self.raw("ev").ravel()[0])
        self.eirene = int(self.raw("b2mndr_eirene").ravel()[0]) != 0
        self.hz = float(self.raw("b2mndr_hz").ravel()[0])
        chars = np.asarray(self.nc["species"][:])
        self.species = ["".join(c.decode() if isinstance(c, bytes) else
                                str(c) for c in row).strip()
                        for row in chars.reshape(self.ns, -1)]

    def close(self):
        self.nc.close()

    def solved(self):
        """Per species: True if B2.5 solves its equations (continuity or
        momentum residual not zero everywhere)."""
        if getattr(self, "_solved", None) is None:
            res = [self.raw(n) for n in ("resco", "resmo")]
            self._solved = [any(bool(np.any(r[:, i] != 0)) for r in res)
                            for i in range(self.ns)]
        return self._solved

    def has(self, name):
        return name in self.nc.variables or OLD_NAMES.get(name) in \
            self.nc.variables

    def raw(self, name):
        """A whole field in the order of the balance scripts."""
        return np.asarray(self.nc[self._name(name)][:]).T

    def _name(self, name):
        if name not in self.nc.variables and OLD_NAMES.get(name) in \
                self.nc.variables:
            return OLD_NAMES[name]
        return name

    def _read(self, name, species, axis):
        """Field transposed, species summed (axis: the species axis of the
        file, counted from the front)."""
        var = self.nc[self._name(name)]
        if species is None:
            a = np.asarray(var[:])
        else:
            index = [slice(None)] * var.ndim
            index[axis] = list(species)
            a = np.asarray(var[tuple(index)]).sum(axis=axis, keepdims=True)
        return a.T

    def _optional(self, name, shape):
        if self.has(name):
            return None
        if name not in self.missing:
            self.missing.append(name)
        return np.zeros(shape)

    def face(self, name, species=None, optional=False):
        """Flux on the faces, (nFc, 2): poloidal and radial component;
        species fields summed over species (all of them if None)."""
        if optional:
            z = self._optional(name, (self.dims["nFc"], 2))
            if z is not None:
                return z
        var = self.nc[self._name(name)]
        if var.ndim == 2:
            return np.asarray(var[:]).T.astype(float)
        a = self._read(name, range(self.ns) if species is None else species,
                       0)
        return a[:, :, 0].astype(float)

    def face_species(self, name, optional=False):
        """Flux on the faces of every species, (nFc, 2, ns)."""
        if optional:
            z = self._optional(name, (self.dims["nFc"], 2, self.ns))
            if z is not None:
                return z
        return self.raw(name).astype(float)

    def cell(self, name, species=None, optional=False):
        """Cell field, (nCv,); species fields summed over species."""
        if optional:
            z = self._optional(name, (self.dims["nCv"],))
            if z is not None:
                return z
        var = self.nc[self._name(name)]
        if var.ndim == 1:
            return np.asarray(var[:]).astype(float)
        if var.ndim == 3:                   # by stratum in older files
            return np.nansum(self.strata(name, species), axis=1)
        a = self._read(name, range(self.ns) if species is None else species,
                       0)
        return a[:, 0].astype(float)

    def cell_species(self, name, optional=False):
        """Cell field of every species, (nCv, ns)."""
        if optional:
            z = self._optional(name, (self.dims["nCv"], self.ns))
            if z is not None:
                return z
        a = self.raw(name).astype(float)
        return np.nansum(a, axis=2) if a.ndim == 3 else a

    def strata(self, name, species=None, optional=False):
        """EIRENE field by stratum, (nCv, nstra); species fields summed."""
        if optional:
            z = self._optional(name, (self.dims["nCv"], self.nstra))
            if z is not None:
                return z
        var = self.nc[self._name(name)]
        if var.ndim == 2:
            return np.asarray(var[:]).T.astype(float)
        a = self._read(name, range(self.ns) if species is None else species,
                       1)
        return a[:, 0, :].astype(float)
