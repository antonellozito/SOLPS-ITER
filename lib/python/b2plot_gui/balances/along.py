"""The balances defined along the field lines only (of the parallel
balance, kinds.py): the force per ion and the total pressure, with the
same two parts as every balance (calc.py)."""

import numpy as np

from . import calc
from .terms import Term

WALLS = "Sides and walls"


# ---------------------------------------------------------------- force
def force(grid, vol, kind, terms, opts, x):
    """Force balance: the momentum balance with the convected momentum
    as the only flux, per ion: every term of a flux tube over the ions
    n_a V of its first cell (radial balance), every cell over its own
    ions (poloidal balance, the flux at the edges of the slices over the
    ions of the cell downstream of the face; the difference to the cells
    is a term of its own, with the flux through the walls)."""
    ends = vol.ends
    zero = np.zeros_like(terms.fy)
    div = calc.divergence(grid, terms.fx, terms.fy, np.concatenate((
        ends.inflow, ends.outflow)), True)
    src = np.column_stack((div, terms.src))
    pdx = calc.divergence(grid, terms.fx, zero)
    pdy = calc.divergence(grid, zero, terms.fy)
    psrc = np.column_stack((pdx, pdy, terms.src))
    ions = np.where(terms.ions > 0, terms.ions, np.inf)
    weight = 1.0 / ions
    area = np.array([ions[cs[0]] for cs in vol.cells])
    names = calc.transport(kind, terms)
    edge = [Term("ions", "Convected momentum: variation of the ions "
                 "along the slice, and walls")]
    edges = calc.cut_edges(grid, vol.cuts, terms.fx, weight)
    return calc.assemble(grid, vol, kind, terms, opts, x, terms.fx, src,
                         psrc, 1, names + terms.sources,
                         edge + names + terms.sources, area, 1.0, edges,
                         weight)


# ------------------------------------------------------ total pressure
def endface_pressures(grid, vol, member, pf, gp):
    """Static pressure contributions of the upstream and downstream faces
    of each tube (baltotpress endface_pressures): the downstream faces
    take sign(cos alpha) * p, the upstream ones share the rest of the
    integrated pressure-gradient source so that each tube balances."""
    val = np.zeros(grid.nFc)
    for i in range(len(vol.tubes)):
        faces = list(vol.up[i]) + list(vol.down[i])
        isup = np.array([True] * len(vol.up[i]) + [False] * len(vol.down[i]))
        fa = np.array(faces, int)
        inside2 = member[grid.fc[fa, 1]]
        side = np.where(inside2, 1.0, -1.0)
        sigma = side * np.sign(grid.qalf[fa])
        ce = sigma * pf[fa]
        k = np.flatnonzero(isup)
        if not len(k):
            k = np.flatnonzero(sigma < 0)
        if not len(k):
            k = np.arange(len(fa))
        ref = np.setdiff1d(np.arange(len(fa)), k)
        ce[k] = (gp[vol.cells[i]].sum() - ce[ref].sum()) / len(k)
        val[fa] = ce / side
    return val


def _static_edges(grid, vol, member, pf, gp):
    """Static pressure at the edges of the slices along each tube: from
    the pressure on its downstream faces, adding the pressure-gradient
    source of each cell going upstream (baltotpress); a tube that ended
    on a wall before is not in the later edges."""
    counts = vol.slices
    e = np.zeros(counts.shape[0])
    for i, t in enumerate(vol.tubes):
        cs = vol.cells[i]
        fs = np.array(grid.faces_at(t, vol.down_pos[i]), int)
        if len(fs):
            side = np.where(member[grid.fc[fs, 1]], 1.0, -1.0)
            sigma = side * np.sign(grid.qalf[fs])
            w = grid.fcS[fs] / grid.fcS[fs].sum()
            v_end = float(np.sum(-sigma * pf[fs] * w))
        else:
            v_end = 0.0
        v = np.empty(len(cs) + 1)
        v[-1] = v_end
        v[:-1] = v_end + np.cumsum(gp[cs][::-1])[::-1]
        for j in range(counts.shape[0]):
            c = counts[j, i]
            if c < len(cs) or vol.reached[i]:
                e[j] += v[c]
    return e


def pressure(grid, vol, kind, terms, opts, x):
    """Total pressure (baltotpress): fixed areas (one per face, at the
    right end, the downstream one unless reversed)."""
    p = terms.pressure
    ends = vol.ends
    member = calc.member_cells(grid, vol)
    zero = np.zeros(grid.nFc)
    conv = p["flux"]
    pex = endface_pressures(grid, vol, member, p["pe"], p["gpe"])
    pix = endface_pressures(grid, vol, member, p["pi"], p["gpi"])
    flux = np.column_stack((conv, pex, pix))
    pair = np.column_stack([calc.divergence(grid, zero[:, None],
                                            y[:, None])[:, 0] / p["apll"]
                            for _, _, y in p["pairs"]])
    names = [Term("raddiv", n, kind.group) for n, _, _ in p["pairs"]]
    src = np.column_stack((pair, terms.src))
    unit = ends.in_unit if vol.reverse else ends.out_unit
    area = np.maximum(calc._sum(ends.n, unit, np.ones(len(unit))), 1)
    right = [grid.faces_at(t, (vol.up_pos if vol.reverse else
                               vol.down_pos)[i])
             for i, t in enumerate(vol.tubes)]
    parea = float(max(sum(len(r) for r in right), 1))
    edges = calc.cut_edges(grid, vol.cuts, np.column_stack((conv, zero,
                                                            zero)))
    edges[:, 1] = _static_edges(grid, vol, member, p["pe"], p["gpe"])
    edges[:, 2] = _static_edges(grid, vol, member, p["pi"], p["gpi"])
    dconv = calc.divergence(grid, conv[:, None], zero[:, None])
    gpe, gpi = np.where(member, p["gpe"], 0.0), np.where(member, p["gpi"],
                                                         0.0)
    psrc = np.column_stack((dconv, gpe, gpi, src))
    walls = [Term("walls", "Dynamic pressure through the sides and walls",
                  WALLS),
             Term("walls", "Electron static pressure on the walls", WALLS),
             Term("walls", "Ion static pressure on the walls", WALLS)]
    sources = names + terms.sources
    return calc.assemble(grid, vol, kind, terms, opts, x, flux, src, psrc,
                         3, sources, walls + sources, area, parea, edges)
