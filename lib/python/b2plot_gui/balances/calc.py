"""The balances of a volume, as radial_balance and poloidal_balance of the
balance scripts compute them: per flux tube (radial resolution, poloidally
integrated) the flux in through the upstream surface, out through the
downstream surface and the walls, the sources in the tube with the radial
divergences, the B2.5 and the post-processing residual; per slice
(poloidal resolution, radially integrated) the flux through the surfaces
between the slices and the sources of the slices."""

from dataclasses import dataclass

import numpy as np

from .terms import RADIAL, Term

AREA_TYPES = (("none", "None"), ("parallel", "Parallel"),
              ("contact", "Contact"))
AREA_ENDS = (("down", "Downstream"), ("up", "Upstream"))
DISTANCES = (("parallel", "Parallel"), ("poloidal", "Poloidal"))
WALLS = "Sides and walls"


@dataclass
class Options:
    areatype: str = "none"
    areaend: str = "down"
    distance: str = "parallel"


@dataclass
class Result:
    """Radial (index t: flux tubes in the order of x) and poloidal
    (index j: slices) balance, already divided by the areas and with the
    sign of the momentum; columns of up, down, edges: the flux terms;
    columns of src and psrc: the source terms (names in sources and
    psources)."""
    x: np.ndarray
    up: np.ndarray
    down: np.ndarray
    src: np.ndarray
    code: np.ndarray
    post: np.ndarray
    fluxes: list
    sources: list
    px_edges: np.ndarray
    px: np.ndarray
    edges: np.ndarray
    psrc: np.ndarray
    pcode: np.ndarray
    ppost: np.ndarray
    psources: list
    unit: str
    order: np.ndarray               # tube of each radial point
    scale_t: np.ndarray             # momfac / area of each tube (sorted)
    scale_p: float
    cell_tube: np.ndarray           # volume cells: index of the point
    cell_slice: np.ndarray
    cells: np.ndarray
    note: str = ""

    def radial_sum(self, values):
        """values (nCv, p) of the volume cells summed per point of x and
        scaled as the sources."""
        out = np.zeros((len(self.x), values.shape[1]))
        np.add.at(out, self.cell_tube, values[self.cells])
        return out * self.scale_t[:, None]

    def poloidal_sum(self, values):
        out = np.zeros((len(self.px), values.shape[1]))
        np.add.at(out, self.cell_slice, values[self.cells])
        return out * self.scale_p

    def messages(self):
        """How well the post-processed residual and the one of B2.5 agree,
        relative to the largest term: [radial, poloidal balance]."""
        lines = []
        for name, post, code, terms in (
                ("Radial", self.post, self.code, (self.up, self.down,
                                                  self.src)),
                ("Poloidal", self.ppost, self.pcode, (self.edges,
                                                      self.psrc))):
            scale = max(float(np.abs(t.sum(axis=1)).max()) for t in terms)
            diff = float(np.abs(post - code).max())
            lines.append("%s balance: the post-processed residual and the "
                         "residual of B2.5 differ by %.1e of the largest "
                         "term." % (name, diff / scale if scale else 0.0))
        return lines


def divergence(grid, fx, fy, exclude=None, parallel=False):
    """Net inflow into each cell of the fluxes fx + fy (nFc, k) through
    its faces (raddiv): on the faces in exclude only fy (parallel) or
    nothing."""
    c = fx + fy
    if exclude is not None and len(exclude):
        c = c.copy()
        c[exclude] = fy[exclude] if parallel else 0.0
    out = np.zeros((grid.nCv, c.shape[1]))
    np.add.at(out, grid.fc[:, 0], -c)
    np.add.at(out, grid.fc[:, 1], c)
    return out


def face_area(grid, areatype):
    """calc_area: area each face flux is divided by."""
    if areatype == "parallel":
        return grid.fcS * np.abs(grid.qalf) * grid.fcBb[:, 0] / \
            grid.fcBb[:, 3]
    if areatype == "contact":
        return grid.fcS.copy()
    return np.ones(grid.nFc)


def momentum_factor(grid, vol, terms):
    """1, or for the momentum -1 if the downstream direction is the
    negative poloidal one, times minus the sign of the mean toroidal
    field direction; the total pressure has the opposite sign (positive
    pressures)."""
    if not terms.ismom:
        return 1.0
    f = -1.0 if vol.reverse else 1.0
    if terms.quantity == "totpress":
        f = -f
    return f * -np.sign(np.mean(grid.cvEb[:, 2]))


def _signs(grid, member, faces, inflow):
    """Signs giving the inflow (or outflow) of the face fluxes."""
    faces = np.asarray(faces, int)
    into = member[grid.fc[faces, 1]]
    return np.where(into if inflow else ~into, 1.0, -1.0)


def _tube_lists(grid, vol, member):
    """Faces, signs and tube index of the upstream and downstream faces."""
    out = {}
    for key, lists, inflow in (("up", vol.up, True),
                               ("down", vol.down, False)):
        faces = [f for fs in lists for f in fs]
        tube = [i for i, fs in enumerate(lists) for _ in fs]
        out[key] = (np.array(faces, int), _signs(grid, member, faces,
                                                 inflow),
                    np.array(tube, int))
    return out


def _sum(n, index, values):
    out = np.zeros((n,) + values.shape[1:])
    np.add.at(out, index, values)
    return out


def _end_area(grid, vol, terms, opts, lists, hz):
    """Area of each tube at the end chosen (1 without area)."""
    n = len(vol.tubes)
    if opts.areaend == "none" or (opts.areatype == "none" and not terms.hz):
        return np.ones(n)
    faces, _, tube = lists["up" if opts.areaend == "up" else "down"]
    a = face_area(grid, opts.areatype)[faces] * hz[faces]
    total = _sum(n, tube, a)
    if opts.areatype == "none":     # mean of the hz factors, not a count
        total /= np.maximum(_sum(n, tube, np.ones(len(faces))), 1)
    return total


def _pol_area(grid, vol, terms, opts, lists, hz):
    if opts.areaend == "none" or (opts.areatype == "none" and not terms.hz):
        return 1.0
    faces = lists["up" if opts.areaend == "up" else "down"][0]
    a = face_area(grid, opts.areatype)[faces] * hz[faces]
    return float(a.mean() if opts.areatype == "none" else a.sum())


def compute(grid, vol, terms, opts, x):
    """Result of the terms in the volume; x: radial coordinate of each
    tube of the volume."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    lists = _tube_lists(grid, vol, member)
    ud = np.concatenate((lists["up"][0], lists["down"][0]))
    momfac = momentum_factor(grid, vol, terms)
    if terms.pressure is not None:
        return _pressure(grid, vol, terms, opts, x, member, lists, momfac)
    if terms.ions is not None:
        return _force(grid, vol, terms, opts, x, member, lists, momfac, ud)
    parallel = opts.areatype == "parallel"
    flux = terms.fx if parallel else terms.fx + terms.fy
    k = flux.shape[1]
    h = terms.b2mndr_hz
    hz = (1 - h) + h * grid.fcHz if terms.hz else np.ones(grid.nFc)
    div = divergence(grid, terms.fx, terms.fy, ud, parallel)
    src = np.column_stack((div, terms.src))
    pdiv = divergence(grid, terms.fx, terms.fy)
    psrc = np.column_stack((pdiv, terms.src))
    divs = [Term(t.key, "Radial transport: " + _lower(t.name), RADIAL)
            for t in terms.fluxes]
    area = _end_area(grid, vol, terms, opts, lists, hz)
    parea = _pol_area(grid, vol, terms, opts, lists, hz)
    return _finish(grid, vol, terms, opts, x, member, lists, momfac, flux,
                   src, psrc, k, divs + terms.sources, divs + terms.sources,
                   area, parea, flux)


def _lower(name):
    return name[:1].lower() + name[1:] if name[1:2].islower() else name


def _finish(grid, vol, terms, opts, x, member, lists, momfac, flux, src,
            psrc, ncorr, sources, psources, area, parea, eflux,
            edges=None, pweight=None):
    """Sums per tube and per slice, scaled; ncorr: number of the first
    poloidal source columns that are the divergences of the flux columns
    (corrected by the flux at the edges of the slices); pweight: factor of
    each cell in the poloidal balance (1)."""
    n = len(vol.tubes)
    upf, ups, upt = lists["up"]
    dnf, dns, dnt = lists["down"]
    fup = _sum(n, upt, flux[upf] * ups[:, None])
    fdown = _sum(n, dnt, flux[dnf] * dns[:, None])
    sint = _sum(n, vol.cell_tube, src[vol.cell])
    rint = _sum(n, vol.cell_tube, terms.res[vol.cell])
    order = np.argsort(x, kind="stable")
    scale = momfac / area
    post = scale * (fup.sum(1) - fdown.sum(1) + sint.sum(1))
    # poloidal
    counts = vol.slices
    m = counts.shape[0] - 1
    cell_slice = np.concatenate([np.searchsorted(counts[:, i], np.arange(
        len(cs)), side="right") - 1 for i, cs in enumerate(vol.cells)])
    if edges is None:
        edges = _edges(grid, vol, eflux, counts, lists)
    w = np.ones(grid.nCv) if pweight is None else pweight
    pint = _sum(m, cell_slice, psrc[vol.cell] * w[vol.cell, None])
    pres = _sum(m, cell_slice, terms.res[vol.cell] * w[vol.cell])
    pint[:, :ncorr] += -edges[:-1, :ncorr] + edges[1:, :ncorr]
    pscale = momfac / parea
    ppost = pscale * (pint.sum(1) - np.diff(edges.sum(1)))
    lengths = _lengths(grid, vol, opts.distance)
    xe = np.concatenate(([0.0], np.cumsum(lengths)))
    xe = xe[-1] - xe
    totals = "none" in (opts.areaend, opts.areatype)
    unit = terms.units[0 if totals and terms.quantity != "totpress" else 1]
    rank = np.empty(n, int)
    rank[order] = np.arange(n)
    return Result(
        x=np.asarray(x)[order], up=(fup * scale[:, None])[order],
        down=(fdown * scale[:, None])[order],
        src=(sint * scale[:, None])[order], code=(scale * rint)[order],
        post=post[order], fluxes=list(terms.fluxes), sources=sources,
        px_edges=xe, px=0.5 * (xe[:-1] + xe[1:]), edges=edges * pscale,
        psrc=pint * pscale, pcode=pres * pscale, ppost=ppost,
        psources=psources, unit=unit, order=order, scale_t=scale[order],
        scale_p=pscale, cell_tube=rank[vol.cell_tube],
        cell_slice=cell_slice, cells=vol.cell, note="; ".join(terms.notes))


def _edge_faces(grid, vol, counts, lists):
    """Faces and signs (flux in the downstream direction) of each edge of
    the slices: [(edge, face, sign, tube)]."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    out = []
    for i, t in enumerate(vol.tubes):
        cs = vol.cells[i]
        n_t = len(cs)
        for j in range(counts.shape[0]):
            c = counts[j, i]
            if c == 0:
                fs = vol.up[i]
                out += [(j, f, s, i) for f, s in zip(
                    fs, _signs(grid, member, fs, True))]
            elif c == n_t:
                if vol.reached[i]:
                    fs = grid.faces_at(t, vol.down_pos[i])
                    out += [(j, f, s, i) for f, s in zip(
                        fs, _signs(grid, member, fs, False))]
            else:
                a, b = cs[c - 1], cs[c]
                p = grid.pos[b] if vol.direction > 0 else grid.pos[a]
                for f in grid.faces_at(t, p):
                    out.append((j, f, 1.0 if grid.fc[f, 0] == a else -1.0,
                                i))
    return out


def _edges(grid, vol, flux, counts, lists, weight=None):
    """Flux in the downstream direction through each edge of the slices;
    weight: factor of each cell, taken on the downstream side of the
    face."""
    e = np.zeros((counts.shape[0], flux.shape[1]))
    for j, f, s, _ in _edge_faces(grid, vol, counts, lists):
        w = 1.0 if weight is None else weight[grid.fc[f, 1 if s > 0 else 0]]
        e[j] += s * flux[f] * w
    return e


# ---------------------------------------------------------------- force
def _force(grid, vol, terms, opts, x, member, lists, momfac, ud):
    """Force balance: the momentum balance with the convected momentum
    as the only flux, per ion: every term of a flux tube over the ions
    n_a V of its first cell (radial balance), every cell over its own
    ions (poloidal balance, the flux at the edges of the slices over the
    ions of the cell downstream of the face; the difference to the cells
    is a term of its own, with the flux through the walls)."""
    zero = np.zeros_like(terms.fy)
    div = divergence(grid, terms.fx, terms.fy, ud, True)
    src = np.column_stack((div, terms.src))
    pdx = divergence(grid, terms.fx, zero)
    pdy = divergence(grid, zero, terms.fy)
    psrc = np.column_stack((pdx, pdy, terms.src))
    ions = np.where(terms.ions > 0, terms.ions, np.inf)
    weight = 1.0 / ions
    area = np.array([ions[cs[0]] for cs in vol.cells])
    radial = [Term(t.key, "Radial transport: " + _lower(t.name), RADIAL)
              for t in terms.fluxes]
    edge = [Term("ions", "Convected momentum: variation of the ions "
                 "along the slice, and walls")]
    edges = _edges(grid, vol, terms.fx, vol.slices, lists, weight)
    return _finish(grid, vol, terms, opts, x, member, lists, momfac,
                   terms.fx, src, psrc, 1, radial + terms.sources,
                   edge + radial + terms.sources, area, 1.0, terms.fx,
                   edges=edges, pweight=weight)


def _lengths(grid, vol, distance):
    """Length of the cells of the reference tube (sumrad): parallel
    (hx over the pitch) or poloidal."""
    cs = vol.cells[vol.ref]
    hx = grid.cvHx[cs]
    if distance == "parallel":
        return hx / np.abs(grid.cvBb[cs, 0] / grid.cvBb[cs, 3])
    return hx


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


def _static_edges(grid, vol, member, counts, pf, gp):
    """Static pressure at the edges of the slices along each tube: from
    the pressure on its downstream faces, adding the pressure-gradient
    source of each cell going upstream (baltotpress); a tube that ended
    on a wall before is not in the later edges."""
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


def _pressure(grid, vol, terms, opts, x, member, lists, momfac):
    """Total pressure (baltotpress): fixed areas (one per face, at the
    right end, the downstream one unless reversed)."""
    p = terms.pressure
    zero = np.zeros(grid.nFc)
    conv = p["flux"]
    pex = endface_pressures(grid, vol, member, p["pe"], p["gpe"])
    pix = endface_pressures(grid, vol, member, p["pi"], p["gpi"])
    flux = np.column_stack((conv, pex, pix))
    pair = np.column_stack([divergence(grid, zero[:, None],
                                       y[:, None])[:, 0] / p["apll"]
                            for _, _, y in p["pairs"]])
    names = [Term("raddiv", n, RADIAL) for n, _, _ in p["pairs"]]
    src = np.column_stack((pair, terms.src))
    end = "down" if not vol.reverse else "up"
    faces, _, tube = lists[end]
    area = np.maximum(_sum(len(vol.tubes), tube, np.ones(len(faces))), 1)
    right = [grid.faces_at(t, (vol.up_pos if vol.reverse else
                               vol.down_pos)[i])
             for i, t in enumerate(vol.tubes)]
    parea = float(max(sum(len(r) for r in right), 1))
    counts = vol.slices
    eflux = np.column_stack((conv, zero, zero))
    edges = _edges(grid, vol, eflux, counts, lists)
    edges[:, 1] = _static_edges(grid, vol, member, counts, p["pe"], p["gpe"])
    edges[:, 2] = _static_edges(grid, vol, member, counts, p["pi"], p["gpi"])
    dconv = divergence(grid, conv[:, None], zero[:, None])
    gpe, gpi = np.where(member, p["gpe"], 0.0), np.where(member, p["gpi"],
                                                         0.0)
    psrc = np.column_stack((dconv, gpe, gpi, src))
    walls = [Term("walls", "Dynamic pressure through the sides and walls",
                  WALLS),
             Term("walls", "Electron static pressure on the walls", WALLS),
             Term("walls", "Ion static pressure on the walls", WALLS)]
    sources = names + terms.sources
    return _finish(grid, vol, terms, opts, x, member, lists, momfac, flux,
                   src, psrc, 3, sources, walls + sources, area, parea,
                   eflux, edges=edges)
