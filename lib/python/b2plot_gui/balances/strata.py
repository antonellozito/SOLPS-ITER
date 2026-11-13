"""The EIRENE strata of b2.neutrals.parameters for the legends and the 2D
plot: kind of each stratum (crcstra: recycling, gas puff, volume
recombination, time-dependent) and the boundary faces of the recycling
ones (kind A: the faces with rcstart <= fcLbl <= rcend, as B2.5 reads it;
kinds N, S, E, W: the guard cells b2plot labels with the stratum, rc)."""

import numpy as np

from ..tools import cellfiles

KINDS = {"C": "gas puff", "V": "volume recombination",
         "T": "time-dependent"}
RECYCLING = "SNWEA"


class Strata:
    """Strata definitions of a run (empty without b2.neutrals.parameters)."""

    def __init__(self, rundir):
        nl = cellfiles.namelist(cellfiles.find(rundir,
                                               "b2.neutrals.parameters"))
        self.kinds = [v.strip("'\" ").upper() for v in nl.get("crcstra", [])]
        n = len(self.kinds)

        def ints(name):
            vals = [int(float(v)) for v in nl.get(name, [])]
            return (vals + [0] * n)[:n]
        self.start, self.end, self.pos = ints("rcstart"), ints("rcend"), \
            ints("rcpos")

    def kind(self, k):
        """Kind of stratum k (0-based), '' if not known."""
        if k >= len(self.kinds):
            return ""
        c = self.kinds[k][:1]
        return "recycling" if c and c in RECYCLING else KINDS.get(c, "")

    def label(self, k):
        kind = self.kind(k)
        return "Stratum %d%s" % (k + 1, " (%s)" % kind if kind else "")

    def recycling(self, k):
        return self.kind(k) == "recycling"

    def needs_rc(self):
        """True if some recycling stratum is of the old kinds (N, S, E,
        W): its faces come from the b2plot label rc."""
        return any(c[:1] in "NSEW" for c in self.kinds if c)

    def faces(self, k, grid, rc=None):
        """Boundary faces of recycling stratum k (0-based)."""
        if not self.recycling(k):
            return np.zeros(0, int)
        code = self.kinds[k][:1]
        if code == "A":
            lbl = grid.fcLbl
            return np.flatnonzero((lbl >= self.start[k]) &
                                  (lbl <= self.end[k]) & (lbl > 0))
        if rc is None:
            return np.zeros(0, int)
        same = [j for j in range(k + 1) if self.kinds[j] == self.kinds[k]
                and (self.start[j], self.end[j], self.pos[j]) ==
                (self.start[k], self.end[k], self.pos[k])]
        cells = np.flatnonzero(np.isin(np.rint(rc[:grid.nCv]),
                                       [j + 1 for j in same[:1]]))
        guard = cells[cells >= grid.nCi]
        mask = np.isin(grid.fc, guard).any(axis=1) & grid.guard
        return np.flatnonzero(mask)
