"""fort.44 of EIRENE (the SOLPS interface, a title line before each field:
"*eirene data field <name> with size <n>"): the species, the surfaces
(additional ones first, their ends in wall_geometry; then the
non-default standard ones, their B2.5 faces through eirdiag and
fnmti_b2) and the surface tallies, the ones by stratum named
<field>(<stratum>); fields read when asked."""

import re

import numpy as np

HEAD = "*eirene data field "
NUMBER = re.compile(r"(\d)([+-]\d{2,3})$")     # 1.0-100: 1.0E-100


def _float(token):
    try:
        return float(token)
    except ValueError:
        return float(NUMBER.sub(r"\1E\2", token))


class Fort44:
    """One fort.44, its fields by name."""

    def __init__(self, path):
        with open(path) as f:
            self.lines = f.read().splitlines()
        lines = self.lines
        self.natm, self.nmol, self.nion = (int(v) for v in
                                           lines[1].split()[:3])
        n = self.natm + self.nmol + self.nion
        names = [line.strip() for line in lines[2:2 + n]]
        self.atoms = names[:self.natm]
        self.molecules = names[self.natm:self.natm + self.nmol]
        self.ions = names[self.natm + self.nmol:]
        self.at = {}
        for i, line in enumerate(lines):
            if line.startswith(HEAD):
                name = re.sub(r"\s+", "", line[len(HEAD):line.index(
                    " with size")])
                self.at[name] = (i, int(line.split()[-1]))
        self.nsurf = self.at["wlarea"][1] if "wlarea" in self.at else 0
        self.nlim = self.at["wall_geometry"][1] // 4 if \
            "wall_geometry" in self.at else 0
        self.nstra = max([int(m.group(1)) for k in self.at for m in
                          [re.fullmatch(r"wldna\((\d+)\)", k)] if m] or [0])

    def has(self, name):
        return name in self.at

    def block(self, name):
        """The numbers of a field (its text lines, names, skipped)."""
        i, n = self.at[name]
        out, j = [], i + 1
        while len(out) < n and j < len(self.lines):
            try:
                out.extend(_float(t) for t in self.lines[j].split())
            except ValueError:
                pass
            j += 1
        return np.array(out[:n], float)

    def by_surface(self, name, m):
        """(surfaces, m) of a field written surface by surface for each
        species (the tallies)."""
        return self.block(name).reshape(m, self.nsurf).T

    def by_species(self, name, m):
        """(surfaces, m) of a field written species by species for each
        surface (wlpump)."""
        return self.block(name).reshape(self.nsurf, m)

    def walls(self):
        """(nlim, 2, 2) ends (R, Z) of the additional surfaces."""
        return self.block("wall_geometry").reshape(self.nlim, 2, 2)

    def standard_faces(self):
        """[B2.5 faces (0-based)] of each non-default standard surface."""
        if not (self.has("eirdiag") and self.has("fnmti_b2")):
            return []
        start = self.block("eirdiag").astype(int)
        faces = self.block("fnmti_b2").astype(int)
        out = []
        for a, b in zip(start[:-1], start[1:]):
            f = faces[a:b - 1]          # segments a+1 .. b-1 (1-based)
            out.append(f[f > 0] - 1)
        return out
