"""b2chords.nc (the B2.5 quantities) and eirenechords.nc (the EIRENE ones
on its triangles) of a run: the profiles in time along the chords of the
*.chords files of the run; a group per chord file (a set of chords) with
one group per chord in it (its points R, z, phi inside the grid, the
distance ds along it from its start, its number: its line in the file),
and the line integrals and averages along a chord."""

import re
from dataclasses import dataclass

import numpy as np

from ..catalog import NEUTRAL_TRIANGLES, OTHER_GROUP, SOLPS_GROUPS, \
    solps_order
from ..tools import measure
from .files import E_CHARGE, Item, NcFile, summed, unit

# groups of the quantities of b2chords.nc (those of eirenechords.nc: one),
# as those of the movie files
GROUPS = SOLPS_GROUPS
TRIANGLES = NEUTRAL_TRIANGLES
OTHER = OTHER_GROUP
SPECIES = ("ns", "natm", "nmol")
GAP = 1.5                           # steps: the chord left the grid there
AMU = 1.66053906892e-27             # kg, the masses as b2plot has them
# quantities of eirenechords.nc computed as the b2plot labels of the final
# state, after the density of each species (atoms a, molecules m): name,
# (kind, species, x/y/z), description, unit
DERIVED = {n: d for k, w in (("a", "Atom"), ("m", "Molecule")) for n, d in (
    [("temp" + k, (("temp", k, ""), w + " temperature", "eV")),
     ("pres" + k, (("pres", k, ""), w + " pressure", "Pa"))] +
    [("v%s%s" % (c, k), (("vel", k, c), "%s %s-directed velocity" % (w, c),
                         "m s^-1")) for c in "xyz"] +
    [("f%sden%s" % (c, k), (("flux", k, c), "%s %s-directed particle flux "
                            "density" % (w, c), "m^-2 s^-1")) for c in "xyz"])}
NEEDS = {"temp": ("p", "e"), "pres": ("e",), "vel": ("p", "v"),
         "flux": ("v",)}


@dataclass
class Chord:
    """A chord of a set: its points inside the grid."""
    number: int                     # its line in its chord file
    group: object                   # its netCDF group
    r: np.ndarray
    z: np.ndarray
    phi: np.ndarray
    ds: np.ndarray                  # distance from its start (m)
    value: float                    # last column of its line

    def parts(self):
        """Index ranges of the parts of the chord inside the grid."""
        d = np.diff(self.ds)
        step = np.median(d) if len(d) else 0.0
        cut = np.flatnonzero(d > GAP * step) + 1 if step > 0 else []
        edges = [0] + list(cut) + [len(self.ds)]
        return [(a, b) for a, b in zip(edges[:-1], edges[1:]) if b > a]


class ChordFile(NcFile):
    """An open b2chords.nc or eirenechords.nc."""

    def __init__(self, path):
        super().__init__(path)
        self.times = self.array(self.nc["times"])
        self.sets, self.chords = {}, {}     # set -> label, [Chord]
        self.masses = dict                  # -> {a, m: [kg per species]}
        for name, s in self.nc.groups.items():
            self.sets[name] = str(getattr(s, "label", name))
            self.chords[name] = [self._chord(g) for g in s.groups.values()]
        first = next((c for cs in self.chords.values() for c in cs), None)
        self.fields = [] if first is None else [
            v for v in first.group.variables.values()
            if v.dimensions[:1] == ("time",)]

    def _chord(self, g):
        def get(name):
            return self.array(g[name], (g.path, name)).ravel() if name in \
                g.variables else np.zeros(0)
        number = get("chord_id")
        value = get("chord_value")
        return Chord(int(number[0]) if number.size else 0, g, get("R"),
                     get("z"), get("phi"), get("ds"),
                     float(value[0]) if value.size else np.nan)

    def items(self):
        """The quantities along the chords, in their groups in order."""
        out = []
        eirene = self.name.startswith("eirene")
        for group, pattern in (((TRIANGLES, r".*"),) if eirene else
                               GROUPS + ((OTHER, r".*"),)):
            for v in self.fields:
                if any(i.name == v.name for i in out) or \
                        not re.fullmatch(pattern, v.name) or \
                        v.name.endswith("sum"):     # sums over the species
                    continue
                long = str(getattr(v, "long_name", v.name)).strip()
                dim = next((d for d in v.dimensions if d in SPECIES), "")
                out.append(Item(v.name, long[:1].upper() + long[1:], group,
                                unit(v), self.name, "chord", dim, long=long))
        return self._with_derived(out) if eirene else out

    @staticmethod
    def _base(kind, k, c):
        """Variables of eirenechords.nc a derived quantity needs."""
        return [b + "den" + k if b != "v" else "v%sden%s" % (c, k)
                for b in NEEDS[kind]]

    def _with_derived(self, items):
        """The items with the DERIVED quantities whose variables exist,
        each species in the order density, temperature, pressure, energy
        density, velocity, particle flux density, momentum density."""
        have = {i.name: i for i in items}
        out = []
        for k, dim in (("a", "natm"), ("m", "nmol")):
            for n in ["pden" + k, "temp" + k, "pres" + k, "eden" + k] + [
                    p % (c, k) for p in ("v%s%s", "f%sden%s", "v%sden%s")
                    for c in "xyz"]:
                if n in have:
                    out.append(have.pop(n))
                elif n in DERIVED and all(b in have or any(
                        i.name == b for i in out)
                        for b in self._base(*DERIVED[n][0])):
                    (_, d, u) = DERIVED[n]
                    out.append(Item(n, d, TRIANGLES, u, self.name, "chord",
                                    dim, long=d))
        return out + list(have.values())

    def chord(self, name, number):
        """The chord of the set with this number, or None."""
        return next((c for c in self.chords.get(name, [])
                     if c.number == number), None)

    def profile(self, item, chord, cols=(0,)):
        """The profiles (nt, npt) of the item along the chord, its species
        columns cols summed."""
        if item.name in DERIVED and item.name not in chord.group.variables:
            return self._derived(DERIVED[item.name][0], chord, list(cols))
        if item.name not in chord.group.variables:
            return None
        a = self.array(chord.group[item.name], (chord.group.path,
                                                item.name))
        return summed(a, 1, cols) if a.ndim == 3 else a

    def _derived(self, what, chord, cols):
        """Profiles of a DERIVED quantity, its species columns cols summed:
        temperature 2/3 of the energy over the particle density, pressure 2/3
        of the energy density, velocity momentum over mass density, particle
        flux density momentum density over mass (zero where the denominator
        is)."""
        kind, k, c = what
        names = self._base(kind, k, c)
        if any(n not in chord.group.variables for n in names):
            return None
        get = {n: self.array(chord.group[n], (chord.group.path, n))
               for n in names}
        m = np.asarray(self.masses().get(k, []), float)
        if kind in ("vel", "flux") and len(m) <= max(cols):
            return None                 # masses not known (yet)

        def ratio(a, b):
            return np.divide(a, b, out=np.zeros_like(a), where=b != 0)
        if kind == "temp":
            return 2.0 / 3.0 * ratio(summed(get["eden" + k], 1, cols),
                                     summed(get["pden" + k], 1, cols))
        if kind == "pres":
            return 2.0 / 3.0 * E_CHARGE * summed(get["eden" + k], 1, cols)
        v = get["v%sden%s" % (c, k)]
        mm = m[None, :v.shape[1], None]
        if kind == "flux":
            return summed(ratio(v, mm * np.ones_like(v)), 1, cols)
        return ratio(summed(v, 1, cols),
                     summed(get["pden" + k] * mm, 1, cols))

    def species_count(self, item):
        return len(self.nc.dimensions[item.dim]) if item.dim else 1


def ordered(items):
    """The quantities of the chord files in the order of their groups (the
    EIRENE triangles after the B2.5 grid, whatever the file order) and
    within them as those of the movie files (catalog.solps_order)."""
    return solps_order(items)


def line_sums(chord, values):
    """(integral, average) along the chord of each profile of values (nt,
    npt), as the Chords section computes them (trapezoids between known
    points), not across the parts outside the grid."""
    s = chord.ds.astype(float)
    cut = [b for _, b in chord.parts()[:-1]]
    mid = [0.5 * (s[b - 1] + s[b]) for b in cut]
    s = np.insert(s, cut, mid)          # a point without value in each gap
    v = np.insert(np.asarray(values, float), cut, np.nan, axis=1)
    sums = np.array([measure.line_sums(s, s, row, None)[1:3] for row in v],
                    float).reshape(-1, 2)
    return sums[:, 0], sums[:, 1]
