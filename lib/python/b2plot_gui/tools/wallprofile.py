"""The wall quantity plotted in the final state as a function of the
distance along the wall, on the B2.5 wall elements (an EIRENE wall
quantity on those of its elements), with its integral and average over
their area above it: the last section of the quantity column, under the
chords, overlay and statistics sections; its figure has the options of a
line profile, Save plot and Export."""

import numpy as np

from ...b2plot import labels
from ...qt import QtWidgets, Signal
from .. import catalog, theme
from ..model import split_unit
from ..plot.overlays import wall_segments, wall_values
from ..scaling import squeezable
from . import measure, smooth
from . import splits
from .figure import STACK_ALPHA, FigureView
from .sections import _button, _text

XLABEL = "distance along the wall (m)"
SHADE = ("#808080", 0.15)       # the targets behind the profile
AREA = catalog.Quantity("wallarea", "Wall area (m^{2})", "Geometry", "wall")


def along(seg):
    """Distance along the wall of the middle of each element [(n, 4)
    r1, z1, r2, z2] (as walldist of b2plot: the gaps between elements
    counted) and where an element does not start at the end of the one
    before it."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    length = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    gap = np.hypot(seg[1:, 0] - seg[:-1, 2], seg[1:, 1] - seg[:-1, 3])
    step = 0.5 * (length[1:] + length[:-1]) + gap
    dist = 0.5 * length[:1].sum() + np.concatenate(([0.0], np.cumsum(step)))
    return dist[:len(seg)], np.concatenate(([False], gap > 1e-4 * max(
        float(length.max(initial=0.0)), 1e-12)))[:len(seg)]


def _cross(seg, a, b):
    """Where the segments seg (n, 4) meet the segments from a to b (k, 2
    each): (element index, fraction along it, point)."""
    p, r = seg[:, None, :2], (seg[:, 2:] - seg[:, :2])[:, None, :]
    q, s = a[None, :, :], (b - a)[None, :, :]
    den = r[..., 0] * s[..., 1] - r[..., 1] * s[..., 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        qp = q - p
        t = (qp[..., 0] * s[..., 1] - qp[..., 1] * s[..., 0]) / den
        u = (qp[..., 0] * r[..., 1] - qp[..., 1] * r[..., 0]) / den
    i, j = np.nonzero((np.abs(den) > 1e-14) & (t >= 0) & (t <= 1) &
                      (u >= 0) & (u <= 1))
    return [(k, float(t[k, m]), seg[k, :2] + t[k, m] * (seg[k, 2:] -
                                                       seg[k, :2]))
            for k, m in zip(i, j)]


def marks(run, seg):
    """[(distance along the wall, name, (R, Z), element)] on the wall
    elements seg: the
    inner and outer midplanes (the lines rzimp, rzomp of b2.user.parameters
    on the high and low field side) and, for each X-point, the two strike
    points of its divertor legs (the separatrix on the wall nearest to it
    on the side away from the O-point, one at smaller and one at larger R
    than it)."""
    from . import cellfiles
    seg = np.asarray(seg, float).reshape(-1, 4)
    if not len(seg):
        return []
    x, _ = along(seg)
    length = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    start = x - 0.5 * length

    def where(k, f):
        return float(start[k] + f * length[k])
    out = []
    size = float(np.ptp(seg[:, [0, 2]]) + np.ptp(seg[:, [1, 3]]))
    for name, (p, q) in cellfiles.midplane_points(run.rundir).items():
        p, q = np.asarray(p, float), np.asarray(q, float)
        d = (q - p) / max(np.hypot(*(q - p)), 1e-12)
        hits = _cross(seg, (p - 2 * size * d)[None], (q + 2 * size * d)[None])
        if hits:
            k, f, pt = (min if name == "inner" else max)(
                hits, key=lambda h: h[2][0])
            out.append((where(k, f), "IMP" if name == "inner" else "OMP",
                        tuple(pt), k))
    sep = run.layers.get("separatrices")
    o, xps = _xpoints(run)
    if sep is None or not len(sep) or not xps:
        return sorted(out, key=lambda m: m[0])
    sep = np.asarray(sep, float).reshape(-1, 4)
    for x0, tag in xps:
        legs = _legs(seg, sep, x0, x0 - o, size)
        if len(legs) > 2:               # the two outermost of the legs
            legs = [min(legs, key=lambda c: c[4]),
                    max(legs, key=lambda c: c[4])]
        for c in legs:
            k, f, pt = c[:3]
            name = "ISP" if pt[0] < x0[0] else "OSP"
            out.append((where(k, f), name + tag, tuple(pt), k))
    return sorted(out, key=lambda m: m[0])


def _xpoints(run):
    """(O-point, [(X-point, tag)]): the tag of an X-point its divertor
    (" upper" or " lower" with two divertors) and, with several X-points
    in a divertor, their number there by increasing rho_p."""
    xp = np.asarray(run.geometry.xpoints, float).reshape(-1, 2)
    if run.psimap is not None:
        o = np.asarray(run.psimap.opoint, float)
    else:
        o = run.geometry.centres[np.asarray(run.geometry.region) == 1].mean(0)
    rho = [float(run.psimap.rhop(np.array([x[0]]), np.array([x[1]]))[0])
           if run.psimap is not None else float(k) for k, x in
           enumerate(xp)]
    side = [" upper" if x[1] > o[1] else " lower" for x in xp]
    if len(set(side)) == 1:             # one divertor: no upper, lower
        side = [""] * len(xp)
    count = {t: side.count(t) for t in side}
    seen, out = {}, []
    for i in np.argsort(rho):           # numbered by rho_p in a divertor
        tag = side[i]
        seen[tag] = seen.get(tag, 0) + 1
        out.append((xp[i], tag + (" %d" % seen[tag] if count[tag] > 1
                                  else "")))
    return o, out


def target_names(run):
    """{target layer of b2plot ("target: 1", ...): name}: IL, OL, IU, OU,
    inner or outer (smaller or larger R than the X-point nearest to the
    middle of the target), lower or upper (below or above the O-point);
    numbered (OL 1, OL 2) when a name repeats; without X-points the
    number of the layer."""
    targets = {k: np.asarray(v, float).reshape(-1, 4) for k, v in
               run.layers.items() if k.startswith("target: ") and
               v is not None and len(v)}
    if not targets or not len(run.geometry.xpoints):
        return {k: k[len("target: "):] for k in targets}
    o, xps = _xpoints(run)
    names = {}
    for k, t in targets.items():
        c = 0.5 * (t[:, :2] + t[:, 2:]).mean(0)
        x0 = min(xps, key=lambda p: np.hypot(*(p[0] - c)))[0]
        names[k] = ("I" if c[0] < x0[0] else "O") + \
            ("U" if c[1] > o[1] else "L")
    count, seen = {}, {}
    for n in names.values():
        count[n] = count.get(n, 0) + 1
    for k in sorted(names, key=lambda k: targets[k][:, 0].mean()):
        n = names[k]
        if count[n] > 1:
            seen[n] = seen.get(n, 0) + 1
            names[k] = "%s %d" % (n, seen[n])
    return names


def target_spans(run, seg):
    """[(start, end, name)] along the wall of the elements seg on each
    target (its name of target_names), one per piece of the wall."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    names = target_names(run)
    if not len(seg) or not names:
        return []
    x, _ = along(seg)
    half = 0.5 * np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    mid = 0.5 * (seg[:, :2] + seg[:, 2:])
    tol = 1e-4 * float(np.ptp(seg[:, [0, 2]]) + np.ptp(seg[:, [1, 3]]))
    out = []
    for key, name in names.items():
        t = np.asarray(run.layers[key], float).reshape(-1, 4)
        tm = 0.5 * (t[:, :2] + t[:, 2:])
        d = np.hypot(mid[:, None, 0] - tm[None, :, 0],
                     mid[:, None, 1] - tm[None, :, 1]).min(1)
        on = np.flatnonzero(d < tol)
        for p in np.split(on, np.flatnonzero(np.diff(on) > 1) + 1):
            if len(p):
                out.append((float(x[p[0]] - half[p[0]]),
                            float(x[p[-1]] + half[p[-1]]), name))
    return out


def _stack(ax, x, parts):
    """The parts [(name, label, values)] on x stacked, positive values
    upwards from zero and negative ones downwards, the parts with negative
    values first (nearest to zero): a band each (in the colours of the
    parts of the vector splits at first) with a thin edge, broken where
    the part changes sign, the line of its row of options (the band in
    the colour of the row); the edge lines."""
    from ..plot.vector import split_colour
    up, down, out = np.zeros_like(x), np.zeros_like(x), []

    def negative(k):
        v = np.nan_to_num(parts[k][2])
        return bool((v < -1e-6 * np.abs(v).max(initial=0.0)).any())
    for k in sorted(range(len(parts)), key=lambda k: not negative(k)):
        name, label, v = parts[k]
        v = np.where(np.isfinite(x), np.nan_to_num(v), np.nan)
        top, bottom = up + np.maximum(v, 0.0), down + np.minimum(v, 0.0)
        colour = split_colour(k, name)
        edge = np.where(v > 0, top, np.where(v < 0, bottom, np.nan))
        cut = np.flatnonzero(np.sign(v[:-1]) * np.sign(v[1:]) < 0) + 1
        ln, = ax.plot(np.insert(x, cut, np.nan), np.insert(edge, cut, np.nan),
                      color=colour, linewidth=0.5, label=label)
        ln.stacked = True
        for a, b in ((up, top), (down, bottom)):
            band = ax.fill_between(x, a, b, color=colour, alpha=STACK_ALPHA,
                                   linewidth=0, zorder=1.5)
            band.line = ln
        out.append(ln)
        up, down = top, bottom
    return out


LEG_ANGLE = np.radians(120.0)   # a leg leaves the X-point within this
LEG_LENGTH = 0.5                # of away and is shorter (machine sizes)


def _legs(seg, sep, x0, away, size, steps=5000):
    """Where the separatrix of the X-point x0 meets the wall elements seg
    along its branches on the divertor side (leaving x0 within LEG_ANGLE
    of away, from the O-point, and reaching the wall within LEG_LENGTH,
    not round the core): the segments sep (n, 4) of the separatrices
    followed
    from x0, node to node (at a fork the one going on straightest), each
    branch to its first crossing of the wall: [(element, fraction, point,
    length along the branch, angle of the branch from away (its
    direction a hundredth of the size of the machine from x0))], one per
    branch."""
    key = np.round(np.vstack((sep[:, :2], sep[:, 2:])) / (1e-7 * size))
    _, node = np.unique(key, axis=0, return_inverse=True)
    node = node.reshape(2, -1)
    at = {}
    for i, (a, b) in enumerate(zip(node[0], node[1])):
        at.setdefault(a, []).append((i, 0))
        at.setdefault(b, []).append((i, 1))
    out = []
    for tol in (1e-3, 1e-2, 3e-2):  # the branches leaving the X-point
        starts = [(i, e) for i in range(len(sep)) for e in (0, 1)
                  if np.hypot(*(sep[i, 2 * e:2 * e + 2] - x0)) < tol * size]
        if starts:
            break
    for i, e in starts:
        p, q = sep[i, 2 * e:2 * e + 2], sep[i, 2 - 2 * e:4 - 2 * e]
        done, dist, aim = {i}, 0.0, None
        for _ in range(steps):
            if aim is None and np.hypot(*(q - x0)) > 0.01 * size:
                aim = q - x0
            d = 0.02 * (q - p)          # ends on the wall: not missed
            hit = _cross(seg, (p - d)[None], (q + d)[None])
            if hit:
                k, f, pt = min(hit, key=lambda h: np.hypot(*(h[2] - p)))
                v = aim if aim is not None else pt - x0
                angle = np.arctan2(away[0] * v[1] - away[1] * v[0],
                                   np.dot(away, v))
                length = dist + np.hypot(*(pt - p))
                if abs(angle) < LEG_ANGLE and length < LEG_LENGTH * size \
                        and not any(abs(angle - c[4]) < 0.05 for c in out):
                    out.append((k, f, pt, length, angle))
                break
            dist += np.hypot(*(q - p))
            n = node[1 - e][i]          # the far node: go on from it
            nxt = [(j, ej) for j, ej in at.get(n, []) if j not in done]
            if not nxt:
                break
            t = (q - p) / max(np.hypot(*(q - p)), 1e-300)

            def straight(c):
                j, ej = c
                v = sep[j, 2 - 2 * ej:4 - 2 * ej] - sep[j, 2 * ej:2 * ej + 2]
                return -np.dot(v, t) / max(np.hypot(*v), 1e-300)
            i, e = min(nxt, key=straight)
            done.add(i)
            p, q = sep[i, 2 * e:2 * e + 2], sep[i, 2 - 2 * e:4 - 2 * e]
    return out


def toroidal_area(seg):
    """Area of each element turned around the axis (m^2)."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    return np.pi * (seg[:, 0] + seg[:, 2]) * np.hypot(
        seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])


class WallProfile(QtWidgets.QGroupBox):
    """The section: the integral and average with Save plot and Export at
    their right, the figure under them; its Smooth also smooths the
    colours of the wall strip, 2D and 3D (smooth_changed)."""

    smooth_changed = Signal()
    marks_changed = Signal()            # the colour of a mark chosen

    def __init__(self, settings, parent=None):
        super().__init__("Wall profile", parent)
        self.text = _text()
        self.view = FigureView(settings)
        self.was_smooth, self.was_marks = False, {}
        changed = self.view.options.changed

        def options_changed():          # Smooth ticked or not: the strip;
            changed()                   # the colour of a mark: its diamond
            if self.smoothed() != self.was_smooth:
                self.was_smooth = self.smoothed()
                self.smooth_changed.emit()
            if self.mark_colours() != self.was_marks:
                self.was_marks = self.mark_colours()
                self.marks_changed.emit()
        self.view.options.changed = options_changed
        self.view.options.xaxes = False     # the distance along the wall
        self.view.options.keep_limits = True    # limits kept for other rows
        self.quantity = None
        self.key = None
        self.asked = None               # the run asked for the areas
        self.tab, self.asked_parts, self.failed = None, set(), None
        self.split = QtWidgets.QCheckBox("Components")
        self.tip = ("The quantity as its parts stacked along the "
                              "B2.5 wall, positive ones upwards and "
                              "negative ones downwards, the total over "
                              "them: a plasma wall flux as the parts of the "
                              "arrows split into physical components, an "
                              "EIRENE wall flux by the place its neutrals "
                              "were born (the strata, as in the Neutrals "
                              "tab of Balances)")
        self.split.setToolTip(self.tip)
        self.split.toggled.connect(lambda *_: self.tab is not None and
                                   self.follow(self.tab))
        row = QtWidgets.QHBoxLayout()
        self.shown = QtWidgets.QCheckBox("Show midplanes and strikepoints")
        self.shown.setToolTip("The midplanes and strike points: vertical "
                              "lines on the profile, diamonds on the wall "
                              "of the 2D plot and of the 3D view")
        self.shown.toggled.connect(self._shown)
        row.addWidget(self.text, 1)
        row.addWidget(_button("Save plot", "The wall profile as an image or "
                              "vector file", lambda: self.view.save()))
        row.addWidget(_button("Export…", "The wall profile as a CSV file",
                              lambda: self.view.export()))
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addLayout(row)
        boxes = QtWidgets.QHBoxLayout()     # what is drawn
        boxes.addWidget(self.shown)
        boxes.addWidget(self.split)
        boxes.addStretch(1)
        lay.addLayout(boxes)
        lay.addWidget(self.view)
        squeezable(self)

    def follow(self, tab):
        """Shown with the wall quantity plotted in the final state (the
        areas of the B2.5 wall elements asked for once per run; those of
        a field with its own segments turned around the axis)."""
        self.tab = tab
        w, q, run = tab.wall_data, tab.wall_wanted, tab.run
        show = run is not None and w is not None and q is not None and \
            tab.time_box.source.currentIndex() == 0    # Final state
        if show and getattr(w, "segments", None) is None:
            d = run.cache.get(("wfield", AREA.name, (), None))
            if d is None and self.asked is not run:
                self.asked = run
                tab.request.emit(("tools", AREA, (), None))
            area = None if d is None else np.ravel(np.asarray(d.values,
                                                              float)[0])
        elif show:
            area = toroidal_area(w.segments)
        show = show and area is not None and len(area) > 0
        self.setVisible(bool(show))
        if not show:
            return
        cols = tab._wall_pair()[1].columns
        unit = labels.any_to_plain(split_unit(q.description)[1] or
                                   getattr(w, "unit", "") or "")
        name = tab._name_of(q, w)
        seg = wall_segments(run, w)
        colour = tab.plot.layer_styles["separatrices"].color
        values = wall_values(w, cols)
        split = q.name in splits.WALL_SPLITS or q.name in splits.BY_STRATUM
        self.split.setVisible(split)
        if q.name in splits.BY_STRATUM:     # the strata need balance.nc
            o = tab.balance.neutrals.get()
            split = o is not None and not o.why
        self.split.setEnabled(split)
        self.split.setToolTip(self.tip if split else
                              "Needs the balance.nc of the state with the "
                              "EIRENE tallies by stratum (for the strata of "
                              "each birth place)")
        parts = self._parts(tab, q, w, cols, values) if \
            self.split.isChecked() and split else None
        near = np.asarray(seg, float)[:len(area)]
        quantity = (q.name, tuple(cols))    # another: y limits automatic
        if quantity != self.quantity:
            self.quantity = quantity
            for e in self.view.options.limits[2:]:
                e.clear()
        self.show_profile((id(run), id(w), name, len(area), colour,
                           quantity, parts is not None,
                           self.shown.isChecked()), name,
                          unit, values, seg, area, q.name,
                          [m[:2] for m in marks(run, near)] if
                          self.shown.isChecked() else [], colour, parts,
                          target_spans(run, near))

    @staticmethod
    def _wanted(tab, q):
        """[(name, label, b2plot fields summed, sign)] of the parts of q:
        the wall fluxes of WALL_SPLITS, or for an EIRENE wall quantity
        the birth places of the Neutrals tab, each the sum of its strata
        (wstrat); None without those (no balance.nc of the state)."""
        run = tab.run
        if q.name in splits.WALL_SPLITS:
            return [(n, splits.wall_label(run, n), [n.lstrip("-")],
                     -1.0 if n.startswith("-") else 1.0)
                    for n in splits.WALL_SPLITS[q.name]]
        o = tab.balance.neutrals.get()
        if o is None or o.why:
            return None
        return [(r.name, r.name, ["%d wstrat %s" % (k + 1, q.name)
                                  for k in r.strata], 1.0)
                for r in o.sources if r.kind != "sputtered"]

    def _parts(self, tab, q, w, cols, total):
        """[(name, label, values)] of the parts of the wall quantity q (w,
        the columns cols, total its values) and the rest, once all arrived
        (asked for once per run), else None (said once when b2plot has
        not got them)."""
        run, out, waiting = tab.run, [], False
        wanted = self._wanted(tab, q)
        if wanted is None:
            if self.failed is not run:
                self.failed = run
                tab.status.emit("Components by birth place need the "
                                "balance.nc of the state (the strata)")
            return None
        for name, text, fields, sign in wanted:
            v = 0.0
            for label in fields:
                key = ("wfield", label, (), None)
                d = run.cache.get(key)
                if d is None:
                    waiting = True
                    if any(r.key == key for r in run.pending):
                        continue
                    if (id(run), label) not in self.asked_parts:
                        self.asked_parts.add((id(run), label))
                        tab.request.emit(("tools", catalog.Quantity(
                            label, label, "", "wall"), (), None))
                        continue
                    if self.failed is not run:
                        self.failed = run
                        tab.status.emit("No wall label %s in b2plot: the "
                                        "components need B2.5 built with "
                                        "them" % label)
                    return None
                v = v + np.asarray(wall_values(d, cols if len(
                    d.columns) == len(w.columns) else range(len(
                        d.columns))), float)[:len(total)]
            if not waiting:
                out.append((name, text, sign * np.asarray(v, float)))
        return None if waiting else splits.wall_parts(total, out)

    def show_profile(self, key, name, unit, values, seg, area, what,
                     places=(), colour="#d62728", parts=None, spans=()):
        """values (plain unit) on the elements seg with their areas (the
        first len(area) elements of the quantity), name its title, what
        its label (file name), places [(distance, name)] marked with a
        vertical line (midplanes, strike points) in colour at first (that
        of the separatrices), parts [(name, label, values)] stacked under
        the total, spans [(start, end, name)] of the targets shaded behind;
        nothing done again for the same key."""
        if key == self.key:
            return
        self.key, self.places = key, list(places)
        n = min(len(area), len(seg), len(values))
        v = np.asarray(values, float)[:n]
        seg = np.asarray(seg, float)[:n]
        area = np.asarray(area, float)[:n]
        x, gaps = along(seg)
        ok = np.isfinite(v) & np.isfinite(area)
        total = float(np.sum(v[ok] * area[ok]))
        a = float(np.sum(area[ok]))
        html = measure.html_unit
        self.text.setText("<br>".join((
            "Integral over the B2.5 wall: %.5g %s" % (
                total, html(measure.times_m(unit, 2))),
            "Average over the B2.5 wall: %.5g %s" % (
                total / a if a > 0 else np.nan, html(unit)))))
        cut = np.flatnonzero(gaps)      # the pieces of the wall apart
        xs, ys = np.insert(x, cut, np.nan), np.insert(v, cut, np.nan)

        stack = [(p, label, np.where(np.isfinite(xs), np.nan_to_num(
            np.insert(np.asarray(u, float)[:n], cut, np.nan)), np.nan))
                 for p, label, u in parts or ()]

        def draw(ax, options):
            ax.set_title(name, fontsize="medium")
            total, = ax.plot(xs, ys, label="Total" if stack else "_",
                             zorder=3)
            bx, bands = xs, stack
            if stack and self.smoothed():   # Smooth: the parts too, the
                done = [smooth.smooth(xs, u) for _, _, u in stack]  # total
                bx = done[0][0]             # their sum
                bands = [(p, label, d[1]) for (p, label, _), d in
                         zip(stack, done)]
                total.smooth_to = (bx, sum(d[1] for d in done))
            ax.stack = (total, _stack(ax, bx, bands)) if stack else None
            for a, b, text in spans:    # the targets behind the curves,
                ax.axvspan(a, b, color=SHADE[0], alpha=SHADE[1], linewidth=0,
                           zorder=0)    # drawn after them (y data limits)
                ax.text(0.5 * (a + b), 0.02, text, ha="center", va="bottom",
                        transform=ax.get_xaxis_transform(), clip_on=True,
                        fontsize="x-small", color=theme.rgb(SHADE[0]))
            if stack:
                ax.legend(fontsize="x-small")
            if n > 1:
                ax.set_xlim(x[0], x[-1])
            for at, text in places:     # a row of options each
                ln = ax.axvline(at, color=colour, linestyle=":",
                                linewidth=0.9, label=text)
                t = ax.text(at, 0.98, " " + text,
                            transform=ax.get_xaxis_transform(), rotation=90,
                            ha="right", va="top", fontsize="x-small",
                            color=theme.rgb(colour), clip_on=True)
                t.line = ln             # in the colour of its line
            ax.set_xlabel(XLABEL)
            ax.set_ylabel(measure.math_unit(unit))
        r, z = 0.5 * (seg[:, 0] + seg[:, 2]), 0.5 * (seg[:, 1] + seg[:, 3])
        self.view.set_figure(
            draw, [XLABEL, "R (m)", "Z (m)", "area (m^2)",
                   "value (%s)" % unit] + ["%s (%s)" % (label, unit)
                                           for _, label, _ in parts or ()],
            [list(row) + [u[i] for _, _, u in parts or ()] for i, row in
             enumerate(zip(x, r, z, area, v))], kind="line",
            space=True,
            name="wall_" + what)

    def _shown(self, *_):
        """Show midplanes and strikepoints: the profile, the diamonds in 2D and 3D."""
        if self.tab is not None:
            self.follow(self.tab)
        self.marks_changed.emit()

    def show_marks(self):
        """Show midplanes and strikepoints ticked: the marks drawn."""
        return self.shown.isChecked()

    def mark_colours(self):
        """{name: colour} of the marks (midplanes, strike points) chosen in
        the rows of the plot options (shown in Final state)."""
        if not self.isVisible():
            return {}
        names = {m for _, m in getattr(self, "places", ())}
        return {r[0]: r[1].color() for r in self.view.options.curves
                if r[0] in names and hasattr(r[1], "color")}

    def smoothed(self):
        """Smooth of the profile ticked (shown in Final state)."""
        rows = self.view.options.curves
        return self.isVisible() and any(
            len(r) > 5 and r[5] is not None and r[5].isChecked()
            for r in rows)

    def clear(self):
        self.key = None
