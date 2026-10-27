"""CLI renderer: draw scene frames as NCAR-like matplotlib figures.

Used by the CLI parity mode (batch.py). Every value and coordinate comes
from the message stream; this module only maps NCAR primitives onto
matplotlib artists, so that the pages look as close as possible to the
PostScript of the NCAR b2plot.
"""

import re

import numpy as np
import matplotlib.tri as mtri
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path
from matplotlib.ticker import FixedLocator, NullLocator

from . import labels
from .scene import Contour, Fill, Image, Markers, Polyline, Text

# Size of the NCAR frame (NDC 0..1) in inches, as in the NCAR PostScript
NDC_INCHES = 7.5
# Plotter address units across the frame (Dashline, Gridall, LABMOD sizes)
PLOTTER_UNITS = 1024.0
# Font size in points for a character width of 1 (fraction of the frame)
TEXT_SCALE = 1.83
# Line width in points for a GKS line width scale factor of 1
LINE_WIDTH = 0.6

FONT = {"family": "serif"}
MARKERS = {1: ".", 2: "+", 3: "*", 4: "o", 5: "x"}
LINESTYLES = {1: "-", 2: "--", 3: ":", 4: "-."}


def _rgb(colors, ci):
    return colors.get(ci, (0.0, 0.0, 0.0))


def fortran_format(fmt):
    """Python formatter for a Fortran edit descriptor such as (F4.1)."""
    f = fmt.strip().strip("()").replace(" ", "").upper()
    scale = 0
    m = re.match(r"^(\d*)P,?(.*)$", f)
    if m:
        scale = int(m.group(1) or 0)
        f = m.group(2)
    m = re.match(r"^([FEGI])(\d+)(?:\.(\d+))?$", f)
    if not m:
        return lambda v: f"{v:g}"
    kind, d = m.group(1), int(m.group(3) or 0)
    if kind == "F":
        if d == 0:
            return lambda v: f"{v:.0f}."
        return lambda v: f"{v:.{d}f}"
    if kind == "I":
        return lambda v: f"{int(round(v))}"
    if kind in "EG":
        def efmt(v):
            if scale >= 1:
                s = f"{v:.{d + 1 - scale}E}"
                mant, exp = s.split("E")
                return f"{mant}E{int(exp):+03d}"
            # without a scale factor Fortran writes 0.ddd with d digits
            if v == 0:
                return f"0.{'0' * d}E+00"
            e = int(np.floor(np.log10(abs(v)))) + 1
            mant = f"{v / 10.0 ** e:.{d}f}"
            if mant.lstrip("-").startswith("1."):
                e += 1
                mant = f"{v / 10.0 ** e:.{d}f}"
            return f"{mant}E{e:+03d}"
        return efmt
    return lambda v: f"{v:g}"


class Renderer:
    """Renders one Frame into a matplotlib Figure."""

    def __init__(self, ndc_inches=NDC_INCHES):
        self.ndc_inches = ndc_inches
        self.ndc_pt = ndc_inches * 72.0

    # ------------------------------------------------------------ figure
    def figure(self, frame, fig=None):
        """Draw frame into fig (a new Figure if None) and return it."""
        xw, yh = frame.xwidth, frame.yheight
        size = (self.ndc_inches * xw, self.ndc_inches * yh)
        if fig is None:
            fig = Figure(figsize=size)
        else:
            fig.set_size_inches(*size)
        fig.patch.set_facecolor(_rgb(frame.colors, 0))
        self.fig, self.colors, self.xw, self.yh = fig, frame.colors, xw, yh
        for panel in frame.panels:
            self._panel(panel)
        for bar in frame.colorbars:
            self._colorbar(bar)
        return fig

    def _font_pt(self, size):
        """Font size for a character width given as a fraction of the frame."""
        return size * self.ndc_pt * TEXT_SCALE

    def _add_axes(self, vl, vr, vb, vt):
        ax = self.fig.add_axes([vl / self.xw, vb / self.yh,
                                (vr - vl) / self.xw, (vt - vb) / self.yh])
        ax.patch.set_visible(False)
        ax.set_autoscale_on(False)
        return ax

    # ------------------------------------------------------------- panel
    def _panel(self, panel):
        vl, vr, vb, vt = panel.viewport
        wl, wr, wb, wt = panel.window
        ax = self._add_axes(vl, vr, vb, vt)
        if panel.lf in (3, 4):
            ax.set_xscale("log")
        if panel.lf in (2, 4):
            ax.set_yscale("log")
        ax.set_xlim(wl, wr)
        ax.set_ylim(wb, wt)
        self.ax, self.panel = ax, panel
        items = panel.items
        i = 0
        while i < len(items):
            item = items[i]
            j = i + 1
            if isinstance(item, Fill):
                while j < len(items) and isinstance(items[j], Fill):
                    j += 1
                self._fills(items[i:j])
            elif isinstance(item, Polyline):
                while (j < len(items) and isinstance(items[j], Polyline)
                       and items[j].style == item.style):
                    j += 1
                self._lines(items[i:j])
            elif isinstance(item, Markers):
                self._markers(item)
            elif isinstance(item, Text):
                self._text(item)
            elif isinstance(item, Image):
                self._image(item)
            elif isinstance(item, Contour):
                getattr(self, "_contour_" + item.kind)(item)
            i = j
        if panel.axes is not None:
            self._axes(panel.axes)
        else:
            ax.set_axis_off()

    # -------------------------------------------------------- primitives
    def _fills(self, fills):
        verts = [np.column_stack((f.x, f.y)) for f in fills]
        colors = [_rgb(self.colors, f.ci) for f in fills]
        pc = PolyCollection(verts, facecolors=colors, edgecolors=colors,
                            linewidths=0.3, antialiaseds=False)
        self.ax.add_collection(pc)

    def _dashes(self, style):
        """matplotlib line style for a Dashline pattern or GKS type."""
        pattern = "".join(c for c in style.dash if c in "$'")
        if "'" not in pattern:
            return LINESTYLES.get(style.ltype, "-")
        unit = style.jcrt / PLOTTER_UNITS * self.ndc_pt
        width = max(style.width * LINE_WIDTH, 0.1)
        seq, run, last = [], 0, pattern[0]
        for c in pattern + "#":
            if c == last:
                run += 1
            else:
                seq.append(run * unit / width)
                run, last = 1, c
        if pattern[0] == "'":
            seq = seq[1:] + seq[:1]
        if len(seq) % 2:
            seq.append(seq[-1])
        return (0, seq)

    def _lines(self, lines):
        style = lines[0].style
        segs = [np.column_stack((l.x, l.y)) for l in lines]
        lc = LineCollection(segs, colors=[_rgb(self.colors, style.ci)],
                            linewidths=style.width * LINE_WIDTH,
                            linestyles=[self._dashes(style)],
                            capstyle="butt", joinstyle="round")
        self.ax.add_collection(lc)

    def _markers(self, m):
        self.ax.plot(m.x, m.y, ls="none", marker=MARKERS.get(m.mtype, "*"),
                     color=_rgb(self.colors, m.ci), markersize=4 * m.scale,
                     clip_on=True)

    def _text(self, t):
        ha = "left" if t.cntr <= -0.5 else ("right" if t.cntr >= 0.5
                                            else "center")
        self.ax.text(t.x, t.y, labels.to_mathtext(t.text, t.fc),
                     rotation=t.angd, ha=ha, va="center", clip_on=False,
                     color=_rgb(self.colors, t.ci),
                     fontsize=self._font_pt(t.size),
                     fontweight="bold" if t.bold else "normal", **FONT)

    def _image(self, img):
        m = img.msg
        idx = m.clria.reshape(m.nyclr, m.nxclr)
        lut = np.array([_rgb(self.colors, ci) for ci in range(int(idx.max())
                                                             + 1)])
        self.ax.imshow(lut[np.clip(idx, 0, None)], origin="lower",
                       extent=(m.xp1, m.xp2, m.yp1, m.yp2),
                       interpolation="nearest", aspect="auto")

    # ---------------------------------------------------------- contours
    @staticmethod
    def _triangulation(mesh):
        lopn, loen, lotn = mesh.lopn, mesh.loen, mesh.lotn
        E = mesh.iedg.reshape(-1, loen)
        T = mesh.itri.reshape(-1, lotn)
        pe = E[:, :2] // lopn
        p = pe[T[:, :3] // loen].reshape(-1, 6)
        a, b = p[:, 0], p[:, 1]
        c = np.where((p[:, 2] != a) & (p[:, 2] != b), p[:, 2], p[:, 3])
        x, y, f = mesh.rpnt[0::lopn], mesh.rpnt[1::lopn], mesh.rpnt[3::lopn]
        tri = mtri.Triangulation(x, y, np.column_stack((a, b, c)),
                                 mask=T[:, 3] != 0)
        return tri, f

    @staticmethod
    def _grid(m, rect):
        k, mm, n = rect.kzdt, rect.mzdt, rect.nzdt
        z = np.array(rect.zdat.reshape(n, k)[:, :mm], dtype=float)
        z = np.ma.masked_equal(z, m.spv) if m.spv != 0 else z
        x = np.linspace(m.xc1, m.xcm, mm)
        y = np.linspace(m.yc1, m.ycn, n)
        return x, y, z

    def _clip_path(self, edges):
        """Union of the area-map polygons with the inside identifier 1."""
        verts, codes = [], []
        for e in edges:
            if e.idr == 1 or e.idl == 1:
                pts = np.column_stack((e.x, e.y))
                verts.extend(pts)
                codes.extend([Path.MOVETO] + [Path.LINETO] * (len(pts) - 1))
        if not verts:
            return None
        patch = PathPatch(Path(np.array(verts), codes),
                          transform=self.ax.transData, fill=False,
                          visible=False)
        self.ax.add_patch(patch)
        return patch

    def _band_colors(self, m):
        """Colour of each band below, between and above the levels."""
        n = m.ncl
        ids = [m.aib[0]] + [m.aia[i] for i in range(n)]
        out = []
        for k in ids:
            ci = m.color[k - 1] if 1 <= k <= m.nid else -1
            out.append((0, 0, 0, 0) if ci < 0 else _rgb(self.colors, ci))
        return out

    def _contour_fill(self, c):
        m = c.msg
        if m.ncl < 1 or c.data is None:
            return
        colors = self._band_colors(m)
        if m.source == 1:
            tri, f = self._triangulation(c.data)
            values = f
        else:
            x, y, z = self._grid(m, c.data)
            values = z.compressed() if np.ma.isMaskedArray(z) else z.ravel()
        # the n NCAR levels framed by the data range give the n+1 bands
        clv = np.asarray(m.clv, float)
        span = max(float(np.ptp(values)), abs(float(clv[-1])), 1.0)
        levels = np.concatenate((
            [min(float(values.min()), clv[0]) - span], clv,
            [max(float(values.max()), clv[-1]) + span]))
        if m.source == 1:
            cs = self.ax.tricontourf(tri, f, levels=levels, colors=colors,
                                     antialiased=False)
        else:
            cs = self.ax.contourf(x, y, z, levels=levels, colors=colors,
                                  antialiased=False)
            clip = self._clip_path(c.edges)
            if clip is not None:
                cs.set_clip_path(clip)

    def _contour_lines(self, c):
        m = c.msg
        if m.ncl < 1 or c.data is None:
            return
        if m.source == 1:
            tri, f = self._triangulation(c.data)
            values = f[np.unique(tri.get_masked_triangles())]
        else:
            x, y, z = self._grid(m, c.data)
            values = z.compressed() if np.ma.isMaskedArray(z) else z.ravel()
        # as in NCAR, only levels crossed by the field give lines
        lo, hi = float(values.min()), float(values.max())
        use = [i for i in range(m.ncl)
               if m.clu[i] in (1, 3) and lo < m.clv[i] < hi]
        if not use:
            return
        levels = np.asarray(m.clv, float)[use]
        widths = [max(m.cll[i], 0.1) * LINE_WIDTH for i in use]
        color = _rgb(self.colors, m.plci)
        if m.source == 1:
            cs = self.ax.tricontour(tri, f, levels=levels, colors=[color],
                                    linewidths=widths)
        else:
            cs = self.ax.contour(x, y, z, levels=levels, colors=[color],
                                 linewidths=widths)
            clip = self._clip_path(c.edges)
            if clip is not None:
                cs.set_clip_path(clip)
        lab = [lv for i, lv in zip(use, levels) if m.clu[i] in (2, 3)]
        if m.llp != 0 and lab:
            width = self.panel.viewport[1] - self.panel.viewport[0]
            texts = self.ax.clabel(cs, lab, inline=True, inline_spacing=2,
                                   fmt=lambda v: f"{v:.4g}",
                                   fontsize=self._font_pt(0.010 * width))
            for t in texts:
                t.set_bbox(dict(facecolor="white", edgecolor="none",
                                pad=0.5))
                t.set_fontfamily(FONT["family"])

    def _contour_info(self, c):
        m = c.msg
        if not m.ilt:
            return
        ha = {0: "left", 1: "center", 2: "right"}[
            {-4: 0, -3: 1, -2: 2, -1: 0, 0: 1, 1: 2, 2: 0, 3: 1, 4: 2}[m.ilp]]
        va = "bottom" if m.ilp <= -2 else ("top" if m.ilp >= 2
                                            else "center")
        width = self.panel.viewport[1] - self.panel.viewport[0]
        self.ax.text(m.ilx, m.ily, labels.to_mathtext(m.ilt),
                     transform=self.ax.transAxes, ha=ha, va=va,
                     fontsize=self._font_pt(0.012 * width), clip_on=False,
                     color=_rgb(self.colors, 1), **FONT)

    # --------------------------------------------------------------- axes
    def _axes(self, a):
        ax = self.ax
        g = a["gaset"]
        frame_ci = int(g.get("CAX", 1)) if g.get("CAX", 1) > 1 else 1
        label_ci = int(g.get("CLB", 1)) if g.get("CLB", 1) > 1 else 1
        width = float(g.get("WAX", 1.0)) * LINE_WIDTH
        for spine in ax.spines.values():
            spine.set_linewidth(width)
            spine.set_color(_rgb(self.colors, frame_ci))
        unit = self.ndc_pt / PLOTTER_UNITS
        # LABMOD: IYDC is the gap below the grid for X labels, IXDC the gap
        # left of the grid for Y labels
        for axis, mjr, mnr, lab, fmt, isz, dec in (
                (ax.xaxis, a["mjrx"], a["mnrx"], a["ixlb"], a["fmtx"],
                 a["iszx"], a["iydc"]),
                (ax.yaxis, a["mjry"], a["mnry"], a["iylb"], a["fmty"],
                 a["iszy"], a["ixdc"])):
            lo, hi = (ax.get_xlim() if axis is ax.xaxis else ax.get_ylim())
            if axis.get_scale() == "linear" and mjr > 0:
                major = np.linspace(lo, hi, mjr + 1)
                axis.set_major_locator(FixedLocator(major))
                if mnr > 1:
                    minor = np.linspace(lo, hi, mjr * mnr + 1)
                    axis.set_minor_locator(FixedLocator(minor))
                else:
                    axis.set_minor_locator(NullLocator())
                f = fortran_format(fmt)
                axis.set_ticklabels([f(v) for v in major] if lab > 0
                                    else [])
            size = max(isz, 4) * unit * TEXT_SCALE
            axis.set_tick_params(which="major", direction="in",
                                 length=16 * unit, width=width,
                                 labelsize=size, pad=dec * unit,
                                 color=_rgb(self.colors, frame_ci),
                                 labelcolor=_rgb(self.colors, label_ci))
            axis.set_tick_params(which="minor", direction="in",
                                 length=8 * unit, width=width,
                                 color=_rgb(self.colors, frame_ci))
            for t in axis.get_ticklabels():
                t.set_fontfamily(FONT["family"])
        ax.tick_params(which="both", top=True, right=True, labeltop=False,
                       labelright=False)

    # ---------------------------------------------------------- colour bar
    def _colorbar(self, bar):
        m = bar.msg
        nbox = abs(m.nbox)
        if nbox == 0:
            return
        ax = self._add_axes(m.xleb, m.xreb, m.ybeb, m.yteb)
        ax.set_axis_off()
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        vertical = m.ihov != 0
        boxw = m.wsfb if vertical else 1.0
        boxh = 1.0 if vertical else m.hsfb
        for k in range(nbox):
            ci = int(m.lfin[k])
            if vertical:
                r = Rectangle((0.0, k / nbox), boxw, 1.0 / nbox)
            else:
                r = Rectangle((k / nbox, 1.0 - boxh), 1.0 / nbox, boxh)
            r.set_facecolor(_rgb(self.colors, ci))
            r.set_edgecolor("black" if m.nbox > 0 else "none")
            r.set_linewidth(LINE_WIDTH)
            ax.add_patch(r)
        if m.lbab == 0 or m.nlbs == 0:
            return
        if m.nlbs == nbox + 1:
            pos = np.arange(nbox + 1) / nbox
        elif m.nlbs == nbox:
            pos = (np.arange(nbox) + 0.5) / nbox
        else:
            pos = (np.arange(m.nlbs) + 1.0) / nbox
        # label size and gap measured on NCAR pages (bar 0.08 of the frame);
        # NCAR shrinks the labels until the longest one fits
        span = (m.xreb - m.xleb) if vertical else (m.yteb - m.ybeb)
        longest = max((len(s.strip()) for s in m.llbs), default=1) or 1
        width = 0.145 * span
        if vertical:
            width = min(width, (1.0 - boxw - 0.18) * span / longest)
        fs = self._font_pt(width)
        for p, s in zip(pos, m.llbs):
            text = labels.to_mathtext(s.strip())
            if vertical:
                ax.text(boxw + 0.18, p, text, ha="left", va="center",
                        fontsize=fs, color=_rgb(self.colors, bar.ci), **FONT)
            else:
                ax.text(p, 1.0 - boxh - 0.08, text, ha="center", va="top",
                        fontsize=fs, color=_rgb(self.colors, bar.ci), **FONT)


def render_frame(frame, ndc_inches=NDC_INCHES, fig=None):
    """Return a matplotlib Figure for one Frame (drawn into fig if given)."""
    return Renderer(ndc_inches).figure(frame, fig)
