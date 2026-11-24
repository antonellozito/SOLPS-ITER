"""Stagnation surface of the parallel flow of one species: the line where
its parallel velocity ua (positive along B) is zero, interpolated between
the vertices of the B2.5 grid, drawn over the 2D plot by its layer (ua
asked for by Flow while the layer is shown)."""

import numpy as np
import matplotlib.tri as mtri

from .. import theme

ZORDER = 5.6                    # over the plasma and vector plots


def column(data, species):
    """The column of ua drawn: species, else the first ion."""
    if species is not None and 0 <= species < len(data.columns):
        return species
    ions = [k for k, c in enumerate(data.columns) if "+" in c]
    return ions[0] if ions else 0


def artists(ax, run, data, col, look):
    """The line ua = 0 of column col of the ua data (look: colour, width,
    style) on ax; [] where ua does not change sign."""
    if data.vertex is None:
        return []
    z = np.asarray(data.vertex[col], float)
    if not np.nanmin(z) < 0 < np.nanmax(z):
        return []
    g = run.geometry
    tri = mtri.Triangulation(g.vx[:, 0], g.vx[:, 1], g.triangles)
    cs = ax.tricontour(tri, np.nan_to_num(z), levels=[0.0],
                       colors=[theme.rgb(look[0])], linewidths=look[1],
                       linestyles=look[2], zorder=ZORDER)
    return [cs]


class Flow:
    """ua for the stagnation surface layer of a Tab2D: asked for from
    b2plot while the layer is shown, for the source shown (Final state,
    the frame of Run movies), kept on the run (stagnation_ua), the layer
    drawn again when it is here; its species in the layers panel."""

    def __init__(self, tab):
        self.tab, self.key, self.asked = tab, None, None

    def set_run(self):
        self.key = self.asked = None

    def _quantity(self):
        tab = self.tab
        qs = tab.movie_quantities if tab.time_box.movie() else \
            tab.final_quantities if tab.time_box.final() else []
        return next((q for q in qs if q.name == "ua"), None)

    def update(self):
        """ua asked for if the layer is shown and it is not the one of
        the source shown."""
        tab = self.tab
        if tab.run is None or not tab.plot.layer_styles[
                "stagnation"].visible:
            return
        q = self._quantity()
        if q is None:
            tab.status.emit("Stagnation surface: no ua in this source")
            return
        key = (id(tab.run), tab._source(q))
        if self.key != key and self.asked != key:
            self.asked = key
            tab.request.emit(("flow", q, (), key[1]))

    def deliver(self, q, data, source):
        tab = self.tab
        if data is None:
            tab.status.emit("Stagnation surface: b2plot returned no ua")
            return
        if (id(tab.run), source) != self.asked:
            return
        self.key = self.asked
        tab.run.stagnation_ua = data
        from ..panels.species import column_names
        st = tab.layers.style("stagnation")
        tab.layers.set_species(column_names(data.columns, tab._species()),
                               column(data, st.species))
        tab.plot.set_layer("stagnation", tab.layers.style("stagnation"))
        tab.canvas.draw_idle()

    follow = update                     # another frame or source
