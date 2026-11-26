"""Geometry of the parallel balance (along the field lines): the volume
between an upstream and a downstream surface, its sides and the parts of
its balance (the flux tubes from end to end, the slices cut), the radial
coordinate of its tubes."""

import numpy as np

from .topology import Cuts, Ends, Volume, cell_slices, finish, signs
from . import topology


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
    vol.surface = up
    finish(grid, vol)
    vol.ends, vol.cuts = layout(grid, vol)
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


def layout(grid, vol):
    """(Ends, Cuts) of the volume: the flux tubes between their upstream
    and downstream faces (and walls), the slices cut by the surfaces
    between them (the flux in the downstream direction)."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    lists = []
    for faces in (vol.up, vol.down):
        lists += [np.array([f for fs in faces for f in fs], int),
                  np.array([i for i, fs in enumerate(faces) for _ in fs],
                           int)]
    ends = Ends(len(vol.tubes), vol.cell_tube, *lists)
    counts = vol.slices
    parts = []
    for i, t in enumerate(vol.tubes):
        cs = vol.cells[i]
        for j in range(counts.shape[0]):
            c = counts[j, i]
            if c == 0:
                fs = vol.up[i]
                parts += [(f, s, j, j + 1) for f, s in zip(
                    fs, signs(grid, member, fs, True))]
            elif c == len(cs):
                if vol.reached[i]:
                    fs = grid.faces_at(t, vol.down_pos[i])
                    parts += [(f, s, j, j + 1) for f, s in zip(
                        fs, signs(grid, member, fs, False))]
            else:
                a, b = cs[c - 1], cs[c]
                p = grid.pos[b] if vol.direction > 0 else grid.pos[a]
                parts += [(f, 1.0 if grid.fc[f, 0] == a else -1.0, j, j + 1)
                          for f in grid.faces_at(t, p)]
    return ends, Cuts(counts.shape[0] - 1, cell_slices(vol), parts)


def rhop(grid, vol, psin):
    """rho poloidal of each tube of the volume at its face of the
    upstream surface."""
    return topology.rhop(grid, [[vol.surface.face[t]] for t in vol.tubes],
                         psin)


def dssep(grid, vol):
    """Distance (m) from the separatrix along the upstream surface, for
    each tube of the volume."""
    return topology.dssep(grid, vol.surface, vol.tubes)
