"""Derived quantities offered ready-made in the calculator.

PRESETS: (group, name, unit, expression). TEMPLATES: (group, name, unit,
parameters, function), for the species of the run (Species) chosen in
the calculator; the function of the chosen species gives the expression.
The atomic, neutral and collision ones follow the MATLAB analysis tools
(Atomic/Distributions, Neutrals/.../neutrals_collisions...): EIRENE atom
density on the B2.5 grid (dab2) for the neutral stage (B2.5 na only for
standalone runs), ADAS years of the run (ratadas.filelist), masses of the
EIRENE species (massa, massm). b2plot computes all of them."""

import re
from dataclasses import dataclass

from ..b2plot.labels import species_text

PRESETS = [
    ("Plasma", "Ti/Te", "", "ti/te"),
    ("Plasma", "Electron pressure", "Pa", "ne*te*qe"),
    ("Plasma", "Ion pressure", "Pa", "ni*ti*qe"),
    ("Plasma", "Plasma pressure", "Pa", "(ne*te + ni*ti)*qe"),
    ("Plasma", "Gradient of Te", "eV/m", "sqrt(ddx(te)**2 + ddy(te)**2)"),
    ("Plasma", "Te gradient length", "m",
     "te/sqrt(ddx(te)**2 + ddy(te)**2)"),
    ("Plasma", "Flux-surface average of Te", "eV", "sumft(te*vol)/sumft(vol)"),
    ("Plasma", "Te change since the previous step", "eV", "te - te0"),
    ("Plasma", "Relative ne change since the previous step", "",
     "(ne - ne0)/ne0"),
    ("Plasma", "Particle source density", "m^{-3} s^{-1}", "pvol(sna)"),
    ("Neutrals", "Atom temperature", "eV", "2/3*edena/pdena"),
    ("Neutrals", "Molecule temperature", "eV", "2/3*edenm/pdenm"),
    ("Neutrals", "Atom pressure", "Pa", "2/3*edena*qe"),
    ("Neutrals", "Molecule pressure", "Pa", "2/3*edenm*qe"),
    ("Neutrals", "Atom flux density, R component", "m^{-2} s^{-1}",
     "vxdena/massa"),
    ("Neutrals", "Atom flux density, Z component", "m^{-2} s^{-1}",
     "vydena/massa"),
    ("Neutrals", "Atom to electron density", "", "etos(pdena)/ne"),
    ("Atomic", "Coronal radiation", "W", "cora()"),
    ("Masks", "Outer midplane cells", "", "iomp"),
    ("Masks", "Flux tube 10", "", "ift == 10"),
    ("Masks", "Te above 10 eV", "", "te > 10"),
]


@dataclass(frozen=True)
class Ion:
    """B2.5 species (column of the plasma quantities)."""
    column: int
    name: str
    element: str
    charge: int


@dataclass(frozen=True)
class Neutral:
    """EIRENE atom (stack a) or molecule (stack m), mass number."""
    stack: str
    column: int
    name: str
    mass: int


class Species:
    """Species of the run: names of the B2.5 species (RUNINFO), EIRENE
    atoms and molecules with their masses (b2plot massa, massm)."""

    def __init__(self, names=()):
        self.ions, self.neutrals = [], []
        for i, text in enumerate(names):
            m = re.match(r"([A-Za-z]+)\+?(\d+)$", species_text(text))
            if m:
                self.ions.append(Ion(i, m.group(0), m.group(1),
                                     int(m.group(2))))

    def set_neutrals(self, stack, names, masses):
        self.neutrals = [n for n in self.neutrals if n.stack != stack] + [
            Neutral(stack, i, name.strip(), int(round(mass)))
            for i, (name, mass) in enumerate(zip(names, masses))
            if name.strip()]

    def _next(self, ion):
        return next((s for s in self.ions if s.column == ion.column + 1
                     and s.element == ion.element), None)

    def choices(self, kind):
        """Species offered for a parameter of this kind."""
        return {"recombining": [s for s in self.ions if self._next(s)],
                "element": [s for s in self.ions if not any(
                    t.element == s.element and t.column < s.column
                    for t in self.ions)],
                "atom": [n for n in self.neutrals if n.stack == "a"],
                "neutral": self.neutrals}[kind]

    @staticmethod
    def label(kind, x):
        return x.element if kind == "element" else x.name

    def density(self, ion):
        """Density of a B2.5 species: for the neutral stage the EIRENE
        atom of the element on the B2.5 grid, as the MATLAB tools."""
        atom = next((n for n in self.neutrals if n.stack == "a" and
                     n.name.lower() == ion.element.lower()), None)
        if ion.charge == 0 and atom is not None:
            return "sel(dab2, %d)" % atom.column
        return "sel(na, %d)" % ion.column

    def main_atom(self):
        atoms = self.choices("atom")
        return "sel(dab2, %d)" % atoms[0].column if atoms else "sel(na, 0)"

    def last(self, ion):
        return max(s.column for s in self.ions if s.element == ion.element)


def _ionisation(sp, s):
    return "ne*%s*sel(adas('scd'), %d)" % (sp.density(s), s.column)


def _recombination(sp, s):
    return "ne*sel(na, %d)*sel(adas('acd'), %d)" % ((s.column + 1,) * 2)


def _charge_exchange(sp, s):
    return "%s*sel(na, %d)*sel(adas('ccd'), %d)" % ((sp.main_atom(),)
                                                    + (s.column + 1,) * 2)


def _radiation(sp, s):
    p = "(adas('plt') + adas('prb'))"
    return "ne*(%s*sel(%s, %d) + sumz(na*%s, %d, %d))" % (
        sp.density(s), p, s.column, p, s.column + 1, sp.last(s))


def _emission(sp, s):
    return ("ne*%s*npec(%d, 6561, 10, 1) + ne*sel(na, %d)*npec(%d, 6561, "
            "10, 2)" % (sp.density(s), s.column, s.column + 1, s.column))


def _pden(n):
    return "sel(pden%s, %d)" % (n.stack, n.column)


def _temperature(n):
    return "2/3*sel(eden%s, %d)/%s" % (n.stack, n.column, _pden(n))


def _coefficient(p, g, t):
    """AMMONX rate coefficient of projectile p in gas g at temperature t,
    the reaction named as by the MATLAB tools (D as H)."""
    def name(n):
        return re.sub(r"^[DT](?![a-z])", "H", n.name).upper()
    return "eamju('AMMONX', 'H.2', 'R-%s-%s', 'EL', %s)" % (
        name(p), name(g), t)


def _s0(p, g):
    return "(%s/10.374*1e6)" % _coefficient(p, g, "0*%s + 1" % _pden(g))


PAIR = (("Projectile", "neutral"), ("Background gas", "neutral"))
TEMPLATES = [
    ("Atomic", "Ionisation rate density of {0} (ADAS)", "m^{-3} s^{-1}",
     (("Species", "recombining"),), _ionisation),
    ("Atomic", "Recombination rate density into {0} (ADAS)", "m^{-3} s^{-1}",
     (("Species", "recombining"),), _recombination),
    ("Atomic", "Charge exchange rate density into {0} (ADAS)",
     "m^{-3} s^{-1}", (("Species", "recombining"),), _charge_exchange),
    ("Atomic", "Radiated power density of {0} (ADAS)", "W m^{-3}",
     (("Element", "element"),), _radiation),
    ("Atomic", "Line emission of {0} at 6561 A (adf15 PEC)",
     "photons m^{-3} s^{-1}", (("Species", "recombining"),), _emission),
    ("Atomic", "Atom ionisation rate density of {0} (AMJUEL 2.1.5)",
     "m^{-3} s^{-1}", (("Atom", "atom"),), lambda sp, a:
     "ne*sel(dab2, %d)*samju('AMJUEL', 'H.4', '2.1.5', 'EI', te, ne)"
     % a.column),
    ("Collisions", "Neutral rate coefficient, {0} on {1}", "m^{3} s^{-1}",
     PAIR, lambda sp, p, g: "%s*(%s*11605)**0.25*1e-6" % (
         _s0(p, g), _temperature(g))),
    ("Collisions", "Neutral collision rate, {0} on {1}", "s^{-1}", PAIR,
     lambda sp, p, g: "%s*%s" % (_coefficient(p, g, _temperature(g)),
                                 _pden(g))),
    ("Collisions", "Neutral collision density rate, {0} on {1}",
     "m^{-3} s^{-1}", PAIR, lambda sp, p, g: "%s*%s*%s" % (
         _coefficient(p, g, _temperature(g)), _pden(g), _pden(p))),
    ("Collisions", "Neutral viscosity, {0} self-collisions", "Pa s",
     (("Gas", "neutral"),), lambda sp, g: "1.381e-17/%s*(%s*11605)**0.75"
     % (_s0(g, g), _temperature(g))),
    ("Collisions", "Neutral diffusivity, {0} in {1}", "m^{2} s^{-1}", PAIR,
     lambda sp, p, g: "1.381e-17/(%s*(%d*%d/(%d + %d)))*6.023e26*(%s*11605)"
     "**0.75/%s" % (_s0(p, g), p.mass, g.mass, p.mass, g.mass,
                    _temperature(g), _pden(g))),
    ("Collisions", "Neutral mean free path, {0} in {1}", "cm", PAIR,
     lambda sp, p, g: "%d**-0.5/%s*1.506e-9*(%s)**0.25/(%s/1e20)" % (
         p.mass, _s0(p, g), _temperature(g), _pden(g))),
]
