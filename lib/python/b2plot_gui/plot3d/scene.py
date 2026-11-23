"""The scene of the 3D view on a PyVista plotter, from a Snapshot of what
the 2D tab shows (plot3d/data): the machine (the closed parts of the
structure as opaque solids with their cut faces and outlines, the outer
boundary of the grid as a transparent vessel, walls, targets, rings at the
X- and O-points, grids and midplanes on the cut faces), the plasma quantity
on the cut faces, the separatrices and flux surfaces as transparent shells
painted with the plasma quantity along them, with their lines on the cut
faces, the wall quantity on the wall elements turned around the axis, the
vector quantity as tracers, the chords. Each actor belongs to a group
whose opacity multiplies its own; a part is built again only when its data
or the sector change."""

import textwrap

import numpy as np

import pyvista as pv

from . import GROUPS, meshes
from ..tools import revolve
from ..tools import births
from ..tools.tracers import FADE, Tracers

STRUCTURE = (0.62, 0.64, 0.68)
CAP = (0.50, 0.52, 0.56)
VESSEL = (0.70, 0.74, 0.80)
PLANE_OFFSET = np.radians(0.035)        # cut planes just outside the sector
LINE_OFFSET = np.radians(0.055)         # lines on them, over the quantity
FLUX_WIDTH, SEP_WIDTH = 1.85, 3.0       # their widths (pixels)
SHELL_RHO = (0.2, 0.4, 0.6, 0.8, 1.0, 1.015, 1.03, 1.045, 1.06, 1.075,
             1.09, 1.105)               # shell opacity against rho_p
SHELL_OPACITY = (0.40, 0.36, 0.32, 0.28, 0.24, 0.22, 0.20, 0.18, 0.16,
                 0.14, 0.12, 0.10)
PICKED = ("m:solids", "m:caps", "m:walls", "m:targets", "p:", "w:")
#                                 the opaque parts the view turns around
BAR_PIXELS = 96                 # width of a colour bar with its labels
BAR_TITLE = 13                  # characters per line of its title


def _offset(actor, factor=-3.0, units=-6.0):
    """Drawn over coincident surfaces (cut planes, lines on them)."""
    m = actor.GetMapper()
    m.SetRelativeCoincidentTopologyPolygonOffsetParameters(factor, units)
    m.SetRelativeCoincidentTopologyLineOffsetParameters(factor, units)


class Scene3D:
    """The actors of the scene on plotter, in their groups."""

    def __init__(self, plotter):
        self.pl = plotter
        self.actors = {}                # name -> (actor, group, opacity)
        self.bars = {}                  # name -> title of its colour bar
        self.factor = {g: 1.0 for g in GROUPS}
        self.keys = {}                  # part -> what it was built from
        self.sector = (0.0, np.pi)
        self.smooth = True
        self.text = (0.0, 0.0, 0.0)     # colour of the bar texts
        self.tracers = None
        self.tracer_opts = dict(n=5000, tail=10, size=1.5, speed=1.0,
                                log=True, born="quantity", fade=True)
        self.rng = np.random.default_rng(7)
        self.snap = None
        self.zcut = (None, None)        # heights kept (vertical cut)

    # ----------------------------------------------------------- actors
    def add(self, name, mesh, group, opacity=1.0, offset=False, **kw):
        self.remove(name)
        if self.zcut != (None, None) and group != "Tracers" and \
                not name.startswith("h:"):  # the vertical cut (not on it)
            mesh = meshes.zclip(mesh, *self.zcut)
        if mesh is None or mesh.n_points == 0:
            return None
        kw.setdefault("pickable", name.startswith(PICKED))
        kw.setdefault("show_scalar_bar", False)
        a = self.pl.add_mesh(mesh, name=name, opacity=opacity *
                             self.factor[group], render=False, **kw)
        if offset:
            _offset(a)
        bar = kw.get("scalar_bar_args") if kw["show_scalar_bar"] else None
        if bar is not None:
            self.bars[name] = bar["title"]
            b = self.pl.scalar_bars[bar["title"]]
            b.SetBarRatio(0.25)
            b.SetTextPositionToPrecedeScalarBar()   # labels inside
        self.actors[name] = (a, group, opacity)
        return a

    def remove(self, name):
        if name in self.actors:
            self.pl.remove_actor(self.actors.pop(name)[0], render=False)
        title = self.bars.pop(name, None)   # else kept for the next one
        if title is not None and title in self.pl.scalar_bars:
            self.pl.remove_scalar_bar(title, render=False)

    def remove_part(self, prefix):
        for name in [n for n in self.actors if n.startswith(prefix)]:
            self.remove(name)

    def set_factor(self, group, f):
        """The opacity of a group (0 to 1), multiplying each actor's."""
        self.factor[group] = f
        for a, g, base in self.actors.values():
            if g == group:
                a.GetProperty().SetOpacity(base * f)

    def bar(self, title):
        """The colour bar of the quantity shown, at the right."""
        w = min(0.3, BAR_PIXELS / max(self.pl.window_size[0], 1))
        return dict(title=textwrap.fill(title, BAR_TITLE), vertical=True,
                    n_labels=5, fmt="%.3g", position_x=0.99 - w,
                    position_y=0.08, width=w, height=0.80, color=self.text,
                    title_font_size=11, label_font_size=11,
                    unconstrained_font_size=True)

    # ------------------------------------------------------------ build
    def update(self, snap, sector=None, zcut=None):
        """Build the parts that changed since the last update (all of
        them for another sector or vertical cut)."""
        if sector is not None and sector != self.sector:
            self.sector, self.keys = sector, {}
        if zcut is not None and tuple(zcut) != self.zcut:
            self.zcut, self.keys = tuple(zcut), {}
        self.snap = snap
        p0, p1 = self.sector
        for part, key, build in (
                ("machine", snap.machine_key, self._machine),
                ("plasma", snap.plasma_key, self._plasma),
                ("flux", snap.flux_key, self._flux),
                ("cut", (snap.machine_key, snap.plasma_key, snap.flux_key),
                 self._cut),
                ("wall", snap.wall_key, self._wall),
                ("vector", snap.vector_key, self._vector),
                ("chords", snap.chords_key, self._chords)):
            if self.keys.get(part) != key:
                self.keys[part] = key
                build(snap, p0, p1)

    def _ends(self, p0, p1):
        return (p0,) if revolve.full(p0, p1) else (p0, p1)

    def _planes(self, p0, p1, offset=PLANE_OFFSET):
        """The planes of the plasma quantity and of the grids on the cut
        faces (offset: of the flux surface lines, over them): just outside
        the sector, over the end caps."""
        if revolve.full(p0, p1):
            return (p0 - offset,)
        return (p0 - offset, p1 + offset)

    def _machine(self, s, p0, p1):
        self.remove_part("m:")
        lay = s.layers
        ends = self._ends(p0, p1)
        spec = dict(smooth_shading=self.smooth, split_sharp_edges=True,
                    specular=0.6, specular_power=18.0, ambient=0.2,
                    diffuse=0.8)
        vessel = [revolve.offset(p, 0.004 * s.size) for p in s.outer] + \
            s.vessel
        self.add("m:vessel", meshes.surface(vessel, p0, p1, closed=True),
                 "Vessel", 0.2, color=VESSEL, **spec)
        self.add("m:vessel_out", meshes.outlines(vessel, ends), "Vessel",
                 0.55, color="black", line_width=0.8)
        if lay["structure"]["visible"]:
            self.add("m:solids", meshes.surface(s.solids, p0, p1,
                                                closed=True),
                     "Structure", 1.0, color=STRUCTURE, **spec)
            if not revolve.full(p0, p1):
                self.add("m:caps", meshes.caps(s.solids, ends), "Structure",
                         0.98, color=CAP, lighting=False, offset=True)
                self.add("m:cut", meshes.outlines(s.solids, ends),
                         "Structure", 0.55, color="black", line_width=1.0,
                         offset=True)
            self.add("m:walls", meshes.surface(s.walls, p0, p1),
                     "Structure", 1.0, color=STRUCTURE, **spec)
        if lay["targets"]["visible"] and s.targets is not None:
            self.add("m:targets", meshes.wall_strip(s.targets[0], None, p0,
                                                    p1, *s.targets[1:]),
                     "Structure", 1.0, color=lay["targets"]["color"],
                     **spec)
        for key in ("xpoints", "opoints"):
            if lay[key]["visible"]:
                for k, (r, z) in enumerate(getattr(s, key)):
                    self.add("m:%s%d" % (key, k), meshes.ring(r, z, p0, p1),
                             "Structure", 1.0, color=lay[key]["color"],
                             line_width=3.0, render_lines_as_tubes=True)
        for key in ("midplanes", "grid", "eirene"):
            seg = getattr(s, key)
            if lay[key]["visible"] and seg is not None and len(seg):
                self.add("m:" + key, meshes.segments(seg, self._planes(
                    p0, p1)), "Structure", 0.9 if key == "midplanes" else
                    0.15,
                         color=lay[key]["color"],
                         line_width=1.5 if key == "midplanes" else 0.5,
                         offset=True)

    def _flux(self, s, p0, p1):
        """Separatrices and flux surfaces: their lines on the cut faces
        (each in the colour of the median of the plasma quantity along it,
        else in the colour of its layer) and transparent shells (the
        plasma quantity along them, else in the colour of the flux
        surfaces; opacity by rho_p, no
        shell for the outermost flux surface or a separatrix on one)."""
        self.remove_part("f:")
        lay = s.layers
        q = s.plasma
        planes = self._planes(p0, p1, LINE_OFFSET)
        shown = [rho for rho, _ in s.flux] if lay["flux"]["visible"] else []
        outer = max(shown) if shown else None
        spec = dict(smooth_shading=self.smooth, specular=0.6,
                    specular_power=18.0, ambient=0.2, diffuse=0.8)
        for key, lines, width in (("separatrices", s.separatrices, SEP_WIDTH),
                                  ("flux", s.flux, FLUX_WIDTH)):
            if not lay[key]["visible"] or not lines:
                continue
            values = [q["at"](ln[:, 0], ln[:, 1]) if q else None
                      for _, ln in lines]
            med = [float(np.median(v[np.isfinite(v)])) if v is not None and
                   np.isfinite(v).any() else np.nan for v in values]
            for coloured in (True, False):
                part = [ln for (_, ln), m in zip(lines, med)
                        if np.isfinite(m) == coloured]
                mesh = meshes.outlines(part, planes, closed=False)
                if mesh is None:
                    continue
                if coloured:
                    mesh.cell_data["values"] = np.repeat(
                        [m for m in med if np.isfinite(m)], len(planes))
                    kw = dict(scalars="values", cmap=q["cmap"],
                              clim=q["clim"], log_scale=q["log"])
                else:
                    kw = dict(color=lay[key]["color"])
                self.add("f:%s_lines%d" % (key, coloured), mesh,
                         "Flux surfaces", 1.0, line_width=width,
                         offset=True, **kw)
            for k, ((rho, ln), v) in enumerate(zip(lines, values)):
                if key == "flux" and abs(rho - outer) < 1e-10 or \
                        key == "separatrices" and any(
                            abs(f - rho) <= 1e-4 for f in shown) or \
                        np.hypot(*np.diff(ln, axis=0).T).sum() <= 0.04:
                    continue
                op = float(np.interp(rho, SHELL_RHO, SHELL_OPACITY)) if \
                    np.isfinite(rho) else SHELL_OPACITY[-1]
                if q is not None:
                    self.add("f:%s%d" % (key, k),
                             meshes.shell(ln, v, p0, p1), "Flux surfaces",
                             op, scalars="values", cmap=q["cmap"],
                             clim=q["clim"], log_scale=q["log"],
                             nan_opacity=0.0, **spec)
                else:
                    self.add("f:%s%d" % (key, k),
                             meshes.surface([ln], p0, p1), "Flux surfaces",
                             op, color=lay["flux"]["color"], **spec)

    def _plasma(self, s, p0, p1):
        """The plasma quantity on the cut faces, just outside the sector,
        interpolated between the nodes, unlit, and on its borders (outer,
        core boundary, the flux surfaces of its band of rho_p) turned
        around the axis; opaque (no value: the background)."""
        self.remove_part("p:")
        q = s.plasma
        if q is None:
            return
        kw = dict(scalars="values", cmap=q["cmap"], clim=q["clim"],
                  log_scale=q["log"], nan_color=s.background)
        for k, phi in enumerate(self._planes(p0, p1)):
            self.add("p:%d" % k, meshes.field(q["plane"], phi),
                     "Plasma quantity", 1.0, lighting=False,
                     smooth_shading=False, offset=True,
                     show_scalar_bar=k == 0,
                     scalar_bar_args=self.bar(q["label"]), **kw)
        for k, border in enumerate(q["borders"]):
            self.add("p:border%d" % k, meshes.shell(*border, p0, p1),
                     "Plasma quantity", 1.0, smooth_shading=self.smooth,
                     specular=0.6, specular_power=18.0, ambient=0.2,
                     diffuse=0.8, **kw)

    def _cut(self, s, p0, p1):
        """On each height of the vertical cut: the closed parts of the
        structure filled where it cuts them, the plasma quantity (its
        values along the cut, turned around the axis), the separatrices
        and flux surfaces crossing it as arcs in the colours of their
        lines."""
        self.remove_part("h:")
        lay, q = s.layers, s.plasma
        for k, z in enumerate(h for h in self.zcut if h is not None):
            name = "h:%d:" % k
            if lay["structure"]["visible"]:
                rings = []
                for p in s.solids:
                    r = np.sort(meshes.crossings(np.vstack((p, p[:1])), z))
                    rings += [(a, b, 0.0, 0.0) for a, b in
                              zip(r[0::2], r[1::2])]
                self.add(name + "caps", meshes.annuli(rings, z, p0, p1),
                         "Structure", 0.98, color=CAP, lighting=False,
                         offset=True)
            if q is not None:
                cut = q["plane"].slice(normal="y", origin=(0.0, z, 0.0))
                if cut.n_cells:
                    ends = cut.lines.reshape(-1, 3)[:, 1:]
                    r, v = cut.points[:, 0], cut.point_data["values"]
                    rings = [(r[a], r[b], v[a], v[b]) for a, b in ends]
                    self.add(name + "plasma", meshes.annuli(rings, z, p0, p1),
                             "Plasma quantity", 1.0, scalars="values",
                             cmap=q["cmap"], clim=q["clim"],
                             log_scale=q["log"], nan_color=s.background,
                             lighting=False, offset=True)
            for key, lines, width in (("separatrices", s.separatrices,
                                       SEP_WIDTH), ("flux", s.flux,
                                                    FLUX_WIDTH)):
                if not lay[key]["visible"] or not lines:
                    continue
                radii, values = [], []
                for _, ln in lines:
                    r = meshes.crossings(ln, z)
                    v = q["at"](ln[:, 0], ln[:, 1]) if q else None
                    m = float(np.median(v[np.isfinite(v)])) if v is not \
                        None and np.isfinite(v).any() else np.nan
                    radii += list(r)
                    values += [m] * len(r)
                mesh = meshes.arcs(radii, z, p0, p1)
                if mesh is None:
                    continue
                values = np.asarray(values)
                if q is not None and np.isfinite(values).all():
                    mesh.cell_data["values"] = values
                    kw = dict(scalars="values", cmap=q["cmap"],
                              clim=q["clim"], log_scale=q["log"])
                else:
                    kw = dict(color=lay[key]["color"])
                self.add(name + key, mesh, "Flux surfaces", 1.0,
                         line_width=width, offset=True, **kw)

    def _wall(self, s, p0, p1):
        """The wall quantity on the wall elements turned around the axis,
        just off them towards the plasma, over the structure."""
        self.remove_part("w:")
        q = s.wall
        if q is None:
            return
        a = self.add("w:strip", meshes.wall_strip(
            q["segments"], q["values"], p0, p1, q["normals"], q["lifts"]),
            "Wall quantity", 1.0, scalars="values", cmap=q["cmap"],
            clim=q["clim"], log_scale=q["log"], lighting=False,
            nan_color=STRUCTURE, show_scalar_bar=True,
            scalar_bar_args=self.bar(q["label"]))
        if a is not None:
            _offset(a, -6.0, -60.0)     # wins over the surfaces it lies on

    def _chords(self, s, p0, p1):
        """The chords: straight lines between their ends (an end on a cut
        face moved in front of the plasma quantity there), a ball at the
        start, a cone at the end, the number beyond it."""
        self.remove_part("c:")
        h = 0.025 * s.size
        for k, a, b, (colour, width, _, number) in s.chords:
            ends = []
            for r, z, phi in (a, b):
                if abs(phi - p0) < 1e-9:
                    phi = p0 - 2.0 * PLANE_OFFSET
                elif abs(phi - p1) < 1e-9:
                    phi = p1 + 2.0 * PLANE_OFFSET
                ends.append(np.array(revolve.on_plane([(r, z)], phi)[0]))
            d = ends[1] - ends[0]
            length = float(np.linalg.norm(d))
            if not length > 0:
                continue
            d = d / length
            c = "c:%d:" % k
            self.add(c + "line", meshes.polylines([np.array(ends)]),
                     "Chords", 1.0, color=colour, line_width=2.0 + 2.0 * width,
                     render_lines_as_tubes=True)
            self.add(c + "start", pv.PolyData(ends[0][None]), "Chords", 1.0,
                     color=colour, point_size=8.0 + 3.0 * width,
                     render_points_as_spheres=True)
            self.add(c + "end", pv.Cone(center=ends[1] - 0.5 * h * d,
                                        direction=d, height=h,
                                        radius=0.3 * h, resolution=16),
                     "Chords", 1.0, color=colour)
            if number:
                a = self.pl.add_point_labels(
                    (ends[1] + 0.8 * h * d)[None], ["%d" % k],
                    text_color=colour, font_size=14, show_points=False,
                    shape=None, always_visible=True, name=c + "number",
                    render=False)
                self.actors[c + "number"] = (a, "Chords", 1.0)

    # ---------------------------------------------------------- tracers
    def _vector(self, s, p0, p1):
        self.remove_part("t:")
        self.tracers = None
        v = s.vector
        if v is None or v.get("field") is None:
            return
        o = self.tracer_opts
        f = v["field"]
        self.clim = self._clim(f, v["range"], o["log"])
        lines = s.lines.get(o["born"]) if o["born"] in births.LINES \
            else None
        if o["born"] in births.LINES and not lines:
            return                      # no such line: no tracers
        tr = self.tracers = Tracers(f, int(o["n"]), int(o["tail"]), p0, p1,
                                    self.rng, self.zcut,
                                    births.weight(o["born"]),
                                    FADE if o["fade"] else 0.0, lines,
                                    self.vref(), o["log"])
        tr.warm_up(self.vref(), o["log"])     # no transient on screen
        n, t = tr.n, tr.tail
        idx = (np.arange(t)[None, :] * n + np.arange(n)[:, None])
        cells = np.hstack((np.full((n, 1), t), idx)).ravel()
        self.tails = pv.PolyData(tr.hist.reshape(-1, 3), lines=cells)
        self.tails.point_data["rgb"] = self._tail_colours()
        self.heads = pv.PolyData(tr.hist[0].copy())
        self.heads.point_data["speed"] = np.maximum(tr.mag, 1e-300)
        size = float(o["size"])
        self.add("t:tails", self.tails, "Tracers", 1.0, scalars="rgb",
                 rgb=True, render_lines_as_tubes=True,
                 line_width=2.5 * size)
        self.add("t:heads", self.heads, "Tracers", 1.0, scalars="speed",
                 cmap=v["cmap"], clim=self.clim, log_scale=o["log"],
                 render_points_as_spheres=True, point_size=7.0 * size,
                 show_scalar_bar=True,
                 scalar_bar_args=self.bar(v["label"]))

    def vref(self):
        f = self.snap.vector["field"]
        return float(self.tracer_opts["speed"]) * f.size / 4.0

    @staticmethod
    def _clim(f, given, log):
        """Colour range of the tracers: given, else up to the 98th
        percentile of the speed, from its lowest shown (log) or zero."""
        lo, hi = given if given is not None else (
            f.vmin if log else 0.0, f.v98)
        if log:
            hi = hi if hi > 0 else 1.0
            lo = lo if 0 < lo < hi else hi * 1e-3
        return (float(lo), float(hi) if hi > lo else float(lo) + 1.0)

    def _tail_colours(self):
        v, tr = self.snap.vector, self.tracers
        lo, hi = self.clim
        m = np.clip(np.where(np.isfinite(tr.mag), tr.mag, lo), lo, hi)
        x = np.log(m / lo) / np.log(hi / lo) if self.tracer_opts["log"] \
            else (m - lo) / (hi - lo)
        base = np.asarray(v["cmap"](x))[:, :3]
        c = tr.colors(base, np.asarray(self.snap.background)[:3])
        return (np.clip(c, 0, 1) * 255).astype(np.uint8)

    def step(self, dt):
        """Move the tracers by dt seconds; True if there are any."""
        tr = self.tracers
        if tr is None:
            return False
        tr.step(dt, self.vref(), self.tracer_opts["log"])
        self.tails.points = tr.hist.reshape(-1, 3)
        self.tails.point_data["rgb"] = self._tail_colours()
        self.heads.points = tr.hist[0].copy()
        self.heads.point_data["speed"] = np.maximum(tr.mag, 1e-300)
        return True

    def rebuild_tracers(self):
        if self.snap is not None:
            self.keys.pop("vector", None)
            self.update(self.snap)
