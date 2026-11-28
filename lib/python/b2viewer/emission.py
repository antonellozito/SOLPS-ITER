"""Radiation and light of the run computed with the run's own coefficients,
as b2plot expressions for the quantities with choices of the plasma tree:
radiation in W m^-3, lines in photons m^-3 s^-1 or W m^-3 (all
directions).

- EIRENE species: the reaction cards of eirene_physics_model.input.json,
  radiation as EIRENE tallies it: per electron-impact event the electron
  energy loss less the energy given to the heavy particles and the
  potential energy (the ionisation potential of the atoms when the energy
  card has none); recombination of the bulk ions: their energy rate, ADAS
  energy rates less EIRENE's bremsstrahlung (b2plot ebrm). Te as EIRENE
  takes it (eirene_te_min, eirene_te_max of b2mn.dat), the EIRENE
  densities on the B2.5 grid.
- Hydrogen lines of EIRENE's default emissivity model (DEFAULT_LINES):
  AMJUEL H.12 population coefficients and the H.12, H.11 density ratios,
  each fit in its own range of the AMJUEL file (EIRENE takes the 400 eV
  limit of H.12 2.0c for all the line fits, so its emiss and emissmol
  differ from these lines where Te is above 400 eV).
- Impurity lines of the adf15 files (b2plot npec): excitation times ne and
  the stage density (the EIRENE atoms for the neutral stage), recombination
  times ne and the next stage, charge exchange times the hydrogen atoms
  and the next stage.
Line power: the photons times the transition energy of the line (the
hydrogen lines: DEFAULT_LINES; adf15: hc over the wavelength of each line
of the window, npec modes 4-6)."""

import json
import math
import os
import re

from .tools import cellfiles

QE = "qe"
VACUUM = "(ne > 1e8)"                   # EIRENE's vacuum cells (DVAC)
CRC = {"EI": "ionisation", "DS": "dissociation", "RC": "recombination"}
# DEFAULT_LINES (setup_default_emissivity.f): name, H.12 suffix, Einstein
# coefficient (1/s), transition energy (eV); wavelength (A) of the line in
# the hydrogen adf15 files
HLINES = (("Balmer alpha", "a", 4.410e7, 1.8889, 6561.9),
          ("Balmer beta", "c", 8.419e6, 2.5500, 4860.6),
          ("Balmer gamma", "d", 2.530e6, 2.8560, 4339.9),
          ("Balmer delta", "e", 9.732e5, 3.0222, 4101.2),
          ("Lyman alpha", "b", 4.699e8, 10.2375, 1215.2),
          ("Lyman beta", "a", 5.575e7, 12.089, 1025.3))
HPARTS = ("total", "atoms", "recombination", "molecules", "molecular ions",
          "negative ions", "H3+ ions")
ZPARTS = ("total", "excitation", "recombination", "charge exchange")
# emitters of the parts of a hydrogen line of the default model (their
# temperature and flow in the line shapes): kind, charge of the moving ion
HKIND = {"atoms": ("atom", None), "recombination": ("ion", 1),
         "molecules": ("molecule", None),
         "molecular ions": ("molecular ion", None),
         "negative ions": ("molecular ion", None),
         "H3+ ions": ("molecular ion", None)}
DENSITY = ("Rate density", "density")           # the outputs
COEFFICIENT = ("Coefficient", "coefficient")
ALL = ("All species", ("all",))
ZTOTAL = 500000                 # npec window (A) of all the lines of a file
TOTAL = (ZTOTAL, ZTOTAL, None)  # window, wavelength of the Total
# reactions of EIRENE offered (AMJUEL, HYDHEL): group -> (equation, file,
# section, reaction, process, reactants); X: the hydrogen isotope
REACTIONS = {
    "ionisation": (
        ("e + X -> X+ + 2e", "AMJUEL", "H.4", "2.1.5", "EI", ("e", "atom")),
        ("e + X2 -> X2+ + 2e", "AMJUEL", "H.4", "2.2.9", "EI",
         ("e", "molecule")),
        ("e + X2+ -> 2X+ + 2e", "AMJUEL", "H.4", "2.2.11", "EI",
         ("e", "molecular ion")),
        ("e + He -> He+ + 2e", "HYDHEL", "H.2", "2.3.9", "EI",
         ("e", "He atom"))),
    "recombination": (
        ("e + X+ -> X", "AMJUEL", "H.4", "2.1.8", "RC", ("e", "ion")),
        ("e + He+ -> He", "AMJUEL", "H.4", "2.3.13a", "RC",
         ("e", "He ion"))),
    "dissociation": (
        ("e + X2 -> e + 2X", "AMJUEL", "H.4", "2.2.5g", "DS",
         ("e", "molecule")),
        ("e + X2 -> 2e + X + X+", "AMJUEL", "H.4", "2.2.10", "DS",
         ("e", "molecule")),
        ("e + X2+ -> e + X + X+", "AMJUEL", "H.4", "2.2.12", "DS",
         ("e", "molecular ion")),
        ("e + X2+ -> 2X", "AMJUEL", "H.4", "2.2.14", "RC",
         ("e", "molecular ion"))),
    "charge exchange": (
        ("X+ + X -> X + X+", "HYDHEL", "H.2", "3.1.8", "CX", ("ion", "atom")),
        ("X+ + X2 -> X + X2+", "HYDHEL", "H.2", "3.2.3", "CX",
         ("ion", "molecule")))}
HYDROGEN = ("h", "d", "t")


def _float(text):
    """Fortran or C number, also '1.00000D 08'."""
    return float(re.sub(r"[dD]\s*", "e", text.strip()))


def _solpstop():
    return os.environ.get("SOLPSTOP", "")


def _json(rundir, name):
    path = cellfiles.find(rundir, name)
    if not path:
        return None
    with open(path) as fh:
        return json.load(fh)


def _element(name):
    """Element symbol of an EIRENE or B2.5 species name (D2+ -> D)."""
    m = re.match(r"([A-Za-z][a-z]?)", name.strip().capitalize())
    return m.group(1) if m else ""


class Cards:
    """The reaction cards of eirene_physics_model.input.json: number ->
    dicts (file, h, reac, crc, dp, adas element and stage)."""

    def __init__(self, strings):
        self.cards = {}
        for i, line in enumerate(strings):
            m = re.match(r"\s*(\d+)\s+CONST\s+(H\.\d+)\s+(\S+)\s", line)
            if m:
                self.cards.setdefault(int(m.group(1)), []).append(dict(
                    file="CONST", h=m.group(2), reac="", crc=m.group(3),
                    dp=0.0))
                continue
            m = re.match(r"\s*(\d+)\s+(\S+)\s+(H\.\d+)\s+(\S+)\s+(\S+)\s+"
                         r"\d+\s+\d+\s+(\S+)", line)
            if m:
                self.cards.setdefault(int(m.group(1)), []).append(dict(
                    file=m.group(2), h=m.group(3), reac=m.group(4),
                    crc=m.group(5), dp=_float(m.group(6))))

    def rate(self, number):
        """The rate (or energy rate) card of a number (the cross section
        cards H.0, H.1 of the same number left out)."""
        found = [c for c in self.cards.get(number, ())
                 if c["h"] not in ("H.0", "H.1")]
        return found[-1] if found else None


class RunEmission:
    """Emission quantities of a run: items(kind) gives the (label,
    payload) choices of the quantities with choices; the expression
    functions below turn the chosen payloads into b2plot expressions."""

    def __init__(self, rundir, species):
        self.rundir, self.species = rundir, species
        self._items = None

    # -- settings of the run -------------------------------------------
    def _load(self):
        r = self.rundir
        tmin = cellfiles.b2mn(r, "eirene_te_min", 0.0)
        tmax = cellfiles.b2mn(r, "eirene_te_max", 1e30)

        def te(floor):
            text = "max(te, rtom(%r))" % max(tmin, floor)
            return "min(%s, rtom(%r))" % (text, tmax) if tmax < 1e29 \
                else text
        self.te_rate = te(0.1)          # rates: Te cut at 0.1 eV
        self.te_energy = te(0.02)       # energy rates: TVAC
        self.te_line = te(math.exp(-2.30))      # emissivity.f: ln Te >= -2.3
        self.ne_fit = "max(ne, rtom(1e14))"      # fits: ne >= 1e8 cm^-3
        pm = (_json(r, "eirene_physics_model.input.json") or {}).get(
            "PHYSICS_MODEL", {})
        ss = pm.get("SPECIES_SPEC", {})
        self.cards = Cards(ss.get("REACTIONS", {}).get(
            "ClassicReactionStrings", []))
        self.atoms = ss.get("ATOMS", {}).get("SPECIES", [])
        self.molecules = ss.get("MOLECULES", {}).get("SPECIES", [])
        self.test_ions = ss.get("TEST_IONS", {}).get("SPECIES", [])
        self.bulk = pm.get("BACKGROUND", {}).get("BULK_IONS", {}).get(
            "SPECIES", [])
        pot = os.path.join(_solpstop(), "modules", "B2.5", "Database",
                           "ionization_potentials")
        for name in ("ionization_potentials", os.path.join(
                os.pardir, "ionization_potentials")):
            if os.path.isfile(os.path.join(r, name)):
                pot = os.path.join(r, name)
                break
        self.potentials = [line.split() for line in open(pot)] if \
            os.path.isfile(pot) else []

    def _column(self, element, charge):
        """B2.5 column of a species (element symbol, charge), or None."""
        hyd = element.lower() in HYDROGEN
        return next((s.column for s in self.species.ions if s.charge ==
                     charge and (s.element.lower() == element.lower() or
                                 hyd and s.element.lower() in HYDROGEN)),
                    None)

    def _eion(self, atom):
        """Ionisation potential EIRENE subtracts for an atom (init_eion.f:
        line of its nuclear charge, hydrogen isotopes with the reduced
        mass; EIRENE's masses)."""
        z, a = atom.get("NCHARA", 0), atom.get("NMASSA", 1)
        if not 0 < z <= len(self.potentials):
            return 0.0
        e = float(self.potentials[z - 1][0])
        if z == 1 and a != 1:
            e *= a * (1.0073 + 5.448e-4) / (5.448e-4 + a * 1.0073)
        return e

    # -- coefficient expressions ---------------------------------------
    def _coefficient(self, card, column, energy=False):
        """Rate (m^3/s) or energy rate (eV m^3/s) of a card, at EIRENE's
        background; ADAS cards with the year of the card, for the B2.5
        column of the stage."""
        if card["file"] == "ADAS":
            if column is None:
                return None
            text = "sel(adas('%s'), %d)" % (card["reac"], column)
            return "(%s/%s)" % (text, QE) if energy else text
        two = card["h"] in ("H.3", "H.4", "H.6", "H.7", "H.9", "H.10",
                            "H.12")
        return "samju('%s', '%s', '%s', '%s', %s%s)" % (
            card["file"], card["h"], card["reac"], card["crc"],
            self.te_energy if energy else self.te_rate,
            ", " + self.ne_fit if two else "")

    def _reactions(self, sp, kind):
        """(label, eV m^3/s expression) of the radiation per event times
        the rate of each electron-impact reaction of an EIRENE species
        (update.F: PRAD = ELEI + EHEAVY - DELE)."""
        k = {"atom": "A", "molecule": "M", "ion": "I"}[kind]
        element = _element(sp["SPECIES"])
        out = []
        for r in sp.get("REACTIONS", []):
            c = self.cards.rate(r.get("IREAC" + k, 0))
            if c is None or c["crc"] not in ("EI", "DS"):
                continue
            col = self._column(element, 0)
            rate = self._coefficient(c, col)
            flag = int(r.get("ISCDE" + k, 0))
            e_el, e_hv = r.get("EELEC" + k, 0.0), r.get("ESCD1" + k, 0.0)
            fr = r.get("FREAC" + k, 1.0)
            if rate is None or (flag // 10000) % 10 not in (0, 1, 3):
                continue
            parts, dele = [], 0.0
            if (flag // 10000) % 10 == 3:
                ce = self.cards.rate(int(e_el))
                en = self._coefficient(ce, col, energy=True) if ce else None
                if en is None:
                    continue
                parts.append(en)
                if ce["dp"] == 0 and kind == "atom":
                    dele = -self._eion(sp)
            elif (flag // 10000) % 10 == 1:
                parts.append("1.5*%s*%s" % (self.te_energy, rate))
                if kind == "atom":
                    dele = -self._eion(sp)
            else:
                parts.append("%r*%s" % (-e_el, rate))
                if kind == "atom":
                    dele = -self._eion(sp)
            if (flag // 100) % 10 == 3:
                ch = self.cards.rate(int(e_hv))
                if ch is not None:
                    parts.append("- " + self._coefficient(ch, col, True))
            elif e_hv:
                parts.append("- %r*%s" % (e_hv, rate))
            if dele:
                parts.append("- %r*%s" % (-dele, rate))
            text = " ".join([parts[0]] + [p if p.startswith("-") else
                                          "+ " + p for p in parts[1:]])
            out.append(("%s, %s %s %s" % (CRC[c["crc"]], c["file"], c["h"],
                                           c["reac"]),
                        "%r*(%s)" % (fr, text) if fr != 1 else text))
        return out

    def _recombination(self, ion):
        """eV m^3/s expression times ne of the radiation of the volume
        recombination of an EIRENE bulk ion (eirmod_infcop.F), or None."""
        element, charge = _element(ion["SPECIES"]), ion.get("NCHRGP", 0)
        col = self._column(element, charge)
        terms = []
        for r in ion.get("REACTIONS", []):
            c = self.cards.rate(r.get("IREACP", 0))
            if c is None or c["crc"] != "RC" or \
                    (int(r.get("ISCDEP", 0)) // 10000) % 10 != 3:
                continue
            ce = self.cards.rate(int(r.get("EELECP", 0)))
            en = self._coefficient(ce, col, energy=True) if ce else None
            if en is None or col is None:
                continue
            if ce["file"] == "ADAS":   # EIRENE's bremsstrahlung taken out
                en = "(%s - sel(ebrm, %d)/ne/%s)" % (en, col, QE)
            fr = r.get("FREACP", 1.0)
            terms.append("%r*%s" % (fr, en) if fr != 1 else en)
        if not terms or col is None:
            return None
        return col, " + ".join(terms)

    # -- choices -------------------------------------------------------
    def items(self, kind, before=()):
        """(label, payload) choices of a kind, those depending on the
        choices before (the items before) from them."""
        if self._items is None:
            self._load()
            tree, stages = self._eirad_tree(), self._zstages(self._zlines())
            self._items = {"eitree": tree, "zstages": stages}
        it = self._items
        if kind == "zsel":              # all, each element, each stage
            stages = it["zstages"]
            els = list(dict.fromkeys(el for el, _, _, _ in stages))
            return [ALL] + [("%s, all stages" % el, ("element", el))
                            for el in els] + [
                (name, ("stage", col, lines)) for _, name, col, lines
                in stages]
        if kind == "zwin":
            sel = before[0][1]
            return [("Total", (sel[1],) + TOTAL)] + list(sel[2]) \
                if sel[0] == "stage" else [("Total", sel)]
        if kind in ("zout", "eiout"):
            return [DENSITY, COEFFICIENT] if before[0][1][0] in (
                "stage", "species") else [DENSITY]
        if kind == "zproc":
            parts = ZPARTS if before[-1] == DENSITY else ZPARTS[1:]
            return [(p, p) for p in parts]
        if kind == "hwin":
            return [("Total", "total")] + [(h[0], h) for h in HLINES] \
                if self._hydrogen() else []
        if kind == "hproc":
            parts = HPARTS if before[-1] == DENSITY else HPARTS[1:]
            return [(p, p) for p in parts]
        if kind == "lightsel":          # all, each element
            els = list(dict.fromkeys([el for el, _, _, _ in it[
                "zstages"]] + ([self._hydrogen_element()] if
                               self._hydrogen() else [])))
            return [ALL] + [(el, ("element", el)) for el in els]
        if kind == "eisel":
            tree = it["eitree"]
            return ([ALL] if tree else []) + [
                (name, ("species", rows)) for name, rows in tree]
        if kind == "eireac":
            sel = before[0][1]
            return [("all reactions", None)] if sel[0] == "all" else \
                list(sel[1])
        if kind in REACTIONS:
            return self._reaction_items(kind)
        if kind == "output":
            return [DENSITY, COEFFICIENT]
        return []

    def _eirad_tree(self):
        """(species, [(reaction, (density, eV m^3/s))]) of the EIRENE
        radiation (radiated: density x ne x the eV m^3/s x qe): each
        species, all its reactions first, then each (when more than one);
        the volume recombination of each bulk ion."""
        out = {}
        groups = (("atom", "dab2", self.atoms), ("molecule", "dmb2",
                  self.molecules), ("ion", "dib2", self.test_ions))
        for kind, field, species in groups:
            for i, sp in enumerate(species):
                dens = "sel(%s, %d)" % (field, i)
                reacs = self._reactions(sp, kind)
                if not reacs:
                    continue
                rows = [("all reactions", (dens, " + ".join(
                    "(%s)" % e for _, e in reacs)))]
                if len(reacs) > 1:
                    rows += [(label, (dens, e)) for label, e in reacs]
                out.setdefault(sp["SPECIES"].strip(), []).extend(rows)
        for ion in self.bulk:
            rec = self._recombination(ion)
            if rec:
                col, text = rec
                out.setdefault(ion["SPECIES"].strip(), []).append((
                    "recombination", ("sel(na, %d)" % col, text)))
        return list(out.items())

    def eirad(self, sel, reaction, output):
        """W m^-3 (rate density) or W m^3 (coefficient: per ne and the
        density) of the EIRENE radiation of a species (sel), one reaction
        or all, or of all species."""
        if sel[0] == "all":
            rows = []
            for _, sp_rows in self._items["eitree"]:
                alls = [x for lbl, x in sp_rows if lbl == "all reactions"]
                rows += alls or [x for _, x in sp_rows]
            return " + ".join("%s*ne*(%s)*%s*%s" % (d, e, QE, VACUUM)
                              for d, e in rows)
        dens, e = reaction[1]
        if output == COEFFICIENT:
            return "(%s)*%s*%s" % (e, QE, VACUUM)
        return "%s*ne*(%s)*%s*%s" % (dens, e, QE, VACUUM)

    def _zstages(self, lines):
        """(element, stage, column, [(line, (column, wl, dwl,
        wavelength))]) of the adf15 lines of each B2.5 stage (_zlines):
        a window of npec per line, lines too close for a window of their
        own together (wavelength: their mean)."""
        out = []
        for s, found in lines:
            rows = []
            for wl, dwl, group in _windows(found):
                waves = ", ".join("%.1f" % w for w in group) if \
                    len(group) <= 3 else "%.1f to %.1f" % (group[0],
                                                           group[-1])
                kinds = ", ".join(k.lower() for k in ("EXCIT", "RECOM",
                                                      "CHEXC")
                                  if any(k in found[w] for w in group))
                rows.append(("%s A (%s)" % (waves, kinds),
                             (s.column, wl, dwl, sum(group) / len(group))))
            out.append((s.element, s.name, s.column, rows))
        return out

    def light(self, sel, line, output, part, power=False):
        """adf15 light: photons m^-3 s^-1 (W m^-3 with power) or the
        coefficient (m^3/s, W m^3) of a line window of a stage, of all
        the lines (Total) of a stage, an element or all species."""
        if sel[0] == "stage":
            if output == COEFFICIENT:
                return self.zcoef(line[1], part[1], power)
            return self.zline(line[1], part[1], power)
        cols = [col for el, _, col, _ in self._items["zstages"]
                if sel[0] == "all" or el == sel[1]]
        return " + ".join("(%s)" % self.zline((c,) + TOTAL, part[1],
                                              power) for c in cols)

    def light_lines(self, sel, line, output, part, power=False):
        """(wavelength A, label, expression, emitters: zparts) of each line
        window of the adf15 light light() gives (their sum)."""
        if sel[0] == "stage" and line[1][1] != ZTOTAL:
            rows = [(line[0], line[1])]
            name = next(n for _, n, c, _ in self._items["zstages"]
                        if c == sel[1])
            rows = [(name, rows)]
        else:
            rows = [(name, r) for el, name, col, r in self._items[
                "zstages"] if sel[0] == "all" or sel[0] == "element" and
                el == sel[1] or sel[0] == "stage" and col == sel[1]]
        coef = output == COEFFICIENT
        f = self.zcoef if coef else self.zline
        return [(w[3], "%s %s" % (name, label), f(w, part[1], power),
                 self.zparts(w, part[1], power, coef))
                for name, r in rows for label, w in r]

    def zparts(self, line, part, power=False, coefficient=False):
        """The emitters of an adf15 line window by their temperature and
        flow: [(kind, element, charge of the moving ion or None,
        expression)], the expressions adding up to the line: the excitation
        of the neutral stage by the atoms ("atom"), that of an ion by the
        ion ("ion"), recombination and charge exchange by the ion above
        (the emitter born from it); a stage of ions whole by its ion."""
        ion = next(s for s in self.species.ions if s.column == line[0])
        el, z = ion.element, ion.charge

        def f(p):
            return self.zcoef(line, p, power) if coefficient else \
                self.zline(line, p, power)
        if part != "total" or coefficient or z > 0:
            if part == "excitation" and z == 0:
                return [("atom", el, None, f(part))]
            return [("ion", el, z + (part in ("recombination",
                                              "charge exchange")), f(part))]
        rest = [x for x in (f("recombination"), f("charge exchange"))
                if x != "0*ne"]
        return [("atom", el, None, f("excitation"))] + (
            [("ion", el, 1, " + ".join(rest))] if rest else [])

    def hlines(self, line, part, power=False, coefficient=False):
        """(wavelength A, label, expression, emitters: hparts) of each line
        hline() gives (their sum)."""
        return [(ln[4], ln[0], self.hline(ln, part, power, coefficient),
                 self.hparts(ln, part, power, coefficient))
                for ln in (HLINES if line == "total" else (line,))]

    def hparts(self, line, part, power=False, coefficient=False):
        """The emitters of a hydrogen line of the default model as zparts:
        each part of the line with its own (HKIND)."""
        el = self._hydrogen_element()
        keys = list(self._hcomponents(line[1])) if part == "total" else \
            [part]
        if coefficient or len(keys) == 1:
            kind, z = HKIND.get(keys[0], ("atom", None))
            return [(kind, el, z, self.hline(line, part, power,
                                             coefficient))]
        return [HKIND[k][:1] + (el, HKIND[k][1], self.hline(line, k, power))
                for k in keys]

    def _hydrogen_element(self):
        atom = next(a for a in self.atoms if a.get("NCHARA") == 1)
        return _element(atom["SPECIES"])

    def _shared(self, el, name, rows):
        """The windows of a hydrogen stage of the adf15 files that hold a
        line of EIRENE's default model (those lines taken from EIRENE)."""
        if el.lower() not in HYDROGEN or not self._hydrogen():
            return []
        return [w for _, w in rows if any(
            w[1] - w[2] <= h[4] <= w[1] + w[2] for h in HLINES)]

    def total_lines(self, sel, power=False):
        """(wavelength A, label, expression, emitters) of every line of a
        selection
        (all species or an element): the adf15 lines, the hydrogen lines
        of EIRENE's default model in place of the same adf15 lines."""
        out = []
        for el, name, col, rows in self._items["zstages"]:
            if sel[0] == "element" and el != sel[1]:
                continue
            shared = self._shared(el, name, rows)
            out += [(w[3], "%s %s" % (name, label), self.zline(
                w, "total", power), self.zparts(w, "total", power))
                for label, w in rows if w not in shared]
        if self._hydrogen() and (sel[0] == "all" or
                                 sel[1] == self._hydrogen_element()):
            out += [(w, "%s %s (Eirene)" % (self._hydrogen_element(), lbl),
                     e, ps) for w, lbl, e, ps in self.hlines(
                         "total", "total", power)]
        return sorted(out, key=lambda x: x[0])

    def total_light(self, sel, power=False):
        """photons m^-3 s^-1 (W m^-3 with power) of total_lines (their
        sum): the stages whole less the windows taken from EIRENE."""
        terms = []
        for el, name, col, rows in self._items["zstages"]:
            if sel[0] == "element" and el != sel[1]:
                continue
            terms.append("(%s)" % self.zline((col,) + TOTAL, "total", power))
            terms += ["- (%s)" % self.zline(w, "total", power)
                      for w in self._shared(el, name, rows)]
        if self._hydrogen() and (sel[0] == "all" or
                                 sel[1] == self._hydrogen_element()):
            terms.append("(%s)" % self.hline("total", "total", power))
        return " ".join([terms[0]] + [t if t.startswith("-") else "+ " + t
                                      for t in terms[1:]]) if terms \
            else "0*ne"

    def _hydrogen(self):
        """Densities of the default model: hydrogenic atoms, bulk ions and
        molecules (sums over the isotopes), or None."""
        atoms = [i for i, a in enumerate(self.atoms)
                 if a.get("NCHARA") == 1]
        mols = [i for i, m in enumerate(self.molecules)
                if _element(m["SPECIES"]).lower() in HYDROGEN and
                m.get("NCHARM") == 2]
        ions = [self._column(_element(b["SPECIES"]), 1) for b in self.bulk
                if b.get("NCHARP") == 1 and b.get("NCHRGP") == 1]
        ions = [c for c in ions if c is not None]
        if not atoms:
            return None
        return (" + ".join("sel(dab2, %d)" % i for i in atoms),
                " + ".join("sel(na, %d)" % c for c in ions) or "0*ne",
                " + ".join("sel(dmb2, %d)" % i for i in mols) or "0*ne")

    def _hcomponents(self, x):
        """{component: (coefficient part, densities)} of the line of H.12
        suffix x of the default model (emissivity.f): the emission is A
        times the part times the densities; the coefficient per the two
        densities (ne and the parent, H2 and H2 for the H3+ ions) A times
        the part over ne."""
        atoms, ions, mols = self._hydrogen()

        def amj(h, r, two=True):
            return "samju('AMJUEL', '%s', '%s', 'OT', %s%s)" % (
                h, r, self.te_line, ", ne" if two else "")
        r20c = amj("H.12", "2.0c")
        return {
            "atoms": (amj("H.12", "2.1.5" + x), atoms),
            "recombination": (amj("H.12", "2.1.8" + x), ions),
            "molecules": (amj("H.12", "2.2.5" + x), mols),
            "molecular ions": ("%s*%s" % (amj("H.12", "2.2.14" + x), r20c),
                               mols),
            "negative ions": ("%s*%s" % (amj("H.12", "7.2" + x),
                                         amj("H.11", "7.0a", False)), mols),
            "H3+ ions": ("%s*%s*%s" % (amj("H.12", "2.2.15" + x), r20c,
                                       amj("H.11", "4.0a", False)),
                         "(%s)*(%s)/ne" % (mols, mols))}

    def hline(self, line, part, power=False, coefficient=False):
        """photons m^-3 s^-1 (W m^-3 with power) of a line of the default
        model (emissivity.f) or of all six ("total"), one component or all;
        with coefficient the coefficient of one component (m^3/s, W m^3:
        per ne and the parent density, per H2 twice for the H3+ ions)."""
        self.items("hwin")
        terms = []
        for ln in (HLINES if line == "total" else (line,)):
            comps = self._hcomponents(ln[1])
            factor = "%r" % (ln[2] * (ln[3] if power else 1.0))
            if coefficient:
                terms.append("%s*(%s)/ne" % (factor, comps[part][0]))
            else:
                text = " + ".join("(%s)*(%s)" % c for c in comps.values()) \
                    if part == "total" else "(%s)*(%s)" % comps[part]
                terms.append("%s*(%s)" % (factor, text))
        text = " + ".join("(%s)" % t for t in terms)
        if power:
            text = "(%s)*%s" % (text, QE)
        return "(%s)*%s" % (text, VACUUM)

    # -- impurity lines -------------------------------------------------
    def _zlines(self):
        """(B2.5 species, {wavelength (A, as b2plot reads it): block
        types}) of the adf15 files of the B2.5 species."""
        top = _solpstop()
        lst = next((p for p in (os.path.join(top, d, "adas",
                    "filelist.adas.adf15") for d in ("data.local",
                    "modules")) if os.path.isfile(p)), None)
        if lst is None:
            return []
        rows = [re.findall(r"'([^']*)'", line) for line in open(lst)]
        root = rows[0][0] if rows and rows[0] else ""
        if root.startswith("SOLPSTOP"):
            root = os.path.join(top, root[8:].lstrip("/"))
        entries = [r for r in rows[2:] if len(r) >= 2]
        out = []
        for s in self.species.ions:
            z = _nuclear(s.element)
            if not 0 < z <= len(entries) or s.charge >= z:
                continue
            grp, ext = entries[z - 1][0].strip(), entries[z - 1][1].strip()
            if grp == "none":
                continue
            el = grp.split("#")[-1]
            path = os.path.join(root, "adf15", grp, "%s_%s#%s%d.dat" % (
                grp, ext, el, s.charge))
            if not os.path.isfile(path):
                continue
            seen = {}
            for line in open(path, errors="replace"):
                m = re.match(r"\s*([0-9.]+)\s*A\s+\d+\s+\d+\s*/.*TYPE\s*=\s*"
                             r"(\w+)", line)
                if m:
                    seen.setdefault(_wla(line), set()).add(
                        m.group(2).upper())
            if seen:
                out.append((s, seen))
        return out

    def hydrogen_atoms(self):
        """Density of the hydrogen atoms: the EIRENE ones on the B2.5 grid,
        else (no EIRENE: fluid neutrals) the B2.5 neutral hydrogen."""
        self.items("zsel")              # the cards read
        atoms = [i for i, a in enumerate(self.atoms)
                 if _element(a["SPECIES"]).lower() in HYDROGEN]
        if atoms:
            return " + ".join("sel(dab2, %d)" % i for i in atoms)
        return " + ".join("sel(na, %d)" % s.column for s in self.species.ions
                          if s.element.lower() in HYDROGEN and
                          s.charge == 0)

    def zline(self, line, part, power=False):
        """photons m^-3 s^-1 (W m^-3 with power) of the adf15 lines of a
        stage within dwl A of a wavelength (npec; line: column, wavelength,
        dwl), one process or all."""
        col, wl, dwl = line[:3]
        ion = next(s for s in self.species.ions if s.column == col)
        nxt = next((s.column for s in self.species.ions if s.element ==
                    ion.element and s.charge == ion.charge + 1), None)
        pec = "npec(%d, %d, %d, %%d)" % (col, wl, dwl)
        mode = (lambda m: m + 3) if power else (lambda m: m)
        nh = self.hydrogen_atoms()
        comps = {"excitation": "%s*ne*%s" % (pec % mode(1),
                                              self.species.density(ion))}
        if nxt is not None:
            comps["recombination"] = "%s*ne*sel(na, %d)" % (pec % mode(2),
                                                             nxt)
            if nh:
                comps["charge exchange"] = "%s*(%s)*sel(na, %d)" % (
                    pec % mode(3), nh, nxt)
        if part == "total":
            return " + ".join(comps.values())
        return comps.get(part, "0*ne")

    @staticmethod
    def zcoef(line, part, power=False):
        """The adf15 photon emission coefficient (m^3/s; with power W m^3,
        hc/lambda of each line) of the lines of a stage within dwl A of a
        wavelength (npec), of one process."""
        col, wl, dwl = line[:3]
        mode = {"excitation": 1, "recombination": 2,
                "charge exchange": 3}[part] + (3 if power else 0)
        return "npec(%d, %d, %d, %d)" % (col, wl, dwl, mode)

    # -- reactions of EIRENE ---------------------------------------------
    def _densities(self):
        """Densities of the reactants of REACTIONS on the B2.5 grid, by
        hydrogen isotope (symbol, mass number) and for helium."""
        out = {}
        hyd = {}
        for i, a in enumerate(self.atoms):
            el = _element(a["SPECIES"])
            if el.lower() in HYDROGEN:
                hyd.setdefault(el, {})["atom"] = "sel(dab2, %d)" % i
            elif el.lower() == "he":
                out["He atom"] = "sel(dab2, %d)" % i
        for i, m in enumerate(self.molecules):
            el = _element(m["SPECIES"])
            if el.lower() in HYDROGEN and m.get("NCHARM") == 2:
                hyd.setdefault(el, {})["molecule"] = "sel(dmb2, %d)" % i
        for i, t in enumerate(self.test_ions):
            el = _element(t["SPECIES"])
            if el.lower() in HYDROGEN and "2" in t["SPECIES"]:
                hyd.setdefault(el, {})["molecular ion"] = "sel(dib2, %d)" % i
        for s in self.species.ions:
            el = s.element.capitalize()
            if el.lower() in HYDROGEN:
                d = hyd.setdefault(el, {})
                if s.charge == 1:
                    d["ion"] = "sel(na, %d)" % s.column
                elif s.charge == 0 and not self.atoms:    # fluid neutrals
                    d["atom"] = "sel(na, %d)" % s.column
            elif el.lower() == "he":
                if s.charge == 1:
                    out["He ion"] = "sel(na, %d)" % s.column
                elif s.charge == 0 and not self.atoms:
                    out["He atom"] = "sel(na, %d)" % s.column
        return hyd, out

    def _reaction_items(self, group):
        """(equation (database), (rate density, coefficient)) of the
        reactions of a group of REACTIONS whose reactants the run has."""
        hyd, other = self._densities()
        out = []
        for eq, db, h, reac, crc, who in REACTIONS[group]:
            isotopes = [(x, d) for x, d in hyd.items()] if "X" in eq else \
                [("", {})]
            for x, d in isotopes:
                dens = dict(other, **d, e="ne")
                if not all(w in dens for w in who):
                    continue
                if crc == "CX":         # heavy particles: T per mass
                    mass = {"h": 1, "d": 2, "t": 3}[x.lower()]
                    t = "max(ti, rtom(0.1))*%r" % (1.0 / mass)
                    coef = "samju('%s', '%s', '%s', '%s', %s)" % (
                        db, h, reac, crc, t)
                elif h == "H.4":
                    coef = "samju('%s', '%s', '%s', '%s', %s, %s)" % (
                        db, h, reac, crc, self.te_rate, self.ne_fit)
                else:
                    coef = "samju('%s', '%s', '%s', '%s', %s)" % (
                        db, h, reac, crc, self.te_rate)
                label = "%s (%s %s %s)" % (eq.replace("X", x).replace(
                    "->", "\u2192"), db, h, reac)
                out.append((label, ("%s*%s*%s" % (coef, dens[who[0]],
                                                  dens[who[1]]), coef)))
        return out


def _wla(header):
    """Wavelength (A) of an adf15 block as b2plot reads it (spect.F: the
    header up to its A, read with f8.1)."""
    k = header.find("A")
    text = header[:10] if k < 0 or k + 2 > 10 else header[:k + 1]
    field = text.ljust(10)[:8].replace("A", " ").strip()
    return float(field) if "." in field else int(field or 0) / 10.0


def _fit(w, i, j):
    """A window (wl, dwl) of npec holding the wavelengths w[i:j + 1] and
    no other of w, else None and whether a wavelength before them is in
    the way."""
    lo, hi = math.floor(w[i]), math.ceil(w[j])
    left = []
    for a, b in ([(lo, hi)] if (lo + hi) % 2 == 0 else
                 [(lo - 1, hi), (lo, hi + 1)]):
        before = i > 0 and w[i - 1] >= a
        after = j + 1 < len(w) and w[j + 1] <= b
        if not before and not after:
            return ((a + b) // 2, (b - a) // 2), False
        left.append(before and not after)
    return None, all(left)


def _windows(found):
    """[(wl, dwl, wavelengths)]: windows of npec (the blocks with |wl -
    lambda| <= dwl, integers) taking each wavelength of found once, the
    wavelengths no window can part taken together."""
    w = sorted(found)
    out = []                    # (wl, dwl, first, last)
    i = 0
    while i < len(w):
        j = i
        while True:
            fit, left = _fit(w, i, j)
            if fit is not None:
                break
            if left and out:
                i = out.pop()[2]
            else:
                j += 1
        out.append(fit + (i, j))
        i = j + 1
    return [(wl, dwl, w[a:b + 1]) for wl, dwl, a, b in out]


def _nuclear(symbol):
    """Nuclear charge of an element symbol (H isotopes 1)."""
    if symbol.lower() in HYDROGEN:
        return 1
    table = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V "
             "Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo").split()
    return table.index(symbol.capitalize()) + 1 if symbol.capitalize() in \
        table else 0
