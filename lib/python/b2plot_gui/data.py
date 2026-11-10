"""Data client of the GUI: raw grid, overlays and fields from b2pl.exe.

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

from ..b2plot import backend, protocol
from .model import (MovieFile, MovieVar, PsiMap, TriMesh, make_field,
                    make_geometry, make_vector)

CACHE_BYTES = 512 * 2 ** 20     # fields kept (movie frames add up)

OP = protocol.OPCODES
# overlay roles of b2plot: 1 mesh.extra, 4 structure.dat
LAYER_ROLES = {1: "vessel", 2: "separatrices", 3: "boundary",
               4: "structure", 5: "wall", 7: "trajectories"}
NAMED = {6: "chords: ", 8: "target: "}  # overlay roles sent per name


@dataclass
class Request:
    ident: int
    kind: str                   # "init", "field", "efield", "vector",
    name: str                   # "evector", "overlay"
    ops: tuple = ()
    result: object = None
    console: list = field(default_factory=list)
    paths: list = field(default_factory=list)   # files of an export
    source: tuple = None        # movie (file, first, last frame)


class Run:
    """One b2pl.exe serving the data of one run directory."""

    def __init__(self, cmd, rundir, record=None):
        self.backend = backend.Backend(cmd, rundir, record)
        self.rundir = rundir
        self.info = None
        self.catalog = []
        self.geometry = None
        self.layers = {}            # role name -> (n, 4) segments
        self.layer_colours = {}     # role name -> colour index per segment
        self.palette = {}           # colour index -> (r, g, b) of b2plot
        self.trimesh = None
        self.psimap = None
        self.movies = {}            # 1, 2 -> MovieFile
        self.cache = {}             # request key -> Field or Vector
        self.pending = []           # requests in flight, in order
        self.next_id = 0
        self.ended = set()
        self.bye = False
        self.exit_status = None
        self.console = []
        self._layer = None
        self._segments, self._colours, self._colour = [], [], 1
        self._result = None
        self._levels = None

    # ------------------------------------------------------------ control
    def start(self):
        self.backend.start()
        return self._request("init", "", "guigeom\nhelp\nguimvinf\n")

    def stop(self):
        self.backend.stop()

    def alive(self):
        return not self.bye and "exit" not in self.ended

    def _request(self, kind, name, text, ops=(), source=None):
        self.next_id += 1
        req = Request(self.next_id, kind, name, tuple(ops), source=source)
        self.pending.append(req)
        self.backend.send(text + "%d sync\n" % req.ident)
        return req

    def _lookup(self, kind, name, ops, source=None):
        key = (kind, name, tuple(ops), source)
        if key in self.cache:
            self.cache[key] = self.cache.pop(key)       # most recent
            return self.cache[key]
        for req in self.pending:
            if (req.kind, req.name, req.ops, req.source) == key:
                return req
        return None

    @staticmethod
    def _movie(name, source):
        """b2plot tokens pushing a movie variable: the mean (or with "std"
        in source the standard deviation) of frames first to last of file
        1 (b2movies.nc), 2 (eirenemovies.nc) or 3 (b2tallies.nc)."""
        cmd = "mvfrstd" if source[3:4] == ("std",) else "mvframe"
        return "'%s' %d %d %d %s" % ((name,) + tuple(source[:3]) + (cmd,))

    @classmethod
    def _push(cls, name, source, ops, eirene):
        """Tokens of a quantity with its operations, minus the reference of
        source (frames, or "final": the final state) when it has one."""
        words = [cls._head(name, source)] + list(ops)
        ref = source[4] if source and len(source) > 4 else None
        if ref is not None:
            back = None if ref == "final" else source[:1] + tuple(ref)
            words += [cls._head(name, back)] + list(ops) + [
                "em-" if eirene else "m-"]
        return words

    @classmethod
    def _head(cls, name, source):
        """Tokens pushing a label or a derived quantity ({name} operands,
        expression.py), the movie frames standing for them with source."""
        if "{" not in name:
            return cls._movie(name, source) if source else name
        return re.sub(r"\{([^}]+)\}", lambda m: cls._movie(
            m.group(1), source) if source else m.group(1), name)

    def field(self, name, eirene=False, ops=(), source=None, wall=False):
        """Cached Field, or a Request whose result arrives later.

        ops are b2plot operations applied after the label, e.g.
        ("0 -1 sumz",) for the sum over the species; source (file,
        first, last) takes the mean of movie frames instead of the
        final state; wall: a field of the wall stack (at the wall
        elements).
        """
        source = tuple(source) if source else None
        kind = "wfield" if wall else "efield" if eirene else "field"
        found = self._lookup(kind, name, ops, source)
        if found is not None:
            return found
        cmd = "guiwfld" if wall else "guiefld" if eirene else "guifield"
        text = " ".join(self._push(name, source, ops, eirene) + [cmd])
        return self._request(kind, name, text + "\n", ops, source)

    def overlay(self, layer, text):
        """Request running the b2plot commands text, whose result is the
        overlay layer they send (e.g. trajectories); never cached."""
        self.layers.pop(layer, None)
        return self._request("overlay", layer, text + "\n")

    def vector(self, first, second, eirene=False, ops=(), source=None):
        """Vector from two quantities (poloidal and radial for B2.5,
        Cartesian R and Z for EIRENE); ops apply to both."""
        source = tuple(source) if source else None
        kind = "evector" if eirene else "vector"
        name = first + " " + second
        found = self._lookup(kind, name, ops, source)
        if found is not None:
            return found
        cmd = "guievect" if eirene else "guivect"
        if source and len(source) == 3 and "{" not in first + second:
            swap = "eswap" if eirene else "swap"
            words = ("'%s' '%s' %d %d %d mvframev" % ((first, second)
                                                     + source),) \
                + tuple(ops) + (swap,) + tuple(ops) + (swap, cmd)
        else:
            words = self._push(first, source, ops, eirene) + self._push(
                second, source, ops, eirene) + [cmd]
        return self._request(kind, name, " ".join(words) + "\n", ops,
                             source)

    def _trim_cache(self):
        """Drop the least recently used fields beyond CACHE_BYTES."""
        def nbytes(d):
            return sum(a.nbytes for a in vars(d).values()
                       if isinstance(a, np.ndarray))
        total = sum(nbytes(d) for d in self.cache.values())
        while total > CACHE_BYTES and len(self.cache) > 1:
            total -= nbytes(self.cache.pop(next(iter(self.cache))))

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
        if op == OP["COLOR_REP"]:
            m = protocol.decode(op, payload)
            self.palette[m.ci] = (m.r, m.g, m.b)
            return None
        if self._layer is not None and op in (21, 40, 41):
            n = len(self._segments)
            if op == 21:
                self._colour = protocol.decode(op, payload).ci
            elif op == 40:
                self._segments.append(struct.unpack_from("=4f", payload))
            else:
                m = protocol.decode(op, payload)
                pts = np.column_stack((m.x, m.y))
                self._segments.extend(np.hstack((pts[:-1], pts[1:])))
            self._colours += [self._colour] * (len(self._segments) - n)
            return None
        if op not in (1, 2, 3, 4, 5, 70, 71, 72, 73, 74, 75, 77, 78, 79,
                      80):
            return None
        m = protocol.decode(op, payload)
        if op == OP["RUNINFO"]:
            self.info = m.fields
        elif op == OP["CATALOG"]:
            self.catalog = m.categories
        elif op == OP["GEOMETRY"]:
            self.geometry = make_geometry(m)
        elif op == OP["OVERLAY_BEGIN"]:
            name = m.fields["name"]       # m.name is the message name
            self._layer = (NAMED[m.role] + name if m.role in NAMED else
                           LAYER_ROLES.get(m.role, name))
            self._segments, self._colours, self._colour = [], [], 1
        elif op == OP["OVERLAY_END"]:
            self.layers[self._layer] = np.asarray(self._segments,
                                                  float).reshape(-1, 4)
            self.layer_colours[self._layer] = np.asarray(self._colours)
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
        elif op == OP["LEVELS"]:
            self._levels = np.asarray(m.lev, float)
        elif op == OP["MOVIEINFO"]:
            self.movies[m.file] = MovieFile(m.file, m.path,
                                            np.asarray(m.times, float))
        elif op == OP["MOVIEVAR"] and m.file in self.movies:
            self.movies[m.file].variables.append(MovieVar(
                m.file, m.var, m.long, m.units, m.location, m.ncol, m.dim))
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
        levels, self._levels = self._levels, None
        if req.kind in ("field", "efield", "wfield") and m is not None \
                and m.op == OP["FIELD"]:
            req.result = make_field(req.name, m, req.ops)
            req.result.levels = levels
            req.result.source = req.source
        elif req.kind in ("vector", "evector") and m is not None \
                and m.op == OP["VECTOR"]:
            req.result = make_vector(req.name, m, req.ops)
            req.result.source = req.source
        elif req.kind == "init":
            req.result = self.geometry
        elif req.kind == "overlay":
            req.result = self.layers.get(req.name)
        if req.result is not None and req.kind not in ("init", "overlay"):
            self.cache[(req.kind, req.name, req.ops, req.source)] = \
                req.result
            self._trim_cache()
        return req
