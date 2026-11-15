"""Geometry of the radial balance (across the flux surfaces): the flux
surfaces picked as its inner and outer surface, the flux tubes between
them, the volume over their whole poloidal extent (a closed region: a
whole turn from a cut at the primary X-point) or between a start and an
end surface, its inner and outer faces, the parts of its balance (the
slices from end to end, the flux tubes cut) and the radial coordinate of
its tubes."""

from dataclasses import dataclass

import numpy as np

from .topology import Cuts, Ends, Volume, cell_slices, finish, surface
from . import topology


def rank(grid, t):
    """Radial position of tube t, growing from the inner to the outer
    side of its region: psi from the separatrix outwards in the core and
    the SOL, the opposite in a PFR (whose inner side is the separatrix)."""
    s = grid.tpsi[t] - (grid.psi_sep if grid.psi_sep is not None else 0.0)
    s *= -grid.core_side if grid.core_side else 1.0
    return -s if grid.kind[grid.region[t]] == "PFR" else s


def _raw(grid, t):
    return rank(grid, t) * (-1 if grid.kind[grid.region[t]] == "PFR" else 1)


def ends(grid, t):
    """The end faces of open tube t (none for a closed one)."""
    if grid.closed[t]:
        return set()
    return set(grid.faces_at(t, 0)) | set(grid.faces_at(
        t, len(grid.tube_cells[t])))


def candidates(grid):
    """Faces a flux surface can be picked at: between two flux tubes, or
    on the boundary of the grid but at the ends of the tubes."""
    end = set()
    for t in range(grid.nFt):
        end |= ends(grid, t)
    edge = [f for f in np.flatnonzero(grid.guard) if f not in end]
    return np.unique(np.concatenate((grid.radial, np.array(edge, int))))


def side_of(grid, t, f, o):
    """"inner" or "outer": the side of tube t that its face f (to cell o,
    not of t) is on, the faces on the boundary of the grid too; None for
    an end face of the tube."""
    if f in ends(grid, t):
        return None
    u = -1 if grid.guard[f] else grid.cvFt[o]
    if u >= 0:
        low = _raw(grid, u) < _raw(grid, t)
    else:                                   # the grid ends: the side with
        lower = [_raw(grid, n) < _raw(grid, t)  # no neighbouring tubes
                 for n in grid.neighbours[t]]
        low = not any(lower) if lower else True
    pfr = grid.kind[grid.region[t]] == "PFR"
    return "inner" if low != pfr else "outer"


def tube_side(grid, t, which):
    """Faces of tube t on its side which ("inner" or "outer")."""
    out = []
    for c in grid.tube_cells[t]:
        for f in grid.cell_faces[c]:
            a, b = grid.fc[f]
            o = b if a == c else a
            if grid.cvFt[o] == t and not grid.guard[f]:
                continue
            if side_of(grid, t, f, o) == which:
                out.append(int(f))
    return out


@dataclass
class FluxSurface:
    """A flux surface picked: the inner (or outer) side of a tube."""
    region: int
    tube: int
    which: str                      # "inner" or "outer"
    faces: list


def pick(grid, p, which, faces, centres, region=None):
    """The flux surface nearest to point p among faces (radial faces):
    the side which of the tube of the cell on the side of p; region: of
    that tube only. None if there is none."""
    if not len(faces):
        return None
    f = int(faces[np.argmin(grid.distance(np.asarray(p), faces))])
    cells = sorted(grid.fc[f], key=lambda c: np.hypot(*(centres[c] - p)))
    for c in cells:
        t = grid.cvFt[c]
        if c >= grid.nCi or t < 0 or (region is not None and
                                      grid.region[t] != region):
            continue
        o = grid.fc[f, 1] if grid.fc[f, 0] == c else grid.fc[f, 0]
        if side_of(grid, t, f, o) == which:
            return FluxSurface(grid.region[t], int(t), which,
                               tube_side(grid, t, which))
    return None


def path(grid, first, last):
    """Tubes from first to last, outwards through neighbouring tubes of
    their region; None if last is not outwards of first."""
    if first == last:
        return [first]
    region, prev, todo = grid.region[first], {first: None}, [first]
    while todo:
        nxt = []
        for t in todo:
            for u in sorted(grid.neighbours[t]):
                if u in prev or grid.region[u] != region or \
                        rank(grid, u) <= rank(grid, t):
                    continue
                prev[u] = t
                if u == last:
                    out = [u]
                    while prev[out[-1]] is not None:
                        out.append(prev[out[-1]])
                    return out[::-1]
                nxt.append(u)
        todo = nxt
    return None


def cut(grid, region):
    """Surface across the closed region at the primary X-point (the one
    touching the region; the lowest of them), or where the open tubes end
    nearest to it (limiter)."""
    tubes = [t for t in range(grid.nFt) if grid.region[t] == region]
    cells = {c for t in tubes for c in grid.tube_cells[t]}
    xs = [v for v in grid.xpoints if cells & set(grid.vcells[v])]
    if xs:
        p = grid.vx[min(xs, key=lambda v: grid.vx[v][1])]
    else:
        ends = [f for f in np.flatnonzero(grid.guard & (grid.qalf != 0))
                if not grid.closed[grid.cvFt[grid.fc[f, 0]]] or
                not grid.closed[grid.cvFt[grid.fc[f, 1]]]]
        verts = grid.vx[np.unique(grid.fv[ends])] if ends else grid.vx
        own = grid.vx[np.unique([v for c in cells for v in grid.cell_vx[c]])]
        d = np.hypot(verts[:, None, 0] - own[None, :, 0],
                     verts[:, None, 1] - own[None, :, 1]).min(axis=1)
        p = verts[int(np.argmin(d))]
    faces = np.array([f for f in grid.sep_faces
                      if grid.region[grid.face_pos[f][0]] == region], int)
    f = int(faces[np.argmin(grid.distance(p, faces))])
    return surface(grid, f, region)


def volume(grid, tubes, start=None, end=None, turn=None):
    """The volume of the radial balance over tubes (inner to outer): per
    tube its cells from start to end (Surfaces; a tube one of them does
    not cross: from or to its own end) in the positive poloidal direction;
    closed tubes from start (or turn, the cut) to end (or turn): a whole
    turn if they meet. A text if it has no cells."""
    out = ([], [], [], [], [], [], [])
    for t in tubes:
        n = len(grid.tube_cells[t])
        if grid.closed[t]:
            a = (start or turn).pos.get(t, 0) if (start or turn) else 0
            b = (end or turn).pos.get(t, a) if (end or turn) else a
            k = (b - a) % n or n
            idx = [(a + i) % n for i in range(k)]
            a, b = a % n, b % n
        else:                           # between the two, either order
            a = start.pos.get(t, 0) if start is not None else 0
            b = end.pos.get(t, n) if end is not None else n
            a, b = min(a, b), max(a, b)
            idx = list(range(a, b))
        if not idx:
            continue
        cs = grid.tube_cells[t][idx]
        uf, df = grid.faces_at(t, a), grid.faces_at(t, b)
        wall = []                       # boundary faces: inner or outer
        for lst, v in zip(out, (t, cs, uf, df + wall, wall, a, b)):
            lst.append(v)
    tubes, cells, ups, downs, walls, upos, dpos = out
    if not tubes:
        return "The volume between the surfaces has no cells"
    vol = Volume(grid.region[tubes[0]], 1, tubes, cells, ups, downs,
                 [True] * len(tubes), upos, dpos)
    vol.kind = "radial"
    vol.walls = np.array([f for w in walls for f in w], int)
    finish(grid, vol)
    vol.sides = sides(grid, vol)
    vol.ends, vol.cuts = layout(grid, vol)
    return vol


def sides(grid, vol):
    """(inner, outer, other) faces of the volume: from its cells to cells
    out of it on the inner or outer side of their tube; other: to cells
    of its own tubes out of it (its ends), not the start and end faces."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    ends = {f for fs in vol.up + vol.down for f in fs}
    own = set(vol.tubes)
    inner, outer, other = [], [], []
    for i, cs in enumerate(vol.cells):
        t = vol.tubes[i]
        for c in cs:
            for f in grid.cell_faces[c]:
                a, b = grid.fc[f]
                o = b if a == c else a
                if f in ends or member[o]:
                    continue
                if not grid.guard[f] and grid.cvFt[o] in own:
                    other.append(int(f))
                    continue
                s = side_of(grid, t, f, o)
                (inner if s == "inner" else outer if s == "outer" else
                 other).append(int(f))
    return inner, outer, other


def layout(grid, vol):
    """(Ends, Cuts) of the volume: the slices between their inner and
    outer faces, the flux tubes cut by the flux surfaces between them (the
    flux outwards, through every face crossing them: between two tubes of
    the volume, or from a tube to the inner or outer side)."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    a, b = grid.fc[:, 0], grid.fc[:, 1]
    loc = np.full(grid.nCv, -1)
    loc[vol.cell] = np.arange(len(vol.cell))
    cell_slice = cell_slices(vol)
    inner, outer, _ = vol.sides
    lists = []
    for faces in (inner, outer):
        faces = np.asarray(faces, int)
        c = np.where(member[a[faces]], a[faces], b[faces])
        lists += [faces, cell_slice[loc[c]]]
    ends = Ends(vol.slices.shape[0] - 1, cell_slice, *lists)
    n = len(vol.tubes)
    index = np.full(grid.nCv, -1)
    index[vol.cell] = vol.cell_tube
    parts = []
    for f in np.flatnonzero(member[a] & member[b] & (index[a] != index[b])):
        ia, ib = index[a[f]], index[b[f]]
        parts.append((f, 1.0, ia + 1, ib + 1) if ia < ib else
                     (f, -1.0, ib + 1, ia + 1))
    for f in inner:
        c = a[f] if member[a[f]] else b[f]
        parts.append((f, 1.0 if b[f] == c else -1.0, 0, index[c] + 1))
    for f in outer:
        c = a[f] if member[a[f]] else b[f]
        parts.append((f, 1.0 if a[f] == c else -1.0, index[c] + 1, n + 1))
    return ends, Cuts(n, vol.cell_tube, parts)


def rhop(grid, vol, psin):
    """rho poloidal of each tube of the volume at its start faces."""
    return topology.rhop(grid, vol.up, psin)


def dssep(grid, vol):
    """Distance (m) from the separatrix along the surface across the
    region through the start face of the tube next to the separatrix,
    for each tube of the volume (nan where it does not cross it)."""
    s = surface(grid, vol.up[vol.ref][0], vol.region)
    return topology.dssep(grid, s, vol.tubes)
