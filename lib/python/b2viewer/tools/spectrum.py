"""What the Spectrum section does (opened with Spectrum, right of Field
line, with a light quantity shown): the chords of the Chords section
(drawn, typed or of the *.chords files: the same tabs, ends and sums under
them), in each tab, instead of the profile, the spectrum along the chord:
the line integral (with Line averages under the tabs: the average) of each
line of the quantity (presets.Entry.lines: an npec window each, the
hydrogen lines of Eirene's model) against the wavelength, the total of the
lines above it, per steradian or not. With Line shapes the lines with
their shapes and, with Continua, the bremsstrahlung and recombination
continua under them (lineshape: the emitters of each line and the plasma
at points along the chord, seen from its first end)."""

import numpy as np
import matplotlib.tri as mtri
from matplotlib.ticker import MaxNLocator

from ...b2plot import labels
from ...qt import QtCore
from .. import catalog
from ..model import split_unit
from ..presets import ENTRY, ENTRY_PREFIX
from ..expression import ExpressionError
from . import lineshape, measure

STEP = 25                       # lines loaded between two redraws
SHOWN = 1e-4                    # the continua over the lines above this
#                                 fraction of the strongest
LIGHT = 0.999                   # the x axis at first over the lines
#                                 holding this fraction of the light
# the plasma the shapes need: name, expression (or the poloidal and radial
# components of a vector: in R, Z)
PLASMA = (("ne", "ne"), ("te", "te"), ("ti", "ti"), ("na", "na"),
          ("bb", "bb"), ("btor", "bz/bb"), ("utor", "ua*bz/bb"),
          ("ta", "2/3*edena/pdena"))
VECTORS = (("uvec", "ua pit m*", "ua ua m-"), ("bvec", "pit", "pit pit m-"))
SHAPE_POINTS = 801              # points along the sight


class Spectrum:
    """The lines of the light quantity shown (their fields asked for once
    per run) and the spectrum of a chord."""

    def __init__(self, tools):
        self.tools = tools
        self.run = None
        self.fields = {}                # tokens -> Field (None: failed)
        self.asked = set()
        self.rows = []                  # (wavelength, label, tokens)
        self.parts = []                 # their emitters (lineshape)
        self.cache = {}
        self._again = QtCore.QTimer(tools.tab)
        self._again.setSingleShot(True)
        self._again.setInterval(300)
        self._again.timeout.connect(self._redraw)

    def entry(self):
        """(entry, items chosen) of the light quantity shown, else None."""
        q = self.tools.tab.quantity
        cur = q.current
        if cur is None or cur.source != "entry":
            return None
        e = ENTRY.get(cur.name[len(ENTRY_PREFIX):])
        items = q.choices_box.items()
        if e is None or e.lines is None or items is None or \
                len(items) < len(e.params):
            return None
        return e, items

    def allowed(self):
        return self.entry() is not None

    def lines(self):
        """The lines of the quantity shown, the fields not yet here asked
        for."""
        tab = self.tools.tab
        if self.run is not tab.run:
            self.run, self.fields, self.asked = tab.run, {}, set()
        got = self.entry()
        if got is None or tab.run is None:
            self.rows = []
            return self.rows
        e, items = got
        rows, parts = [], []
        for wl, label, expr, emitters in e.lines(tab.species, *items):
            tokens, kind = tab.translate(expr)
            rows.append((wl, label, tokens))
            self._ask(tokens, label, e.group, kind, expr)
            ps = []
            for k, el, z, x in emitters:
                t, kd = tab.translate(x)
                ps.append((k, el, z, t, kd, x))
            parts.append(ps)
        self.rows, self.parts = rows, parts
        if self.tools.chords_section.shapes.isChecked():
            self.want_shapes(parts)
        return rows

    def _ask(self, tokens, label, group, kind, expr, vector=None):
        """A field asked for once per run (vector: its poloidal and radial
        components)."""
        if tokens in self.fields or tokens in self.asked:
            return
        self.asked.add(tokens)
        q = catalog.Quantity(tokens, label, group, "vector", *vector) if \
            vector else catalog.Quantity(tokens, label, group, kind,
                                         expr=expr)
        self.tools.tab.request.emit(("spectrum", q, (), None))

    def want_shapes(self, parts):
        """The fields of the emitters (parts) and of the plasma the shapes
        need asked for; True when all are here."""
        tab = self.tools.tab
        if tab.run is None:
            return False
        for name, expr in PLASMA:
            try:
                tokens, kind = tab.translate(expr)
            except ExpressionError:     # no Eirene: the ion temperature
                continue
            self._ask(tokens, name, "spectrum", kind, expr)
        for name, pol, rad in VECTORS:
            self._ask(pol + " " + rad, name, "spectrum", "vector",
                      None, (pol, rad))
        for ps in parts:
            for k, el, z, t, kd, x in ps:
                self._ask(t, k, "spectrum", kd, x)
        return not self.asked

    def _field(self, expr):
        try:
            return self.fields.get(self.tools.tab.translate(expr)[0])
        except ExpressionError:
            return None

    def _at(self, f, r, z, col=0, vector=False):
        """Values (vector: R and Z components) of field f in column col at
        the points (R, Z), NaN outside its cells or triangles."""
        plot = self.tools.tab.plot
        if f.location == "cells":
            tri = plot._cell_tri(None)
            finder = plot.run.geometry.trifinder(tri)
            comps = [f.vxr[col], f.vxz[col]] if vector else [f.vertex[col]]
        else:
            tri, comps = measure._grid(plot, f, col)
            finder = None
        vals = [np.ma.filled(mtri.LinearTriInterpolator(
            tri, np.asarray(a, float), trifinder=finder)(r, z), np.nan)
            for a in comps]
        return vals if vector else vals[0]

    def shaped(self, rows, parts, points, d, s, sticks, scale, instrument,
               continua, photons):
        """The spectrum along the sight d (unit, x y z) through points
        (n, 3) at distances s: (wavelengths A, lines, bremsstrahlung,
        recombination) per A, each line with the integral of its stick
        (sticks: per row, None for those left out), the continua times
        scale (per steradian, per length); None while fields are missing."""
        sp = self.tools.tab.species
        r, z = np.hypot(points[:, 0], points[:, 1]), points[:, 2]
        need = [self._field(x) for x in ("ne", "te", "ti", "bb", "bz/bb",
                                         "na", "ua*bz/bb")]
        vec = {n: self.fields.get(p + " " + q) for n, p, q in VECTORS}
        if any(f is None for f in need) or None in vec.values():
            return None
        ne, te, ti, bb, btor = (self._at(f, r, z) for f in need[:5])
        inside = np.isfinite(ne)
        w = lineshape.weights(s, inside)
        lr, lz, lt = lineshape.sight_parts(points, d)
        br, bz = self._at(vec["bvec"], r, z, vector=True)
        norm = np.sqrt(br ** 2 + bz ** 2 + btor ** 2)
        cos = np.clip(np.nan_to_num((br * lr + bz * lz + btor * lt) /
                                    np.where(norm > 0, norm, 1.0)), -1, 1)
        vlos, dens = {}, {}
        for ion in sp.ions:
            ur, uz = self._at(vec["uvec"], r, z, ion.column, True)
            ut = self._at(need[6], r, z, ion.column)
            vlos[(ion.element, ion.charge)] = np.nan_to_num(
                ur * lr + uz * lz + ut * lt)
            if ion.charge > 0:
                dens.setdefault(ion.charge, 0.0)
                dens[ion.charge] = dens[ion.charge] + np.nan_to_num(
                    self._at(need[5], r, z, ion.column))
        ta = {}
        tf = self._field("2/3*edena/pdena")
        if tf is not None:
            for n in sp.neutrals:
                if n.stack == "a":
                    t = self._at(tf, r, z, n.column)
                    ta[n.name] = np.where(np.isfinite(t) & (t > 0), t, ti)
        zero = np.zeros(len(r))
        rows_in, kept = [], []
        for (wl, label, tokens), ps, stick in zip(rows, parts, sticks):
            if stick is None:
                continue
            comps = []
            for k, el, zc, t, kd, x in ps:
                f = self.fields.get(t)
                if f is None:
                    return None
                e = np.nan_to_num(self._at(f, r, z)) * w
                temp = ta.get(el, ti) if k == "atom" else ti if \
                    k == "ion" else np.full(len(r), 2.0 / 3.0 *
                                            lineshape.FRAGMENT[k])
                comps.append([e, temp, lineshape.mass(el, sp.neutrals),
                              vlos.get((el, zc), zero) if k == "ion" else
                              zero, ne])
            tot = sum(c[0].sum() for c in comps)
            for c in comps:             # the integral of the stick
                c[0] = c[0] * (stick / tot if tot > 0 else 0.0)
            rows_in.append((wl, ps[0][1] if ps else "", comps))
            kept.append((wl, stick))
        if not rows_in:
            return None
        lines = lineshape.profiles(rows_in, bb, cos, instrument)
        wls = np.array([k[0] for k in kept])
        ys = np.array([k[1] for k in kept])
        big = ys >= SHOWN * np.abs(ys).max()
        lo, hi = wls[big].min(), wls[big].max()
        pad = 0.03 * max(hi - lo, 1.0)
        lo, hi = max(lo - pad, 1.0), hi + pad
        cuts = lineshape.edges(sorted(dens), lo, hi) if continua else []
        lam = lineshape.grid(lines, lo, hi, cuts)
        curve = lineshape.line_curves(lines, lam)
        ff = fb = np.zeros(len(lam))
        if continua and dens:
            coarse = np.unique(np.concatenate((np.geomspace(
                lo, hi, lineshape.COARSE), np.ravel([
                    c * np.array([1 - 1e-6, 1 + 1e-6]) for c in cuts]))))
            f1, f2 = lineshape.continua(coarse, ne, te, dens, w * scale)
            if photons:                 # W -> photons
                hnu = lineshape.HC / (coarse * 1e-10)
                f1, f2 = f1 / hnu, f2 / hnu
            ff = np.interp(lam, coarse, f1, 0.0, 0.0)
            fb = np.interp(lam, coarse, f2, 0.0, 0.0)
        return lam, curve, ff, fb

    def delivered(self, q, data):
        """A line arrived: the spectra again once all are here (and every
        STEP lines, the count shown meanwhile)."""
        self.asked.discard(q.name)
        self.fields[q.name] = data
        if not self.asked or len(self.fields) % STEP == 0:
            self._again.start()

    def _redraw(self):
        if self.tools.section == "spectrum":
            self.tools._chords_all()

    def show(self, t, k, coords, m, per_sr, average):
        """The spectrum of chord k (its ends coords; m: the quantity shown,
        as Tools._measured gives it) in its tab t: the total above the
        figure."""
        data, q = m[0], m[1]
        rows = self.rows
        r0, z0, f0, r1, z1, f1 = coords
        nodes, w, inside = measure.chord_weights(
            self.tools.tab.plot, data, (r0, z0), (r1, z1), phi=(f0, f1))
        scale = 1.0 / (4.0 * np.pi) if per_sr else 1.0
        if average:
            scale = scale / inside if inside > 0 else np.nan
        got, sticks = [], []
        for wl, label, tokens in rows:
            f = self.fields.get(tokens)
            if f is None:
                sticks.append(None)
                continue
            v = np.asarray(f.vertex[0], float)[nodes]
            got.append((wl, label, scale * float(np.dot(
                w, np.where(np.isfinite(v), v, 0.0)))))
            sticks.append(got[-1][2])
        unit = _unit(q, average, per_sr)
        total = sum(y for _, _, y in got)
        what = "Average" if average else "Total"
        text = "%s of the %d lines along the line: %.5g %s" % (
            what, len(got), total, measure.html_unit(unit))
        if len(got) < len(rows):
            text += " (lines loaded: %d of %d)" % (len(got), len(rows))
        name = self.tools._name(q, m[4])
        wl = np.array([x[0] for x in got], float)
        y = np.array([x[2] for x in got], float)
        sec = self.tools.chords_section
        shaped = None
        if sec.shapes.isChecked() and got:
            opts = sec.shape_options()
            key = (tuple(coords), scale, opts, tuple(sticks),
                   id(self.rows))
            shaped = self.cache.get(key)
            if shaped is None and self.want_shapes(self.parts):
                a0, a1 = np.radians((f0, f1))
                points, d, s = lineshape.segment(
                    (r0 * np.cos(a0), r0 * np.sin(a0), z0),
                    (r1 * np.cos(a1), r1 * np.sin(a1), z1), SHAPE_POINTS)
                shaped = self.shaped(
                    self.rows, self.parts, points, d, s, sticks, scale,
                    10.0 * opts[0], opts[1] and _density(q) is not None,
                    "photons" in unit)
                if shaped is not None:
                    self.cache = {key: shaped}
            text += "<br>" + shape_text(shaped, opts, unit, self.asked)
        t.text.setText(text)
        if shaped is not None:
            self._draw_shaped(t, k, name, unit, average, wl, y, shaped)
            return

        def draw(ax, options):
            pos = y[y > 0]
            logy = options.logy.isChecked()
            base = pos.min() / 10.0 if logy and len(pos) else 0.0
            ax.plot(np.repeat(wl, 3), np.column_stack((
                np.full(len(y), base), y, np.full(len(y), np.nan))).ravel(),
                label="Lines")
            if not logy:
                ax.set_ylim(bottom=0.0)
            fit_x(ax, wl, y, options.logx.isChecked())
            ax.set_title(name, fontsize="medium")
            ax.set_xlabel("wavelength (Å)")
            ax.set_ylabel(measure.math_unit(unit))
        t.view.options.allow(())
        t.view.set_figure(draw, ["wavelength (A)", "line",
                                 "%s (%s)" % ("average" if average else
                                              "integral", unit)],
                          [list(x) for x in got], kind="spectrum",
                          space=False, name="spectrum_chord_%d" % (k + 1))


    def _draw_shaped(self, t, k, name, unit, average, wl, y, shaped):
        lam, curve, ff, fb = shaped
        cont = ff + fb
        total = curve + cont
        per = unit + " Å^-1"

        def draw(ax, options):
            ax.plot(lam, total, label="Spectrum", linewidth=1.0)
            if cont.any():
                ax.plot(lam, cont, label="Continua", linewidth=0.8,
                        linestyle="--")
            if not options.logy.isChecked():
                ax.set_ylim(bottom=0.0)
            fit_x(ax, wl, y, options.logx.isChecked())
            ax.set_title(name, fontsize="medium")
            ax.set_xlabel("wavelength (Å)")
            ax.set_ylabel(measure.math_unit(per))
        t.view.options.allow(())
        what = "average" if average else "integral"
        t.view.set_figure(draw, ["wavelength (A)", "lines (%s)" % per,
                                 "bremsstrahlung (%s)" % per,
                                 "recombination (%s)" % per,
                                 "%s (%s)" % (what, per)],
                          [[a, b, c, e, b + c + e] for a, b, c, e in
                           zip(lam, curve, ff, fb)], kind="spectrum",
                          space=False, name="spectrum_chord_%d" % (k + 1))


def shape_text(shaped, opts, unit, asked):
    """The line of the shapes under the total (shaped: Spectrum.shaped)."""
    if shaped is None:
        return "Line shapes: loading the plasma and the emitters (%d " \
            "fields)…" % len(asked) if asked else "Line shapes: no plasma " \
            "along the line"
    lam, curve, ff, fb = shaped
    text = "Lines with their shapes (Doppler, flows, Zeeman, Stark of " \
        "Balmer alpha and beta), instrument %.3g nm" % opts[0]
    if ff.any() or fb.any():
        tw = np.zeros(len(lam))
        tw[1:] += 0.5 * np.diff(lam)
        tw[:-1] += 0.5 * np.diff(lam)
        on = np.flatnonzero(ff + fb > 0)
        text += "; continua from %.0f to %.0f Å: bremsstrahlung %.4g, " \
            "recombination %.4g %s" % (lam[on[0]], lam[on[-1]], ff @ tw,
                                       fb @ tw, measure.html_unit(unit))
    return text


def _density(q):
    """"photons" or "W" for a photon or power density, else None."""
    from .cameratool import _density as density
    return density(q.description)


def light_range(wl, y, logx=False, fraction=LIGHT):
    """(from, to) in A: the shortest wavelength range (in log on a
    logarithmic axis) holding fraction of the light of the lines (y),
    else None."""
    wl, y = np.asarray(wl, float), np.maximum(np.nan_to_num(y), 0.0)
    if not len(wl) or y.sum() <= 0:
        return None
    o = np.argsort(wl)
    x, c = wl[o], np.concatenate(([0.0], np.cumsum(y[o])))
    need = fraction * c[-1] * (1.0 - 1e-12)
    end = np.searchsorted(c, c[:-1] + need) - 1     # the last line held
    ok = np.flatnonzero(end < len(x))
    key = np.log(np.maximum(x, 1e-30)) if logx else x
    i = ok[np.argmin(key[end[ok]] - key[ok])]
    return float(x[i]), float(x[end[i]])


def fit_x(ax, wl, y, logx, band=None):
    """The x axis over the lines that hold LIGHT of the light (not the far
    ones that hold almost none), and over band (from, to in A) if
    given."""
    got = light_range(wl, y, logx)
    if got is None:
        return
    lo, hi = got
    if band is not None:
        lo, hi = min(lo, band[0]), max(hi, band[1])
    if logx:
        ax.set_xlim(lo / 1.2, hi * 1.2)
    else:
        pad = max(0.03 * (hi - lo), 1e-3 * hi)
        ax.set_xlim(max(lo - pad, 0.0), hi + pad)
        ax.xaxis.set_major_locator(MaxNLocator(6))


def _unit(q, average, per_sr):
    """Plain unit of the lines along a chord: the unit of the quantity
    (its description) times m (integrals), per steradian."""
    unit = labels.any_to_plain(split_unit(q.description)[1])
    if not average:
        unit = measure.times_m(unit, 1)
    return (unit + " sr^-1") if per_sr else unit
