"""Neutrals: the particles of the EIRENE neutrals of each element.

The ionisation (balance.nc alone, exact): the plasma particle sources of
the strata (papl + pmpl + pipl, a neutral keeping its stratum through
charge exchange and dissociation) by region, summed over the strata of
each birth place (the strata of b2.neutrals.parameters with one name
together: recycling by the boundary faces of the stratum, the name most
of them have; gas puff; volume recombination) and over the strata of the
other elements (the particles they sputter).

The balance (all the neutrals of an element): the sources, the particles
launched (recycling the atoms and molecules released by the plasma ions
of the strata, fort.44 wldpa, wldpm; the puff userfluxparm, the atoms
EIRENE launches, tflux of b2mod_eirene, shared by gpfc over the elements;
the recombination the plasma sink of its strata, balance.nc pppl; the
sputtered atoms and molecules, wldspta, wldsptm, by surface: a
non-default standard surface by its faces, the additional surfaces as the
vessel), and the sinks: the ionisation in each region, what EIRENE
absorbs at each surface (wlpump: atoms, molecules and test ions by their
atoms), absorbed by a non-default standard surface (in contact with the
plasma: named as its faces), pumped by an additional surface recycling
less than all (wlabsrp, 1 - recyct, above zero: numbered) or deposited on
the other additional surfaces (the vessel, kept by its material, e.g.
tungsten). The residual: sources minus sinks (balance.nc averaged over the
time steps of the run while fort.44 holds the last EIRENE call,
ionisation outside the B2.5 grid).

Molecules and test ions count by their atoms (mlcmp of
b2.neutrals.parameters, the test ion as its molecule).

EIRENE runs every stratum with its full source strength, B2.5 keeps the
fraction of its recycling coefficient (b2mod_eirene): the fort.44 tallies
and the puff of a stratum are scaled by it (recyceir of the stratum, or
with eirene_use_recyceir 0 in b2mn.dat recyc of the first ion of the
element; balance.nc holds the scaled sources). fort.44 gives the absorbed
and pumped fluxes by stratum from 20261126 (wlpump(A,k), ...), before only
summed over the strata: then scaled where all the strata of the element
have the same coefficient, else as EIRENE gives them.

The fate (with the pumped fluxes by stratum): what the neutrals of each
birth place become, the strata of the birth place (or, Sputtered, of the
other elements) by stratum: launched, sputtered in these strata, ionised,
absorbed, pumped, deposited, the residual."""

import json
import os
import re
from dataclasses import dataclass, field

import numpy as np

from ..catalog import Quantity
from ..model import Field
from ..tools import cellfiles, inspect, regions
from ..tools.equilibrium import vertex_values
from ..tools.wallprofile import _xpoints, target_names
from . import ncfile
from .fort44 import Fort44
from .strata import Strata

TALLY = ("eirene_mc_papl_sna_bal", "eirene_mc_pmpl_sna_bal",
         "eirene_mc_pipl_sna_bal")
PROCESSES = (("all", "Atoms, molecules and molecular ions", TALLY),
             ("atoms", "Atoms", TALLY[:1]),
             ("molecules", "Molecules", TALLY[1:2]),
             ("ions", "Molecular ions", TALLY[2:]))
RECOMBINATION = "eirene_mc_pppl_sna_bal"
GROUP = "Particle sources by neutral origin"
PREFIX = "nborn"                # names of the maps: nborn<row>[.<element>]
TOTAL = "t"                     # all the neutrals
SPUTTERED = "s"                 # the sputtered ones
UNIT = "m^{-3}.s^{-1}"
KINDS = {"C": ("Gas puff", "puff"),
         "V": ("Volume recombination", "recombination"),
         "T": ("Time-dependent source", "source")}
SIDES = {"I": "Inner", "O": "Outer", "L": "lower", "U": "upper"}
QUIET = 1e-4                    # a residual below this share: closed


def element(name):
    """Element of a species name (D0, D+1, Ne+10: D, D, Ne)."""
    return re.sub(r"(\+\d+|0)$", "", name.strip())


def lower_first(text):
    """First letter lower case unless the word is an abbreviation."""
    return text[:1].lower() + text[1:] if text[1:2].islower() else text


def _target(code, two):
    """IL: Inner lower target (two divertors) or Inner target, OL 2: Outer
    lower target 2, 3: Target 3."""
    head, _, num = code.partition(" ")
    if len(head) == 2 and head[0] in "IO" and head[1] in "LU":
        name = "%s %starget" % (SIDES[head[0]],
                                SIDES[head[1]] + " " if two else "")
        return name + (" " + num if num else "")
    return "Target " + code


@dataclass
class Row:
    name: str
    kind: str                   # recycling, puff, recombination, source,
    #                             sputtered, absorbed, pumped, deposited
    strata: list = field(default_factory=list)      # 0-based
    faces: list = field(default_factory=list)       # B2.5 faces (0-based)
    walls: list = field(default_factory=list)       # additional surfaces
    surfaces: list = field(default_factory=list)    # fort.44 (0-based)
    points: list = field(default_factory=list)      # the puff:
    #                                                 [(stratum, (R, Z))]

    @property
    def phrase(self):
        """How the map says it: born at the inner lower target, ..."""
        if self.kind == "puff":
            return "of the gas puff"
        if self.kind == "recombination":
            return "born by volume recombination"
        if self.kind == "sputtered":
            return lower_first(self.name)
        return "born at the " + lower_first(self.name)


def _namelist(rundir):
    """{key without blanks: values} of b2.neutrals.parameters."""
    nl = cellfiles.namelist(cellfiles.find(rundir, "b2.neutrals.parameters"))
    return {re.sub(r"\s+", "", k): v for k, v in nl.items()}


def _values(nl, key):
    return [float(str(v).replace("d", "e").replace("D", "E"))
            for v in nl.get(key, [])]


def _sequence(nl, key):
    """Values of a namelist entry, repeats (r*c) expanded."""
    out = []
    for v in nl.get(key, []):
        m = re.fullmatch(r"(\d+)\*(.+)", str(v))
        n, text = (int(m.group(1)), m.group(2)) if m else (1, str(v))
        out += [float(text.replace("d", "e").replace("D", "E"))] * n
    return out


def b2mn_int(rundir, name, default):
    """Integer value of name in b2mn.dat (the last one given, as B2.5
    reads it), default without it."""
    return int(cellfiles.b2mn(rundir, name, default))


class Origin:
    """The neutrals balance of the run (balance.nc at path, fort.44 and the
    strata of the run)."""

    def __init__(self, run, path):
        self.run = run
        self.bf = ncfile.BalanceFile(path)
        bf = self.bf
        self.why = "" if bf.nstra and bf.eirene and all(
            bf.has(n) and bf.nc[n].ndim == 3 for n in TALLY) else \
            "This balance.nc has no EIRENE tallies by stratum"
        self.ncv = bf.dims["nCv"]
        self.vol = bf.raw("cvVol").astype(float)
        self.cvreg = bf.raw("cvReg").astype(int)
        self.lbl = bf.raw("fcLbl").astype(int)
        self.geo = inspect.files(run)[0]
        self.nl = _namelist(run.rundir)
        f44 = os.path.join(run.rundir, "fort.44")
        try:
            self.f44 = Fort44(f44) if os.path.isfile(f44) else None
        except (OSError, ValueError, KeyError, IndexError):
            self.f44 = None
        if self.f44 is not None and self.f44.nstra != bf.nstra:
            self.f44 = None             # not the strata of balance.nc
        self.places = self._places()
        self.coef = self._coefficients()
        self.unscaled = set()           # elements whose absorbed and pumped
        #                                 fluxes could not be scaled
        self.drawn = None               # cells of the drawn region
        self._cache = {}
        self.regions = self._regions()
        self.sources, self.sinks = ([], []) if self.why else self._rows()
        self.elements = [] if self.why else [
            e for e in dict.fromkeys(element(s) for s in bf.species)
            if self._by_strata(e).any() or self.launched(e).any()]

    def close(self):
        self.bf.close()

    # ------------------------------------------------------------ names
    def _places(self):
        """{boundary face (0-based): name}: the targets, the PFR walls,
        the core boundary, the main chamber wall; with two divertors (an
        upper and a lower one) Inner lower target, ..., Lower and Upper PFR
        wall, Inner and Outer main chamber wall, with one Inner target,
        Outer target, PFR wall, Main chamber wall."""
        geo, run = self.geo, self.run
        if geo is None or geo.get("fcLbl") is None:
            return {}
        lbl = geo.get("fcLbl")
        nfc = len(lbl)
        fv, cv = geo.table("fcVx", nfc), geo.table("fcCv", nfc)
        x, y = geo.get("vxX"), geo.get("vxY")
        if fv is None or cv is None:
            return {}
        mid = 0.5 * (np.column_stack((x[fv[0] - 1], y[fv[0] - 1])) +
                     np.column_stack((x[fv[1] - 1], y[fv[1] - 1])))
        faces = np.flatnonzero(lbl)
        o, xps = _xpoints(run)
        tags = " ".join(t for _, t in xps)
        two = "upper" in tags and "lower" in tags
        out = {}
        tol = 1e-4 * float(np.ptp(x) + np.ptp(y))
        for key, code in target_names(run).items():
            seg = np.asarray(run.layers[key], float).reshape(-1, 4)
            tm = 0.5 * (seg[:, :2] + seg[:, 2:])
            d = np.hypot(mid[faces, None, 0] - tm[None, :, 0],
                         mid[faces, None, 1] - tm[None, :, 1]).min(axis=1)
            for f in faces[d < tol]:
                out[int(f)] = _target(code, two)
        nci = geo.scalar("nCi") or len(x)
        ft, ftreg = geo.get("cvFt"), geo.get("ftReg")
        for f in faces:
            if int(f) in out:
                continue
            c = (cv[0][f] if cv[0][f] <= nci else cv[1][f]) - 1
            reg = int(ftreg[ft[c] - 1]) if ft is not None and \
                ftreg is not None and 0 <= c < len(ft) and ft[c] >= 1 else 2
            if reg == 1:
                out[int(f)] = "Core boundary"
            elif reg == 3:
                out[int(f)] = (("Upper " if mid[f, 1] > o[1] else "Lower ")
                               if two else "") + "PFR wall"
            elif two:
                out[int(f)] = ("Inner" if mid[f, 0] < o[0] else "Outer") + \
                    " main chamber wall"
            else:
                out[int(f)] = "Main chamber wall"
        return out

    def _coefficients(self):
        """(atoms of fort.44, strata) the recycling coefficient B2.5 keeps
        of each stratum for the atoms of each element: recyceir of the
        stratum, or with eirene_use_recyceir 0 recyc of the first ion of
        the element (the species of one element and mass in a row; the
        next species for a duplicate atomic species, eb2atcr), as
        b2mod_eirene scales the sources; 1 where there is none."""
        f, ns = self.f44, self.bf.nstra
        c = np.ones((f.natm if f is not None else 0, ns))
        if f is None:
            return c
        if b2mn_int(self.run.rundir, "eirene_use_recyceir", 1) > 0:
            for key in self.nl:
                m = re.fullmatch(r"recyceir(?:\((\d+)\))?", key)
                if m is None:
                    continue
                k0 = int(m.group(1)) - 1 if m.group(1) else 0
                for n, v in enumerate(_sequence(self.nl, key)):
                    if 0 <= k0 + n < ns:
                        c[:, k0 + n] = v
            return c
        el = [element(n) for n in self.bf.species]
        za = self.bf.raw("za").astype(float)
        am = self.bf.raw("am").astype(float)
        nsp = len(el)
        seq, j = [], 0                  # b2espcr: the element sequences
        for i in range(nsp):
            if i == 0 or el[i] != el[i - 1] or abs(am[i] - am[i - 1]) >= \
                    1e-3:
                j += 1
            seq.append(j)
        recyc = np.array([[1.0 if za[i] != 0 and el[i] != "C" else 0.0] *
                          ns for i in range(nsp)])    # defaults of B2.5
        for key in self.nl:
            m = re.fullmatch(r"recyc(?:\((\d+),(\d+)\))?", key)
            if m is None:
                continue
            i0, k0 = (int(m.group(1)), int(m.group(2)) - 1) if \
                m.group(1) else (0, 0)
            for n, v in enumerate(_sequence(self.nl, key)):
                if 0 <= i0 + n < nsp and 0 <= k0 < ns:
                    recyc[i0 + n, k0] = v
        first = {}
        for i in range(nsp):
            first.setdefault(seq[i], i)
        given = [int(v) for v in _sequence(self.nl, "eb2atcr")]
        for ia in range(f.natm):
            ref = next((i for i in range(nsp) if za[i] != 0 and
                        seq[i] == ia + 1), None)
            if ref is None:             # a duplicate atomic species
                j = given[ia] if ia < len(given) else first.get(ia + 1, -1)
                if 0 <= j and j + 1 < nsp and za[j] < za[j + 1] and \
                        el[j] == el[j + 1] and abs(am[j] - am[j + 1]) < 1e-2:
                    ref = j + 1
            if ref is not None:
                c[ia] = recyc[ref]
        return c

    def _name(self, faces, fallback):
        """The name most of the faces have."""
        names = [self.places[int(f)] for f in faces if int(f) in
                 self.places]
        return max(set(names), key=names.count) if names else fallback

    def _puff(self, k):
        """[(R, Z)] middles of the source surfaces of stratum k (0-based)
        in eirene.input.json: INSOR an additional surface, minus a
        non-default standard one (as EIRENE samsrf; INDIM 1 to 3, grid
        surfaces, left out)."""
        path = cellfiles.find(self.run.rundir, "eirene.input.json")
        f = self.f44
        if not path or f is None:
            return []
        try:
            with open(path) as fh:
                strata = json.load(fh).get("SOURCES", {}).get("STRATA", [])
        except (OSError, ValueError):
            return []
        out = []
        std = f.standard_faces()
        for s in strata:
            if s.get("ISTRA") != k + 1:
                continue
            for sub in s.get("SUBSTRATA", []):
                i = int(sub.get("INSOR", 0))
                if sub.get("INDIM") in (1, 2, 3) or i == 0:
                    continue
                if 0 < i <= f.nlim:
                    p = f.walls()[i - 1].mean(axis=0)
                elif -len(std) <= i < 0 and len(std[-i - 1]) and \
                        self.geo is not None:
                    faces = std[-i - 1]
                    fv = self.geo.table("fcVx", len(self.lbl))
                    x, y = self.geo.get("vxX"), self.geo.get("vxY")
                    v = np.concatenate((fv[0][faces], fv[1][faces])) - 1
                    p = np.array((x[v].mean(), y[v].mean()))
                else:
                    continue
                if not any(np.allclose(p, q) for q in out):
                    out.append(tuple(map(float, p)))
        return out

    def _rows(self):
        """(sources, sinks) as Rows."""
        st = Strata(self.run.rundir)
        births = {}
        owner = self._strata_elements()     # puffs numbered by element
        puffs = [k for k in range(self.bf.nstra) if k < len(st.kinds) and
                 KINDS.get(st.kinds[k][:1], ("", ""))[1] == "puff"]
        for k in range(self.bf.nstra):
            code = st.kinds[k][:1] if k < len(st.kinds) else ""
            faces = []
            if code == "A":
                lo, hi = sorted((st.start[k], st.end[k]))
                faces = np.flatnonzero((self.lbl >= lo) & (self.lbl <= hi) &
                                       (self.lbl != 0)).tolist()
                name = self._name(faces, "Boundary label %d" % lo
                                  if lo == hi else
                                  "Boundary labels %d to %d" % (lo, hi))
                kind = "recycling"
            elif code in KINDS:
                name, kind = KINDS[code]
                same = [j for j in puffs if owner[j] == owner[k]]
                if kind == "puff" and len(same) > 1:
                    name = "%s %d" % (name, same.index(k) + 1)
            elif code in ("N", "S", "E", "W"):
                name, kind = "Stratum %d (%s boundary)" % (k + 1, code), \
                    "recycling"
            else:
                name, kind = "Stratum %d" % (k + 1), "source"
            row = births.setdefault(name, Row(name, kind))
            row.strata.append(k)
            row.faces += faces
            if kind == "puff":
                row.points += [(k, p) for p in self._puff(k)]
        sources, sinks = list(births.values()), []
        f = self.f44
        if f is None:
            return sources, sinks
        std = f.standard_faces()
        sput, pump = self._surface_totals()
        named = {}
        for s in np.flatnonzero(sput.any(axis=1)):
            if s < f.nlim:
                key = "Sputtered at the vessel"
                row = named.setdefault(key, Row(key, "sputtered"))
                row.walls.append(int(s))
            else:
                faces = std[s - f.nlim] if s - f.nlim < len(std) else []
                key = "Sputtered at the " + lower_first(
                    self._name(faces, "standard surface %d" % (s - f.nlim
                                                               + 1)))
                row = named.setdefault(key, Row(key, "sputtered"))
                row.faces += list(map(int, faces))
            row.surfaces.append(int(s))
        sources += list(named.values())
        absorbed, n = {}, 0
        recycled = ~(f.by_species("wlabsrp(A)", f.natm) > 0).any(axis=1) \
            if f.has("wlabsrp(A)") else np.zeros(f.nsurf, bool)
        deposit = Row("Deposited on the vessel", "deposited")
        for s in np.flatnonzero(pump.any(axis=1)):
            if s < f.nlim and recycled[s]:      # kept by its material
                deposit.walls.append(int(s))
                deposit.surfaces.append(int(s))
            elif s < f.nlim:                    # a pump: recycles < 1
                n += 1
                sinks.append(Row("Pumping surface %d" % n, "pumped",
                                 walls=[int(s)], surfaces=[int(s)]))
            else:
                faces = std[s - f.nlim] if s - f.nlim < len(std) else []
                key = "Absorbed by the " + lower_first(self._name(
                    faces, "standard surface %d" % (s - f.nlim + 1)))
                row = absorbed.setdefault(key, Row(key, "absorbed"))
                row.faces += list(map(int, faces))
                row.surfaces.append(int(s))
        if len(sinks) == 1:                     # one pump: no number
            sinks[0].name = "Pumping surface"
        return sources, list(absorbed.values()) + sinks + (
            [deposit] if deposit.surfaces else [])

    # ------------------------------------------------------- composition
    def _atoms(self, el):
        """(index of the atom of el in fort.44 or None, {molecule index:
        atoms of el in it}, {test ion index: atoms of el in it})."""
        f = self.f44
        if f is None:
            return None, {}, {}
        ia = next((i for i, a in enumerate(f.atoms)
                   if a.strip().lower() == el.lower()), None)
        mols = {}
        for im in range(f.nmol):
            w = _values(self.nl, "mlcmp(1,%d)" % (im + 1))
            if ia is not None and ia < len(w) and w[ia]:
                mols[im] = w[ia]
        ions = {}
        for ii, name in enumerate(f.ions):
            base = name.strip().rstrip("+")
            im = next((m for m, mn in enumerate(f.molecules)
                       if mn.strip() == base), None)
            if im in mols:
                ions[ii] = mols[im]
        return ia, mols, ions

    def _surface_totals(self):
        """(sputtered, absorbed) (surfaces, atoms of fort.44), all
        strata, the molecules and test ions by their atoms."""
        f = self.f44
        sput = np.zeros((f.nsurf, f.natm))
        pump = np.zeros((f.nsurf, f.natm))
        for ia in range(f.natm):
            sput[:, ia], pump[:, ia] = self._element_surfaces(ia)
        return sput, pump

    def by_stratum(self):
        """Whether fort.44 has the absorbed and pumped fluxes by stratum."""
        return self.f44 is not None and self.f44.has("wlpump(A,1)")

    def _stratum_surfaces(self, ia, k):
        """(sputtered, absorbed) by surface of the atoms of fort.44 atom ia
        (molecules and test ions by their atoms of ia) in stratum k
        (0-based), scaled by its recycling coefficient; absorbed None
        without the pumped fluxes by stratum."""
        key = ("surfk", ia, k)
        if key in self._cache:
            return self._cache[key]
        f = self.f44
        _, mols, ions = self._atoms(f.atoms[ia].strip())
        c = self.coef[ia, k]
        sput = np.zeros(f.nsurf)
        if f.has("wldspta(%d)" % (k + 1)):
            sput += f.by_surface("wldspta(%d)" % (k + 1), f.natm)[:, ia]
        if mols and f.has("wldsptm(%d)" % (k + 1)):
            sm = f.by_surface("wldsptm(%d)" % (k + 1), f.nmol)
            sput += sum(w * sm[:, im] for im, w in mols.items())
        pump = None
        if self.by_stratum():
            pump = f.by_species("wlpump(A,%d)" % (k + 1), f.natm)[:, ia].copy()
            if mols and f.has("wlpump(M,%d)" % (k + 1)):
                pm = f.by_species("wlpump(M,%d)" % (k + 1), f.nmol)
                pump += sum(w * pm[:, im] for im, w in mols.items())
            if ions and f.has("wlpump(I,%d)" % (k + 1)):
                pi = f.by_species("wlpump(I,%d)" % (k + 1), f.nion)
                pump += sum(w * pi[:, ii] for ii, w in ions.items())
            pump *= c
        self._cache[key] = (c * sput, pump)
        return self._cache[key]

    def _element_surfaces(self, ia):
        """(sputtered, absorbed) by surface of the atoms of fort.44 atom
        ia (molecules and test ions by their atoms of ia)."""
        key = ("surf", ia)
        if key in self._cache:
            return self._cache[key]
        f = self.f44
        if self.by_stratum():           # exact: by stratum
            parts = [self._stratum_surfaces(ia, k) for k in range(f.nstra)]
            self._cache[key] = (sum(p[0] for p in parts),
                                sum(p[1] for p in parts))
            return self._cache[key]
        _, mols, ions = self._atoms(f.atoms[ia].strip())
        c = self.coef[ia]
        sput = np.zeros(f.nsurf)
        for k in range(1, f.nstra + 1):
            if f.has("wldspta(%d)" % k):
                sput += c[k - 1] * f.by_surface("wldspta(%d)" % k,
                                                f.natm)[:, ia]
            if mols and f.has("wldsptm(%d)" % k):
                sm = f.by_surface("wldsptm(%d)" % k, f.nmol)
                sput += c[k - 1] * sum(w * sm[:, im]
                                       for im, w in mols.items())
        pump = np.zeros(f.nsurf)
        if f.has("wlpump(A)"):
            pump += f.by_species("wlpump(A)", f.natm)[:, ia]
        if mols and f.has("wlpump(M)"):
            pm = f.by_species("wlpump(M)", f.nmol)
            pump += sum(w * pm[:, im] for im, w in mols.items())
        if ions and f.has("wlpump(I)"):
            pi = f.by_species("wlpump(I)", f.nion)
            pump += sum(w * pi[:, ii] for ii, w in ions.items())
        if (c == c[0]).all():           # summed over the strata in fort.44
            pump *= c[0]
        elif pump.any():
            self.unscaled.add(f.atoms[ia].strip().lower())
        self._cache[key] = (sput, pump)
        return sput, pump

    # ----------------------------------------------------------- values
    def puffs(self, row, el):
        """[(R, Z)] where the strata of a puff row puff element el."""
        owner = self._strata_elements()
        return list(dict.fromkeys(p for k, p in row.points
                                  if owner[k] in (None, el)))

    def _species(self, el):
        return [i for i, s in enumerate(self.bf.species) if element(s) == el]

    def _strata_elements(self):
        """Element of each stratum (species_start), None if not known."""
        start = [int(v) for v in _values(self.nl, "species_start")]
        sp = self.bf.species
        return [element(sp[start[k]]) if k < len(start) and
                0 <= start[k] < len(sp) else None
                for k in range(self.bf.nstra)]

    def _by_strata(self, el, process="all"):
        """(nCv, nstra) particles of el the plasma gets (s^-1) from the
        neutrals of each stratum by the collisions of process (key of
        PROCESSES; the molecules negative where they take ions)."""
        key = ("strata", el, process)
        if key not in self._cache:
            names = dict((p[0], p[2]) for p in PROCESSES)[process]
            self._cache[key] = sum(self.bf.strata(n, self._species(el))
                                   for n in names)
        return self._cache[key]

    def _mine(self, el):
        """The strata of el (or of no known element)."""
        return np.array([o in (None, el) for o in self._strata_elements()])

    def cells(self, el, key, process="all"):
        """(nCv,) particles of el ionised (s^-1) from a source of the
        ionisation table: key a birth place (index in sources), "s" the
        sputtered particles (in the strata of the other elements), "t"
        all the neutrals."""
        s, mine = self._by_strata(el, process), self._mine(el)
        if key == TOTAL:
            return s.sum(axis=1)
        if key == SPUTTERED:
            return s[:, ~mine].sum(axis=1)
        k = [k for k in self.sources[int(key)].strata if mine[k]]
        return s[:, k].sum(axis=1)

    def ionisation(self, el, process="all", extra=()):
        """The ionisation table of el (balance.nc alone): rows the birth
        places with a stratum of el and Sputtered (the strata of the other
        elements), with their key of cells, then Total; columns the
        regions and the extra (name, cells) ones: {"rows": [(name, kind,
        Row, key)], "columns": names, "values": (rows, columns)}."""
        cols = self.regions + list(extra)
        rows, values = [], []
        mine = self._mine(el)
        keys = [str(j) for j, r in enumerate(self.sources)
                if r.kind != "sputtered" and any(mine[k] for k in r.strata)
                and self.cells(el, str(j)).any()]     # something ionised
        if (~mine).any() and self.cells(el, SPUTTERED).any():
            keys.append(SPUTTERED)
        for key in keys:
            c = self.cells(el, key, process)
            if key == SPUTTERED:
                row = Row("Sputtered", "sputtered")
                for r in self.sources:
                    if r.kind == "sputtered":
                        row.faces += r.faces
                        row.walls += r.walls
                name = "Sputtered"
            else:
                row = self.sources[int(key)]
                name = row.name
            rows.append((name, row.kind, row, key))
            values.append([c[m].sum() for _, m in cols])
        c = self.cells(el, TOTAL, process)
        rows.append(("Total", "total", None, TOTAL))
        values.append([c[m].sum() for _, m in cols])
        return {"rows": rows, "columns": [n for n, _ in cols],
                "values": np.array(values, float).reshape(len(rows),
                                                          len(cols))}

    def launched(self, el):
        """(sources,) particles of el launched (s^-1) by each source."""
        key = ("launch", el)
        if key in self._cache:
            return self._cache[key]
        f, out = self.f44, np.zeros(len(self.sources))
        ia, mols, _ = self._atoms(el)
        owner = self._strata_elements()
        sp = self._species(el)
        rec = self.bf.strata(RECOMBINATION, sp) if \
            self.bf.has(RECOMBINATION) else None
        flux = _values(self.nl, "userfluxparm(1,1)")
        for j, r in enumerate(self.sources):
            mine = [k for k in r.strata if owner[k] in (None, el)]
            if r.kind == "recycling" and f is not None and ia is not None:
                for k in mine:
                    n = f.by_surface("wldpa(%d)" % (k + 1),
                                     f.natm)[:, ia].sum()
                    if mols:
                        pm = f.by_surface("wldpm(%d)" % (k + 1), f.nmol)
                        n += sum(w * pm[:, im].sum()
                                 for im, w in mols.items())
                    out[j] += self.coef[ia, k] * n
            elif r.kind == "puff" and ia is not None:
                for k in mine:          # the atoms of the stratum, shared
                    g = _values(self.nl, "gpfc(1,%d)" % (k + 1))
                    if k < len(flux) and ia < len(g) and sum(g) > 0:
                        out[j] += self.coef[ia, k] * flux[k] * g[ia] / \
                            sum(g)
            elif r.kind == "recombination" and rec is not None:
                out[j] = -rec[:, mine].sum() if mine else 0.0
            elif r.kind == "sputtered" and ia is not None:
                out[j] = self._element_surfaces(ia)[0][r.surfaces].sum()
        self._cache[key] = out
        return out

    def lost(self, el):
        """(sinks,) particles of el absorbed or pumped (s^-1)."""
        ia, _, _ = self._atoms(el)
        if ia is None:
            return np.zeros(len(self.sinks))
        pump = self._element_surfaces(ia)[1]
        return np.array([pump[r.surfaces].sum() for r in self.sinks])

    def balance(self, el):
        """The balance table of el (all the neutrals): sources (positive,
        those of el: recycled at each birth place, gas puff, volume
        recombination, sputtered at each place) and sinks (negative:
        ionised in each region, absorbed by, pumped by, deposited on each
        surface): {"rows": [(name, kind, Row or region index)], "values":
        atoms per second, "sources": their sum, "missing": the residual,
        sources minus sinks}."""
        launched, lost = self.launched(el), self.lost(el)
        ion = self._by_strata(el).sum(axis=1)
        rows, values = [], []
        for j, r in enumerate(self.sources):
            if launched[j]:
                name = "Recycled at the " + lower_first(r.name) if \
                    r.kind == "recycling" and not r.name.startswith(
                        "Stratum") else r.name
                rows.append((name, r.kind, r))
                values.append(launched[j])
        for i, (name, m) in enumerate(self.regions):
            rows.append(("Ionised in the " + lower_first(name), "ionised",
                         i))
            values.append(-ion[m].sum())
        for j, r in enumerate(self.sinks):
            if lost[j]:
                rows.append((r.name, r.kind, r))
                values.append(-lost[j])
        values = np.array(values, float)
        sources = float(values[values > 0].sum()) if len(values) else 0.0
        return {"rows": rows, "values": values, "sources": sources,
                "missing": float(values.sum())}

    def fate(self, el):
        """The fate of the neutrals of el by birth place (None without the
        pumped fluxes by stratum): rows the birth places with a stratum of
        el, Sputtered (the strata of the other elements), those with a
        value, and Total; columns Launched (the source, as the balance),
        Sputtered (in these strata), Ionised (in the regions, as the
        balance), the sinks of the balance, Residual: {"rows": [(name,
        kind, Row, key of the ionisation)], "columns": names, "values":
        (rows, columns) atoms per second}."""
        if not self.by_stratum():
            return None
        ia, _, _ = self._atoms(el)
        if ia is None:
            return None
        mine = self._mine(el)
        rows = [(r.name, r.kind, r, str(j)) for j, r in
                enumerate(self.sources) if r.kind != "sputtered" and
                any(mine[k] for k in r.strata)]
        if (~mine).any():
            rows.append(("Sputtered", "sputtered", None, SPUTTERED))
        rows.append(("Total", "total", None, TOTAL))
        ion = self._by_strata(el)[self.cvreg > 0].sum(axis=0)
        launched = self.launched(el)
        parts = [self._stratum_surfaces(ia, k) for k in range(self.f44.nstra)]
        lost = self.lost(el)
        sinks = [j for j, r in enumerate(self.sinks) if lost[j]]
        values = []
        for name, kind, row, key in rows:
            if key == TOTAL:
                strata = list(range(self.f44.nstra))
            elif key == SPUTTERED:
                strata = [k for k in range(self.f44.nstra) if not mine[k]]
            else:
                strata = [k for k in self.sources[int(key)].strata if mine[k]]
            if key == TOTAL:
                src = sum(launched[j] for j, r in enumerate(self.sources)
                          if r.kind != "sputtered")
            elif key == SPUTTERED:
                src = 0.0
            else:
                src = launched[int(key)]
            sput = sum(parts[k][0].sum() for k in strata)
            out = [ion[strata].sum()] + [
                sum(parts[k][1][self.sinks[j].surfaces].sum()
                    for k in strata) for j in sinks]
            values.append([src, sput] + out + [src + sput - sum(out)])
        keep = [i for i, v in enumerate(values) if i == len(values) - 1 or
                any(values[i][:-1])]    # rows with a value, and Total
        rows, values = [rows[i] for i in keep], [values[i] for i in keep]
        return {"rows": rows, "columns": ["Launched", "Sputtered",
                                          "Ionised"] +
                [self.sinks[j].name for j in sinks] + ["Residual"],
                "values": np.array(values, float)}

    def why_missing(self, el=None):
        """Likely cause of a Not accounted row (of element el)."""
        if el is not None and el.lower() in self.unscaled:
            return ("fort.44 gives the absorbed and pumped fluxes only "
                    "summed over the strata, whose recycling coefficients "
                    "differ: left as EIRENE gives them")
        b2mn = cellfiles.find(self.run.rundir, "b2mn.dat")
        text = open(b2mn).read() if b2mn else ""
        if re.search(r"'balance_average'\s+'1'", text):
            return ("balance.nc is averaged over the time steps of the run "
                    "(balance_average), fort.44 holds the last EIRENE call")
        return ("e.g. particles ionised outside the B2.5 grid, or a puff "
                "set at run time (feedback) instead of userfluxparm")

    def _regions(self):
        """[(name, cells (nCv,) bool)] of the volume regions."""
        names = regions.region_names(self.run, self.geo)[0] if \
            self.geo is not None else None
        return [((names or {}).get(int(r)) or "Region %d" % r,
                 self.cvreg == r) for r in sorted(set(self.cvreg.tolist()))
                if r > 0]

    # ------------------------------------------------------------- maps
    def describe(self, key, el, process="all", region=None):
        """Quantity of the map of a source of the ionisation table (key of
        cells) of element el by process (the Neutrals tab), only in a
        region (index of a column of the ionisation, the drawn region
        last) if given."""
        phrase = "from all the neutrals" if key == TOTAL else \
            "from the sputtered neutrals" if key == SPUTTERED else \
            "from the neutrals " + self.sources[int(key)].phrase
        if region is not None:
            phrase += " in the " + lower_first(
                self.regions[region][0] if region < len(self.regions)
                else "drawn region")
        what = el if process == "all" else "%s, %s" % (
            el, dict((p[0], p[1]) for p in PROCESSES)[process].lower())
        return Quantity("%s%s.%s.%s%s" % (
            PREFIX, key, el, process, "" if region is None else
            ".r%d" % region), "Particle source %s [%s] (%s)" % (
                phrase, what, UNIT), GROUP, "neutrals")

    def field(self, name, ops=()):
        """The map name (PREFIX...) as a Field of the cells: the source
        per volume (m^-3 s^-1); the scale factor of ops applied."""
        m = re.fullmatch(PREFIX + r"(\d+|%s|%s)(?:\.(\w+)\.(\w+)"
                         r"(?:\.r(\d+))?)?" % (TOTAL, SPUTTERED), name)
        if m is None or self.why:
            return None
        key, el, process = m.group(1), m.group(2), m.group(3) or "all"
        region = None if m.group(4) is None else int(m.group(4))
        els = [el] if el else list(self.elements)
        factor = 1.0
        for op in ops:
            words = op.split()
            if len(words) == 2 and words[1] == "rm*":
                factor *= float(words[0].replace("d", "e").replace("D", "E"))
        with np.errstate(divide="ignore", invalid="ignore"):
            vol = np.where(self.vol > 0, self.vol, np.nan)
            values = np.array([self.cells(e, key, process) / vol
                               for e in els]) * factor
        if region is not None:          # only in the region
            cells = self.regions[region][1] if region < len(self.regions) \
                else self.drawn
            if cells is not None:
                values[:, ~cells] = np.nan
        vertex = None
        if self.geo is not None and self.geo.get("vxCvP") is not None:
            vertex = np.array([vertex_values(self.geo, v) for v in values])
        return Field(name=name, label=name, location="cells",
                     columns=els if not el else [""], values=values,
                     vertex=vertex, ops=tuple(ops))
