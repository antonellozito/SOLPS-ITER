"""Topology of the B2.5 grid of balance.nc for the balance volumes, from
balance.nc alone: flux tubes (their cells in the positive poloidal
direction of B2.5, closed or with two ends), X-points, topological regions
(core, SOL, PFR), surfaces across a region and the volume between two of
them, with the slices of its poloidal balance.

A position on a tube of n cells is the place between two of its cells:
0 to n on an open tube (0 and n its two ends), 0 to n-1 on a closed one.
Faces are 0-based here."""

from collections import deque
from dataclasses import dataclass, field

import numpy as np


def _lists(pointer, items):
    """Lists of a B2.5 pointer pair (first 1-based, count) into items."""
    return [items[a - 1:a - 1 + n] - 1 for a, n in pointer]


class Grid:
    """Grid arrays of balance.nc and the flux tubes."""

    def __init__(self, bf):
        r = bf.raw
        d = bf.dims
        self.nCv, self.nCi, self.nFc = d["nCv"], d["nCi"], d["nFc"]
        self.fc = r("fcCv").astype(int) - 1             # (nFc, 2)
        self.fv = r("fcVx").astype(int) - 1             # (nFc, 2)
        self.vx = np.column_stack((r("vxX"), r("vxY"))).astype(float)
        self.qalf = r("fcQalf")[:, 0].astype(float)
        self.fcS = r("fcS").astype(float)
        self.fcHz = r("fcHz").astype(float)
        self.fcBb = r("fcBb").astype(float)
        self.fcLbl = r("fcLbl").astype(int)
        cvft = r("cvFt").astype(int) - 1
        self.cvHx = r("cvHx").astype(float)
        self.cvHz = r("cvHz").astype(float)
        self.cvVol = r("cvVol").astype(float)
        self.cvBb = r("cvBb").astype(float)
        self.cvEb = r("cvEb").astype(float)
        self.psi = r("vxFpsi").astype(float)
        self.cell_faces = _lists(r("cvFcP").astype(int),
                                 r("cvFc").astype(int))
        self.cell_vx = _lists(r("cvVxP").astype(int), r("cvVx").astype(int))
        # the tubes of interior cells (classical grids list the target
        # guard cells too, and the radial guard rows as tubes of their own)
        tubes = [c[c < self.nCi] for c in _lists(r("ftCvP").astype(int),
                                                 r("ftCv").astype(int))]
        keep = [t for t, c in enumerate(tubes) if len(c)]
        new = np.full(len(tubes) + 1, -1)
        new[keep] = np.arange(len(keep))
        self.cvFt = new[cvft]
        self.tube_cells = [tubes[t] for t in keep]
        self.nFt = len(self.tube_cells)
        self._tubes()
        self._xpoints()
        self._regions()

    # -------------------------------------------------------------- tubes
    def out_plus(self, f, c):
        """True if the positive poloidal direction leaves cell c through
        face f (the normal of f goes from its first to its second cell)."""
        return (self.fc[f, 0] == c) == (self.qalf[f] > 0)

    def _tubes(self):
        fc, nCi = self.fc, self.nCi
        guard = (fc >= nCi).any(axis=1)
        self.guard = guard
        both = ~guard & (self.cvFt[fc[:, 0]] == self.cvFt[fc[:, 1]])
        pair = {}
        for f in np.flatnonzero(both):
            pair[(min(fc[f]), max(fc[f]))] = f
        self.radial = np.flatnonzero(~guard & (self.cvFt[fc[:, 0]] !=
                                              self.cvFt[fc[:, 1]]))
        self.pos = np.full(self.nCv, -1)
        self.closed = np.zeros(self.nFt, bool)
        self.iface, self.ends = [], []
        self.face_pos = {}                  # separating face -> (tube, pos)
        for t, cells in enumerate(self.tube_cells):
            n = len(cells)
            self.pos[cells] = np.arange(n)
            inner = [pair.get((min(a, b), max(a, b))) for a, b in
                     zip(cells[:-1], cells[1:])]
            poloidal = [(c, f) for c in cells for f in self.cell_faces[c]
                        if guard[f] and self.qalf[f] != 0]
            loop = pair.get((min(cells[0], cells[-1]),
                             max(cells[0], cells[-1]))) if n > 2 else None
            closed = not poloidal and loop is not None
            self.closed[t] = closed
            if closed:
                faces = [loop] + inner              # position k: before cell k
                ends = ([], [])
            else:
                faces = [None] + inner + [None]
                ends = ([f for c, f in poloidal if c == cells[0] and
                         not self.out_plus(f, c)],
                        [f for c, f in poloidal if c == cells[-1] and
                         self.out_plus(f, c)])
            self.iface.append(faces)
            self.ends.append(ends)
            for k, f in enumerate(faces):
                if f is not None:
                    self.face_pos[f] = (t, k)
            for k, side in ((0, ends[0]), (n, ends[1])):
                for f in side:
                    self.face_pos[f] = (t, k)
        self.sep_faces = np.array(sorted(self.face_pos), int)

    def faces_at(self, t, k):
        """Separating faces of tube t at position k."""
        n = len(self.tube_cells[t])
        if not self.closed[t] and k in (0, n):
            return list(self.ends[t][0 if k == 0 else 1])
        f = self.iface[t][k % n if self.closed[t] else k]
        return [] if f is None else [f]

    def tube_psi(self, t):
        cells = self.tube_cells[t]
        return float(np.mean(self.psi[np.concatenate(
            [self.cell_vx[c] for c in cells])]))

    # ----------------------------------------------------------- X-points
    def _xpoints(self):
        """Interior vertices touched by cells of three or more tubes."""
        on_guard = np.zeros(len(self.vx), bool)
        on_guard[self.fv[self.guard].ravel()] = True
        self.vcells = [[] for _ in range(len(self.vx))]
        for c in range(self.nCi):
            for v in self.cell_vx[c]:
                self.vcells[v].append(c)
        self.xpoints = [v for v, cs in enumerate(self.vcells)
                        if not on_guard[v] and
                        len({self.cvFt[c] for c in cs}) >= 3]

    # ------------------------------------------------------------ regions
    def _regions(self):
        """Regions: tubes of one kind (closed or open) joined by radial
        faces that do not touch an X-point (a separatrix)."""
        parent = list(range(self.nFt))

        def root(t):
            while parent[t] != t:
                parent[t] = parent[parent[t]]
                t = parent[t]
            return t
        xset = set(self.xpoints)
        self.neighbours = [set() for _ in range(self.nFt)]
        self.separatrix = set()
        for f in self.radial:
            a, b = self.cvFt[self.fc[f]]
            self.neighbours[a].add(b)
            self.neighbours[b].add(a)
            if xset & set(self.fv[f]):
                self.separatrix.add((min(a, b), max(a, b)))
        for a in range(self.nFt):
            for b in self.neighbours[a]:
                if a < b and (a, b) not in self.separatrix and \
                        self.closed[a] == self.closed[b]:
                    parent[root(a)] = root(b)
        roots = sorted({root(t) for t in range(self.nFt)},
                       key=lambda r: min(t for t in range(self.nFt)
                                         if root(t) == r))
        self.region = np.array([roots.index(root(t))
                                for t in range(self.nFt)])
        self.nreg = len(roots)
        tpsi = np.array([self.tube_psi(t) for t in range(self.nFt)])
        self.tpsi = tpsi
        mixed = [f for f in self.radial if self.closed[self.cvFt[
            self.fc[f, 0]]] != self.closed[self.cvFt[self.fc[f, 1]]]]
        self.psi_sep = float(np.mean(self.psi[self.fv[mixed]])) if mixed \
            else None
        self.core_side = np.sign(np.mean(tpsi[self.closed]) - self.psi_sep) \
            if mixed else 0.0
        self._kinds()

    def _kinds(self):
        """core (closed), PFR (at an X-point, the region opposite to the
        one nearer to the core, on the same side of its psi), else SOL;
        then the SOL regions next to each other joined: only the primary
        separatrix separates regions of the SOL, the PFRs of all X-points
        are regions of their own."""
        adj = [set() for _ in range(self.nreg)]
        for a in range(self.nFt):
            for b in self.neighbours[a]:
                if self.region[a] != self.region[b]:
                    adj[self.region[a]].add(self.region[b])
        core = {self.region[t] for t in np.flatnonzero(self.closed)}
        dist = [None] * self.nreg
        todo = deque(core)
        for r in core:
            dist[r] = 0
        while todo:
            r = todo.popleft()
            for q in adj[r]:
                if dist[q] is None:
                    dist[q] = dist[r] + 1
                    todo.append(q)
        self.kind = ["core" if r in core else "SOL" for r in range(self.nreg)]
        self.region_x = [None] * self.nreg      # X-point of a PFR
        for v in self.xpoints:
            tubes = {self.cvFt[c] for c in self.vcells[v]}
            sides = {}
            for t in tubes:
                side = np.sign(self.tpsi[t] - self.psi[v])
                sides.setdefault(side, set()).add(self.region[t])
            for regs in sides.values():
                known = [r for r in regs if dist[r] is not None]
                if len(known) < 2:
                    continue
                near = min(dist[r] for r in known)
                for r in known:
                    if dist[r] > near and self.kind[r] != "core":
                        self.kind[r] = "PFR"
                        self.region_x[r] = v
        self._join_sol()
        self._names()

    def _join_sol(self):
        parent = list(range(self.nreg))

        def root(r):
            while parent[r] != r:
                r = parent[r]
            return r
        for a in range(self.nFt):
            for b in self.neighbours[a]:
                ra, rb = self.region[a], self.region[b]
                if self.kind[ra] == self.kind[rb] == "SOL" and \
                        root(ra) != root(rb):
                    parent[root(ra)] = root(rb)
        roots = sorted({root(r) for r in range(self.nreg)})
        new = np.array([roots.index(root(r)) for r in range(self.nreg)])
        kind, xpt = [None] * len(roots), [None] * len(roots)
        for r in range(self.nreg):
            kind[new[r]] = self.kind[r]
            xpt[new[r]] = xpt[new[r]] if xpt[new[r]] is not None else \
                self.region_x[r]
        self.region, self.nreg = new[self.region], len(roots)
        self.kind, self.region_x = kind, xpt

    def _names(self):
        """Readable names of the regions."""
        core = np.flatnonzero(self.closed)
        cells = np.concatenate([self.tube_cells[t] for t in core]) if \
            len(core) else np.arange(self.nCi)
        centre = self.vx[np.concatenate([self.cell_vx[c] for c in cells])
                         ].mean(axis=0)
        self.names = list(self.kind)
        for kind in ("SOL", "PFR"):
            regs = [r for r in range(self.nreg) if self.kind[r] == kind]
            if len(regs) < 2:
                continue
            for r in regs:
                tubes = np.flatnonzero(self.region == r)
                c = self.vx[np.concatenate(
                    [self.cell_vx[k] for t in tubes
                     for k in self.tube_cells[t]])].mean(axis=0)
                if kind == "SOL":
                    self.names[r] = "SOL, %s-field side" % (
                        "low" if c[0] > centre[0] else "high")
                else:
                    self.names[r] = "PFR, %s" % ("lower" if c[1] < centre[1]
                                                 else "upper")
                    v = self.region_x[r]
                    if v is not None and self._secondary(v, centre):
                        self.names[r] += ", secondary X-point"
        for name in set(self.names):
            same = [r for r in range(self.nreg) if self.names[r] == name]
            if len(same) > 1:
                for i, r in enumerate(same):
                    self.names[r] = "%s %d" % (name, i + 1)

    def _secondary(self, v, centre):
        """True if X-point v is not the one of its side (lower or upper)
        nearest to the core in psi."""
        if self.psi_sep is None:
            return False
        lower = self.vx[v, 1] < centre[1]
        side = [x for x in self.xpoints if (self.vx[x, 1] < centre[1]) ==
                lower]
        first = min(side, key=lambda x: abs(self.psi[x] - self.psi_sep))
        return v != first

    # ----------------------------------------------------------- geometry
    def segment(self, f):
        return self.vx[self.fv[f]]

    def distance(self, p, faces):
        """Distances of point p to the faces (segments)."""
        a, b = self.vx[self.fv[faces, 0]], self.vx[self.fv[faces, 1]]
        ab = b - a
        t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1),
                                                       1e-300), 0.0, 1.0)
        return np.hypot(*(a + t[:, None] * ab - p).T)


@dataclass
class Surface:
    """A surface across a region: per tube one separating face, ordered
    across the tubes; segments oriented along that order."""
    region: int
    tubes: list
    pos: dict                       # tube -> position
    face: dict                      # tube -> face drawn
    segments: dict                  # tube -> (2, 2) along the order

    def polyline(self):
        return [self.segments[t] for t in self.tubes]


def surface(grid, f0, region=None):
    """The surface through separating face f0, across the tubes of its
    region (or of region), walking from tube to tube at the far vertex of
    each face (the nearest face of the next tube where the grid is not
    conformal)."""
    t0, k0 = grid.face_pos[f0]
    region = grid.region[t0] if region is None else region
    if grid.region[t0] != region:
        return None
    pos, face = {t0: k0}, {t0: f0}
    chains = []
    for v0 in grid.fv[f0]:
        chain, t_cur, v = [], t0, v0
        while True:
            cand = [c for c in grid.vcells[v]
                    if grid.cvFt[c] != t_cur and grid.cvFt[c] not in pos and
                    grid.region[grid.cvFt[c]] == region]
            if not cand:
                break
            tubes = sorted({grid.cvFt[c] for c in cand},
                           key=lambda t: t not in grid.neighbours[t_cur])
            t = tubes[0]
            faces = sorted({f for c in cand if grid.cvFt[c] == t
                            for f in grid.cell_faces[c]
                            if f in grid.face_pos})
            if not faces:
                break
            with_v = [f for f in faces if v in grid.fv[f]]
            if with_v:
                f = with_v[0]
                nxt = grid.fv[f, 1] if grid.fv[f, 0] == v else grid.fv[f, 0]
            else:
                f = faces[int(np.argmin(grid.distance(grid.vx[v],
                                                      np.array(faces))))]
                d = np.hypot(*(grid.vx[grid.fv[f]] - grid.vx[v]).T)
                nxt = grid.fv[f, int(np.argmax(d))]
            near = grid.fv[f, 0] if nxt == grid.fv[f, 1] else grid.fv[f, 1]
            pos[t], face[t] = grid.face_pos[f][1], f
            chain.append((t, near, nxt))
            t_cur, v = t, nxt
        chains.append(chain)
    order = [t for t, _, _ in reversed(chains[0])] + [t0] + \
        [t for t, _, _ in chains[1]]
    seg = {t0: grid.vx[grid.fv[f0]]}
    for t, near, far in chains[0]:
        seg[t] = grid.vx[[far, near]]
    for t, near, far in chains[1]:
        seg[t] = grid.vx[[near, far]]
    return Surface(region, order, pos, face, seg)


@dataclass
class Volume:
    """The cells between an upstream and a downstream surface: per tube
    of the upstream surface, its cells in the downstream direction (sign
    of the positive poloidal direction: direction), its upstream faces and
    its downstream faces (the downstream surface, or the end of the tube,
    and the walls the cells touch)."""
    region: int
    direction: int
    tubes: list
    cells: list                     # per tube, in the downstream order
    up: list                        # per tube, faces
    down: list                      # per tube, faces
    reached: list                   # per tube, True at the downstream surface
    up_pos: list
    down_pos: list
    walls: np.ndarray = None        # wall faces of the cells
    cell: np.ndarray = None         # all cells
    cell_tube: np.ndarray = None    # index in tubes of each cell
    ref: int = 0                    # index of the tube along the separatrix
    slices: list = field(default_factory=list)

    @property
    def reverse(self):
        return self.direction < 0


def _arc(grid, t, a, b, step):
    """Cells of closed tube t from position a to position b going step."""
    n = len(grid.tube_cells[t])
    count = ((b - a) * step) % n
    first = a if step > 0 else a - 1
    return [(first + step * i) % n for i in range(count)]


def span_tubes(up, span):
    """The tubes of surface up from one tube of span (two tubes) to the
    other, in the order of the surface; all of them without span."""
    if span is None or span[0] not in up.pos or span[1] not in up.pos:
        return list(up.tubes)
    i, j = sorted(up.tubes.index(t) for t in span)
    return list(up.tubes[i:j + 1])


def volume(grid, up, down, span=None):
    """The volume between surfaces up and down (same region), across the
    tubes of span (two tubes of up: from one to the other; None: all), or
    a text saying why there is none."""
    if up.region != down.region:
        return "The two surfaces are in different regions"
    common = [t for t in up.tubes if t in down.pos]
    if not common:
        return "The downstream surface crosses none of the flux tubes of " \
            "the upstream one"
    closed = grid.closed[up.tubes[0]]
    if closed:
        t = min(common, key=lambda t: abs(grid.tpsi[t] - grid.psi_sep)
                if grid.psi_sep is not None else 0)
        length = {s: grid.cvHx[grid.tube_cells[t][_arc(
            grid, t, up.pos[t], down.pos[t], s)]].sum() for s in (1, -1)}
        step = 1 if length[1] <= length[-1] else -1
    else:
        votes = sum(np.sign(down.pos[t] - up.pos[t]) for t in common)
        step = 1 if votes >= 0 else -1
    tubes, cells, ups, downs, walls, reached, upos, dpos = \
        [], [], [], [], [], [], [], []
    reach = []                      # tubes at the downstream surface
    for t in span_tubes(up, span):
        n = len(grid.tube_cells[t])
        pu = up.pos[t]
        if closed:
            if t not in down.pos:
                continue
            pd, hit = down.pos[t], True
            idx = _arc(grid, t, pu, pd, step)
        else:
            hit = t in down.pos and (down.pos[t] - pu) * step > 0
            pd = down.pos[t] if hit else (n if step > 0 else 0)
            idx = list(range(pu, pd)) if step > 0 else \
                list(range(pu - 1, pd - 1, -1))
        if not idx:
            continue
        if closed or hit:
            reach.append(len(tubes))
        cs = grid.tube_cells[t][idx]
        uf, df = grid.faces_at(t, pu), grid.faces_at(t, pd)
        wall = sorted({f for c in cs for f in grid.cell_faces[c]
                       if grid.guard[f] and grid.qalf[f] != 0} -
                      set(uf) - set(df))
        tubes.append(t)
        cells.append(cs)
        ups.append(uf)
        downs.append(df + wall)
        walls.append(wall)
        reached.append(hit)
        upos.append(pu)
        dpos.append(pd)
    keep = _ending_on_walls(grid, cells, reach)
    tubes, cells, ups, downs, walls, reached, upos, dpos = (
        [a[i] for i in keep] for a in (tubes, cells, ups, downs, walls,
                                       reached, upos, dpos))
    if not tubes:
        return "The volume between the two surfaces has no cells"
    vol = Volume(up.region, step, tubes, cells, ups, downs, reached, upos,
                 dpos)
    vol.walls = np.array([f for w in walls for f in w], int)
    _finish(grid, vol)
    return vol


def sides(grid, vol, up):
    """Faces of the sides of the volume: the faces between its cells and
    the cells out of it, but the upstream, downstream and wall faces;
    (first, last, other): the side towards the beginning of the order of
    surface up, towards its end (where the region or the grid ends: the
    side of the nearer end tube), faces of neither (towards tubes of the
    volume, at its upstream and downstream ends)."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    ends = {f for fs in vol.up + vol.down for f in fs}
    order = {t: i for i, t in enumerate(up.tubes)}
    lo, hi = order[vol.tubes[0]], order[vol.tubes[-1]]
    if lo > hi:
        lo, hi = hi, lo
    first, last, other = [], [], []
    for i, cs in enumerate(vol.cells):
        k = order[vol.tubes[i]]
        for c in cs:
            for f in grid.cell_faces[c]:
                a, b = grid.fc[f]
                o = b if a == c else a
                if f in ends or member[o]:
                    continue
                t = -1 if grid.guard[f] else grid.cvFt[o]
                if t in order:
                    side = first if order[t] < lo else last if \
                        order[t] > hi else other
                else:                   # the region or the grid ends:
                    side = first if k - lo <= hi - k else last  # nearer end
                side.append(f)
    return first, last, other


def corner(grid, vol, up, which):
    """Point where the upstream and downstream faces of the end tube of
    side which ("first" or "last", as sides) meet: the vertex they share
    (the one farthest from the other end tube), else the middle of their
    nearest vertices; for a side without faces."""
    order = {t: i for i, t in enumerate(up.tubes)}
    ends = sorted(range(len(vol.tubes)), key=lambda i: order[vol.tubes[i]])
    i, j = (ends[0], ends[-1]) if which == "first" else (ends[-1], ends[0])
    uv = {int(v) for f in vol.up[i] for v in grid.fv[f]}
    dv = {int(v) for f in vol.down[i] for v in grid.fv[f]}
    if not uv or not dv:
        return None
    common = uv & dv
    if common:
        far = grid.vx[grid.fv[np.array(vol.up[j], int)]].reshape(-1, 2) \
            .mean(axis=0)
        v = max(common, key=lambda v: np.hypot(*(grid.vx[v] - far)))
        return tuple(grid.vx[v])
    a = grid.vx[sorted(uv)]
    b = grid.vx[sorted(dv)]
    d = np.hypot(a[:, None, 0] - b[None, :, 0], a[:, None, 1] - b[None, :, 1])
    k, m = np.unravel_index(np.argmin(d), d.shape)
    return tuple(0.5 * (a[k] + b[m]))


def _ending_on_walls(grid, cells, reach):
    """Indices of the tubes in the volume: those at the downstream surface
    and, joined one by one, those that end on a wall in between (the last
    cell next to a cell of the volume); a tube that goes on past the
    downstream surface elsewhere is left out."""
    keep = set(reach)
    inside = np.zeros(grid.nCv, bool)
    for i in keep:
        inside[cells[i]] = True
    added = True
    while added:
        added = False
        for i in range(len(cells)):
            if i in keep:
                continue
            last = cells[i][-1]
            near = [c for f in grid.cell_faces[last] for c in grid.fc[f]
                    if c != last and c < grid.nCi]
            if any(inside[c] for c in near):
                keep.add(i)
                inside[cells[i]] = True
                added = True
    return sorted(keep)


def _finish(grid, vol):
    """Cell lists, the reference tube and the slices."""
    vol.cell = np.concatenate(vol.cells)
    vol.cell_tube = np.concatenate([np.full(len(c), i)
                                    for i, c in enumerate(vol.cells)])
    if grid.psi_sep is not None:
        vol.ref = int(np.argmin([abs(grid.tpsi[t] - grid.psi_sep)
                                 for t in vol.tubes]))
    vol.slices = slices(grid, vol)


def slices(grid, vol):
    """Number of cells of each tube in the first k slices, k = 0 to m (m
    cells of the reference tube): the surfaces through the faces between
    the cells of the reference tube cut the other tubes; monotone, all
    cells in the last."""
    t_ref = vol.tubes[vol.ref]
    cs_ref = vol.cells[vol.ref]
    m = len(cs_ref)
    counts = np.zeros((m + 1, len(vol.tubes)), int)
    step = vol.direction
    for k in range(1, m):
        a, b = cs_ref[k - 1], cs_ref[k]
        p = grid.pos[b] if step > 0 else grid.pos[a]
        f = grid.faces_at(t_ref, p)
        s = surface(grid, f[0], vol.region) if f else None
        for i, t in enumerate(vol.tubes):
            n_t = len(vol.cells[i])
            c = counts[k - 1, i]
            if s is not None and t in s.pos:
                n = len(grid.tube_cells[t])
                off = (s.pos[t] - vol.up_pos[i]) * step
                if grid.closed[t]:
                    off %= n
                    if off > n_t + (n - n_t) // 2:
                        off = 0
                c = max(c, min(max(off, 0), n_t))
            counts[k, i] = c
    counts[m] = [len(c) for c in vol.cells]
    return counts


# --------------------------------------------------------- coordinates
def dssep(grid, up, vol):
    """Distance (m) along the upstream surface from the separatrix to the
    middle of the face of each tube of the volume: positive in the SOL,
    negative in the core and the PFR."""
    order = up.tubes
    length, total, last = {}, 0.0, None
    for t in order:
        a, b = up.segments[t]
        if last is not None:
            total += float(np.hypot(*(a - last)))
        length[t] = total + 0.5 * float(np.hypot(*(b - a)))
        total += float(np.hypot(*(b - a)))
        last = b
    if grid.psi_sep is not None and len(order) > 1 and \
            abs(grid.tpsi[order[-1]] - grid.psi_sep) < \
            abs(grid.tpsi[order[0]] - grid.psi_sep):
        length = {t: total - v for t, v in length.items()}
    sign = 1.0 if grid.kind[up.region] == "SOL" else -1.0
    return np.array([sign * length[t] for t in vol.tubes])


def rhop(grid, up, vol, psin):
    """rho poloidal of each tube of the volume: square root of the
    normalised psi (psin(r, z)) at the ends of its upstream face."""
    out = []
    for t in vol.tubes:
        p = psin(*grid.vx[grid.fv[up.face[t]]].T)
        v = np.nanmean(p) if np.isfinite(p).any() else np.nan
        out.append(np.sqrt(v) if v >= 0 else np.nan)
    return np.array(out)
