"""b2time.nc of a run: the time traces B2.5 writes at each time step (by
place: traces.py) and the profiles (at the midplanes, along the targets),
with the cells of the profiles on the plot. B2.5 names the targets by the
edges of the grid (Western, Eastern): the inner one is the one at the
smaller major radius."""

import numpy as np

from .files import B2TIME, Item, NcFile, summed, unit

# profiles by the letter after 3d: group, place, distance from the
# separatrix, cells of the values
PROFILES = {"a": ("Outer midplane", "mid_a", "dsa", "cvlista"),
            "i": ("Inner midplane", "mid_i", "dsi", "cvlisti"),
            "l": ("{W} target", "target_w", "dsl", "cvlistl"),
            "r": ("{E} target", "target_e", "dsr", "cvlistr")}
SPECIES = ("ns", "natm", "nmol")
PLACES = {"mid_a": "the outer midplane", "mid_i": "the inner midplane",
          "target_w": "the {w} target", "target_e": "the {e} target"}


class B2Time(NcFile):
    """An open b2time.nc; set_geometry places its cells on the plot."""

    def __init__(self, path):
        super().__init__(path)
        self.times = self.array(self.nc["timesa"])
        self.sides = ("Western", "Eastern")     # inner, outer once known
        self.lines = {}                 # place -> (n, 2) cell centres

    def set_geometry(self, geometry):
        """The cell centres of the lists of the profiles (B2.5 grid of the
        plot); the inner target: the one of smaller mean R."""
        row = {int(c): i for i, c in enumerate(geometry.cells)}
        self.lines = {}
        for group, place, ds, cells in PROFILES.values():
            if cells in self.nc.variables:
                icv = self.array(self.nc[cells]).astype(int).ravel()
                self.lines[place] = np.array(
                    [geometry.centres[row[c]] if c in row else
                     (np.nan, np.nan) for c in icv], float).reshape(-1, 2)
        r = [np.nanmean(self.lines[p][:, 0]) if p in self.lines else np.nan
             for p in ("target_w", "target_e")]
        if np.all(np.isfinite(r)) and r[0] != r[1]:
            self.sides = ("inner", "outer") if r[0] < r[1] else \
                ("outer", "inner")

    def side_text(self, text):
        """{W}, {E}, {w}, {e} and the Western and Eastern edges of the
        long names as the inner and outer targets, where known."""
        w, e = self.sides
        text = text.format(W=w[0].upper() + w[1:], E=e[0].upper() + e[1:],
                           w=w, e=e)
        if w != "Western":
            text = text.replace("Western edge", w + " target").replace(
                "Eastern edge", e + " target").replace(
                "Western", w).replace("Eastern", e)
        return text

    def _item(self, name, group, place):
        var = self.nc[name]
        long = str(getattr(var, "long_name", name)).strip()
        what = long.rsplit(", ", 1)[0] if ", " in long else long
        dim = next((d for d in var.dimensions if d in SPECIES), "")
        return Item(name, what[:1].upper() + what[1:], self.side_text(group),
                    unit(var), B2TIME, "profile", dim, 0,
                    self.side_text(group.lower()), place,
                    self.side_text(long))

    def items(self):
        """The profiles, in their groups in order."""
        variables = [v for v in self.nc.variables.values()
                     if v.dimensions[:1] == ("time",) and "3d" in v.name]
        return [self._item(v.name, group, place)
                for letter, (group, place, _, _) in PROFILES.items()
                for v in variables if v.name.split("3d")[-1] == letter]

    def series(self, item, cols=(0,)):
        """The profiles (nt, n) of the item, its species columns cols
        summed."""
        a = self.array(self.nc[item.name])
        return summed(a, 1, cols) if a.ndim == 3 else a

    def species_count(self, item):
        return len(self.nc.dimensions[item.dim]) if item.dim else 1

    def distance(self, item):
        """Distance from the separatrix of the points of a profile (m)."""
        name = PROFILES[item.name.split("3d")[-1]][2]
        return self.array(self.nc[name]).ravel() if name in \
            self.nc.variables else None

    def place(self, item):
        """("line", (n, 2)) of a profile on the plot, or None."""
        line = self.lines.get(item.place)
        return None if line is None else ("line", line)

    def place_text(self, item):
        """Where on the plot the item is, for the status bar."""
        return self.side_text(PLACES[item.place]) if item.place in PLACES \
            else ""
