"""b2chords.nc (the B2.5 quantities) and eirenechords.nc (the EIRENE ones
on its triangles) of a run: the profiles in time along the chords of the
*.chords files of the run; a group per chord file (a set of chords) with
one group per chord in it (its points R, z, phi inside the grid, the
distance ds along it from its start, its number: its line in the file),
and the line integrals and averages along a chord."""

import re
from dataclasses import dataclass

import numpy as np

from ..tools import measure
from .files import Item, NcFile, summed, unit

# groups of the quantities of b2chords.nc (those of eirenechords.nc: one)
GROUPS = (("Plasma state", r"na|ne|ua|te|ti|po"),
          ("Flux densities", r"f(na|he|hi|ch)[xy]"),
          ("Transport coefficients", r"dna|dpa|hc[ei]|vla[xy]|vsa"),
          ("Sources", r"r(sa|ra|cx)(na|hi|hisum)|rqahe(sum)?|rqrad(sum)?"),
          ("Neutrals on the B2.5 grid (EIRENE)", r"[dt][am]b2"),
          ("Neutral fluxes on the B2.5 grid (EIRENE)",
           r"(r|p|re|pe)flux[am]"),
          ("Neutral sources on the B2.5 grid (EIRENE)",
           r"eirene_\w+|eneutrad(sum)?|emolrad(sum)?"))
TRIANGLES = "Neutrals on the EIRENE triangles"
OTHER = "Other"
SPECIES = ("ns", "natm", "nmol")
GAP = 1.5                           # steps: the chord left the grid there


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
                        not re.fullmatch(pattern, v.name):
                    continue
                long = str(getattr(v, "long_name", v.name)).strip()
                dim = next((d for d in v.dimensions if d in SPECIES), "")
                out.append(Item(v.name, long[:1].upper() + long[1:], group,
                                unit(v), self.name, "chord", dim, long=long))
        return out

    def chord(self, name, number):
        """The chord of the set with this number, or None."""
        return next((c for c in self.chords.get(name, [])
                     if c.number == number), None)

    def profile(self, item, chord, cols=(0,)):
        """The profiles (nt, npt) of the item along the chord, its species
        columns cols summed."""
        if item.name not in chord.group.variables:
            return None
        a = self.array(chord.group[item.name], (chord.group.path,
                                                item.name))
        return summed(a, 1, cols) if a.ndim == 3 else a

    def species_count(self, item):
        return len(self.nc.dimensions[item.dim]) if item.dim else 1


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
