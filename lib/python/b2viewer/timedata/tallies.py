"""b2tallies.nc of a run: the tallies B2.5 writes at each time step, by
volume region (cvReg; 0: the whole plasma) and by face region (fcReg), in
categories; the regions on the plot (the outlines and the cells of the
volume regions, the faces of the face regions) and their names (for the
texts: the plot shows none), those of a standard topology (tools.regions),
else numbers."""

import numpy as np

from ..tools import regions
from .files import TALLIES, Item, NcFile, summed, unit
from .traces import _faces

SOURCES = tuple("b2%s_%s_reg" % (k, q) for k in ("stbr", "stbc")
                for q in ("sna", "smo", "she", "shi", "sch"))
ATOMIC = ("rsanareg", "rsamoreg", "rsahireg", "rranareg", "rramoreg",
          "rrahireg", "rcxnareg", "rcxmoreg", "rcxhireg", "rqahereg",
          "rqradreg", "rqbrmreg")
ENERGY = ("b2qie", "b2joule", "b2visa", "b2fraa", "b2exbe", "b2exba",
          "b2divue", "b2divua")
VOLUME = (("Plasma state", ("nereg", "nareg", "tereg", "tireg", "poreg")),
          ("Plasma sources", SOURCES + ATOMIC + ENERGY),
          ("Residuals", ("resco_reg", "resmo_reg", "resmt_reg",
                         "reshe_reg", "reshi_reg", "respo_reg")))
SURFACE = (("Plasma fluxes", ("fnareg", "fhereg", "fhireg", "fhtreg",
                              "fchreg", "fhjreg", "fhmreg", "fhpreg")),)
# left out: the weighted and total ion densities, the electron particle
# sources and the additional and external sources, the radiation of b2
# and of the neutrals, the strange and obsolete terms, the volume, the
# convected energies, the incoming heat sources and those of b2sihs
LEFT_OUT = {"ne2reg", "nireg", "b2radreg", "b2bremreg", "rdneureg",
            "b2str", "b2wrong1", "b2wrong2", "b2wrong3", "volreg",
            "qconvereg", "qconvireg", "b2she", "b2shi", "b2she0",
            "b2shi0"} | {
    "b2%s_%s_reg" % (k, q) for k in ("stbr", "stbc", "stbm", "sext")
    for q in ("sne", "sna", "smo", "she", "shi", "sch")
    if k in ("stbm", "sext") or q == "sne"}
OTHER = "Other"
# what the tallies are, as the manual (appendix Quantities stored in
# b2tallies.nc) says
DESCRIBE = {
    "nereg": "Average electron density", "nareg": "Average ion density",
    "tereg": "Average electron temperature",
    "tireg": "Average ion temperature", "poreg": "Average potential",
    "rsanareg": "Ionisation particle source",
    "rsamoreg": "Ionisation parallel momentum source",
    "rsahireg": "Ionisation ion heat source",
    "rranareg": "Recombination particle source",
    "rramoreg": "Recombination parallel momentum source",
    "rrahireg": "Recombination ion heat source",
    "rcxnareg": "Charge-exchange particle source",
    "rcxmoreg": "Charge-exchange ion parallel momentum source",
    "rcxhireg": "Charge-exchange ion energy source",
    "rqahereg": "Electron cooling rate", "rqradreg": "Line radiation",
    "rqbrmreg": "Bremsstrahlung",
    "b2qie": "Electron/ion exchange term", "b2joule": "Joule heating",
    "b2visa": "Ion viscous heating",
    "b2fraa": "Heating from inter-species friction",
    "b2exbe": "Heating term to electrons from E\u00d7B",
    "b2exba": "Heating term to ions from E\u00d7B",
    "b2divue": "Heating term from \u2207u (electrons)",
    "b2divua": "Heating term from \u2207u (ions)",
    "b2she": "Incoming electron heat sources",
    "b2shi": "Incoming ion heat sources",
    "b2she0": "Electron heat sources from b2sihs",
    "b2shi0": "Ion heat sources from b2sihs",
    "resco_reg": "Continuity equation residuals",
    "resmo_reg": "Parallel momentum equations residuals",
    "resmt_reg": "Total parallel momentum equation residuals",
    "reshe_reg": "Electron heat equation residuals",
    "reshi_reg": "Ion heat equation residuals",
    "respo_reg": "Potential equation residuals",
    "fnareg": "Particle flux", "fhereg": "Electron thermal energy flux",
    "fhireg": "Ion thermal energy flux", "fhtreg": "Total energy flux",
    "fchreg": "Current", "fhjreg": "Electrostatic energy flux",
    "fhmreg": "Flux of parallel kinetic energy",
    "fhpreg": "Ionisation energy flux"}
WHOLE = "v0"                        # the whole plasma (volume region 0)


class Tallies(NcFile):
    """An open b2tallies.nc; set_geometry places its regions on the
    plot."""

    def __init__(self, path):
        super().__init__(path)
        self.times = self.array(self.nc["times"])
        self.shapes, self.names, self.at = {}, {}, {}
        self.cells = {}                 # volume region -> cell rows
        self.reg = None                 # cvReg of the cell rows

    def regions(self, kind):
        """The places of kind "v" (volume) or "f" (face) with values."""
        n = len(self.nc.dimensions["vreg" if kind == "v" else "freg"])
        return [k for k in ("%s%d" % (kind, r) for r in range(n))
                if k in self.names]

    def set_geometry(self, run, geo):
        """The regions on the plot from the geometry file geo of the run:
        each volume region its outline (faces between it and others) and
        its cells, each face region its faces; their names and where
        they go (volume: middle of its cells; faces: their middle, away
        from the centre; the whole plasma over the grid)."""
        g = run.geometry
        top = regions.topology(run, geo) if geo is not None else None
        vnames, fnames = (top[0], top[1]) if top else ({}, {})
        cvreg = geo.get("cvReg") if geo is not None else None
        freg, seg = _faces(geo) if geo is not None and "fcReg" in geo \
            else (None, None)
        xy = np.asarray(g.centres, float)
        centre = 0.5 * (np.nanmin(xy, axis=0) + np.nanmax(xy, axis=0))
        nv = len(self.nc.dimensions["vreg"])
        if cvreg is not None:
            rows = np.asarray(g.cells, int) - 1
            ok = (rows >= 0) & (rows < len(cvreg))
            self.reg = np.where(ok, cvreg[np.clip(rows, 0, len(cvreg) - 1)],
                                0)
            cv = geo.table("fcCv", len(freg)) if freg is not None else None
            for r in range(1, nv):
                inside = np.flatnonzero(self.reg == r)
                if not len(inside):
                    continue
                key = "v%d" % r
                self.cells[r] = inside
                self.shapes["a" + key] = ("area", [g.polygons[i]
                                                   for i in inside])
                if cv is not None:
                    side = [np.isin(cv[k] - 1, np.flatnonzero(cvreg == r))
                            for k in (0, 1)]
                    edge = side[0] != side[1]
                    self.shapes[key] = ("lines", seg[edge])
                else:
                    self.shapes[key] = ("lines", np.empty((0, 2, 2)))
                self.names[key] = vnames.get(r, "Volume region %d" % r)
                self.at[key] = (np.nanmean(xy[inside], axis=0), False)
            top_y = np.nanmax(xy[:, 1])
            self.names[WHOLE] = "Whole plasma"
            self.at[WHOLE] = (np.array([centre[0], top_y]), True)
        if freg is not None:
            nf = len(self.nc.dimensions["freg"])
            for r in range(1, nf):
                s = seg[freg == r]
                if not len(s):
                    continue
                key = "f%d" % r
                self.shapes[key] = ("lines", s)
                self.names[key] = fnames.get(r, "Face region %d" % r)
                self.at[key] = (s[len(s) // 2].mean(axis=0), True)
        self.centre = centre

    def region_at(self, row):
        """The volume region of the cell row of the plot, or None."""
        if self.reg is None or row is None or row < 0 or \
                row >= len(self.reg):
            return None
        key = "v%d" % int(self.reg[row])
        return key if key in self.names else None

    def items(self, place):
        """The tallies of a place ("v0" ... volume regions, "f1" ... face
        regions) in their categories, in order."""
        kind, r = place[:1], int(place[1:])
        dim = "vreg" if kind == "v" else "freg"
        groups = VOLUME if kind == "v" else SURFACE
        names = [v.name for v in self.nc.variables.values()
                 if v.dimensions[:1] == ("time",) and
                 v.dimensions[-1:] == (dim,)]
        known = {n for _, ns in groups for n in ns} | LEFT_OUT
        where = self.names.get(place, place).lower()
        out = []
        for group, ns in groups + ((OTHER, tuple(n for n in names
                                                 if n not in known)),):
            for n in ns:
                if n not in names:
                    continue
                var = self.nc[n]
                long = str(getattr(var, "long_name", n)).strip() or n
                text = DESCRIBE.get(n, long if long != n else n)
                out.append(Item(n, text[:1].upper() + text[1:], group,
                                unit(var), TALLIES, "tally",
                                "ns" if "ns" in var.dimensions else "", 0,
                                where, place, long, ((n, ""),)))
        return out

    def curves(self, item, cols=(0,)):
        """[("", tally (nt,))] of the item at its region, its species
        columns cols summed."""
        a = self.array(self.nc[item.name])[..., int(item.place[1:])]
        return [("", summed(a, 1, cols) if a.ndim == 2 else a)]

    def species_count(self, item):
        return len(self.nc.dimensions["ns"]) if item.dim else 1
