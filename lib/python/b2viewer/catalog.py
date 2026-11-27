"""Quantities of the 2D tab from the b2plot command catalogue (CATALOG).

Matrix quantities are B2.5 cell fields, Eirene quantities are fields on
the EIRENE triangles. A poloidal and a radial quantity with otherwise the
same description form a vector quantity, and so do EIRENE quantities
whose labels differ only by x and y (Cartesian R and Z components). The
groups only sort the list for the user; the names are the b2plot labels.
"""

import re
from dataclasses import dataclass, replace

from ..b2plot import labels
from . import describe
from .expression import ExpressionError, Translator, names_of
from .model import split_unit

GROUPS = [
    ("Magnetic equilibrium",
     ("flux function", "volume", "area", "length", "coordinate", "metric",
      "magnetic", "angle", "pitch", "b_{", "connection")),
    ("Plasma fluxes", ("flux", "current")),
    ("Sources and sinks",
     ("source", "sink", "rate", "loss", "power", "heating", "radiat")),
    ("Plasma state", ("velocity", "mach", "speed")),
    ("Transport coefficients",
     ("coefficient", "diffusiv", "conductiv", "viscosit", "resistiv")),
    ("Plasma state",
     ("density", "temperature", "pressure", "potential", "energy",
      "charge", "z_{eff}", "zeff")),
]
# Labels with an integer argument (masks): argument of the Mask box, or
# written ixeq(10) in derived quantities
INTEGER = re.compile(r"i[xysc](lt|le|eq|ne|ge|gt)|nreg|freg|clbl|flbl|tlbl|"
                     r"ifeq|iveq|fteq")
# Labels of cells set to 1, the others 0 (masks without argument)
FLAGS = re.compile(r"bdcl|gdcl|rlcl|npcl|iimp|iomp")
# Labels with their values on the guard cells (no area), drawn on the
# boundary faces of those cells (as the masks are)
GUARD = re.compile(r"rc|bc")
# Families of labels, checked before the description keywords of GROUPS
FAMILIES = [
    ("Neutrals state", r"[dt][ami]b2"),     # atoms, molecules, test ions
    # the plasma state by kind
    ("Plasma densities", r"ne|ni|na|zeff"),
    ("Plasma velocities", r"ue|ua|mach|ve?exb\.[xy]|w[ae]dia\.[xy]|ww"),
    ("Plasma temperatures", r"te|ti|tn|ke|kt"),
    ("Plasma pressures", r"pz|p\*"),
    ("Plasma potential", r"po"),
    # the fluxes by kind, the neutral ones as in the movie files
    ("Particle fluxes", r"fnax|fnay|fnaxpll|fnaypll|fnaxpnch|fnaypnch|fnaxecrb|fnayecrb|fnaxdia|fnaydia|fnaxch|fnaych|fnaxnanm|fnaynanm|fnaxpanm|fnaypanm|fnaxmdf|fnaymdf|fnaxps|fnayps|fnax32|fnay32|fnax52|fnay52|fnaxfcor|fnayfcor|fnaxhe|fnayhe|fnaxnodr|fnaynodr|fnex|fney|fnex32|fney32|fnex52|fney52|fnix32|fniy32|fnix52|fniy52|fmx|fmy|fax_ext|fay_ext"),
    ("Momentum fluxes", r"fmox|fmoy|fmoxflua|fmoyflua|fmoxcvsa|fmoycvsa|fmoxhybr|fmoyhybr"),
    ("Total energy fluxes", r"fhtx|fhty|fhex|fhey|fhix|fhiy|fhnx|fhny|fhjx|fhjy|fhpx|fhpy|fhmx|fhmy|fntx|fnty|fktx|fkty"),
    ("Electron heat fluxes", r"fhexconv|fheyconv|fhexcond|fheycond|fhexthj|fheythj|fhexdia|fheydia|fhexstr|fheystr|fhexmdf|fheymdf|fhexps|fheyps"),
    ("Ion heat fluxes", r"fhixconv|fhiyconv|fhixcond|fhiycond|fhixdia|fhiydia|fhixstr|fhiystr|fhixinrt|fhiyinrt|fhixvspa|fhiyvspa|fhixvspe|fhiyvspe|fhixvisq|fhiyvisq|fhixanml|fhiyanml|fhixvskt|fhiyvskt|fhixvzh|fhiyvzh|fhixmdf|fhiymdf|fhixps|fhiyps"),
    ("Current fluxes", r"fchx|fchy|fchp|fchxn|fchyn|fchxdia|fchydia|fchxanml|fchyanml|fchxinrt|fchyinrt|fchxvspa|fchyvspa|fchxvspe|fchyvspe|fchxvisq|fchyvisq|fcxviskt|fcyviskt|fchx32|fchy32|fchx52|fchy52"),
    ("Neutrals fluxes", r"pfla|rfla|pefa|refa|pflm|rflm|pefm|refm|fnnx|fnny|fnnx32|fnny32|fnnx52|fnny52"),
    # the sources by equation, each with the terms of its sum
    ("Particle sources", r"sna|bcna|brna|snap[ampi]pl|snapppl|snacore|bmna|exna|rsan|rran|rcxn"),
    ("Momentum sources", r"rsam|rram|rcxm|smo|bcmo|brmo|smom[ampi]pl|smomppl|bmmo|exmo|smq|smaf|smfr|smpt|smpr|smag|smav|smcf"),
    ("Electron energy sources", r"she|bche|brhe|shee[ampi]el|bmhe|exhe|rqae|b2ra|b2br|b2iz|b2rc|dvue|exbe|joul"),
    ("Ion energy sources", r"shi|bchi|brhi|shie[ampi]pl|bmhi|exhi|rsai|rrai|rcxi|dvua|exba|visa|fraa|shei|brhn|brkt"),
    ("Charge sources", r"sch|bcch|bmch|exch"),
    ("Residuals", r"rco|rmo|ree|rei|rpo"),
    ("Neutrals radiation", r"neutrad|molrad|ionrad|recrad"),
    ("Plasma coefficients",
     r"ldebye|wpe|wpi|wce|wci|omega|rhol|betae|beta|lnlam|taue|taui|taueq|"
     r"nustarc|deltabc|wb|"
     r"deltparc|vthe|vthi|colle|colli"),
    ("Collisional parallel transport coefficients",
     r"kpe|kpi|vispar|sigpar|alfpar"),
    ("Anomalous transport coefficients",
     r"d|dp|ky[ei]|vla[xy]|visc|sig|alf|dkt"),
    ("Flux limiters", r"fle|fli|nflf..x?y?|flvisc|fluc.|flk.|flalc?"),
    ("Collisional radial transport coefficients",
     r"dnneo|vnneo|chineo|vwneo"),
    ("Magnetic equilibrium", r"bx|by|bz|bb|psi|conn|pit|ffbz"),
    ("Cell masks and indices", INTEGER.pattern
     + r"|rlcl|gdcl|bdcl|npcl|iimp|iomp|ix|iy|iix|iiy|ic|ift|xymap|bc|rc"),
]
OTHER = "Other geometric quantities"
NEUTRALS = "Neutrals (triangles)"           # as in the Run movies tab
NEUTRAL_VELOCITIES = "Neutrals velocities"
# groups of the plasma table shown again in the vector table: each
# quantity of them with a poloidal and a radial component, in their order
VECTOR_GROUPS = ("Plasma velocities", "Particle fluxes", "Momentum fluxes",
                 "Total energy fluxes", "Electron heat fluxes",
                 "Ion heat fluxes", "Current fluxes", "Neutrals fluxes")
# vectors of a quantity without radial component (the radial one zero):
# their poloidal component in b2plot tokens; the parallel velocities (positive
# along the poloidal field) projected on the poloidal direction with the pitch
ZERO_RADIAL = {"ue": "ue pit m*", "ua": "ua pit m*", "fchp": "fchp"}
# neutral fluxes of fort.44 left out of the vector table: the same arrows
# as the flux densities of the triangles, shown there
NO_VECTOR = ("pfla", "pefa", "pflm", "pefm")
DERIVED = "Derived quantities"
EQUILIBRIUM = "Magnetic equilibrium"   # b2plot labels and derived maps
CHORD_POINTS = 33               # points of each chord sent by guigeom
ORDER = [DERIVED, "Plasma densities", "Plasma velocities",
         "Plasma temperatures", "Plasma pressures", "Plasma potential",
         "Plasma state", "Particle fluxes", "Momentum fluxes",
         "Total energy fluxes", "Electron heat fluxes",
         "Ion heat fluxes", "Current fluxes", "Plasma fluxes",
         "Particle sources", "Particle sources by neutral origin",
         "Momentum sources", "Electron energy sources",
         "Ion energy sources", "Charge sources",
         "Sources and sinks", "Neutrals state", NEUTRAL_VELOCITIES,
         "Neutrals fluxes", "Neutrals radiation", NEUTRALS, EQUILIBRIUM,
         "Plasma coefficients",
         "Collisional parallel transport coefficients",
         "Collisional radial transport coefficients",
         "Anomalous transport coefficients", "Transport coefficients",
         "Flux limiters", "Residuals", FAMILIES[-1][0], OTHER]
# quantities computed from labels, by group: the expression shown, its
# b2plot tokens and the description. Plasma coefficients: the divisions
# zero where the time is zero, as for the neutral species. Collisional
# radial transport coefficients: each NEOART coefficient by contribution,
# the contribution set before the label (b2plot neo_ic: 0 classical,
# 2 Pfirsch-Schlueter, 1 banana-plateau, 4 all)
NEO_PARTS = (("cl", 0, "classical"), ("ps", 2, "Pfirsch-Schlüter"),
             ("bp", 1, "banana-plateau"), ("", 4, "total"))
NEO = (("dnneo", "Radial particle diffusivity", "m^{2}.s^{-1}"),
       ("vnneo", "Radial pinch velocity", "m.s^{-1}"),
       ("chineo", "Radial heat diffusivity", "m^{2}.s^{-1}"),
       ("vwneo", "Radial heat pinch velocity", "m.s^{-1}"))
COMPUTED = {
    "Plasma coefficients": (
        ("1/taue", "{taue} {taue} m/ {taue} m/",
         "Electron collision frequency (electron-ion) (s^{-1})"),
        ("1/taui", "{taui} {taui} m/ {taui} m/",
         "Ion collision frequency (ion-ion) (s^{-1})"),
        ("vthe*taue", "{vthe} {taue} m*", "Electron mean free path (m)"),
        ("vthi*taui", "{vthi} {taui} m*", "Ion mean free path (m)")),
    "Collisional radial transport coefficients": tuple(
        (("%s %s" % (n, k)).strip(), "%d neo_ic {%s}" % (ic, n),
         "%s, %s (%s)" % (d, part, u))
        for n, d, u in NEO for k, ic, part in NEO_PARTS)}
# order within the groups (the main plasma state as in the movie files,
# velocities after it), the others by name; labels left out of the list
FINAL_WITHIN = {"Plasma densities": ("ne", "ni", "na", "zeff"),
                # as the equations: continuity, momentum, electron and ion
                # energy, potential
                "Residuals": ("rco", "rmo", "ree", "rei", "rpo"),
                # divergences of the main fluxes first, as the residuals
                OTHER: ("dfna", "dfmo", "dfhe", "dfhi", "dfch"),
                # the field components and strength, the poloidal flux,
                # the pitch, then lengths along the field lines
                EQUILIBRIUM: ("bx", "by", "bz", "bb", "psi", "pitch",
                              "pitchangle", "conn", "dspol", "dspar",
                              "dspole", "dspare", "lpol", "lpar", "fexp",
                              "qsafety", "shear"),
                # Debye length, plasma and gyro-frequencies, Larmor
                # radius, plasma beta, Coulomb logarithm, collision times
                # and frequencies, thermal velocities, mean free paths,
                # collisionalities with the banana width, the equilibration
                # time last
                "Plasma coefficients": (
                    "ldebye", "wpe", "wpi", "wce", "wci", "omega", "rhol",
                    "betae", "beta", "lnlam", "taue",
                    "taui", "1/taue", "1/taui", "vthe", "vthi", "vthe*taue",
                    "vthi*taui", "nustarc", "deltabc", "wb", "deltparc",
                    "colle", "colli", "taueq"),
                # particles, then heat, each diffusivity and pinch
                "Collisional radial transport coefficients": tuple(
                    e for e, _, _ in COMPUTED[
                        "Collisional radial transport coefficients"]),
                # in the order of their anomalous counterparts
                "Collisional parallel transport coefficients": (
                    "kpi", "kpe", "vispar", "sigpar", "alfpar"),
                # as in b2.transport.inputfile (kind_coeff 1 to 9), the
                # E×B turbulent energy diffusivity last
                "Anomalous transport coefficients": (
                    "d", "dp", "kyi", "kye", "vlax", "vlay", "visc", "sig",
                    "alf", "dkt"),
                "Plasma velocities": ("ue", "ua", "vexb.x", "vexb.y",
                                      "wadia.x", "wadia.y", "veexb.x",
                                      "veexb.y", "wedia.x", "wedia.y", "ww",
                                      "mach"),
                "Plasma temperatures": ("te", "ti", "tn", "ke", "kt"),
                "Plasma pressures": ("pz", "p*"),
                "Particle fluxes": ("fnax", "fnay", "fnaxpll", "fnaypll", "fnaxpnch", "fnaypnch", "fnaxecrb", "fnayecrb", "fnaxdia", "fnaydia", "fnaxps", "fnayps", "fnaxch", "fnaych", "fnaxnanm", "fnaynanm", "fnaxpanm", "fnaypanm", "fnex", "fney"),
                "Momentum fluxes": ("fmox", "fmoy", "fmoxflua", "fmoyflua", "fmoxcvsa", "fmoycvsa", "fmoxhybr", "fmoyhybr"),
                "Total energy fluxes": ("fhtx", "fhty", "fhex", "fhey", "fhix", "fhiy", "fhnx", "fhny", "fhjx", "fhjy", "fhpx", "fhpy", "fhmx", "fhmy", "fntx", "fnty", "fktx", "fkty"),
                "Electron heat fluxes": ("fhex", "fhey", "fhexconv", "fheyconv", "fhexcond", "fheycond", "fhexthj", "fheythj", "fhexdia", "fheydia", "fhexps", "fheyps", "fhexstr", "fheystr"),
                "Ion heat fluxes": ("fhix", "fhiy", "fhixconv", "fhiyconv", "fhixcond", "fhiycond", "fhixdia", "fhiydia", "fhixps", "fhiyps", "fhixstr", "fhiystr", "fhixinrt", "fhiyinrt", "fhixvspa", "fhiyvspa", "fhixvspe", "fhiyvspe", "fhixvisq", "fhiyvisq", "fhixvzh", "fhiyvzh", "fhixanml", "fhiyanml", "fhixvskt", "fhiyvskt"),
                "Current fluxes": ("fchx", "fchy", "fchp", "fchxn", "fchyn", "fchxdia", "fchydia", "fchxvspa", "fchyvspa", "fchxvspe", "fchyvspe", "fchxvisq", "fchyvisq", "fchxinrt", "fchyinrt", "fchxanml", "fchyanml", "fcxviskt", "fcyviskt"),
                "Neutrals fluxes": ("pfla", "rfla", "pefa", "refa", "pflm", "rflm", "pefm", "refm", "fnnx", "fnny", "fnnx32", "fnny32", "fnnx52", "fnny52"),
                # the atomic terms of B2.5, the neutral total and its EIRENE
                # parts, boundary, additional and external sources, with the
                # further terms of the equation before the boundary ones
                "Particle sources": ("rsan", "rran", "rcxn", "brna", "snapapl", "snapmpl", "snapipl", "snapppl", "snacore", "bcna", "bmna", "exna"),
                "Momentum sources": ("rsam", "rram", "rcxm", "brmo", "smomapl", "smommpl", "smomipl", "smomppl", "smfr", "smpt", "smpr", "smag", "smav", "smcf", "bcmo", "bmmo", "exmo"),
                "Electron energy sources": ("b2ra", "b2br", "b2iz", "b2rc", "brhe", "sheeael", "sheemel", "sheeiel", "sheepel", "dvue", "exbe", "joul", "-shei", "bche", "bmhe", "exhe"),
                "Ion energy sources": ("rsai", "rrai", "rcxi", "brhi", "shieapl", "shiempl", "shieipl", "shieppl", "dvua", "exba", "visa", "fraa", "shei", "bchi", "bmhi", "exhi", "brhn", "brkt"),
                "Charge sources": ("bcch", "bmch", "exch"),
                "Neutrals radiation": ("neutrad", "molrad", "ionrad",
                                       "recrad"),
                "Neutrals state": ("dab2", "tab2", "dmb2", "tmb2", "dib2",
                                   "tib2"),
                # by species as in the movie files: density, temperature,
                # pressure, energy density, velocity, particle flux density
                # and momentum density (x, y, z)
                NEUTRALS: tuple(n % k for k in "ami" for n in (
                    "pden%s", "temp%s", "pres%s", "eden%s", "vx%s", "vy%s",
                    "vz%s", "fxden%s", "fyden%s", "fzden%s", "vxden%s",
                    "vyden%s", "vzden%s"))}
# EIRENE labels not listed: masses, triangle geometry, unit vectors of the
# cells (still usable in derived quantities)
EIRENE_HIDDEN = {"massa", "massm", "massi", "tindex", "tr", "tz", "triarea",
                 "triavol", "pux", "puy", "pvx", "pvy"}
HIDDEN = {"alph", "na_ext", "ne_ext", "nh", "pot*", "pot", "poti", "ro",
          "ta_ext", "za2", "za2_ext", "za_ext", "zi", "zn", "zn_ext",
          "mach4", "mch2", "ua_ext", "up", "pr", "ud", "vd", "vadia.x",
          "vadia.y", "vedia.x", "vedia.y", "vv",
          # particle flux splittings other than the main one
          "fnaxmdf", "fnaymdf", "fnax32", "fnay32", "fnax52", "fnay52",
          "fnaxfcor", "fnayfcor", "fnaxhe", "fnayhe", "fnaxnodr", "fnaynodr",
          "fax_ext", "fay_ext", "fmx", "fmy", "fnex32", "fnex52",
          "fney32", "fney52", "fnix32", "fnix52", "fniy32", "fniy52",
          "fhexmdf", "fheymdf", "fhixmdf", "fhiymdf",
          # currents never updated (old files only), the diamagnetic one
          # also as fchxdia/fchydia
          "fchx32", "fchy32", "fchx52", "fchy52", "cd", "dd",
          # fluid neutral particle flux and its parts: not in b2fplasma
          # (fnn) or never computed (fnn_32, fnn_52), always zero here
          "fnnx", "fnny", "fnnx32", "fnny32", "fnnx52", "fnny52",
          # energy flux without the electrostatic part, electron and ion
          # energy fluxes never computed (zero), turbulent enstrophy flux
          "fetx", "fety", "fhetx", "fhety", "fhitx", "fhity", "fztx",
          "fzty",
          # electron particle source: in no equation solved
          "sne", "bcne", "brne", "bmne", "exne",
          # never filled (always zero): neutral charge source, strange term
          "brch", "str",
          # turbulent enstrophy sources (as its flux)
          "szt", "bczt", "brzt",
          # totals of the source groups (not always the total of their
          # equation): only the terms are listed, the momentum friction and
          # thermal forces and the atomic momentum source by their parts
          "sna", "smo", "she", "shi", "sch", "shn", "skt", "smq", "smaf",
          # the electron cooling by its parts
          "rqae",
          # sums or parts of the other momentum terms
          "smth", "smp",
          # boundary sources of the fluid neutral and turbulent energy
          "bchn", "bckt",
          # Halpha emissivities of atoms and molecules
          "ahal", "mhal",
          # molecule dissociation rate and its potential energy
          "srcml", "edissml",
          # total ion and fluid neutral heat diffusivities, E×B turbulent
          # enstrophy diffusivity
          "kyi0", "kyn0", "dzt",
          # collision frequencies and collisionality of the neoclassical
          # module (its own Coulomb logarithms and prefactor) and its ratios
          # built on them: as times, frequencies, collisionality and ratios
          # from the classical transport
          "nua", "nuab", "nustar", "deltab", "deltapar",
          # gradient lengths and their ratio to the Larmor radius, the
          # thermal velocities again (as vthe, vthi)
          "lnn", "ltt", "deltal", "vth",
          # Alfvén velocity per species (not that of the plasma), banana
          # width ratios to the gradient lengths
          "valfven", "deltaw", "deltawn", "deltawt",
          # Chang-Hinton ion heat diffusivity (analytic, not from NEOART),
          # the NEOART coefficients by their contributions instead
          "chhichii", "dnneo", "vnneo", "chineo", "vwneo",
          # corrections of the last iteration, residuals of the total
          # momentum, fluid neutral and E×B turbulence equations
          "cpa", "cua", "cut", "cte", "cti", "cpo", "ckt", "czt", "ctn",
          "rmt", "ren", "rkt", "rzt",
          # toroidal flux function, parallel length of the cell (map)
          "ffbz", "lparcell",
          # field components together, EIRENE species of the atoms and
          # ions, energy equipartition coefficient, cell centre and its
          # unit vectors, drift and viscosity factors, radial width, ion
          # masses, Z^2-weighted density, b2plot safety factor, turbulent
          # enstrophy
          "b", "b2eatcr", "b2espcr", "ceqp", "cr", "cz", "ehx", "ehy",
          "fac_ExB", "fac_vis", "facdrift", "hy1", "mi", "mi_ext", "ne2",
          "q", "zt",
          # magnetic shear of b2plot (zero outside the closed surfaces): the
          # derived map instead
          "s",
          # divergences other than those of the main fluxes
          "dhet", "dhit", "dfhj", "dfhm", "dfhp", "dfhn", "dfkt", "dfzt",
          # classical viscosity face coefficients (conductances)
          "cvsx", "cvsy",
          # balances and the previous time step
          "ebal", "ebld", "ebls", "pbal", "na0", "ne0", "ni0", "te0", "ti0",
          "ua0", "po0", "tn0", "kt0", "zt0"}
# labels also listed first in these groups, as their totals
TOTALS = {"fhex": "Electron heat fluxes", "fhey": "Electron heat fluxes",
          "fhix": "Ion heat fluxes", "fhiy": "Ion heat fluxes"}
# labels also in a second group with the opposite sign: the equipartition,
# a source of the ions and a sink of the electrons
NEGATED = {"shei": "Electron energy sources"}


@dataclass
class Quantity:
    name: str                   # b2plot label, "pol rad" for vectors
    description: str
    group: str
    source: str                 # "matrix", "eirene", "vector", "evector",
    #                             "equilibrium", "neutrals" (computed by
    #                             the GUI)
    poloidal: str = ""
    radial: str = ""
    movie: int = 0              # 1 b2movies.nc, 2 eirenemovies.nc
    expr: str = ""              # derived: the expression (name: tokens)
    per: tuple = ()             # b2plot tokens of the density: dividing by
    #                             the cell volume or face area (vectors:
    #                             poloidal and radial component)

    def __post_init__(self):
        self.description = describe.wording(self.description)

    @property
    def text(self):
        return labels.tex_to_plain(self.description)

    @property
    def label(self):
        """What the lists show: the expression of a derived quantity."""
        return self.expr or self.name


def _group(name, description):
    for group, pattern in FAMILIES:
        if re.fullmatch(pattern, name):
            return group
    d = description.lower()
    for name, keys in GROUPS:
        if any(k in d for k in keys):
            return name
    return OTHER


def _epairs(entries):
    """(R, Z, description) for EIRENE labels differing by x and y."""
    descs = {n: d for n, d, _ in entries}
    out = []
    for name, desc, _ in entries:
        if "x" not in name:
            continue
        partner = name.replace("x", "y", 1)
        if partner in descs:
            text = re.sub(r"(?i)\b(cartesian\s+)?x-(directed\s+)?", "",
                          desc, count=1)
            out.append((name, partner, text[:1].upper() + text[1:]))
    return out


_UNIT = re.compile(r"\s*\([^()]*(\([^()]*\)[^()]*)*\)\s*$")


def _side(name, names):
    """"poloidal" or "radial" when the quantity has its other component
    in names (x and y swapped, or the p and r of the neutral fluxes)."""
    for k, c in enumerate(name):
        if c in "xy" and name[:k] + "yx"["xy".index(c)] + name[k + 1:] \
                in names:
            return "poloidal" if c == "x" else "radial"
    if name[:1] in "pr" and "rp"["pr".index(name[0])] + name[1:] in names:
        return "poloidal" if name[0] == "p" else "radial"
    return None


# labels keeping their "Poloidal ..." and "Radial ..." descriptions
KEEP_SIDE = {"vlax", "vlay", "bx", "by"}


def components(items):
    """Descriptions of the quantities with a poloidal and a radial
    component written "What (poloidal component) (unit)" (items with name
    and description, changed in place; masks and indices left as they
    are)."""
    names = {i.name for i in items}
    for i in items:
        d = i.description
        which = _side(i.name, names)
        if i.name in KEEP_SIDE or not which or "component)" in d or \
                re.search(
                r"(?i)index|coordinate|\bcells?\b", d):
            continue
        m = _UNIT.search(d)
        unit, body = (m.group(0).strip(), d[:m.start()]) if m else ("", d)
        new = re.sub(r"(?i)\b%s\s+(component\s+of\s+(the\s+)?)?" % which,
                     "", body, count=1)
        if new == body:
            continue
        new = new.strip()
        i.description = "%s%s (%s component)%s" % (
            new[:1].upper(), new[1:], which, " " + unit if unit else "")
    return items


def _radial(name, names):
    """Radial partner of a poloidal label in names (an x swapped for a y,
    or the r of a neutral flux for its p), else None."""
    for k, c in enumerate(name):
        if c == "x" and name[:k] + "y" + name[k + 1:] in names:
            return name[:k] + "y" + name[k + 1:]
    if name[:1] == "p" and "r" + name[1:] in names:
        return "r" + name[1:]
    return None


# groups whose quantities b2plot gives per cell (sources) or through the
# projected cell faces (fluxes: velocity times density times cvHy cvHz,
# poloidal, or cvHx cvHz, radial, as in intflux), shown as densities: per
# volume (vol) or per area (sxperp, sy); those already per m^3 or m^2 stay
SOURCE_GROUPS = ("Particle sources", "Momentum sources",
                 "Electron energy sources", "Ion energy sources",
                 "Charge sources", "Neutrals radiation")
FLUX_GROUPS = ("Particle fluxes", "Momentum fluxes", "Total energy fluxes",
               "Electron heat fluxes", "Ion heat fluxes", "Current fluxes")


def density_unit(unit, power, sep="."):
    """Unit of the density: 's^{-1}' -> 'm^{-3}.s^{-1}', 'W' -> 'W.m^{-3}'
    (power 3; 2 for the areas; sep " " as in the movie files)."""
    m = "m^{-%d}" % power
    if "s^{-1}" in unit:
        return unit.replace("s^{-1}", m + sep + "s^{-1}", 1)
    return unit + sep + m


def _density(q):
    """q as a density, when it is a source or a flux given per cell."""
    flux = q.group in FLUX_GROUPS
    if not (flux or q.group in SOURCE_GROUPS) or \
            q.source not in ("matrix", "vector"):
        return q
    text, unit = split_unit(q.description)
    if not unit or "m^{-" in unit:
        return q
    if not flux:
        per = ("vol m/",)
    elif q.source == "vector":
        per = ("sxperp m/", "sy m/")
    else:
        per = ("sy m/",) if re.search(r"(?i)\brad(ial)?\b", text) \
            else ("sxperp m/",)
    return replace(q, description="%s (%s)" % (
        text, density_unit(unit, 3 if not flux else 2)), per=per)


def _vectors(scalars):
    """Vectors of the groups of VECTOR_GROUPS, from their quantities with a
    poloidal and a radial component (in the order of the plasma table)."""
    out = []
    for g in VECTOR_GROUPS:
        group = [q for q in scalars if q.group == g]
        names = {q.name for q in group}
        for q in group:
            if q.name in NO_VECTOR:
                continue
            p, r, name = q.name, _radial(q.name, names), None
            d = re.sub(r",? \(?poloidal component\)?", "", q.description)
            if q.name in ZERO_RADIAL:
                p, r = ZERO_RADIAL[q.name], "%s %s m-" % (q.name, q.name)
                name = q.name + " 0"
                if p != q.name:
                    d = "Poloidal projection of the " + d[:1].lower() + d[1:]
            if r:
                out.append(Quantity(name or p + " " + r, d, g, "vector", p,
                                    r))
    return out


# EIRENE species letter of a label: atoms, molecules, test ions,
# recombination (snapapl ... snapppl, vxa ... vxi, fxdena ... vxdeni)
_SPECIES = re.compile(r"(sna|smo|she|shi)(p|m|e)([amip])(pl|el)|"
                      r"([fv][xyz](?:den)?)([ami])\b")


def _species_order(name):
    """The name for sorting, the EIRENE species letter in the order atoms,
    molecules, test ions, recombination."""
    def key(m):
        if m.group(3):
            return "%s%s%d%s" % (m.group(1), m.group(2),
                                 "amip".index(m.group(3)), m.group(4))
        return "%s%d" % (m.group(5), "ami".index(m.group(6)))
    return _SPECIES.sub(key, name)


def quantities(categories, maps=(), extra=()):
    """List of Quantity from the categories of the CATALOG message, the
    2D maps of the derived equilibrium quantities (name, label: the GUI
    computes them from the geometry files, source "equilibrium") and extra
    ones (the neutral sources by origin, source "neutrals")."""
    cats = dict(categories)
    matrix = [e for e in cats.get("Matrix quantities", []) if e[0].strip()]
    eirene = [e for e in cats.get("Eirene quantities", []) if e[0].strip()]
    # groups from the b2plot texts, the lists show those of describe
    out = [Quantity(n.strip(), describe.MATRIX.get(n.strip()) or d.strip()
                    or n.strip(), _group(n.strip(), d), "matrix")
           for n, d, _ in matrix if n.strip() not in HIDDEN]
    # the electron and ion heat fluxes also first in their own groups
    out += [replace(q, group=TOTALS[q.name], description=re.sub(
        r"(?i)^(poloidal|radial) ", r"\1 total ", q.description))
            for q in out if q.name in TOTALS]
    out += [Quantity("{%s} chs" % q.name, q.description, NEGATED[q.name],
                     q.source, expr="-" + q.name)
            for q in out if q.name in NEGATED]
    names = {n.strip() for n, _, _ in matrix}      # hidden ones too
    out += [Quantity(tokens, d, group, "matrix", expr=e)
            for group, entries in COMPUTED.items() for e, tokens, d in entries
            if set(re.findall(r"\{(\w+)\}", tokens)) <= names]
    components([q for q in out if q.source == "matrix"])
    eirene = [(n, describe.EIRENE.get(n.strip()) or d, u)
              for n, d, u in eirene if n.strip() not in EIRENE_HIDDEN]
    out += [Quantity(n.strip(), d.strip() or n.strip(), NEUTRALS, "eirene")
            for n, d, _ in eirene]
    # EIRENE vectors: velocities, the momentum densities with the neutral
    # fluxes
    out += [Quantity(x + " " + y, d, NEUTRAL_VELOCITIES if re.fullmatch(
        r"vx[ami]", x) else "Neutrals fluxes", "evector", x, y)
            for x, y, d in _epairs(eirene)]
    def within(q):
        w = FINAL_WITHIN.get(q.group, ())
        return w.index(q.label) if q.label in w else len(w)
    out.sort(key=lambda q: (ORDER.index(q.group), within(q),
                            _species_order(q.name.lower())))
    vectors = _vectors([q for q in out if q.source == "matrix"])
    out = [_density(q) for q in out + vectors]
    names = {n for n, _ in maps}
    out = [q for q in out if not (q.name == "pit" and "pitch" in names)]
    out += [Quantity(n, d, EQUILIBRIUM, "equilibrium") for n, d in maps
            if n not in HIDDEN] + list(extra)
    out.sort(key=lambda q: (ORDER.index(q.group), within(q)))  # maps too
    return out


# wall fluxes of the plasma, on the boundary faces per face area, in the
# order of the plasma flux groups
WALL_FLUXES = ("wallflux", "wallfne", "wallfmo", "wallhflx", "wallfhe",
               "wallfhi", "wallfhn", "wallfhj", "wallfhp", "wallfhm",
               "wallfnt", "wallfkt", "wallfch")
# fluxes of the neutrals of EIRENE on its wall (the B2.5 wall elements,
# the core boundary and the additional surfaces), per element area, in
# this order
WALL_NEUTRALS = ("wldna", "wldnm", "wldra", "wldrm", "ewlda", "ewldm",
                 "ewldea", "ewldem", "ewldk", "ewldp", "wldpa", "wldpm",
                 "ewldrp", "wldspta", "wldsptm", "wlpump")
# the net deposited energy flux and its terms in this order, with their
# texts in this group (the terms of other groups are listed there too)
DEPOSITED = "Deposited energy fluxes"
WALL_DEPOSITED = (("walldep", "Net deposited energy flux (W.m^{-2})"),
                  ("wallhflx", "Plasma energy load (W.m^{-2})"),
                  ("wallrad", "Radiation heat load (W.m^{-2})"),
                  ("ewldk", "Neutrals kinetic energy load (W.m^{-2})"),
                  ("ewldp", "Potential energy of molecules formed at the "
                   "wall (W.m^{-2})"),
                  ("ewldrp", "Energy released by recycled ions (W.m^{-2})"))
# first of their group, in this order: the surface temperature and the
# incident energy the yields use
SURFACE = "Surface coefficients"
WALL_FIRST = ("walltemp", "ei")
WALL_GROUPS = [       # groups of the wall labels of b2plot, in this order
    ("Plasma fluxes", "|".join(WALL_FLUXES)),
    ("Neutrals fluxes", "|".join(WALL_NEUTRALS)),
    (DEPOSITED, r"walldep|wallrad"),
    (SURFACE,
     r"walltemp|ei|sput\w*|backsca\w*|impdepth|erosion|deposit|ero_ml|"
     r"depo_ml|erel|stckcoef"),
    ("Geometry", r"wallarea|[rz][12]|walldist|wallngth|nseg|north|south|"
     r"west|east|ibnd|imap[xy]")]
# order within the groups (the others as listed by b2plot)
WALL_ORDER = {"Plasma fluxes": WALL_FLUXES, "Neutrals fluxes": WALL_NEUTRALS,
              DEPOSITED: tuple(n for n, _ in WALL_DEPOSITED),
              SURFACE: WALL_FIRST,
              "Geometry": ("graze", "lparwall", "lpolwall")}  # GUI ones
WALL_OTHER = "Other wall quantities"
# material data and state of the plate model (bulk material, coating,
# deposited layers, temperatures and evaporation), the index masks of
# the wall elements and layers (iwlt, iswlt, ...), the radiation
# enhanced sublimation, the monolayer erosion and deposition, the
# chemical sputtering factor, the sticking coefficient, the layer
# fractions, the ends, sides, neighbours and indices of the elements, the
# parts of the wall fluxes (drawn stacked in the wall profile)
WALL_HIDDEN_RE = re.compile(
    r"kappa\w*|tgdns|cp_b\d|bbdyemis|vapprs\w*|sublheat|ckapp\w*|ctgdns|"
    r"c_cp_b\d|coathick|plathick|l(kappa|rho|cp|emis|thick|depth)|"
    r"cooltemp|"
    r"vaprtemp|time|qevap|qrad|thermev|i(s)?w\w*|"
    r"w(na|mo|he|hi|ch)\w+")
WALL_HIDDEN = {"sputres", "ero_ml", "depo_ml", "erel", "stckcoef",
               "sputfrac", "r1", "r2", "z1", "z2", "north", "south", "west",
               "east", "nseg", "ibnd", "imapx", "imapy",
               "ewldt",         # shown as its parts, ewldk and ewldp
               "wstrat"}        # applies to the next quantity (splits)


def _wall_group(name):
    return next((g for g, pattern in WALL_GROUPS if re.fullmatch(
        pattern, name)), WALL_OTHER)


def wall_quantities(categories, extra=()):
    """Quantities of the wall stack (b2plot wall labels) and extra ones
    in their groups, in the order of WALL_GROUPS."""
    order = [g for g, _ in WALL_GROUPS] + [WALL_OTHER]
    out = [Quantity(n.strip(), describe.WALL.get(n.strip()) or d.strip()
                    or n.strip(), _wall_group(n.strip()), "wall")
           for n, d, _ in dict(categories).get("Wall quantities", [])
           if n.strip() and n.strip() not in WALL_HIDDEN and
           not WALL_HIDDEN_RE.fullmatch(n.strip())]
    names = {q.name for q in out}
    out += [Quantity(n, text, DEPOSITED, "wall") for n, text in WALL_DEPOSITED
            if n in names and _wall_group(n) != DEPOSITED] + list(extra)

    def key(q):
        within = WALL_ORDER.get(q.group, ())
        return (order.index(q.group), within.index(q.name)
                if q.name in within else len(within))
    return sorted(out, key=key)


# groups of the B2.5 and EIRENE quantities of the movie files and of the
# chord files (the same variables), by name in this order; EIRENE ones on
# its triangles one group; vectors: the plasma and the neutral fluxes
SOLPS_GROUPS = (("Plasma state", r"na|ne|ua|te|ti|po"),
                ("Plasma fluxes", r"f(na|he|hi|ch)[xy]"),
                ("Plasma sources",
                 r"r(sa|ra|cx)(na|hi|hisum)|rqahe(sum)?|rqrad(sum)?|"
                 r"eirene_\w+|eneutrad(sum)?|emolrad(sum)?"),
                ("Anomalous transport coefficients",
                 r"dna|dpa|hc[ei]|vla[xy]|vsa"),
                ("Neutrals state", r"[dt][am]b2"),
                ("Neutrals fluxes", r"(r|p|re|pe)flux[am][xy]?"))
NEUTRAL_TRIANGLES = NEUTRALS
OTHER_GROUP = "Other"
MOVIE_ORDER = [g for g, _ in SOLPS_GROUPS] + [NEUTRAL_TRIANGLES,
                                              OTHER_GROUP]
MOVIE_ORDER.insert(MOVIE_ORDER.index("Neutrals fluxes"), NEUTRAL_VELOCITIES)
# vectors of the movie frames computed as those of the vector table of the
# final state without radial component (ZERO_RADIAL, the pitch not a frame)
PLASMA_MOVIE_VELOCITIES = "Plasma velocities"
MOVIE_ORDER.insert(MOVIE_ORDER.index("Plasma fluxes"), PLASMA_MOVIE_VELOCITIES)
PLASMA_MOVIE_VECTORS = [("ua*pit", "ua-ua", "Poloidal projection of the "
                         "parallel ion velocity (m s^{-1})")]
# quantities of the EIRENE movie frames computed as the b2plot labels of
# the final state (tempa, presa, vxa, fxdena; the masses are constant, the
# b2plot labels massa and massm, not frames): (expression, description) of
# the atoms and the molecules, and the vectors of their x and y components
NEUTRAL_MOVIE = [(e % ((k,) * e.count("%")), d % w) for k, w in (
    ("a", "Atom"), ("m", "Molecule")) for e, d in (
    ("2/3*eden%s/pden%s", "%s temperature (eV)"),
    ("2/3*eden%s*qe", "%s pressure (Pa)")) + tuple(
    ("v%sden%%s/(pden%%s*mass%%s)" % c,
     "%%s %s-directed velocity (m s^{-1})" % c) for c in "xyz") + tuple(
    ("v%sden%%s/mass%%s" % c,
     "%%s %s-directed particle flux density (m^{-2} s^{-1})" % c)
    for c in "xyz")]
NEUTRAL_MOVIE_VECTORS = [
    ("v%sden%s/(pden%s*mass%s)", NEUTRAL_VELOCITIES, "%s velocity (m s^{-1})"),
    ("v%sden%s/mass%s", "Neutrals fluxes",
     "%s particle flux density (m^{-2} s^{-1})")]
# order of the quantities within some groups (the others: as in the files)
WITHIN = {"Plasma state": ("ne", "na", "ua", "te", "ti", "po"),
          # as in b2.transport.inputfile (kind_coeff 1 to 7)
          "Anomalous transport coefficients": ("dna", "dpa", "hci", "hce",
                                               "vlax", "vlay", "vsa"),
          # by kind: particles, electron energy (with the radiation of
          # B2.5), ion energy, neutral radiation;
          # the B2.5 ones (ionisation, recombination, charge exchange)
          # before the EIRENE ones (atoms, molecules, recombination)
          "Plasma sources": ("rsana", "rrana", "rcxna", "eirene_papl_sna",
                             "eirene_pmpl_sna", "eirene_pppl_sna", "rqahe",
                             "rqrad", "eirene_eael_she", "eirene_emel_she",
                             "eirene_epel_she", "rsahi", "rrahi", "rcxhi",
                             "eirene_eapl_shi", "eirene_empl_shi",
                             "eirene_eppl_shi", "eneutrad", "emolrad")}


def solps_order(items, first=()):
    """items (with name and group) of the movie or chord files in the order
    of their groups (MOVIE_ORDER; first: groups before them), within a
    group as WITHIN says, the poloidal neutral fluxes (pflux*, peflux*)
    before their radial ones (rflux*, reflux*), else in file order."""
    order = list(first) + MOVIE_ORDER
    at = {i.name: k for k, i in reversed(list(enumerate(items)))}

    def rank(k, i):
        within = WITHIN.get(i.group, ())
        if i.name in within:
            return (within.index(i.name), 0)
        twin = re.sub(r"^p(e?flux)", r"r\1", i.name)
        if twin != i.name and twin in at:       # poloidal: before radial
            return (len(within) + at[twin], 0)
        return (len(within) + k, 1 if re.match(r"re?flux", i.name) else 0)
    return [i for _, _, i in sorted(
        ((order.index(i.group) if i.group in order else len(order),
          rank(k, i), k), k, i) for k, i in enumerate(items))]


def solps_group(name, eirene=False, vector=False):
    """Group of a quantity of the movie or chord files (vector: of a flux
    vector, plasma or neutral)."""
    neutral = eirene or re.fullmatch(SOLPS_GROUPS[5][1], name)
    if vector:
        return SOLPS_GROUPS[5][0] if neutral else SOLPS_GROUPS[1][0]
    if eirene:
        return NEUTRAL_TRIANGLES
    return next((g for g, p in SOLPS_GROUPS if re.fullmatch(p, name)),
                OTHER_GROUP)


def translator(categories):
    """Translator of expressions with the quantities and constants of a
    CATALOG message."""
    cats = dict(categories)
    kinds = {n.strip(): k for cat, k in (("Matrix quantities", "matrix"),
                                         ("Eirene quantities", "eirene"))
             for n, _, _ in cats.get(cat, []) if n.strip()}
    return Translator(kinds, [n.strip() for n, _, _ in
                              cats.get("Constants", [])])


def derived(specs, translate):
    """Quantities of the derived quantities saved by the user (dicts with
    expr, name, unit), and the messages of those that do not translate."""
    out, errors = [], []
    for spec in specs:
        try:
            tokens, kind = translate(spec["expr"])
        except ExpressionError as err:
            errors.append("%s: %s" % (spec["expr"], err))
            continue
        text = spec.get("name") or spec["expr"]
        if spec.get("unit"):
            text += " (%s)" % spec["unit"]
        out.append(Quantity(tokens, text, DERIVED, kind, expr=spec["expr"]))
    return out, errors


def units_tex(units):
    """Movie file units in the catalogue form: 'm^-3 s^-1' -> 'm^{-3}
    s^{-1}'."""
    return re.sub(r"\^(-?\d+)", r"^{\1}", units)


# descriptions of the anomalous transport coefficients of b2movies.nc as
# in the final state, with their units (all in m^2 s^-1 but the pinch
# velocities; older files give m^-2 s^-1 and m kg^-1 s^-1)
MOVIE_TEXT = {"dna": "Density-driven particle diffusivity (m^{2} s^{-1})",
              "dpa": "Pressure-driven particle diffusivity (m^{2} s^{-1})",
              "hci": "Ion heat diffusivity (m^{2} s^{-1})",
              "hce": "Electron heat diffusivity (m^{2} s^{-1})",
              "vlax": "Poloidal pinch velocity (m s^{-1})",
              "vlay": "Radial pinch velocity (m s^{-1})",
              "vsa": "Viscosity (m^{2} s^{-1})"}


def _movie_text(v):
    if v.file == 1 and v.name in MOVIE_TEXT:
        return MOVIE_TEXT[v.name]
    text = v.long or v.name
    return "%s (%s)" % (text, units_tex(v.units)) if v.units else text


def _movie_density(q):
    """A plasma flux of b2movies.nc as a density: the face fluxes, put on
    the cells by b2plot (mvframe, x or y by the last letter of the name),
    divided by the projected cell area; the sources of the file are
    already per m^3 (cdfmovie divides them by the cell volume)."""
    if q.group != SOLPS_GROUPS[1][0] or q.source not in ("matrix", "vector") \
            or q.movie != 1:
        return q
    text, unit = split_unit(q.description)
    if not unit or "m^{-" in unit:
        return q
    per = ("sxperp m/", "sy m/") if q.source == "vector" else (
        ("sy m/",) if q.name.endswith("y") else ("sxperp m/",))
    return replace(q, description="%s (%s)" % (
        text, density_unit(unit, 2, " ")), per=per)


def _movie_partner(v, names):
    """Name of the y component of v: fnax -> fnay, vxdena -> vydena."""
    if v.name.startswith("vx") and "vy" + v.name[2:] in names:
        return "vy" + v.name[2:]
    if v.name.endswith("x") and v.name[:-1] + "y" in names:
        return v.name[:-1] + "y"
    return None


def _neutral_movie(movies, translate):
    """Quantities and vectors of NEUTRAL_MOVIE from the EIRENE movie file
    (file 2) with the translator of the run, those of its variables only."""
    if translate is None or 2 not in movies:
        return [], []
    have = {v.name for v in movies[2].variables}

    def tokens(expr):
        t = translate(expr)[0]
        return re.sub(r"\{(mass[am])\}", r"\1", t)      # not movie frames
    out, vectors = [], []
    for expr, desc in NEUTRAL_MOVIE:
        try:
            t = tokens(expr)
        except ExpressionError:
            continue
        if names_of(t) <= have:
            out.append(Quantity(t, desc, NEUTRAL_TRIANGLES, "eirene",
                                movie=2, expr=expr))
    for k, w in (("a", "Atom"), ("m", "Molecule")):
        for e, group, desc in NEUTRAL_MOVIE_VECTORS:
            x, y = (e % ((c,) + (k,) * (e.count("%") - 1)) for c in "xy")
            try:
                tx, ty = tokens(x), tokens(y)
            except ExpressionError:
                continue
            if names_of(tx + " " + ty) <= have:
                vectors.append(Quantity(tx + " " + ty, desc % w, group,
                                        "evector", tx, ty, movie=2))
    return out, vectors


def _plasma_movie(movies, translate):
    """Vectors of PLASMA_MOVIE_VECTORS from the B2.5 movie file with the
    variables of their expressions, with the translator of the run."""
    out = []
    if translate is None:
        return out
    for x, y, desc in PLASMA_MOVIE_VECTORS:
        try:
            tx, ty = (re.sub(r"\{(pit)\}", r"\1", translate(e)[0])
                      for e in (x, y))          # not movie frames
        except ExpressionError:
            continue
        for f in sorted(movies):
            if f != 2 and names_of(tx + " " + ty) <= {
                    v.name for v in movies[f].variables}:
                out.append(Quantity(tx + " " + ty, desc,
                                    PLASMA_MOVIE_VELOCITIES, "vector", tx,
                                    ty, movie=f))
                break
    return out


def movie_quantities(movies, derived_quantities=(), translate=None):
    """Quantities of the movie files (data.MovieFile per file): every
    variable, x/y component pairs as vectors, the derived quantities
    whose operands are all variables of one file, and the neutral ones of
    NEUTRAL_MOVIE (with translate, the translator of the run)."""
    out, vectors = [], []
    for q in derived_quantities:
        names = names_of(q.name)
        for f in sorted(movies):
            if names <= {v.name for v in movies[f].variables}:
                out.append(Quantity(q.name, q.description, DERIVED,
                                    q.source, movie=f, expr=q.expr))
                break
    for f in sorted(movies):
        variables = movies[f].variables
        names = {v.name: v for v in variables}
        for v in variables:
            if v.name.endswith("sum"):
                continue                # sums over the species: hidden
            out.append(Quantity(v.name, _movie_text(v),
                                solps_group(v.name, f == 2),
                                "eirene" if f == 2 else "matrix", movie=f))
            y = _movie_partner(v, names)
            w = names.get(y)
            if w is None or (w.location, w.ncol) != (v.location, v.ncol) \
                    or solps_group(v.name, f == 2) == SOLPS_GROUPS[3][0]:
                continue            # no vector of transport coefficients
            #                         (the anomalous pinch velocities)
            desc = re.sub(r"(?i)\b(poloidal|x-directed)\s+", "",
                          _movie_text(v), count=1)
            vectors.append(Quantity(
                "%s %s" % (v.name, y), desc[:1].upper() + desc[1:],
                solps_group(v.name, f == 2, vector=True),
                "evector" if f == 2 else "vector",
                v.name, y, movie=f))
    components([q for q in out if q.source != "vector" and q.group != DERIVED])
    extra, extra_vectors = _neutral_movie(movies, translate)
    extra_vectors += _plasma_movie(movies, translate)
    res = solps_order(out + extra + vectors + extra_vectors, first=(DERIVED,))
    res = [_movie_density(q) for q in res]
    # the neutral triangle quantities by species, as in the plasma table
    at = [i for i, q in enumerate(res)
          if q.group == NEUTRAL_TRIANGLES and q.source == "eirene"]
    for i, q in zip(at, sorted((res[i] for i in at), key=_neutral_rank)):
        res[i] = q
    # their vectors: particle flux densities before momentum densities
    at = [i for i, q in enumerate(res)
          if q.source == "evector" and q.group == "Neutrals fluxes"]
    for i, q in zip(at, sorted((res[i] for i in at),
                               key=lambda q: "{" not in q.name)):
        res[i] = q
    return res


def _neutral_rank(q):
    """(species, kind) of a neutral triangle quantity of the movies:
    density, temperature, pressure, energy density, velocity, particle flux
    density, momentum density."""
    s = q.expr or q.name
    m = re.search(r"(?:pden|eden|v[xyz]den)([ami])", s)
    kinds = (r"^pden", r"^2/3\*eden.*/pden", r"\*qe$", r"^eden",
             r"^vxden.*/\(", r"^vyden.*/\(", r"^vzden.*/\(",
             r"^vxden.*/mass", r"^vyden.*/mass", r"^vzden.*/mass", r"^vxden",
             r"^vyden", r"^vzden")
    kind = next((n for n, k in enumerate(kinds) if re.search(k, s)),
                len(kinds))
    return ("ami".find(m.group(1)) if m else 3, kind)
