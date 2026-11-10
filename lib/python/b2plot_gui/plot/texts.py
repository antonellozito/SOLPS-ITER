"""Texts of the 2D plot: title, axis labels, extra label, global header
and the colour bars, as the b2plot label commands; colour bars as the
AUGVIEW equilibrium tab (compact ticks with the power of ten above the
bar, the label inside the bar, an empty placeholder when nothing is
plotted)."""

import numpy as np
from matplotlib.colors import LogNorm, SymLogNorm
from matplotlib.ticker import (FuncFormatter, LogFormatterSciNotation,
                               LogLocator, ScalarFormatter)

from ...b2plot import labels
from .. import theme

PLACEHOLDER = "Quantity"


def fit_size(s, size, width, bold=False):
    """Font size, at most size, with which the text s fits in width points
    (long run paths in the standard label)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    if not s.strip():
        return size
    try:
        w = TextPath((0, 0), s, size=size, prop=FontProperties(
            weight="bold" if bold else "normal")).get_extents().width
    except (ValueError, RuntimeError):     # text mathtext cannot parse
        return size
    return size if w <= width else max(size * width / w, 4.0)


def _detach(bar):
    """Detach a colour bar from its mappable (which may be reused)."""
    if bar is not None:
        cid = getattr(bar.mappable, "colorbar_cid", None)
        if cid is not None:
            bar.mappable.callbacks.disconnect(cid)
        bar.mappable.colorbar = None


def _empty(ax):
    """A colour-bar slot emptied: matplotlib wraps the axes locator of the
    slot in each new colour bar, so stale ones (with extension triangles)
    would shrink the next bars; the locator and the box are reset."""
    ax.cla()
    ax.set_axes_locator(None)
    ax.set_position(ax.get_position(original=True))


class TextMixin:
    """Labels and colour bars of Plot2D."""

    def _drop_colorbar(self):
        _detach(self.cbar)
        self.cbar = None
        _empty(self.cax)

    def _drop_bottom_bar(self):
        """The bar under the plot (wall strip) away, the plot box back."""
        _detach(self.bbar)
        self.bbar = None
        _empty(self.bax)
        self.bax.set_visible(False)
        if self.bottom_bar:
            self.bottom_bar = False
            self._place()

    def _placeholder(self):
        """Empty colour-bar slot of a fixed plot (hidden otherwise)."""
        if not self.fixed:
            self.cax.set_visible(False)
            return
        face, frame, text = theme.placeholder()
        cax = self.cax
        _empty(cax)
        cax.set_visible(True)
        cax.set_facecolor(face)
        cax.set_xticks([])
        cax.set_yticks([])
        for spine in cax.spines.values():
            spine.set_color(frame)
        cax.text(0.5, 0.5, PLACEHOLDER, rotation=90, ha="center",
                 va="center", fontsize=9.0, color=text,
                 transform=cax.transAxes)

    def _colorbar(self, data, st):
        self._drop_colorbar()
        if self.mappable is None or not st.colorbar:
            self._placeholder()
            return
        self.cax.set_visible(True)
        self.cbar = self.fig.colorbar(self.mappable, cax=self.cax)
        self._style_bar(self.cbar, self.unit)

    def bottom_colorbar(self, mappable, label):
        """A horizontal colour bar under the plot (the wall strip); the
        plot box gets shorter while it is shown."""
        if not self.bottom_bar:
            self.bottom_bar = True
            self._place()
        self.bax.set_visible(True)
        self.bbar = self.fig.colorbar(mappable, cax=self.bax,
                                      orientation="horizontal")
        self._style_bar(self.bbar, label)

    def _style_bar(self, bar, label, size=None):
        """Ticks (compact, as AUGVIEW), frame and the label inside the bar,
        in the colours of the theme."""
        vertical = bar.orientation == "vertical"
        axis = bar.ax.yaxis if vertical else bar.ax.xaxis
        fs = size or 10.0 * self.label_style.size
        color = theme.label_color(self.label_style.color)
        norm = bar.mappable.norm
        if isinstance(norm, LogNorm):
            bar.locator = LogLocator()
            bar.formatter = LogFormatterSciNotation()
            bar.update_ticks()
        elif not isinstance(norm, SymLogNorm):
            self._compact_ticks(bar, axis, vertical, fs, color)
        bar.ax.tick_params(labelsize=0.9 * fs, colors=color)
        bar.outline.set_edgecolor(color)
        bar.set_label("")
        text = labels.any_to_mathtext(label or "")
        if text.strip():
            bar.ax.text(0.5, 0.5, text, rotation=90 if vertical else 0,
                        ha="center", va="center", fontsize=fs, color=color,
                        transform=bar.ax.transAxes, gid="bar-label",
                        bbox=dict(boxstyle="round,pad=0.15",
                                  facecolor=theme.figure_bg(),
                                  edgecolor="none", alpha=0.6))

    @staticmethod
    def _compact_ticks(bar, axis, vertical, fs, color):
        """Plain ticks, or the values divided by a power of ten written
        above (or right of) the bar when they are large or small."""
        lo, hi = bar.mappable.get_clim()
        top = np.nanmax(np.abs([lo, hi])) if np.isfinite([lo, hi]).any() \
            else np.nan
        if not (top > 0 and (top >= 1e3 or top < 1e-2)):
            f = ScalarFormatter(useMathText=True)
            f.set_powerlimits((-3, 4))
            bar.formatter = f
            bar.update_ticks()
            axis.get_offset_text().set_visible(False)
            return
        p = int(np.floor(np.log10(top)))
        bar.formatter = FuncFormatter(
            lambda v, _=None: "0" if abs(v / 10.0 ** p) < 5e-13 else
            "%g" % (v / 10.0 ** p))
        bar.update_ticks()
        axis.get_offset_text().set_visible(False)
        bar.ax.text(*((0.5, 1.01) if vertical else (1.01, 0.5)),
                    r"$\times 10^{%d}$" % p, transform=bar.ax.transAxes,
                    ha="center" if vertical else "left",
                    va="bottom" if vertical else "center",
                    fontsize=0.9 * fs, color=color, clip_on=False,
                    gid="bar-exponent")

    def set_labels(self, ls, title, values=None, header=True):
        """Texts, sizes and colours of a LabelStyle; title is the automatic
        title, values expand ${NAME}; header False leaves the global
        header to the page (composer)."""
        for a in self.label_artists:
            a.remove()
        self.label_artists, self.label_style = [], ls
        fs = 10.0 * ls.size
        color = theme.label_color(ls.color)
        kw = dict(color=color, fontweight="bold" if ls.bold else "normal")

        def text(s):
            return labels.tex_to_mathtext(labels.expand(s, values))
        pw, pts = self.inches() * 72.0
        head = ls.header.strip() and header
        self._top_pts = (1.8 * fs if head else 0.0) + (
            1.5 * fs if ls.extra.strip() else 0.0)
        self._place()
        wide = 0.98 * self.rect[2] * pw
        box = self.ax.get_position()
        mid = 0.5 * (box.x0 + box.x1)   # the title is centred on the axes
        half = min(mid - self.rect[0], self.rect[0] + self.rect[2] - mid)
        s = text(ls.title or title)
        for ax in [a for a in (self.ax, self.ax3d) if a is not None]:
            ax.set_title(s, fontsize=fit_size(s, 1.1 * fs, 1.96 * half * pw,
                                              ls.bold), **kw)
            ax.set_xlabel(text(ls.xlabel or "R (m)"), fontsize=fs, **kw)
            ax.set_ylabel(text(ls.ylabel or "Z (m)"), fontsize=fs, **kw)
            ax.tick_params(labelsize=0.9 * fs, colors=color)
            for spine in ax.spines.values():
                spine.set_color(color)
            ax.axis("on" if ls.axes else "off")
        x, y, w, h = self.rect
        top = y + h       # fixed: the texts just above the title room
        if self.fixed:
            top -= max(3.3 * 10.0 - self._top_pts, 0.0) / pts
        if ls.extra.strip():
            s = text(ls.extra)
            self.label_artists.append(self.fig.text(
                x + 0.5 * w, top - (self._top_pts - 0.2 * fs) / pts, s,
                ha="center", va="bottom", fontsize=fit_size(
                    s, 0.9 * fs, wide, ls.bold), **kw))
        if head:
            s = text(ls.header)
            self.label_artists.append(self.fig.text(
                x + 0.5 * w, top - 0.4 * fs / pts, s, ha="center",
                va="top", fontsize=fit_size(s, 1.2 * fs, wide, ls.bold),
                **kw))
        for bar in (self.cbar, self.bbar):
            if bar is not None:
                for t in bar.ax.texts:
                    t.set(color=color, fontsize=fs if t.get_gid() ==
                          "bar-label" else 0.9 * fs)
                bar.ax.tick_params(labelsize=0.9 * fs, colors=color)
                bar.outline.set_edgecolor(color)
