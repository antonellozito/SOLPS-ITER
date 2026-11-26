"""Masks of the 2D plot (tools.regions): cells filled by region over the
field, faces drawn thick over the wall strip, each with its legend inside
the plot box and no colour bar."""

from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .. import theme

CELL_ZORDER, FACE_ZORDER = 2.5, 5.6     # over the field, the wall strip
LEGEND = dict(fontsize=6.5, framealpha=0.85, borderpad=0.4,
              handlelength=1.6, labelspacing=0.3)


class MaskMixin:
    """Masks of Plot2D: set_masks([("cells", rows, colours, legend) or
    ("faces", segments, colours, legend)]), legend [(text, colour)]."""

    def set_masks(self, masks):
        self.masks = list(masks)
        self.draw_masks()

    def draw_masks(self):
        for a in getattr(self, "mask_artists", []):
            try:
                a.remove()
            except (ValueError, NotImplementedError):
                pass
        self.mask_artists = []
        if self.run is None:
            return
        for kind, data, colours, legend in getattr(self, "masks", []):
            cells = kind == "cells"
            rgb = theme.rgb_array([tuple(c) for c in colours])
            if cells:
                polys = self.run.geometry.polygons
                art = PolyCollection([polys[r] for r in data], facecolors=rgb,
                                     edgecolors=theme.rgb("0.6"),
                                     linewidths=0.05, zorder=CELL_ZORDER)
                handles = [Patch(facecolor=theme.rgb(c), edgecolor="0.3",
                                 label=t) for t, c in legend]
            else:
                art = LineCollection(data, colors=rgb, linewidths=2.8,
                                     capstyle="butt", zorder=FACE_ZORDER)
                handles = [Line2D([0], [0], color=theme.rgb(c), lw=3,
                                  label=t) for t, c in legend]
            self.ax.add_collection(art, autolim=False)
            box = Legend(self.ax, handles, [h.get_label() for h in handles],
                         loc="upper left" if cells else "upper right",
                         **LEGEND)
            box.set_zorder(7.0)
            self.ax.add_artist(box)
            self.mask_artists += [art, box]
