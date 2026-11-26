"""Files of a run read by the GUI, found as B2.5 finds them (the run
directory, .., ../baserun, ../../baserun): the B2.5 grid geometry of
b2fgmtry (b2fgmtry_us first; the variables documented in b2cdcv), the
EIRENE triangles of fort.33 (nodes), fort.34 (corners) and fort.35
(neighbours), and the midplane segments rzimp and rzomp of
b2.user.parameters. Arrays are read when first asked for."""

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


_NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][-+]?\d+)?")
_ITEM = re.compile(r"\b(rz[io]mp)\s*\(\s*(\d)\s*,\s*(\d)\s*\)\s*=", re.I)


def midplane_points(rundir):
    """{"inner": ((R1, Z1), (R2, Z2)), "outer": ...}: the segments rzimp
    and rzomp of b2.user.parameters (a Fortran namelist; rz(1, k) is the
    R of point k, rz(2, k) its Z; values after one index fill the next
    ones in column order), those given completely."""
    path = find(rundir, "b2.user.parameters")
    if path is None:
        return {}
    with open(path) as f:
        text = "\n".join(line.split("!")[0] for line in f)
    values = {"rzimp": np.full(4, np.nan), "rzomp": np.full(4, np.nan)}
    items = list(_ITEM.finditer(text))
    for k, m in enumerate(items):
        end = items[k + 1].start() if k + 1 < len(items) else len(text)
        rhs = re.split(r"[A-Za-z_]\w*\s*(?:\(|=)|/", text[m.end():end])[0]
        start = int(m.group(2)) - 1 + 2 * (int(m.group(3)) - 1)
        for j, word in enumerate(_NUMBER.findall(rhs)):
            if start + j < 4:
                values[m.group(1).lower()][start + j] = float(
                    word.replace("d", "e").replace("D", "E"))
    out = {}
    for name, side in (("rzimp", "inner"), ("rzomp", "outer")):
        v = values[name]
        if np.isfinite(v).all() and (v[0], v[1]) != (v[2], v[3]):
            out[side] = ((v[0], v[1]), (v[2], v[3]))
    return out


def inside_segments(p0, p1, inside, n=4001):
    """The parts of the segment p0-p1 where inside(points) holds, as rows
    (R0, Z0, R1, Z1), sampled at n points."""
    t = np.linspace(0.0, 1.0, n)
    pts = np.asarray(p0, float) + t[:, None] * (np.asarray(p1, float) -
                                                np.asarray(p0, float))
    ok = np.asarray(inside(pts), bool)
    edges = np.flatnonzero(np.diff(np.concatenate(([0], ok.astype(int),
                                                   [0]))))
    return np.array([np.concatenate((pts[a], pts[b - 1]))
                     for a, b in zip(edges[::2], edges[1::2]) if b - a > 1]
                    ).reshape(-1, 4)


_NAME = re.compile(r"([A-Za-z_]\w*(?:\([^)]*\))?)\s*=")


def namelist(path):
    """{name: [values as text]} of the variables of a Fortran namelist
    file (lower-case names, indexed ones such as enepar(1,1) with their
    index); {} without the file."""
    if path is None:
        return {}
    with open(path) as f:
        text = "\n".join(line.split("!")[0] for line in f)
    items = list(_NAME.finditer(text))
    out = {}
    for k, m in enumerate(items):
        end = items[k + 1].start() if k + 1 < len(items) else len(text)
        rhs = text[m.end():end].split("/")[0]
        out[m.group(1).lower()] = re.findall(r"'[^']*'|\"[^\"]*\"|[^\s,]+",
                                             rhs)
    return out
