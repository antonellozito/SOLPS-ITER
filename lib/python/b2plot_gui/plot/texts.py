"""Texts of the 2D plot: title, axis labels, extra label, global header
and the colour bar, as the b2plot label commands."""

from matplotlib.ticker import LogFormatterSciNotation, LogLocator
from matplotlib.colors import LogNorm

from ...b2plot import labels


def fit_size(s, size, width, bold=False):
    """Font size, at most size, with which the text s fits in width points
    (long run paths in the standard label)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    try:
        w = TextPath((0, 0), s, size=size, prop=FontProperties(
            weight="bold" if bold else "normal")).get_extents().width
    except (ValueError, RuntimeError):     # text mathtext cannot parse
        return size
    return size if w <= width else max(size * width / w, 4.0)


class TextMixin:
    """Labels and colour bar of Plot2D."""

    def _drop_colorbar(self):
        """Detach the colour bar from its (possibly reused) mappable."""
        cb, self.cbar = self.cbar, None
        if cb is not None:
            cid = getattr(cb.mappable, "colorbar_cid", None)
            if cid is not None:
                cb.mappable.callbacks.disconnect(cid)
            cb.mappable.colorbar = None
        self.cax.cla()

    def _colorbar(self, data, st):
        self._drop_colorbar()
        if self.mappable is None or not st.colorbar:
            self.cax.set_visible(False)
            return
        self.cax.set_visible(True)
        self.cbar = self.fig.colorbar(self.mappable, cax=self.cax)
        if isinstance(self.mappable.norm, LogNorm):
            self.cbar.locator = LogLocator()
            self.cbar.formatter = LogFormatterSciNotation()
            self.cbar.update_ticks()
        self.cbar.set_label(labels.any_to_mathtext(self.unit))

    def set_labels(self, ls, title, values=None, header=True):
        """Texts, sizes and colours of a LabelStyle; title is the automatic
        title, values expand ${NAME}; header False leaves the global
        header to the page (composer)."""
        for a in self.label_artists:
            a.remove()
        self.label_artists, self.label_style = [], ls
        fs = 10.0 * ls.size
        kw = dict(color=ls.color, fontweight="bold" if ls.bold else "normal")

        def text(s):
            return labels.tex_to_mathtext(labels.expand(s, values))
        pts = self.fig.get_size_inches()[1] * 72.0
        head = ls.header.strip() and header
        self._top_pts = (1.8 * fs if head else 0.0) + (
            1.5 * fs if ls.extra.strip() else 0.0)
        self._place()
        pw = self.fig.get_size_inches()[0] * 72.0
        wide = 0.98 * self.rect[2] * pw
        box = self.ax.get_position()
        mid = 0.5 * (box.x0 + box.x1)   # the title is centred on the axes
        half = min(mid - self.rect[0], self.rect[0] + self.rect[2] - mid)
        s = text(ls.title or title)
        self.ax.set_title(s, fontsize=fit_size(s, 1.1 * fs, 1.96 * half * pw,
                                               ls.bold), **kw)
        self.ax.set_xlabel(text(ls.xlabel or "R (m)"), fontsize=fs, **kw)
        self.ax.set_ylabel(text(ls.ylabel or "Z (m)"), fontsize=fs, **kw)
        self.ax.tick_params(labelsize=0.9 * fs, labelcolor=ls.color)
        self.ax.axis("on" if ls.axes else "off")
        x, y, w, h = self.rect
        if ls.extra.strip():
            s = text(ls.extra)
            self.label_artists.append(self.fig.text(
                x + 0.5 * w, y + h - (self._top_pts - 0.2 * fs) / pts, s,
                ha="center", va="bottom", fontsize=fit_size(
                    s, 0.9 * fs, wide, ls.bold), **kw))
        if head:
            s = text(ls.header)
            self.label_artists.append(self.fig.text(
                x + 0.5 * w, y + h - 0.4 * fs / pts, s, ha="center",
                va="top", fontsize=fit_size(s, 1.2 * fs, wide, ls.bold),
                **kw))
        if self.cbar is not None:
            self.cbar.ax.tick_params(labelsize=0.9 * fs,
                                     labelcolor=ls.color)
            self.cbar.set_label(labels.any_to_mathtext(self.unit or ""),
                                fontsize=fs, **kw)
