"""Data client of the GUI: raw grid, overlays and fields from b2pl_gui.exe.

The GUI sends only the data commands of b2plot (guigeom, guifield,
guiefld, guivect, each request ended by "<id> sync") and receives raw
arrays. Reading the run and computing the quantities stay in Fortran;
this module only decodes and caches what b2plot sends.
"""

import queue
import re
import struct
from dataclasses import dataclass, field

import numpy as np

from . import backend, protocol

OP = protocol.OPCODES
LAYER_ROLES = {1: "structure", 2: "separatrices", 3: "boundary",
               4: "device"}


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
class Field:
    """One b2plot quantity, all species columns."""
    name: str
    label: str
    location: str               # "cells" or "triangles"
    columns: list
    values: np.ndarray          # (ncol, n)
    vertex: np.ndarray = None   # (ncol, nVx) for cell fields
    ops: tuple = ()             # b2plot operations after the label

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

    @property
    def unit(self):
        return split_unit(self.label)[1]


@dataclass
class Request:
    ident: int
    kind: str                   # "init", "field", "efield", "vector",
    name: str                   # "evector"
    ops: tuple = ()
    result: object = None
    console: list = field(default_factory=list)


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
        tri_cell=cell, visible=visible)


def make_field(name, m, ops=()):
    ncol, n = m.ncol, m.n
    vertex = (np.asarray(m.vertex).reshape(ncol, m.nvx) if m.nvx else None)
    return Field(name=name, label=m.label, columns=list(m.columns),
                 location="cells" if m.location == 1 else "triangles",
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


class Run:
    """One b2pl_gui.exe serving the data of one run directory."""

    def __init__(self, cmd, rundir, record=None):
        self.backend = backend.Backend(cmd, rundir, record)
        self.rundir = rundir
        self.info = None
        self.catalog = []
        self.geometry = None
        self.layers = {}            # role name -> (n, 4) segments
        self.trimesh = None
        self.psimap = None
        self.cache = {}             # (kind, name) -> Field or Vector
        self.pending = []           # requests in flight, in order
        self.next_id = 0
        self.ended = set()
        self.bye = False
        self.exit_status = None
        self.console = []
        self._layer = None
        self._segments = []
        self._result = None

    # ------------------------------------------------------------ control
    def start(self):
        self.backend.start()
        return self._request("init", "", "guigeom\nhelp\n")

    def stop(self):
        self.backend.stop()

    def alive(self):
        return not self.bye and "exit" not in self.ended

    def _request(self, kind, name, text, ops=()):
        self.next_id += 1
        req = Request(self.next_id, kind, name, tuple(ops))
        self.pending.append(req)
        self.backend.send(text + "%d sync\n" % req.ident)
        return req

    def _lookup(self, kind, name, ops):
        key = (kind, name, tuple(ops))
        if key in self.cache:
            return self.cache[key]
        for req in self.pending:
            if (req.kind, req.name, req.ops) == key:
                return req
        return None

    def field(self, name, eirene=False, ops=()):
        """Cached Field, or a Request whose result arrives later.

        ops are b2plot operations applied after the label, e.g.
        ("0 -1 sumz",) for the sum over the species.
        """
        kind = "efield" if eirene else "field"
        found = self._lookup(kind, name, ops)
        if found is not None:
            return found
        cmd = "guiefld" if eirene else "guifield"
        text = " ".join((name,) + tuple(ops) + (cmd,))
        return self._request(kind, name, text + "\n", ops)

    def vector(self, first, second, eirene=False, ops=()):
        """Vector from two quantities (poloidal and radial for B2.5,
        Cartesian R and Z for EIRENE); ops apply to both."""
        kind = "evector" if eirene else "vector"
        name = first + " " + second
        found = self._lookup(kind, name, ops)
        if found is not None:
            return found
        cmd = "guievect" if eirene else "guivect"
        text = " ".join((first,) + tuple(ops) + (second,) + tuple(ops)
                        + (cmd,))
        return self._request(kind, name, text + "\n", ops)

    # ------------------------------------------------------------- events
    def poll(self, budget=None):
        """Decode the waiting events; return the requests completed."""
        import time
        done = []
        t0 = time.monotonic()
        while budget is None or time.monotonic() - t0 < budget:
            try:
                event = self.backend.events.get_nowait()
            except queue.Empty:
                break
            kind = event[0]
            if kind == "message":
                req = self._message(event[1], event[2])
                if req is not None:
                    done.append(req)
            elif kind == "console":
                self.console.append(event[1])
                if self.pending:
                    self.pending[0].console.append(event[1])
            elif kind == "error":
                self.console.append("protocol error: %s\n" % event[1])
            else:
                self.ended.add(kind)
                if kind == "exit":
                    self.exit_status = event[1]
        del self.console[:-200]
        return done

    def _message(self, op, payload):
        if self._layer is not None and op in (40, 41):
            if op == 40:
                self._segments.append(struct.unpack_from("=4f", payload))
            else:
                m = protocol.decode(op, payload)
                pts = np.column_stack((m.x, m.y))
                self._segments.extend(np.hstack((pts[:-1], pts[1:])))
            return None
        if op not in (1, 2, 3, 4, 5, 70, 71, 72, 73, 74, 75, 77):
            return None
        m = protocol.decode(op, payload)
        if op == OP["RUNINFO"]:
            self.info = m.fields
        elif op == OP["CATALOG"]:
            self.catalog = m.categories
        elif op == OP["GEOMETRY"]:
            self.geometry = make_geometry(m)
        elif op == OP["OVERLAY_BEGIN"]:
            self._layer = LAYER_ROLES.get(m.role, m.name)
            self._segments = []
        elif op == OP["OVERLAY_END"]:
            self.layers[self._layer] = np.asarray(self._segments,
                                                  float).reshape(-1, 4)
            self._layer = None
        elif op == OP["TRIMESH"]:
            self.trimesh = TriMesh(np.asarray(m.x, float),
                                   np.asarray(m.y, float),
                                   np.asarray(m.tri).reshape(-1, 3) - 1)
        elif op == OP["PSIMAP"]:
            psin = np.asarray(m.psin, float).reshape(m.nz, m.nr)
            self.psimap = PsiMap(np.asarray(m.r, float),
                                 np.asarray(m.z, float), psin,
                                 (m.ro, m.zo), (m.rs, m.zs))
        elif op in (OP["FIELD"], OP["VECTOR"]):
            self._result = m
        elif op == OP["BYE"]:
            self.bye = True
        elif op == OP["SYNC"]:
            return self._synced(m.id)
        return None

    def _synced(self, ident):
        if not self.pending or self.pending[0].ident != ident:
            return None
        req = self.pending.pop(0)
        m, self._result = self._result, None
        if req.kind in ("field", "efield") and m is not None \
                and m.op == OP["FIELD"]:
            req.result = make_field(req.name, m, req.ops)
        elif req.kind in ("vector", "evector") and m is not None \
                and m.op == OP["VECTOR"]:
            req.result = make_vector(req.name, m, req.ops)
        elif req.kind == "init":
            req.result = self.geometry
        if req.result is not None and req.kind != "init":
            self.cache[(req.kind, req.name, req.ops)] = req.result
        return req
