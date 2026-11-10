"""The geometry files of a run for the cell inspector, found as B2.5 finds
them (the run directory, .., ../baserun, ../../baserun): the B2.5 grid
geometry of b2fgmtry (b2fgmtry_us first; the variables documented in
b2cdcv) and the EIRENE triangles of fort.33 (nodes), fort.34 (corners)
and fort.35 (neighbours). Arrays are read when first asked for."""

import os
import re

import numpy as np

from ...run_plots.geometry import GEOMETRY

SEARCH = ("", os.pardir, os.path.join(os.pardir, "baserun"),
          os.path.join(os.pardir, os.pardir, "baserun"))
_HEAD = re.compile(r"^\*cf:\s+(\w+)\s+(\d+)\s+(\S+)[^\n]*\n", re.M)


def find(rundir, name):
    """Path of a run file (not empty), or None."""
    for folder in SEARCH:
        path = os.path.normpath(os.path.join(rundir, folder, name))
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


class GeometryFile:
    """The arrays of a b2fgmtry file (*cf: blocks); get(name) gives a 1D
    array (Fortran order), a string for text, None when absent."""

    def __init__(self, path):
        self.path = path
        with open(path) as f:
            self._text = f.read()
        heads = list(_HEAD.finditer(self._text))
        self._blocks = {}
        for k, m in enumerate(heads):
            end = heads[k + 1].start() if k + 1 < len(heads) else \
                len(self._text)
            for name in m.group(3).split(","):
                self._blocks.setdefault(name, (m.group(3), m.group(1),
                                               int(m.group(2)), m.end(),
                                               end))
        self._cache = {}

    def __contains__(self, name):
        return name in self._blocks and self._blocks[name][2] > 0

    def get(self, name):
        if name not in self:
            return None
        if name not in self._cache:
            block, kind, count, start, end = self._blocks[name]
            text = self._text[start:end]
            if kind == "char":
                self._cache[name] = text.strip()
            else:
                words = text.split()[:count]
                try:
                    a = np.array(words, float)
                except ValueError:          # Fortran D exponents
                    a = np.array([w.replace("D", "E") for w in words], float)
                a = a.astype(int) if kind == "int" else a
                names = block.split(",")
                if len(names) > 1:          # several scalars in one block
                    for i, n in enumerate(names):
                        self._cache[n] = a[i:i + 1]
                else:
                    self._cache[name] = a
        return self._cache[name]

    def scalar(self, name):
        a = self.get(name)
        return None if a is None or isinstance(a, str) else int(a[0])

    def table(self, name, n):
        """An array of first dimension n as rows: [k][i] for (i, k)."""
        a = self.get(name)
        return None if a is None or isinstance(a, str) or len(a) % n else \
            a.reshape(-1, n)


def geometry(rundir):
    """The unstructured B2.5 geometry of the run, or None."""
    for name in GEOMETRY:
        path = find(rundir, name)
        if path is not None:
            g = GeometryFile(path)
            if "cvX" in g:
                return g
    return None


class Triangles:
    """EIRENE triangles: nodes (R, Z in m), corners and neighbours
    (numbers from 1, as in the files)."""

    def __init__(self, paths):
        self.paths = paths
        x, y = _nodes(paths[0])
        self.r, self.z = x / 100.0, y / 100.0           # cm in the files
        self.corners = _rows(paths[1])[:, 1:4]
        n = _rows(paths[2])
        self.neighbours = n[:, 1:10:3]
        self.sides = n[:, 2:10:3]
        self.surfaces = n[:, 3:10:3]
        self.extra = n[:, 10:]      # iCv and three iFc, or ix, iy


def triangles(rundir):
    """The EIRENE triangles of the run, or None."""
    paths = [find(rundir, "fort.%d" % k) for k in (33, 34, 35)]
    if None in paths:
        return None
    try:
        return Triangles(paths)
    except (ValueError, IndexError):
        return None


def _nodes(path):
    """Node coordinates of fort.33: "i x y" lines, or all x then all y."""
    with open(path) as f:
        n = int(f.readline().split()[0])
        first = f.readline()
        words = first.split() + f.read().split()
    if len(first.split()) == 3:
        a = np.array(words[:3 * n], float).reshape(n, 3)
        return a[:, 1], a[:, 2]
    a = np.array([w.replace("D", "E") for w in words[:2 * n]], float)
    return a[:n], a[n:]


def _rows(path):
    """The numbers of fort.34 or fort.35, one row per triangle."""
    with open(path) as f:
        n = int(f.readline().split()[0])
        first = f.readline().split()
        words = first + f.read().split()
    return np.array(words[:n * len(first)], int).reshape(n, len(first))
