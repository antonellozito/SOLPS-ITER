"""The balances of a volume, as radial_balance and poloidal_balance of the
balance scripts compute them, the same for both kinds (kinds.py): per
unit with ends (parallel: flux tube, poloidally integrated; radial:
slice, radially integrated) the flux in through one end, out through the
other, the sources in the unit with the transport through its other
faces, the B2.5 and the post-processing residual; per unit cut
(parallel: slice; radial: flux tube) the flux across the boundaries
between the units and the sources of the units. The quantities defined
along the field lines only are in along.py."""

from dataclasses import dataclass

import numpy as np

from . import along
from .kinds import KINDS
from .terms import Term
from .topology import signs

DISTANCES = (("parallel", "Parallel"), ("poloidal", "Poloidal"))


@dataclass
class Options:
    areatype: str = "none"
    areaend: str = "down"
    distance: str = "parallel"


@dataclass
class Part:
    """One part of the balance, already divided by the areas and with the
    sign of the momentum: per point (unit) its coordinate x along axis;
    ends part: the flux in and out (inflow, outflow; columns: the flux
    terms); cut part: the flux across the boundaries 0 to n between the
    points (across) at the coordinates edges; the sources (columns: names
    in sources), the residual of B2.5 and the post-processed one; scale:
    of each point (ends part) or of all (cut part); cell: the point of
    each cell of the volume (cells); order: the unit of each point."""
    axis: str
    x: np.ndarray
    src: np.ndarray
    code: np.ndarray
    post: np.ndarray
    sources: list
    scale: object
    cell: np.ndarray
    cells: np.ndarray
    order: np.ndarray
    inflow: np.ndarray = None
    outflow: np.ndarray = None
    across: np.ndarray = None
    edges: np.ndarray = None

    def flux_terms(self):
        return (self.inflow, self.outflow) if self.across is None else \
            (self.across,)

    def sum(self, values):
        """values (nCv, p) of the volume cells summed per point and scaled
        as the sources."""
        out = np.zeros((len(self.x), values.shape[1]))
        np.add.at(out, self.cell, values[self.cells])
        return out * (self.scale[:, None] if np.ndim(self.scale) else
                      self.scale)

    def agreement(self):
        """Largest difference of the post-processed residual and the one
        of B2.5, relative to the largest term."""
        scale = max(float(np.abs(t.sum(axis=1)).max())
                    for t in self.flux_terms() + (self.src,))
        diff = float(np.abs(self.post - self.code).max())
        return diff / scale if scale else 0.0


@dataclass
class Result:
    kind: str
    ends: Part
    cut: Part
    fluxes: list
    unit: str
    note: str = ""

    def part(self, name):
        return self.ends if name == "ends" else self.cut

    def messages(self):
        """How well the post-processed residual and the one of B2.5 agree:
        [radial, poloidal balance], each of the part along that axis (the
        plot it is shown under)."""
        parts = sorted((self.ends, self.cut), key=lambda p: p.axis !=
                       "radial")
        return ["%s balance: the post-processed residual and the residual "
                "of B2.5 differ by %.1e of the largest term." % (
                    p.axis.capitalize(), p.agreement()) for p in parts]


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


def member_cells(grid, vol):
    """True for each cell of the volume."""
    member = np.zeros(grid.nCv, bool)
    member[vol.cell] = True
    return member


def _sum(n, index, values):
    out = np.zeros((n,) + values.shape[1:])
    np.add.at(out, index, values)
    return out


def _lower(name):
    return name[:1].lower() + name[1:] if name[1:2].islower() else name


def transport(kind, terms):
    """The sources of the transport into a unit with ends through its
    other faces (the divergences of the flux columns)."""
    return [Term(t.key, kind.transport + ": " + _lower(t.name), kind.group)
            for t in terms.fluxes]


def compute(grid, vol, terms, opts, x):
    """Result of the terms in the volume; x: radial coordinate of each
    tube of the volume."""
    kind = KINDS[vol.kind]
    if terms.pressure is not None:
        return along.pressure(grid, vol, kind, terms, opts, x)
    if terms.ions is not None:
        return along.force(grid, vol, kind, terms, opts, x)
    ends = vol.ends
    parallel = opts.areatype == "parallel"
    flux = terms.fx if parallel else terms.fx + terms.fy
    div = divergence(grid, terms.fx, terms.fy, np.concatenate((
        ends.inflow, ends.outflow)), parallel)
    src = np.column_stack((div, terms.src))
    psrc = np.column_stack((divergence(grid, terms.fx, terms.fy),
                            terms.src))
    sources = transport(kind, terms) + terms.sources
    area, parea = _areas(grid, vol, kind, terms, opts)
    return assemble(grid, vol, kind, terms, opts, x, flux, src, psrc,
                    flux.shape[1], sources, sources, area, parea,
                    cut_edges(grid, vol.cuts, flux))


def _areas(grid, vol, kind, terms, opts):
    """Area of each unit with ends at the end chosen (a unit without it:
    at the other end, else 1) and of the whole end (1 without area; no
    area: the mean hz factor at the end, if the kind takes it)."""
    ends = vol.ends
    n = ends.n
    if opts.areatype == "none" and not (kind.hz_without_area and terms.hz):
        return np.ones(n), 1.0
    h = terms.b2mndr_hz
    hz = (1 - h) + h * grid.fcHz if terms.hz else np.ones(grid.nFc)
    sides = [(ends.outflow, ends.out_unit), (ends.inflow, ends.in_unit)]
    if opts.areaend != kind.area_ends[0][0]:
        sides = sides[::-1]
    sums = []
    for faces, unit in sides:
        a = face_area(grid, opts.areatype)[faces] * hz[faces]
        total = _sum(n, unit, a)
        if opts.areatype == "none":     # mean of the hz factors, not a count
            total /= np.maximum(_sum(n, unit, np.ones(len(faces))), 1)
        sums.append((total, float(a.mean() if opts.areatype == "none" else
                                  a.sum())))
    (here, whole), (there, _) = sums
    area = np.where(here != 0, here, np.where(there != 0, there, 1.0))
    return area, whole if whole != 0 else 1.0


def cut_edges(grid, cuts, flux, weight=None):
    """Flux across each boundary between the units cut (towards the
    units of higher index); weight: factor of each cell, taken on the
    side the flux goes to."""
    e = np.zeros((cuts.n + 1, flux.shape[1]))
    for f, s, a, b in cuts.parts:
        w = 1.0 if weight is None else weight[grid.fc[f, 1 if s > 0 else 0]]
        e[a:b] += s * flux[f] * w
    return e


def assemble(grid, vol, kind, terms, opts, x, flux, src, psrc, ncorr,
             sources, psources, area, parea, edges, weight=None):
    """Sums per unit of both parts, scaled: area, parea: of each unit with
    ends and of the cut part; ncorr: number of the first source columns of
    the cut part that are the divergences of the flux columns (corrected
    by the flux at the boundaries of the units); weight: factor of each
    cell in the cut part (1)."""
    ends, cuts = vol.ends, vol.cuts
    member = member_cells(grid, vol)
    n = ends.n
    fin = _sum(n, ends.in_unit, flux[ends.inflow] * signs(
        grid, member, ends.inflow, True)[:, None])
    fout = _sum(n, ends.out_unit, flux[ends.outflow] * signs(
        grid, member, ends.outflow, False)[:, None])
    sint = _sum(n, ends.cell, src[vol.cell])
    rint = _sum(n, ends.cell, terms.res[vol.cell])
    momfac = momentum_factor(grid, vol, terms)
    scale = momfac / area
    post = scale * (fin.sum(1) - fout.sum(1) + sint.sum(1))
    m = cuts.n
    w = np.ones(grid.nCv) if weight is None else weight
    pint = _sum(m, cuts.cell, psrc[vol.cell] * w[vol.cell, None])
    pres = _sum(m, cuts.cell, terms.res[vol.cell] * w[vol.cell])
    pint[:, :ncorr] += -edges[:-1, :ncorr] + edges[1:, :ncorr]
    pscale = momfac / parea
    ppost = pscale * (pint.sum(1) - np.diff(edges.sum(1)))
    xe, (xc, ec) = _coordinates(grid, vol, kind, opts, x)
    order = np.argsort(xe, kind="stable")
    rank = np.empty(n, int)
    rank[order] = np.arange(n)
    totals = "none" in (opts.areaend, opts.areatype)
    unit = terms.units[0 if totals and terms.quantity != "totpress" else 1]
    return Result(
        kind=kind.key,
        ends=Part(kind.axis("ends"), xe[order],
                  (sint * scale[:, None])[order], (scale * rint)[order],
                  post[order], sources, scale[order], rank[ends.cell],
                  vol.cell, order, inflow=(fin * scale[:, None])[order],
                  outflow=(fout * scale[:, None])[order]),
        cut=Part(kind.axis("cut"), xc, pint * pscale, pres * pscale, ppost,
                 psources, pscale, cuts.cell, vol.cell, np.arange(m),
                 across=edges * pscale, edges=ec),
        fluxes=list(terms.fluxes), unit=unit, note="; ".join(terms.notes))


def _coordinates(grid, vol, kind, opts, x):
    """Coordinate of each unit with ends, (coordinate of each unit cut,
    of the boundaries between them): the tubes at x (the boundaries
    halfway between them), the slices at their distance along the
    reference tube from its start or its end."""
    lengths = _lengths(grid, vol, opts.distance)
    se = np.concatenate(([0.0], np.cumsum(lengths)))
    if kind.from_end:
        se = se[-1] - se
    slices = 0.5 * (se[:-1] + se[1:])
    xt = np.asarray(x, float)
    if kind.ends_units == "tubes":
        return xt, (slices, se)
    mid = 0.5 * (xt[:-1] + xt[1:])
    n = len(xt)
    first = xt[0] - (mid[0] - xt[0]) if n > 1 else xt[0] - 0.5
    last = xt[-1] + (xt[-1] - mid[-1]) if n > 1 else xt[-1] + 0.5
    return slices, (xt, np.concatenate(([first], mid, [last])))


def _lengths(grid, vol, distance):
    """Length of the cells of the reference tube (sumrad): parallel
    (hx over the pitch) or poloidal."""
    cs = vol.cells[vol.ref]
    hx = grid.cvHx[cs]
    if distance == "parallel":
        return hx / np.abs(grid.cvBb[cs, 0] / grid.cvBb[cs, 3])
    return hx
