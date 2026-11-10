"""What the GUI keeps of the b2plot data messages: grid, EIRENE mesh,
psi map, movie files, fields and vectors, built from the decoded
messages (b2plot.protocol)."""

import re
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Geometry:
    """B2.5 grid as plotted by b2plot (cells with a region number)."""
    vx: np.ndarray              # (nVx, 2) vertex coordinates
    psin: np.ndarray            # normalised psi at the vertices or None
    cells: np.ndarray           # (ncell,) cell numbers iCv, 1-based
    polygons: list              # ncell arrays (nv, 2)
    centres: np.ndarray         # (ncell, 2)
    region: np.ndarray
    ix: np.ndarray              # classical grid indices or -1
    iy: np.ndarray
    xpoints: np.ndarray         # (nxpt, 2)
    classical: bool
    triangles: np.ndarray       # (ntri, 3) fan triangles of the cells
    tri_cell: np.ndarray        # (ntri,) row of the cell of each triangle
    visible: np.ndarray = None  # cells with an area (not degenerate guards)
    corners: list = None        # ncell arrays of vertex rows (0-based)

    @property
    def bbox(self):
        lo, hi = self.vx[self.used].min(axis=0), self.vx[self.used].max(axis=0)
        return float(lo[0]), float(hi[0]), float(lo[1]), float(hi[1])

    @property
    def used(self):
        return np.unique(self.triangles)


@dataclass
class PsiMap:
    """Normalised poloidal flux on the box of rzpsi.dat (from b2plot)."""
    r: np.ndarray
    z: np.ndarray
    psin: np.ndarray            # (nz, nr)
    opoint: tuple
    spoint: tuple               # point that defines psiN = 1


@dataclass
class TriMesh:
    """EIRENE triangles (0-based node numbers)."""
    x: np.ndarray
    y: np.ndarray
    triangles: np.ndarray


@dataclass
class MovieVar:
    """One variable of a movie file (MOVIEVAR); location 1 cells, 2 faces
    (sent at the cells), 3 EIRENE tally cells (sent at the triangles)."""
    file: int
    name: str
    long: str
    units: str
    location: int
    ncol: int
    dim: str


@dataclass
class MovieFile:
    """b2movies.nc (file 1) or eirenemovies.nc (file 2) as b2plot found
    it: frame times and usable variables."""
    file: int
    path: str
    times: np.ndarray
    variables: list = field(default_factory=list)

    @property
    def nt(self):
        return len(self.times)


@dataclass
class Field:
    """One b2plot quantity, all species columns."""
    name: str
    label: str
    location: str               # "cells", "triangles" or "wall"
    columns: list
    values: np.ndarray          # (ncol, n)
    vertex: np.ndarray = None   # (ncol, nVx) for cell fields
    ops: tuple = ()             # b2plot operations after the label
    levels: np.ndarray = None   # contour levels b2plot set (clvp, eclvp)
    source: tuple = None        # movie (file, first, last frame)

    @property
    def title(self):
        return split_unit(self.label)[0]

    @property
    def unit(self):
        return split_unit(self.label)[1]


@dataclass
class Vector:
    """(R, Z) vector from two b2plot quantities (poloidal and radial, or
    EIRENE Cartesian R and Z)."""
    name: str
    label: str
    columns: list
    vr: np.ndarray              # (ncol, n) at cell centres or triangles
    vz: np.ndarray
    vxr: np.ndarray = None      # (ncol, nVx) at the vertices (cells only)
    vxz: np.ndarray = None
    location: str = "cells"     # "cells" or "triangles"
    ops: tuple = ()
    source: tuple = None        # movie (file, first, last frame)

    @property
    def unit(self):
        return split_unit(self.label)[1]


def split_unit(label):
    """'Electron density (m^{-3})' -> ('Electron density', 'm^{-3}')."""
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", label.strip())
    return (m.group(1), m.group(2)) if m else (label.strip(), "")


def fan_triangles(nv):
    """Fan triangulation of polygons with nv vertices each."""
    nv = np.asarray(nv)
    starts = np.concatenate(([0], np.cumsum(nv)[:-1]))
    ntri = np.maximum(nv - 2, 0)
    cell = np.repeat(np.arange(len(nv)), ntri)
    first = np.repeat(starts, ntri)
    k = np.arange(ntri.sum()) - np.repeat(np.cumsum(ntri) - ntri, ntri)
    return np.column_stack((first, first + k + 1, first + k + 2)), cell


def make_geometry(m):
    vx = np.column_stack((m.vxX, m.vxY)).astype(float)
    vlist = np.asarray(m.vlist) - 1
    pos, cell = fan_triangles(m.nv)
    offsets = np.cumsum(m.nv)[:-1]
    polygons = np.split(vx[vlist], offsets)
    span = np.ptp(vx, axis=0).max() if len(vx) else 1.0
    area = np.array([0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1))
                               - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
                     for p in polygons])
    visible = (np.asarray(m.nv) >= 3) & (area > 1e-12 * span ** 2)
    return Geometry(
        vx=vx, psin=np.asarray(m.psin, float) if m.haspsi else None,
        cells=np.asarray(m.cells), polygons=polygons,
        centres=np.column_stack((m.cx, m.cy)).astype(float),
        region=np.asarray(m.reg), ix=np.asarray(m.ix), iy=np.asarray(m.iy),
        xpoints=np.asarray(m.xpt, float).reshape(-1, 2),
        classical=bool(m.isClassicalGrid), triangles=vlist[pos],
        tri_cell=cell, visible=visible, corners=np.split(vlist, offsets))


LOCATIONS = {1: "cells", 2: "triangles", 3: "wall"}


def make_field(name, m, ops=()):
    ncol, n = m.ncol, m.n
    vertex = (np.asarray(m.vertex).reshape(ncol, m.nvx) if m.nvx else None)
    return Field(name=name, label=m.label, columns=list(m.columns),
                 location=LOCATIONS.get(m.location, "triangles"),
                 values=np.asarray(m.values).reshape(ncol, n),
                 vertex=vertex, ops=tuple(ops))


def vector_label(label):
    """Label of a vector from the label of its first component."""
    label = re.sub(r"(?i)\bpoloidal\s+", "", label, count=1)
    label = re.sub(r"(?i)\bcartesian\s+x-", "", label, count=1)
    return label[:1].upper() + label[1:]


def make_vector(name, m, ops=()):
    ncol, n, nvx = m.ncol, m.n, m.nvx
    vxr = np.asarray(m.vxr).reshape(ncol, nvx) if nvx else None
    vxz = np.asarray(m.vxz).reshape(ncol, nvx) if nvx else None
    return Vector(name=name, label=vector_label(m.label),
                  columns=list(m.columns),
                  vr=np.asarray(m.vr).reshape(ncol, n),
                  vz=np.asarray(m.vz).reshape(ncol, n), vxr=vxr, vxz=vxz,
                  location="cells" if m.location == 1 else "triangles",
                  ops=tuple(ops))
