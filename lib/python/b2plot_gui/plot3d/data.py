"""What the 3D view shows, taken from the 2D tab: a Snapshot of the run
geometry and layers, the plasma quantity of the plot (with its colours),
the wall quantity, and the vector quantity gridded in (R, Z) with its
toroidal component (asked for from b2plot: the EIRENE z component, or the
poloidal one turned along or across the field with B_tor/B_pol)."""

from dataclasses import dataclass, field, replace

import matplotlib.tri as mtri
import numpy as np

from ...qt import QtCore, Signal
from .. import theme
from ..catalog import Quantity
from ..model import split_unit
from ..plot import shapes
from ..plot.overlays import smoothed_strip, structure
from ..tools.wallprofile import marks
from ..plot.scalar import node_values
from ..plot.styles import PlotStyle, cmap_for, norm_for
from ..tools import births, fieldlines, revolve, vector3d as v3
from ..tools.tracers import Field
from ...b2plot import labels


@dataclass
class Snapshot:
    machine_key: object = None
    flux_key: object = None
    plasma_key: object = None
    wall_key: object = None
    vector_key: object = None
    chords_key: object = None
    magnetic_key: object = None
    layers: dict = field(default_factory=dict)
    outer: list = field(default_factory=list)       # vessel, outer loops
    vessel: list = field(default_factory=list)      # other vessel loops
    solids: list = field(default_factory=list)
    walls: list = field(default_factory=list)       # open structure
    targets: tuple = None       # (segments, normals, lifts)
    xpoints: list = field(default_factory=list)
    opoints: list = field(default_factory=list)
    midplanes: object = None
    grid: object = None
    eirene: object = None
    separatrices: list = field(default_factory=list)  # (rho_p, line)
    flux: list = field(default_factory=list)          # (rho_p, line)
    plasma: dict = None
    wall: dict = None
    vector: dict = None
    chords: list = field(default_factory=list)  # (number, end, end, look)
    magnetic: dict = None       # field line, directions
    lines: dict = field(default_factory=dict)   # tracer births: polylines
    centre: tuple = (1.0, 0.0)
    box: tuple = (0.0, 1.0, -1.0, 1.0)  # R, Z of the 2D plot at the start
    size: float = 1.0
    background: tuple = (1.0, 1.0, 1.0)


TARGET_LIFT = 0.02      # targets off the structure, in element lengths
WALL_LIFT = 0.04        # the wall quantity over them


def background():
    """Background of the 3D view (RGB): dark grey in the dark theme,
    light grey in the light one."""
    return (0.149, 0.149, 0.149) if theme.is_dark() else \
        (0.941, 0.941, 0.941)


def _flux_lines(run, st):
    """(rho_p, line) of the flux surface layer (on the B2.5 grid)."""
    return [(lv if st.rho else float(np.sqrt(max(lv, 0.0))), ln)
            for lv, ln in shapes.flux_lines(run, st)]


def _inward(plot, seg):
    """Unit normals (n, 2) of the wall elements towards the plasma: the
    side of the B2.5 grid (else of the EIRENE grid, else of the middle of
    the B2.5 grid)."""
    a, b = seg[:, :2], seg[:, 2:]
    t = b - a
    n = np.column_stack((t[:, 1], -t[:, 0]))
    n /= np.maximum(np.hypot(*n.T), 1e-300)[:, None]
    mid = 0.5 * (a + b)
    eps = 1e-3 * max(float(np.ptp(seg[:, [0, 2]])), 1e-3)
    g = plot.run.geometry
    side = np.zeros(len(seg))
    for find in (g.finder, plot.efinder):
        if find is None:
            continue
        for sign in (1.0, -1.0):
            p = mid + sign * eps * n
            hit = (np.asarray(find(p[:, 0], p[:, 1])) >= 0) & (side == 0)
            side[hit] = sign
    centre = np.mean(g.centres, axis=0)
    rest = side == 0
    side[rest] = np.where(np.sum((centre - mid[rest]) * n[rest], 1) >= 0,
                          1.0, -1.0)
    return n * side[:, None]


def _lifts(seg, normals, struct, extra):
    """How far each element (n, 4) is moved along its normal (towards the
    plasma) to lie over the structure: past the structure outline crossed
    within one element length in front of it (at a tenth, the middle and
    nine tenths of it), and by extra times its length more."""
    a0, b0 = seg[:, :2], seg[:, 2:]
    length = np.hypot(*(b0 - a0).T)
    lift = extra * length
    struct = np.asarray(struct, float).reshape(-1, 4)
    if not len(struct):
        return lift
    a, e = struct[:, :2], struct[:, 2:] - struct[:, :2]
    small = 1e-12 * np.hypot(*e.T)[None, :]
    for f in (0.1, 0.5, 0.9):
        p = a0 + f * (b0 - a0)
        for k in range(0, len(seg), 256):
            d, q, h = normals[k:k + 256], p[k:k + 256], length[k:k + 256]
            den = d[:, :1] * e[None, :, 1] - d[:, 1:] * e[None, :, 0]
            w = a[None] - q[:, None]
            ok = np.abs(den) > small
            den = np.where(ok, den, 1.0)
            t = (w[..., 0] * e[None, :, 1] - w[..., 1] * e[None, :, 0]) / den
            u = (w[..., 0] * d[:, 1:] - w[..., 1] * d[:, :1]) / den
            hit = ok & (t > 0) & (t <= h[:, None]) & (u >= 0) & (u <= 1)
            front = np.where(hit, t, 0.0).max(axis=1)
            lift[k:k + 256] = np.maximum(lift[k:k + 256],
                                         front + extra * h)
    return lift


def _borders(plot, loops):
    """The boundary loops [(points (n, 2), values (n,))] of the plasma
    quantity (the outer border, the core boundary or the flux surfaces of
    the band of rho_p, ...) lifted over the structure as the wall
    quantity."""
    struct = structure(plot.run)
    out = []
    for loop, vals in loops:
        seg = np.hstack((loop[:-1], loop[1:]))
        n = _inward(plot, seg)
        d = n * _lifts(seg, n, struct, WALL_LIFT)[:, None]
        move = np.zeros_like(loop)      # each node: the mean of its two
        move[:-1] += d                  # elements
        move[1:] += d
        move[1:-1] /= 2.0
        if np.allclose(loop[0], loop[-1]):  # closed: the joint too
            move[0] = move[-1] = 0.5 * (d[0] + d[-1])
        out.append((loop + move, vals))
    return out


def _rho_of(run, line):
    """rho_p of a line (the median along it), nan without rzpsi.dat."""
    m = run.psimap
    if m is None:
        return float("nan")
    v = np.asarray(m.rhop(line[:, 0], line[:, 1]), float)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


class Data3D(QtCore.QObject):
    """Snapshots of the 2D tab for the 3D view; the toroidal component of
    a vector quantity asked for with request (role "view3d") and answered
    in deliver; changed: a new snapshot can be taken."""

    request = Signal(object)
    changed = Signal()
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.q = self.source = None
        self.comp_q = self.comp = None
        self.ratio_q = self.ratio = None
        self._machine = None            # (key, parts) of the run
        self._field = None              # (key, Field)

    def reset(self):
        self.q = self.comp = self.comp_q = self.ratio = self.ratio_q = None
        self._machine = self._field = None

    # ---------------------------------------------------------- vectors
    def want(self, tab):
        """Ask for the component the toroidal one needs, if the vector
        quantity or its frames changed. True if it is here."""
        q = tab.vector_wanted
        if q is None or tab.vector_data is None:
            self.q = None
            return True
        source = tab._source(q)
        if self.q is not None and (q.poloidal, q.radial, source) == (
                self.q.poloidal, self.q.radial, self.source):
            return self._ready()
        self.q, self.source = q, source
        how = v3.rule(q)
        self.comp = self.comp_q = None
        if how != v3.NONE:
            per = (q.per[0],) if q.per else ()
            self.comp_q = Quantity(
                v3.component_tokens(q, how), "Component", q.group,
                "eirene" if how == v3.DATA else "matrix", movie=q.movie,
                per=per)
            self.request.emit(("view3d", self.comp_q, (), source))
        if q.source == "vector" and self.ratio is None and \
                self.ratio_q is None:
            self.ratio_q = Quantity(v3.RATIO, "B_tor/B_pol", q.group,
                                    "matrix")
            self.request.emit(("view3d", self.ratio_q, (), None))
        return self._ready()

    def _ready(self):
        if self.q is None:
            return True
        if self.comp_q is not None and self.comp is None:
            return False
        return self.q.source != "vector" or self.ratio is not None

    def deliver(self, q, data):
        if q is not self.comp_q and q is not self.ratio_q:
            return
        if data is None:            # the tracers without toroidal part
            self.status.emit("3D view: b2plot returned no data for %s; "
                             "no toroidal component" % q.name)
            if q is self.ratio_q:
                self.ratio_q, self.ratio = None, False
            else:
                self.comp_q = None
            if self._ready():
                self.changed.emit()
            return
        if q is self.ratio_q:
            self.ratio = data
        else:
            self.comp = data
        if self._ready():
            self.changed.emit()

    # --------------------------------------------------------- snapshot
    def snapshot(self, tab):
        """The Snapshot of what the 2D tab shows."""
        plot, run = tab.plot, tab.run
        s = Snapshot()
        import matplotlib.colors as mc
        s.background = background()
        st = plot.layer_styles
        s.layers = {k: {"visible": bool(v.visible),
                        "color": mc.to_rgb(v.color), "width": float(v.width),
                        "ring": float(getattr(v, "ring", 2.0))}
                    for k, v in st.items()}
        layer_key = tuple(sorted((k, v["visible"], v["color"], v["width"],
                                  v["ring"]) for k, v in s.layers.items()))
        self._geometry(run, plot, s)
        s.machine_key = (id(run), layer_key)
        self._plasma(tab, s)
        s.flux_key = (id(run), layer_key, s.plasma_key,
                      st["flux"].levels, st["flux"].rho)
        self._wall(tab, s)
        self._vector(tab, s)
        if s.vector is not None:        # the lines tracers may be born on
            drawn = tuple(map(tuple, tab.quantity.streams.seeds))
            s.lines = {k: births.lines(tab.run, k, drawn)
                       for k in births.LINES}
            s.vector_key = s.vector_key + (drawn,)
        self._chords(tab, s)
        s.magnetic, s.magnetic_key = self._magnetic(tab)
        return s

    @staticmethod
    def _magnetic(tab):
        """The field line of the 3D view (tools/fieldtool), the directions
        (their layer shown): a dict and its key."""
        run, plot = tab.run, tab.plot
        line = tab.tools.fieldline.for_3d()
        st = plot.layer_styles["directions"]
        d = fieldlines.directions(run) if st.visible else None
        out = dict(line=line, directions=d, dstyle=st)
        key = (id(run), None if line is None else (id(line[0]),) + tuple(
            line[1:3]) + (line[3],), repr(st), d is not None)
        return out, key

    @staticmethod
    def _chords(tab, s):
        """The chords while their section is open: their ends (R, Z,
        toroidal angle in degrees) and looks."""
        tools = tab.tools
        if tools.section != "chords":
            return
        for k, (c, look) in enumerate(zip(tools.chords, tools._looks()), 1):
            r0, z0, f0, r1, z1, f1 = (float(x) for x in c)
            s.chords.append((k, (r0, z0, np.radians(f0)),
                             (r1, z1, np.radians(f1)), tuple(look)))
        s.chords_key = tuple(s.chords)

    def _geometry(self, run, plot, s):
        key = (id(run), tuple((k, v.visible, v.levels if k == "flux" else 0,
                               getattr(v, "rho", 0))
                              for k, v in plot.layer_styles.items()))
        if self._machine is None or self._machine[0] != key:
            self._machine = (key, self._build_geometry(run, plot))
        for k, v in self._machine[1].items():
            setattr(s, k, v)

    def _build_geometry(self, run, plot):
        g = run.geometry
        out = {}
        solids, vessel, walls = [], [], []
        for p in shapes.polylines(structure(run)):
            if shapes.closed(p):
                inside = shapes.Path(p).contains_points(g.centres).mean()
                (vessel if inside >= 0.5 else solids).append(p)
            else:
                walls.append(p)
        t = run.trimesh
        if t is not None:
            outer = revolve.outer_loop(revolve.boundary_edges(
                np.asarray(t.x), np.asarray(t.y), t.triangles))
        else:
            outer = revolve.outer_loop(revolve.boundary_edges(
                plot.tri.x, plot.tri.y, plot.tri.triangles))
        out["outer"] = [outer] if outer is not None else []
        size = float(np.ptp(g.vx, axis=0).max()) if len(g.vx) else 1.0
        if outer is not None:
            vessel = [p for p in vessel if np.median(
                revolve.distance(p, outer)) > 0.005 * size]
        out.update(solids=solids, vessel=vessel, walls=walls, size=size,
                   centre=tuple(np.mean(g.centres, axis=0)),
                   box=tuple(plot.full_box()))
        sep = run.layers.get("separatrices")
        out["separatrices"] = [(_rho_of(run, p), p) for p in
                               revolve.chains(sep)] \
            if sep is not None and len(sep) else []
        tseg = [v for k, v in run.layers.items() if k.startswith("target: ")]
        out["targets"] = None
        if tseg:                        # over the structure, under the wall
            tseg = np.vstack(tseg).reshape(-1, 4)       # quantity
            n = _inward(plot, tseg)
            out["targets"] = (tseg, n, _lifts(tseg, n, structure(run),
                                              TARGET_LIFT))
        out["midplanes"] = run.layers.get("midplanes")
        out["xpoints"] = [tuple(p) for p in np.asarray(
            g.xpoints, float).reshape(-1, 2)]
        out["opoints"] = [tuple(np.asarray(run.psimap.opoint, float))] \
            if run.psimap is not None else []
        st = plot.layer_styles
        out["grid"] = out["eirene"] = None  # the grids: not in 3D
        out["flux"] = _flux_lines(run, st["flux"]) if \
            st["flux"].visible and run.psimap is not None else []
        return out

    def _plasma(self, tab, s):
        """The plasma quantity at the nodes of the cells (or triangles)
        shown, interpolated linearly between them, in the colours of the
        2D plot, cut to the band of rho_p of the 3D view options."""
        plot = tab.plot
        f, st = plot.data, plot.style
        if f is None or st is None or st.mask:
            return
        col = plot._column(f, st)
        g = plot.run.geometry
        if f.location == "cells":
            tri = plot._cell_tri(plot.mask)
            cells = np.asarray(f.values[col], float)
            shown = cells[g.cells[np.flatnonzero(plot.mask)] - 1]
            nodes = np.asarray(f.vertex[col], float) if f.vertex is not \
                None else node_values(tri, cells[g.cells[g.tri_cell] - 1])
            finder = g.trifinder(tri)
        else:
            tri = plot.etri
            shown = np.asarray(f.values[col], float)
            nodes = node_values(plot.run.trimesh, shown)
            finder = tri.get_trifinder()
        norm = norm_for(shown, st)
        cmap = cmap_for(st, norm)
        log = st.scale == "log"
        if log:
            nodes = np.where(nodes > 0, nodes, np.nan)
        ok = np.isfinite(nodes)
        interp = mtri.LinearTriInterpolator(tri, np.where(ok, nodes, 0.0),
                                            trifinder=finder)
        bad = mtri.LinearTriInterpolator(tri, (~ok).astype(float),
                                         trifinder=finder)

        def at(r, z):
            r, z = np.asarray(r, float), np.asarray(z, float)
            v = np.ma.filled(interp(r, z).astype(float), np.nan)
            return np.where(np.ma.filled(bad(r, z), 1.0) > 0.0, np.nan, v)
        from . import meshes            # PyVista only with the 3D view
        band = tab.mode3d.rho_band()
        rho = None
        if band is not None:
            rho = np.asarray(plot.run.psimap.rhop(tri.x, tri.y), float)
            rho = np.where(np.isfinite(rho), rho, np.nanmin(rho))
        flat = meshes.plane(np.column_stack((tri.x, tri.y)),
                            tri.get_masked_triangles(), nodes, rho, band)
        s.plasma = dict(plane=flat, borders=_borders(
                            plot, meshes.boundary(flat)),
                        cmap=cmap, clim=(float(norm.vmin), float(norm.vmax)),
                        log=log, at=at, label=labels.any_to_plain(
                            f.label or f.name or ""))
        s.plasma_key = (id(f), repr(st), hash(plot.mask.tobytes()), band)

    def _wall(self, tab, s):
        import matplotlib.colors as mc
        pair = tab._wall_pair()
        if pair is None:
            return
        data, o, label = pair
        seg = data.segments if getattr(data, "segments", None) is not None \
            else tab.run.layers.get("wall", np.zeros((0, 4)))
        last = len(data.columns) - 1        # the sum of the columns chosen
        v = sum(np.asarray(data.values[min(max(c, 0), last)], float)
                for c in o.columns or (0,))[:len(seg)]
        if o.scale == "log":
            v = np.where(v > 0, v, np.nan)
        if not len(v) or not np.isfinite(v).any():
            return
        seg = np.asarray(seg, float).reshape(-1, 4)[:len(v)]
        colours = tab.wall_profile.mark_colours()   # midplanes, strike
        sep = mc.to_rgb(tab.plot.layer_styles["separatrices"].color)
        points = [(p, mc.to_rgb(colours[n]) if n in colours else sep)
                  for _, n, p, _ in marks(tab.run, seg)] if \
            tab.wall_profile.show_marks() else []       # points
        if getattr(o, "smooth", False) and len(v) > 1:  # as in 2D
            seg, v = smoothed_strip(seg, v)
        pst = replace(PlotStyle(), cmap=o.cmap, reverse=o.reverse,
                      scale=o.scale, auto=o.auto, vmin=o.vmin, vmax=o.vmax)
        norm = norm_for(v, pst)
        n = _inward(tab.plot, seg)
        s.wall = dict(segments=seg, normals=n, lifts=_lifts(
            seg, n, structure(tab.run), WALL_LIFT), values=v,
                      cmap=cmap_for(pst, norm),
                      clim=(float(norm.vmin), float(norm.vmax)),
                      log=o.scale == "log",
                      label=labels.any_to_plain(data.label or label or ""),
                      marks=points)
        s.wall_key = (id(data), repr(o), tuple(
            sorted(s.layers["separatrices"].items())), tuple(
                sorted(colours.items())), len(points))

    def _vector(self, tab, s):
        if tab.vector_wanted is None or tab.vector_data is None or \
                self.q is None or not self._ready():
            return
        args = tab._vector_args()
        if args is None:
            return
        v, col = tab.summed_vector(tab.vector_data)
        style = tab.quantity.vector_style(col)
        mask = tab.plot.vector_mask
        key = (id(tab.vector_data), col, tab.quantity.vector_species.text(),
               id(self.comp), id(self.ratio),
               None if mask is None else hash(mask.tobytes()))
        if self._field is None or self._field[0] != key:
            self._field = (key, self._grid(tab, v, col))
            if self._field[1] is None:
                self.status.emit("3D view: %s is zero everywhere, no "
                                 "tracers" % self.q.name)
        f = self._field[1]
        if f is None:
            return
        unit = split_unit(self.q.description)[1] or ""
        name = labels.any_to_plain(split_unit(self.q.description)[0])
        s.vector = dict(field=f, cmap=cmap_for(style),
                        range=None if style.auto else (style.vmin,
                                                       style.vmax),
                        log=style.scale == "log",   # the colour scale
                        label="Tracers: " + name + (
                            " (%s)" % labels.any_to_plain(unit) if unit
                            else ""))
        s.vector_key = (key, style.cmap, style.reverse, style.bw,
                        style.auto, style.vmin, style.vmax, style.scale)

    def _grid(self, tab, v, col):
        """The vector with its toroidal component, gridded in (R, Z); the
        toroidal component along the angle of the 3D view (anticlockwise
        seen from above), the opposite of that of B2.5 and EIRENE."""
        plot = tab.plot
        pos, u, w, tri, nu, nw = plot._vector_data(v, col)
        how = v3.rule(self.q)
        g = plot.run.geometry

        def nodes(values, vertex):
            if v.location == "triangles":
                return node_values(plot.run.trimesh, values)
            return vertex if vertex is not None else node_values(
                tri, values[g.cells[g.tri_cell] - 1])
        ratio = self.ratio if self.ratio is not False else None
        if how == v3.NONE or self.comp is None or how != v3.DATA and \
                ratio is None:
            nt = np.zeros_like(nu)
        else:
            cols = list(tab._columns(self.comp,
                                     tab.quantity.vector_species))
            vals = np.asarray(self.comp.values, float)[cols].sum(0)
            vert = None if self.comp.vertex is None else np.asarray(
                self.comp.vertex, float)[cols].sum(0)
            nt = nodes(vals, vert)
            if how != v3.DATA:
                r = np.asarray(ratio.values, float)[0]
                rv = None if ratio.vertex is None else np.asarray(
                    ratio.vertex, float)[0]
                nt = v3.toroidal(how, nt, nodes(r, rv))
            nt = -nt        # B2.5 and EIRENE: clockwise seen from above
        box = (float(pos[:, 0].min()), float(pos[:, 0].max()),
               float(pos[:, 1].min()), float(pos[:, 1].max()))
        xs, ys, fields = v3.resample(tri, (nu, nw, nt), box)
        f = Field(xs, ys, fields)
        return f if f.valid and np.isfinite(f.v98) and f.v98 > 0 else None

