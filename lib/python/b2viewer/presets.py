"""Derived quantities offered ready-made: expressions in the calculator,
quantities with choices in the plasma quantity tree.

PRESETS: (group, name, unit, expression) of the calculator. ENTRIES: the
quantities of the plasma tree with choices (groups Atomic rates,
Radiation rates, Light emission, Neutrals collisions rate), each choice
a menu for the species of the run (Species); the function of the items
chosen gives the expression.
The atomic, neutral and collision ones follow the MATLAB analysis tools
(Atomic/Distributions, Neutrals/.../neutrals_collisions...): EIRENE atom
density on the B2.5 grid (dab2) for the neutral stage (B2.5 na only for
standalone runs), ADAS years of the run (ratadas.filelist), masses of the
EIRENE species (massa, massm). b2plot computes all of them."""

import glob
import os
import re
from dataclasses import dataclass

from ..b2plot.labels import species_text
from .emission import ALL, COEFFICIENT, DENSITY, HYDROGEN, REACTIONS

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
        self.emission = None            # emission.RunEmission of the run
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

    def choices(self, kind, before=()):
        """The choices of a parameter of this kind: B2.5 species, EIRENE
        neutrals, (label, payload) pairs (the emission kinds from the run's
        coefficients, those depending on the choices before from
        before)."""
        if kind in EMISSION:
            return self.emission.items(kind, before) if self.emission \
                else []
        if kind in SELECTIONS:          # all, each element, each stage
            ions = [s for s in self.ions if SELECTIONS[kind](self, s)]
            label = {"prb": self.recombination, "prc": self.cx}.get(
                kind[:3], lambda s: s.name)
            return self._selection(ions, label) if ions else []
        if kind == "runsel":
            return self._run_selection()
        if kind == "radout":
            return [DENSITY, COEFFICIENT] if before[0][1][0] == "stage" \
                else [DENSITY]
        if kind in ("ionising", "recombining"):
            return [s for s in self.ions if self._next(s)]
        if kind == "cx":
            return [s for s in self.ions if self._next(s)] if \
                self.hydrogen() != "0*ne" else []
        if kind == "element":
            return [s for s in self.ions if not any(
                t.element == s.element and t.column < s.column
                for t in self.ions)]
        if kind == "atom":
            return [n for n in self.neutrals if n.stack == "a"]
        return {"neutral": self.neutrals}[kind]

    def label(self, kind, x):
        if isinstance(x, tuple):
            return x[0]
        return {"element": lambda s: s.element, "ionising": self.ionisation,
                "recombining": self.recombination, "cx": self.cx}.get(
                    kind, lambda s: s.name)(x)

    @staticmethod
    def _selection(ions, label):
        """All species, each element (all its stages), each stage."""
        els = list(dict.fromkeys(s.element for s in ions))
        return [ALL] + [("%s, all stages" % el, ("element", el))
                        for el in els] + [(label(s), ("stage", s))
                                          for s in ions]

    def _run_selection(self):
        """All species, each element (its B2.5 species, its EIRENE atom,
        the recombination of its ions), each EIRENE molecule and molecular
        ion: (label, payload) for _run_total."""
        els = list(dict.fromkeys(s.element for s in self.ions))
        out = [ALL] + [(el, ("element", el)) for el in els]
        em = self.emission
        if em is not None:
            em.items("eisel")           # the EIRENE species read
            out += [(m["SPECIES"].strip(), ("eirene", "molrad", i))
                    for i, m in enumerate(em.molecules)]
            out += [(t["SPECIES"].strip(), ("eirene", "ionrad", i))
                    for i, t in enumerate(em.test_ions)]
        return out

    def ionisation(self, s):
        return "%s \u2192 %s" % (s.name, self._next(s).name)

    def recombination(self, s):
        return "%s \u2192 %s" % (self._next(s).name, s.name)

    def cx(self, s):
        h0, hp = self.hydrogen_names()
        return "%s + %s \u2192 %s + %s" % (self._next(s).name, h0, s.name,
                                           hp)

    def hydrogen_names(self):
        """Names of the hydrogen atom and ion of the run (D0, D+1)."""
        hyd = [s for s in self.ions if s.element.lower() in HYDROGEN]
        h0 = next((s.name for s in hyd if s.charge == 0), "H0")
        return h0, next((s.name for s in hyd if s.charge == 1), "H+1")

    def hydrogen(self):
        """Density of the hydrogen atoms: the EIRENE ones on the B2.5 grid,
        else the B2.5 (fluid) neutral hydrogen."""
        if self.emission is not None:
            return self.emission.hydrogen_atoms() or "0*ne"
        return self.main_atom()

    def prc_year(self, element):
        """Year of the newest ADAS PRC file of an element (data.local,
        else modules), or None: the charge exchange radiation needs it."""
        el = "h" if element.lower() in HYDROGEN else element.lower()
        top = os.environ.get("SOLPSTOP", "")
        found = sorted(glob.glob(os.path.join(top, "data.local", "adas",
                                              "adf11", "prc*", "prc*_%s.dat"
                                              % el)) +
                       glob.glob(os.path.join(top, "modules", "adas",
                                              "adf11", "prc*", "prc*_%s.dat"
                                              % el)))
        years = [re.search(r"prc(\d+)_", os.path.basename(f)).group(1)
                 for f in found]
        return max(years, key=lambda y: (int(y) + 50) % 100) if years \
            else None

    def density(self, ion):
        """Density of a B2.5 species: for the neutral stage the EIRENE
        atom of the element on the B2.5 grid, as the MATLAB tools."""
        atom = next((n for n in self.neutrals if n.stack == "a" and
                     n.name.lower() == ion.element.lower()), None)
        if ion.charge == 0 and atom is not None:
            return "sel(dab2, %d)" % atom.column
        return "sel(na, %d)" % ion.column

    def main_atom(self):
        atoms = [n for n in self.neutrals if n.stack == "a"]
        return "sel(dab2, %d)" % atoms[0].column if atoms else "sel(na, 0)"

    def last(self, ion):
        return max(s.column for s in self.ions if s.element == ion.element)


def _stages(sp, sel, pick):
    """The B2.5 species of a selection (all, an element, a stage) that
    pick accepts."""
    if sel[0] == "stage":
        return [sel[1]]
    return [s for s in sp.ions if pick(sp, s) and (
        sel[0] == "all" or s.element == sel[1])]


def _plt(sp, s, out):
    """Line radiation of stage s (ADAS PLT): W m^-3, or W m^3."""
    c = "sel(adas('plt'), %d)" % s.column
    return c if out == COEFFICIENT else "ne*%s*%s" % (sp.density(s), c)


def _prb(sp, s, out):
    """Recombination radiation and bremsstrahlung of the stage after s
    (ADAS PRB of the recombining ion): W m^-3, or W m^3."""
    n = sp._next(s).column
    c = "sel(adas('prb'), %d)" % n
    return c if out == COEFFICIENT else "ne*sel(na, %d)*%s" % (n, c)


def _prc(sp, s, out):
    """Charge exchange recombination radiation of the stage after s with
    the hydrogen atoms (ADAS PRC): W m^-3, or W m^3."""
    n = sp._next(s).column
    c = "sel(adas('prc%s'), %d)" % (sp.prc_year(s.element), n)
    return c if out == COEFFICIENT else "%s*sel(na, %d)*%s" % (
        sp.hydrogen(), n, c)


def _radiation(part, pick):
    """Radiation of a selection (rate density: the sum over its stages) or
    the coefficient of a stage."""
    def f(sp, sel, out):
        sel = sel[1]
        return " + ".join("(%s)" % part(sp, s, out) for s in _stages(
            sp, sel, pick))
    return f


def _total(sp, sel):
    """All the radiation of the stages of a selection (ADAS), each stage
    as B2.5 counts it: its line radiation (if it has a next stage), its
    recombination radiation and bremsstrahlung and, where a PRC file is
    there, its charge exchange radiation (if it has a stage before)."""
    terms = []
    for s in _stages(sp, sel[1], lambda sp, s: True):
        if sp._next(s):
            terms.append(_plt(sp, s, DENSITY))
        before = next((t for t in sp.ions if sp._next(t) == s), None)
        if before is not None:
            terms.append(_prb(sp, before, DENSITY))
            if sp.prc_year(s.element) and sp.hydrogen() != "0*ne":
                terms.append(_prc(sp, before, DENSITY))
    return " + ".join("(%s)" % t for t in terms) or "0*ne"


def _run_total(sp, sel):
    """The radiation of the run (W per cell: B2.5 b2ra + b2br, EIRENE
    neutrad, molrad, ionrad, recrad) over the cell volume: its volume
    integral the power the run radiates. Of all species, an element (its
    B2.5 species, its EIRENE atom, the recombination of its ions) or an
    EIRENE molecule or molecular ion."""
    sel = sel[1]
    em = sp.emission
    eirene = em is not None and bool(em.atoms)
    last = max(s.column for s in sp.ions)
    if sel[0] == "eirene":
        terms = ["sel(%s, %d)" % (sel[1], sel[2])]
    elif sel[0] == "all":
        terms = ["sumz(b2ra + b2br, 0, %d)" % last]
        if eirene:
            terms.append("sumz(recrad, 0, %d)" % last)
            for name, species in (("neutrad", em.atoms), ("molrad",
                                  em.molecules), ("ionrad", em.test_ions)):
                if species:
                    terms.append("sumz(%s, 0, %d)" % (name, len(species) - 1))
    else:
        cols = [s.column for s in sp.ions if s.element == sel[1]]
        terms = ["sumz(b2ra + b2br, %d, %d)" % (min(cols), max(cols))]
        if eirene:
            terms.append("sumz(recrad, %d, %d)" % (min(cols), max(cols)))
            terms += ["sel(neutrad, %d)" % i for i, a in enumerate(em.atoms)
                      if a["SPECIES"].strip().lower() == sel[1].lower()]
    return "(%s)/max(vol, rtom(1e-30))" % " + ".join(terms)


def _rate(density, coefficient):
    """A rate density of a transition (of species s), or its rate
    coefficient."""
    return lambda sp, s, o: coefficient(sp, s) if o == COEFFICIENT else \
        density(sp, s)


def _ionisation(sp, s):
    return "ne*%s*%s" % (sp.density(s), _scd(sp, s))


def _scd(sp, s):
    return "sel(adas('scd'), %d)" % s.column


def _acd(sp, s):
    return "sel(adas('acd'), %d)" % sp._next(s).column


def _ccd(sp, s):
    return "sel(adas('ccd'), %d)" % sp._next(s).column


def _recombination(sp, s):
    return "ne*sel(na, %d)*%s" % (sp._next(s).column, _acd(sp, s))


def _charge_exchange(sp, s):
    return "%s*sel(na, %d)*%s" % (sp.hydrogen(), sp._next(s).column,
                                  _ccd(sp, s))


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
    return "(%s/10.374*1e6)" % _coefficient(p, g, "rtoe(1)")


EMISSION = ("zsel", "zwin", "zout", "zproc", "hwin", "hproc", "lightsel",
            "eisel",
            "eireac", "eiout", "output") + tuple(REACTIONS)
SELECTIONS = {                  # the stages a selection offers
    "pltsel": lambda sp, s: sp._next(s) is not None,
    "prbsel": lambda sp, s: sp._next(s) is not None,
    "prcsel": lambda sp, s: sp._next(s) is not None and bool(
        sp.prc_year(s.element)) and sp.hydrogen() != "0*ne",
    "totsel": lambda sp, s: True}
PAIR = (("Projectile", "neutral"), ("Background gas", "neutral"))
RADIATION_GROUP, LIGHT_GROUP = "Radiation rates", "Light emission"
RATES_GROUP = "Atomic rates"
COLLISIONS_GROUP = "Neutrals collisions rate (triangles)"
PLACE = {RADIATION_GROUP: "Charge sources", LIGHT_GROUP: "Charge sources",
         RATES_GROUP: "Charge sources",
         COLLISIONS_GROUP: "Neutrals (triangles)"}  # below these groups


@dataclass(frozen=True)
class Entry:
    """A quantity of the plasma tree with choices: its group and title,
    the choices (label, kind: Species.choices, a kind may depend on the
    choices before), its unit (or a function of the items chosen), the
    function of the items chosen giving the expression; lines: for the
    light, the function giving its lines (wavelength A, label, expression,
    emitters: emission.RunEmission.zparts; the expression their sum), the
    Spectrum of the chords."""
    group: str
    title: str
    params: tuple
    unit: object
    function: object
    lines: object = None

    def unit_of(self, items):
        return self.unit(*items) if callable(self.unit) else self.unit

    def units(self):
        """Its units in the plasma tree: with an Output menu that of the
        rate density or that of the coefficient."""
        if not callable(self.unit):
            return self.unit
        return " or ".join(dict.fromkeys(self.unit(o)
                                         for o in (DENSITY, COEFFICIENT)))


def _units(density, coefficient):
    """Unit by the output chosen."""
    return lambda *items: coefficient if COEFFICIENT in items else density


PHOTONS = _units("photons m^{-3} s^{-1}", "m^{3} s^{-1}")
POWER = _units("W m^{-3}", "W m^{3}")
RATES = _units("m^{-3} s^{-1}", "m^{3} s^{-1}")
OUTPUT = ("Output", "output")


def _eirene(sp, r, o):
    return r[1][1] if o == COEFFICIENT else r[1][0]


ENTRIES = [
    Entry(RATES_GROUP, "Ionisation (ADAS)",
          (("Transition", "ionising"), OUTPUT), RATES,
          _rate(_ionisation, _scd)),
    Entry(RATES_GROUP, "Recombination (ADAS)",
          (("Transition", "recombining"), OUTPUT), RATES,
          _rate(_recombination, _acd)),
    Entry(RATES_GROUP, "Charge-exchange with H0 (ADAS)",
          (("Transition", "cx"), OUTPUT), RATES,
          _rate(_charge_exchange, _ccd)),
    Entry(RATES_GROUP, "Ionisation (Eirene)",
          (("Reaction", "ionisation"), OUTPUT), RATES, _eirene),
    Entry(RATES_GROUP, "Recombination (Eirene)",
          (("Reaction", "recombination"), OUTPUT), RATES, _eirene),
    Entry(RATES_GROUP, "Dissociation (Eirene)",
          (("Reaction", "dissociation"), OUTPUT), RATES, _eirene),
    Entry(RATES_GROUP, "Charge exchange (Eirene)",
          (("Reaction", "charge exchange"), OUTPUT), RATES, _eirene),
    Entry(RADIATION_GROUP, "Line radiation (ADAS)",
          (("Species", "pltsel"), ("Output", "radout")), POWER,
          _radiation(_plt, SELECTIONS["pltsel"])),
    Entry(RADIATION_GROUP,
          "Recombination + bremsstrahlung radiation (ADAS)",
          (("Transition", "prbsel"), ("Output", "radout")), POWER,
          _radiation(_prb, SELECTIONS["prbsel"])),
    Entry(RADIATION_GROUP, "Charge-exchange radiation with H0 (ADAS)",
          (("Transition", "prcsel"), ("Output", "radout")), POWER,
          _radiation(_prc, SELECTIONS["prcsel"])),
    Entry(RADIATION_GROUP, "Total radiation (ADAS)",
          (("Species", "totsel"),), "W m^{-3}", _total),
    Entry(RADIATION_GROUP, "Neutrals radiation (Eirene)",
          (("Species", "eisel"), ("Reaction", "eireac"),
           ("Output", "eiout")), POWER,
          lambda sp, s, r, o: sp.emission.eirad(s[1], r, o)),
    Entry(RADIATION_GROUP, "Total radiation (ADAS+Eirene)",
          (("Species", "runsel"),), "W m^{-3}", _run_total),
    Entry(LIGHT_GROUP, "Photon emission (ADAS)",
          (("Species", "zsel"), ("Line", "zwin"), ("Output", "zout"),
           ("Process", "zproc")), PHOTONS,
          lambda sp, s, l, o, p: sp.emission.light(s[1], l, o, p),
          lambda sp, s, l, o, p: sp.emission.light_lines(s[1], l, o, p)),
    Entry(LIGHT_GROUP, "Power coefficient (ADAS)",
          (("Species", "zsel"), ("Line", "zwin"), ("Output", "zout"),
           ("Process", "zproc")), POWER,
          lambda sp, s, l, o, p: sp.emission.light(s[1], l, o, p, True),
          lambda sp, s, l, o, p: sp.emission.light_lines(s[1], l, o, p,
                                                         True)),
    Entry(LIGHT_GROUP, "Hydrogenic photon emission (Eirene)",
          (("Line", "hwin"), OUTPUT, ("Part", "hproc")), PHOTONS,
          lambda sp, l, o, p: sp.emission.hline(
              l[1], p[1], coefficient=o == COEFFICIENT),
          lambda sp, l, o, p: sp.emission.hlines(
              l[1], p[1], coefficient=o == COEFFICIENT)),
    Entry(LIGHT_GROUP, "Hydrogenic power coefficient (Eirene)",
          (("Line", "hwin"), OUTPUT, ("Part", "hproc")), POWER,
          lambda sp, l, o, p: sp.emission.hline(
              l[1], p[1], power=True, coefficient=o == COEFFICIENT),
          lambda sp, l, o, p: sp.emission.hlines(
              l[1], p[1], power=True, coefficient=o == COEFFICIENT)),
    Entry(LIGHT_GROUP, "Total photon emission (ADAS+Eirene)",
          (("Species", "lightsel"),), "photons m^{-3} s^{-1}",
          lambda sp, s: sp.emission.total_light(s[1]),
          lambda sp, s: sp.emission.total_lines(s[1])),
    Entry(LIGHT_GROUP, "Total power coefficient (ADAS+Eirene)",
          (("Species", "lightsel"),), "W m^{-3}",
          lambda sp, s: sp.emission.total_light(s[1], True),
          lambda sp, s: sp.emission.total_lines(s[1], True)),
    Entry(COLLISIONS_GROUP, "Collisions rate", PAIR + (OUTPUT,), RATES,
          lambda sp, p, g, o: _coefficient(p, g, _temperature(g)) if
          o == COEFFICIENT else "%s*%s*%s" % (
              _coefficient(p, g, _temperature(g)), _pden(g), _pden(p))),
    Entry(COLLISIONS_GROUP, "Neutral viscosity",
          (("Gas", "neutral"),), "Pa s",
          lambda sp, g: "1.381e-17/%s*(%s*11605)**0.75" % (
              _s0(g, g), _temperature(g))),
    Entry(COLLISIONS_GROUP, "Neutral diffusivity", PAIR, "m^{2} s^{-1}",
          lambda sp, p, g: "1.381e-17/(%s*(%d*%d/(%d + %d)))*6.023e26*"
          "(%s*11605)**0.75/%s" % (_s0(p, g), p.mass, g.mass, p.mass,
                                   g.mass, _temperature(g), _pden(g))),
    Entry(COLLISIONS_GROUP, "Neutral mean free path", PAIR, "cm",
          lambda sp, p, g: "%d**-0.5/%s*1.506e-9*(%s)**0.25/(%s/1e20)" % (
              p.mass, _s0(p, g), _temperature(g), _pden(g))),
]
ENTRY = {e.title: e for e in ENTRIES}
ENTRY_PREFIX = "entry:"         # tree name of an entry: the prefix, its title
