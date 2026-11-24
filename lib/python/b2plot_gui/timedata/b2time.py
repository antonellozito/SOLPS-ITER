"""b2time.nc of a run: the time traces B2.5 writes at each time step (by
place: traces.py) and the profiles (at the midplanes, along the targets),
by place of the plot (the lines of their cells, clicked as the places of
the time traces) and in categories. B2.5 names the targets by the edges
of the grid (Western, Eastern): the inner one is the one at the smaller
major radius."""

import re

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
NAMES = {"mid_a": "Outer midplane", "mid_i": "Inner midplane",
         "target_w": "{W} target", "target_e": "{E} target"}
SHOWN = tuple(NAMES)                # the places on the plot, named
# the categories of the profiles by the name before 3d, in order; left
# out: the atom and molecule densities of B2.5 (an, mn: those of EIRENE
# are dab, dmb) and the radial neutral flux limiters (lh, ln)
GROUPS = ("Plasma state", "Plasma fluxes", "Transport coefficients",
          "Neutrals state")
CATEGORIES = (("ne", "na", "te", "ti", "po"),
              ("fn", "fl", "fo", "fe", "fi", "ft", "fc"),
              ("dn", "dp", "vx", "vy", "vs", "ke", "ki"),
              ("dab", "tab", "dmb", "tmb"))
LEFT_OUT = ("an", "mn", "lh", "ln")
# the fluxes along the targets shown as densities: divided by the target
# areas of b2time.nc (fcS of the target faces: the flux density on the
# target surface, as flush probes measure it) or by the poloidal contact
# areas (fcS |fcQalf|: the poloidal flux density)
TARGET_AREAS = {"l": {"target": "dsLT", "contact": "dsLP"},
                "r": {"target": "dsRT", "contact": "dsRP"}}
AREA_TEXT = {"target": "per target area",
             "contact": "per poloidal contact area"}


def flux_density_unit(u):
    """'s^-1' -> 'm^-2 s^-1', 'W' -> 'W m^-2' (the plain units)."""
    return u.replace("s^-1", "m^-2 s^-1", 1) if "s^-1" in u else \
        (u + " m^-2").strip()


class B2Time(NcFile):
    """An open b2time.nc; set_geometry places its cells on the plot."""

    def __init__(self, path):
        super().__init__(path)
        self.times = self.array(self.nc["timesa"])
        self.sides = ("Western", "Eastern")     # inner, outer once known
        self.codes = self.sides                 # IL, OL, IU, OU
        self.lines = {}                 # place -> (n, 2) cell centres

    def set_geometry(self, geometry):
        """The cell centres of the lists of the profiles (B2.5 grid of the
        plot); the inner target: the one of smaller mean R, a lower one
        below the middle of the core."""
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
            core = geometry.centres[np.asarray(geometry.region) == 1]
            z = np.nanmean((core if len(core) else geometry.centres)[:, 1])
            self.codes = tuple(s[0].upper() + (
                "L" if np.nanmean(self.lines[p][:, 1]) < z else "U")
                for s, p in zip(self.sides, ("target_w", "target_e")))

    def side_text(self, text):
        """{W}, {E}, {w}, {e} (the targets) and the Western and Eastern
        edges of the long names as the targets IL, OL, IU, OU, where
        known."""
        w, e = self.sides
        cw, ce = self.codes
        text = text.format(W=cw, E=ce, w=cw, e=ce)
        if w != "Western":
            text = text.replace("Western edge", cw + " target").replace(
                "Eastern edge", ce + " target").replace(
                "Western", w).replace("Eastern", e)
        return text

    def areas(self, item):
        """The areas ("target", "contact") the flux profile item can be
        divided by (none: not a flux along a target)."""
        base, letter = item.name.split("3d")[0], item.name.split("3d")[-1]
        if base not in CATEGORIES[1]:
            return ()
        return tuple(k for k, v in TARGET_AREAS.get(letter, {}).items()
                     if v in self.nc.variables)

    def _area(self, name, kind="target"):
        """The areas (n,) of kind dividing the flux profile name, or None
        (not a flux along a target)."""
        base, letter = name.split("3d")[0], name.split("3d")[-1]
        area = TARGET_AREAS.get(letter, {}).get(kind)
        if base not in CATEGORIES[1] or area not in self.nc.variables:
            return None
        a = self.array(self.nc[area]).ravel()
        return np.where(a > 0, a, np.nan)

    def _item(self, name, group, where, place):
        var = self.nc[name]
        long = str(getattr(var, "long_name", name)).strip()
        what = long.rsplit(", ", 1)[0] if ", " in long else long
        dim = next((d for d in var.dimensions if d in SPECIES), "")
        if name.split("3d")[0] in CATEGORIES[1]:
            # the plasma fluxes along the targets without "poloidal", the
            # electron and ion energy fluxes as heat fluxes
            what = re.sub(r"(?i)^poloidal\s+", "", what)
            if name.split("3d")[0] in ("fe", "fi"):
                what = what.replace("energy flux", "heat flux")
        u = unit(var)
        if self._area(name) is not None:
            u = flux_density_unit(u)
        return Item(name, what[:1].upper() + what[1:], group, u,
                    B2TIME, "profile", dim, 0,
                    self.side_text(where.lower()), place,
                    self.side_text(long))

    def items(self, place):
        """The profiles of a place (NAMES) in their categories, in order
        (a profile of no category with the plasma state)."""
        letter = next((k for k, p in PROFILES.items() if p[1] == place),
                      None)
        if letter is None:
            return []
        where = PROFILES[letter][0]
        names = [v.name for v in self.nc.variables.values()
                 if v.dimensions[:1] == ("time",) and "3d" in v.name and
                 v.name.split("3d")[-1] == letter and
                 v.name.split("3d")[0] not in LEFT_OUT]
        known = [b + "3d" + letter for c in CATEGORIES for b in c]
        out = []
        for group, bases in zip(GROUPS, CATEGORIES):
            out += [self._item(b + "3d" + letter, group, where, place)
                    for b in bases if b + "3d" + letter in names]
            if group == GROUPS[0]:
                out += [self._item(n, group, where, place) for n in names
                        if n not in known]
        return out

    def shapes(self):
        """{place: ("lines", (n, 2, 2) segments)}: the lines of the cell
        centres of the profiles (Marks.places)."""
        out = {}
        for place, line in self.lines.items():
            ok = np.isfinite(line).all(axis=1)
            seg = np.stack((line[:-1], line[1:]), axis=1)[ok[:-1] & ok[1:]]
            if len(seg):
                out[place] = ("lines", seg)
        return out

    @staticmethod
    def anchors(shapes, centre=None):
        """{place: (point, away)}: where the names go, away from the
        centre of the grid: the outer end of a midplane, the middle of a
        target."""
        if centre is None and shapes:
            centre = np.concatenate([s.reshape(-1, 2) for _, s in
                                     shapes.values()]).mean(axis=0)
        out = {}
        for k, (_, seg) in shapes.items():
            if k.startswith("mid"):
                v = seg.reshape(-1, 2)
                out[k] = (v[np.argmax(np.hypot(*(v - centre).T))], True)
            else:
                out[k] = (seg[len(seg) // 2].mean(axis=0), True)
        return out

    def series(self, item, cols=(0,), area="target"):
        """The profiles (nt, n) of the item, its species columns cols
        summed; a flux along a target per area (target or contact)."""
        a = self.array(self.nc[item.name])
        a = summed(a, 1, cols) if a.ndim == 3 else a
        div = self._area(item.name, area)
        return a if div is None else a / div

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
