"""Physical labels of the run plot quantities.

Descriptions of the tracing columns as B2.5 defines them (b2mod_blns.F,
b2mod_blne.F); species labels from the SOLPS_FLUIDS names.
"""

import re

PARTICLE_UNIT = "particles per second [s$^{-1}$]"
POWER_UNIT = "power [W]"

# blnn_SPb.trc, per element
PARTICLE = {
    "ion_core": "ion flow across the core boundary",
    "ntr_core": "neutral flow across the core boundary",
    "ion_targ": "ion flow to the targets",
    "ntr_targ_tot": "net neutral flow through the targets",
    "ntr_targ_rec": "neutral source by recycling on the targets",
    "ntr_targ_spt": "neutral source by sputtering on the targets",
    "ntr_targ_pmp": "neutrals pumped at the targets",
    "ion_wall": "ion flow to the walls",
    "ntr_wall_tot": "net neutral flow through the walls",
    "ntr_wall_rec": "neutral source by recycling on the walls",
    "ntr_wall_spt": "neutral source by sputtering on the walls",
    "ntr_wall_pmp": "neutrals pumped at the walls",
    "src_ioniz": "ion source by ionisation",
    "ntr_puff": "gas puff",
    "flux_tot": "total flow into the plasma",
    "src_ext": "external source",
    "ion_dn/dt": "rate of change of the ion content, dN/dt",
}

# blne.trc, global and per element
ENERGY = {
    "pwr_totl": "sum of inputs and losses (zero in steady state)",
    "pwr_tscl": "sum of inputs and losses over the energy content",
    "tot_core": "power input from the core",
    "tot_targ": "power to the targets",
    "tot_wall": "power to the walls",
    "tot_rad": "radiated power",
    "heat_cor": "heat from the core",
    "ptnt_cor": "potential energy from the core",
    "ntrl_cor": "neutral power loss to the core",
    "plsm_trg": "plasma heat load to the targets",
    "ntrl_trg": "neutrals heat load to the targets",
    "plsm_wll": "plasma heat load to the walls",
    "ntrl_wll": "neutrals heat load to the walls",
    "brms_rad": "bremsstrahlung",
    "ntrl_rad": "power radiated by neutrals",
    "imp_rad": "power radiated by impurity ions",
    "tot_enrg": "plasma energy content",
    "tot_enre": "electron energy content",
    "tot_enri": "ion energy content",
}

# blne.trc, per surface
SURFACE_QUANTITY = {
    "totl": "total power",
    "plsm": "plasma heat load",
    "neut": "neutrals heat load",
    "ionz": "ionisation energy",
    "diss": "dissociation energy",
}
# B2.5 names the targets inner and outer itself (upper single null
# included); lower and upper only with four targets
SURFACE = {"il": "inner target", "ol": "outer target",
           "iu": "upper inner target", "ou": "upper outer target",
           "wl": "main wall"}
SURFACE_FOUR = dict(SURFACE, il="lower inner target", ol="lower outer target")


def species_label(name):
    """D0 gives D^0, D+1 gives D^+, N+3 gives N^3+ (mathtext)."""
    m = re.match(r"^(.*?)(\+?)([0-9]+)$", name)
    if not m:
        return name
    element, plus, charge = m.groups()
    if not plus:
        sup = charge
    elif charge == "1":
        sup = "+"
    else:
        sup = charge + "+"
    return r"%s$^{%s}$" % (element, sup)


def surfaces(four_targets=False, swapped=False):
    """Names of the blne.trc surfaces; swapped: il is the outer target
    (geometry.first_target_outer, single null only)."""
    if four_targets:
        return SURFACE_FOUR
    if swapped:
        return dict(SURFACE, il=SURFACE["ol"], ol=SURFACE["il"])
    return SURFACE


def tracing_label(name, elements, four_targets=False, element=None,
                  surface=None, swapped=False):
    """Legend text of a tracing column, the element after a comma; the
    element or surface of the page title (element, surface) is left out."""
    surfaces_ = surfaces(four_targets, swapped)
    m = re.match(r"^pwr_(totl|plsm|neut|ionz|diss)_(il|ol|iu|ou|wl)$", name)
    if m:
        text = SURFACE_QUANTITY[m.group(1)]
        if m.group(2) == surface:
            return text
        return "%s to the %s" % (text, surfaces_[m.group(2)])
    for e in elements:
        if name.endswith("_" + e):
            base = name[:-len(e) - 1]
            text = PARTICLE.get(base) or ENERGY.get(base)
            if text:
                return text if e == element else "%s, %s" % (text, e)
    return PARTICLE.get(name) or ENERGY.get(name) or name


def _tracing_kind(base):
    if base in PARTICLE:
        return PARTICLE_UNIT
    if base in ("tot_enrg", "tot_enre", "tot_enri"):
        return "energy [J]"
    if base == "pwr_tscl":
        return "[s$^{-1}$]"
    if base.startswith("pwr_") or base in ENERGY:
        return POWER_UNIT
    return ""


def tracing_unit(names):
    """y axis label for tracing columns, empty when kinds are mixed."""
    kinds = set(_tracing_kind(re.sub(r"_[A-Z][a-z]?$", "", n))
                for n in names)
    return kinds.pop() if len(kinds) == 1 else ""


# b2ftrace residuals: (title, y label)
RESIDUAL = {
    "co": ("Residual norm of the continuity equations, per species",
           "norm of the continuity residual"),
    "mo": ("Residual norm of the parallel momentum equations, per species",
           "norm of the momentum residual"),
    "he": ("Residual norm of the electron energy equation",
           "norm of the electron energy residual"),
    "hi": ("Residual norm of the ion energy equation",
           "norm of the ion energy residual"),
}


# b2time.nc and b2batch.nc time traces: quantity, symbol, unit by the start
# of the name (units checked against the stored values)
TRACE_QUANTITY = (
    ("pwmx", "maximum total power flux density", "$q_{max}$", "W m$^{-2}$"),
    ("dab", "density", "$n$", "m$^{-3}$"),
    ("dmb", "molecule density (EIRENE)", "$n_m$", "m$^{-3}$"),
    ("tab", "atom temperature (EIRENE)", "$T_a$", "eV"),
    ("tmb", "molecule temperature (EIRENE)", "$T_m$", "eV"),
    ("fni", "particle flux", r"$\Gamma$", "s$^{-1}$"),
    ("fee", "electron energy flux", "$Q_e$", "W"),
    ("fei", "ion energy flux", "$Q_i$", "W"),
    ("fet", "total internal energy flux", "$Q$", "W"),
    ("fch", "current", "$I$", "A"),
    ("ne", "electron density", "$n_e$", "m$^{-3}$"),
    ("na", "density", "$n$", "m$^{-3}$"),
    ("te", "electron temperature", "$T_e$", "eV"),
    ("ti", "ion temperature", "$T_i$", "eV"),
    ("po", "potential", r"$\phi$", "V"),
    ("kt", "turbulent kinetic energy", "$k$", "eV"),
    ("dn", "particle diffusion coefficient", "$D_n$", "m$^2$ s$^{-1}$"),
    ("dp", "pressure diffusion coefficient", "$D_p$", "m$^2$ s$^{-1}$"),
    ("ke", "electron thermal diffusivity", r"$\chi_e$", "m$^2$ s$^{-1}$"),
    ("ki", "ion thermal diffusivity", r"$\chi_i$", "m$^2$ s$^{-1}$"),
    ("vx", "poloidal pinch velocity", "$v_x$", "m s$^{-1}$"),
    ("vy", "radial pinch velocity", "$v_y$", "m s$^{-1}$"),
    ("vs", "viscosity coefficient", r"$\eta$", "m kg$^{-1}$ s$^{-1}$"),
)
TRACE_TOTAL = {
    "tmne": ("total number of particles", "$N$", ""),
    "tmte": ("total electron energy", "$E_e$", "eV"),
    "tmti": ("total ion energy", "$E_i$", "eV"),
}
_LOCATION = re.compile(r"^(sepm|sepi|sepa|mxip|mxap|xip|xap|yip|yap|sipp|"
                       r"sapp|sip|sap|ip|ap)(_av|_std)?$")


class Configuration:
    """Location names from NREG (its first number); for a single null,
    swapped tells whether the first target is the outer one
    (geometry.first_target_outer; None: left and right)."""

    def __init__(self, nreg, swapped=None):
        try:
            self.n = int(str(nreg).split()[0])
        except (ValueError, IndexError, TypeError):
            self.n = 0
        self.swapped = swapped

    def single_null(self):
        return self.n in (4, 5)

    def target(self, side, row=0):
        """side i or a, row 0 or 1 of the nc rows."""
        if self.single_null():
            if self.swapped is None:
                return {"i": "left target", "a": "right target"}[side]
            inner = (side == "i") != self.swapped
            return "inner target" if inner else "outer target"
        if self.n == 8:
            return "%s %s target" % (("bottom", "top")[min(row, 1)],
                                     {"i": "inner", "a": "outer"}[side])
        if self.n == 7:
            names = (("inner target", "primary outer target"),
                     ("far-SOL outer target", "secondary outer target"))
            return names[min(row, 1)][side == "a"]
        return {"i": "left target", "a": "right target"}[side]

    def midplane(self, row=0):
        if self.n in (1, 2):
            return "midpoint"
        if self.n == 8 and row == 1:
            return "inner midplane"
        return "outer midplane"

    def radial(self, side, row=0):
        where = {"i": "main chamber", "a": "divertor region"}[side]
        if self.n == 8:
            where += ", %s side" % ("outer", "inner")[min(row, 1)]
        return where

    def location(self, code, row=0, rows=1):
        if code == "sepm":
            return "separatrix, " + self.midplane(row)
        if code in ("sepi", "sepa"):
            return "separatrix, " + self.target(code[-1], row)
        if code in ("mxip", "mxap"):
            return "maximum, " + self.target(code[2], row)
        if code in ("xip", "xap"):
            return "poloidal, into the " + self.target(code[1], row)
        if code in ("ip", "ap"):
            return self.target(code[0], row)
        if code in ("yip", "yap"):
            return "radial, " + self.radial(code[1], row)
        throat = {"sip": "into the inner divertor throat",
                  "sap": "into the outer divertor throat",
                  "sipp": "core X-point region",
                  "sapp": "X-point private flux region"}[code]
        return "poloidal, " + throat + ("" if rows == 1
                                        else ", row %d" % (row + 1))


class Trace:
    """The parts of a time-trace label; the page puts the shared ones in
    the title and the others in the legend."""

    def __init__(self, quantity, symbol, unit, location="", species=""):
        self.quantity, self.symbol, self.unit = quantity, symbol, unit
        self.location, self.species = location, species

    def parts(self):
        return [self.quantity, self.species, self.location]


def trace(name, config, row=0, rows=1, species=None, long_name=""):
    """Label parts of a b2time.nc name (species: the label of the species
    index of a species name such as nasepm1)."""
    plain = re.sub(r"_(av|std)$", "", name)
    average = name.endswith("_av") and " (batch average)" or \
        (name.endswith("_std") and " (batch standard deviation)" or "")
    if plain in TRACE_TOTAL:
        q, s, u = TRACE_TOTAL[plain]
        return Trace(q + average, s, u)
    for start, q, s, u in TRACE_QUANTITY:
        if plain.startswith(start):
            m = _LOCATION.match(plain[len(start):])
            if m:
                return Trace(q + average, s, u,
                             config.location(m.group(1), row, rows),
                             species or "")
    text = long_name or name
    return Trace(text + ("" if rows == 1 else ", row %d" % (row + 1)),
                 "", "", species=species or "")


def species_of(base, index, names, neutrals):
    """Legend label of the species index of a species name: EIRENE atom
    and molecule names (dab, tab, dmb, tmb) count the neutral species."""
    eirene = base[:3] in ("dab", "tab", "dmb", "tmb")
    pool = neutrals if eirene else names
    if index >= len(pool):
        return "species %d" % index
    label = species_label(pool[index])
    return label + " atoms (EIRENE)" if base.startswith("dab") else label
