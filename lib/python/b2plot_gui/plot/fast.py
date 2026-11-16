"""Fast frames of the 2D plot: when only the frame of the movie quantities
changes (the slider moved, a movie prepared), the canvas is not drawn
again as a whole. What does not change is kept after one full draw: an
image of the figure without the field and the parts that follow it, and
the pixels of the layers over the field (structure, grids, separatrices,
masks...). Each frame then restores the image, draws the field, lays the
kept layer pixels over it and draws what changes above (vectors, wall
strip, chords, title, the colour bars)."""

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg, RendererAgg


class FastMixin:
    """Frames of Plot2D drawn by repainting only what changes."""

    fast = None                 # (key, background, layer pixels, statics)

    def _statics(self):
        """The artists over the field that no frame changes: the layers,
        the masks and their legend."""
        out = [a for v in self.layer_artists.values()
               for a in (v if isinstance(v, list) else [v])
               if a is not None and a.get_visible()]
        out += [a for a in self.mask_artists if a.get_visible()]
        legend = self.ax.get_legend()
        if legend is not None and legend.get_visible():
            out.append(legend)
        return out

    def _changing(self):
        """The artists drawn again at each frame: everything in the axes
        but the statics (field, contours, vectors, wall strip, chords,
        cell values, the overlay colour bar), the title and the texts of
        the figure, the colour bars of the plasma, vector and wall plots
        (the placeholders of empty slots are kept)."""
        ax, statics = self.ax, set(self._statics())
        inside = [a for a in (list(ax.collections) + list(ax.lines) +
                              list(ax.texts) + list(ax.patches) +
                              list(ax.images) + list(ax.artists) +
                              list(ax.child_axes))
                  if a not in statics]
        bars = [self.cax] + [a for a, bar in ((self.vax, self.vbar),
                                              (self.wax, self.wbar))
                             if bar is not None]
        titles = [ax.title, ax._left_title, ax._right_title]
        return inside, titles + list(self.label_artists), bars

    def _fast_key(self):
        """What the kept parts depend on."""
        from .. import theme
        statics = self._statics()
        return (tuple(self.fig.canvas.get_width_height(physical=True)),
                self.fig.dpi, tuple(self.ax.viewLim.bounds),
                tuple(self.ax.get_position().bounds), theme.name(),
                tuple(id(a) for a in statics), repr(self.label_style),
                self.wbar is None, self.vbar is None, self.ax.axison)

    def _keep(self):
        """After a full draw: the image of what does not change and the
        pixels of the layers over the field."""
        canvas = self.fig.canvas
        inside, texts, bars = self._changing()
        statics = self._statics()
        hidden = [a for a in inside + texts + bars + statics + list(
            self.ax.spines.values()) if a.get_visible()]   # drawn per frame
        for a in hidden:
            a.set_visible(False)
        try:
            FigureCanvasAgg.draw(canvas)
            background = canvas.copy_from_bbox(self.fig.bbox)
        finally:
            for a in hidden:
                a.set_visible(True)
        r0 = canvas.get_renderer()
        layer = RendererAgg(r0.width, r0.height, self.fig.dpi)
        for a in sorted(statics, key=lambda a: a.get_zorder()):
            a.draw(layer)
        rgba = np.asarray(layer.buffer_rgba()).reshape(-1, 4)
        where = np.flatnonzero(rgba[:, 3])
        alpha = rgba[where, 3:4].astype(np.float32) / 255.0
        pixels = (where, rgba[where, :3].astype(np.float32) * alpha, alpha)
        self.fast = (self._fast_key(), background, pixels,
                     min([a.get_zorder() for a in statics] + [np.inf]))

    def fast_draw(self, blit=True):
        """The frame drawn by repainting only what changes (the kept parts
        made first, with a full draw, when missing or out of date); blit:
        shown on the screen."""
        canvas = self.fig.canvas
        if self.run is None:
            return False
        if self.fast is None or self.fast[0] != self._fast_key():
            FigureCanvasAgg.draw(canvas)
            self._keep()
            FigureCanvasAgg.draw(canvas)
        else:
            _, background, (where, colour, alpha), z0 = self.fast
            inside, texts, bars = self._changing()
            canvas.restore_region(background)
            renderer = canvas.get_renderer()
            shown = sorted((a for a in inside if a.get_visible()),
                           key=lambda a: a.get_zorder())
            for a in shown:
                if a.get_zorder() < z0:
                    a.draw(renderer)
            for spine in self.ax.spines.values():
                spine.draw(renderer)
            buf = np.asarray(renderer.buffer_rgba()).reshape(-1, 4)
            under = buf[where, :3].astype(np.float32)
            buf[where, :3] = (colour + under * (1.0 - alpha) + 0.5).astype(
                np.uint8)
            for a in shown:
                if a.get_zorder() >= z0:
                    a.draw(renderer)
            for a in texts + bars:
                if a.get_visible():
                    a.draw(renderer)
        if blit:
            canvas.blit(self.fig.bbox)
        return True
