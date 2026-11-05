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


def tracing_label(name, elements, four_targets=False, element=None,
                  surface=None):
    """Legend text of a tracing column, the element after a comma; the
    element or surface of the page title (element, surface) is left out."""
    surfaces = SURFACE_FOUR if four_targets else SURFACE
    m = re.match(r"^pwr_(totl|plsm|neut|ionz|diss)_(il|ol|iu|ou|wl)$", name)
    if m:
        text = SURFACE_QUANTITY[m.group(1)]
        if m.group(2) == surface:
            return text
        return "%s to the %s" % (text, surfaces[m.group(2)])
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
