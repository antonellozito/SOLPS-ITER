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

GROUPS = [
    ("Geometry and magnetic field",
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
    ("Convergence (residuals, corrections)",
     r"r(co|mo|mt|ee|ei|po|en|kt|zt)|c(pa|ua|ut|te|ti|po|kt|zt|tn)"),
    ("Atomic physics and radiation",
     r"neutrad|molrad|ionrad|srcml|edissml"),
    ("Transport coefficients",
     r"d|dp|ky[ei]|kyi0|kyn0|vla[xy]|visc|sig|alf|dkt|dzt"),
    ("Flux limiters", r"fle|fli|nflf..x?y?|flvisc|fluc.|flk.|flalc?"),
    ("Neoclassical, collisionality, plasma frequencies",
     r"dnneo|chineo|vnneo|vwneo|lnn|ltt|nuab|nua|nustar|vth|rhol|deltal|wb|"
     r"deltaw[nt]?|omega|deltab|deltapar|chhichii|colle|colli|lnlam|wpe|wce|"
     r"wci|vthe|vthi|valfven"),
    ("Cell masks and indices", INTEGER.pattern
     + r"|rlcl|gdcl|bdcl|npcl|iimp|iomp|ix|iy|iix|iiy|ic|ift|xymap|bc|rc"),
]
OTHER = "Other matrix quantities"
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
CHORDS = "Chord contributions (*.chords files)"
EQUILIBRIUM = "Magnetic equilibrium (derived)"
CHORD_POINTS = 33               # points of each chord sent by guigeom
ORDER = [DERIVED, "Plasma densities", "Plasma velocities",
         "Plasma temperatures", "Plasma pressures", "Plasma potential",
         "Plasma state", "Particle fluxes", "Momentum fluxes",
         "Total energy fluxes", "Electron heat fluxes",
         "Ion heat fluxes", "Current fluxes", "Plasma fluxes",
         "Particle sources", "Momentum sources", "Electron energy sources",
         "Ion energy sources", "Charge sources",
         "Sources and sinks", "Atomic physics and radiation", "Transport "
         "coefficients", "Neoclassical, collisionality, plasma frequencies",
         "Flux limiters", "Convergence (residuals, corrections)",
         "Neutrals state", NEUTRAL_VELOCITIES,
         "Neutrals fluxes", NEUTRALS,
         "Geometry and "
         "magnetic field", EQUILIBRIUM, FAMILIES[-1][0], OTHER, CHORDS]
# order within the groups (the main plasma state as in the movie files,
# velocities after it), the others by name; labels left out of the list
FINAL_WITHIN = {"Plasma densities": ("ne", "ni", "na", "zeff"),
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
    #                             "equilibrium" (computed by the GUI)
    poloidal: str = ""
    radial: str = ""
    movie: int = 0              # 1 b2movies.nc, 2 eirenemovies.nc
    expr: str = ""              # derived: the expression (name: tokens)

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


def components(items):
    """Descriptions of the quantities with a poloidal and a radial
    component written "What (poloidal component) (unit)" (items with name
    and description, changed in place; masks and indices left as they
    are)."""
    names = {i.name for i in items}
    for i in items:
        d = i.description
        which = _side(i.name, names)
        if not which or "component)" in d or re.search(
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


def quantities(categories, maps=()):
    """List of Quantity from the categories of the CATALOG message, and
    the 2D maps of the derived equilibrium quantities (name, label: the
    GUI computes them from the geometry files, source "equilibrium")."""
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
    out += _vectors([q for q in out if q.source == "matrix"])
    out += [Quantity(n, d, EQUILIBRIUM, "equilibrium") for n, d in maps]
    out.sort(key=lambda q: ORDER.index(q.group))       # maps in their order
    return out


WALL_GROUPS = [       # groups of the wall labels of b2plot, in this order
    ("Fluxes and loads", r"ei|wallflux|wallhflx|thermev|qevap|qrad"),
    ("Temperatures", r"walltemp|cooltemp|vaprtemp|vapprs|time"),
    ("Sputtering and reflection",
     r"sput\w*|backsca\w*|erosion|deposit|ero_ml|depo_ml|erel|stckcoef"),
    ("Geometry", r"wallarea|[rz][12]|walldist|wallngth|nseg|north|south|"
     r"west|east|ibnd|imap[xy]|plathick"),
    ("Bulk material", r"kappa\w*|tgdns|cp_b\d|bbdyemis|vapprs_[ab]|"
     r"sublheat"),
    ("Coating", r"ckapp\w*|ctgdns|c_cp_b\d|coathick"),
    ("Layers", r"l(kappa|rho|cp|emis|thick|depth)"),
    ("Indices", r"i(s)?w\w*")]
WALL_OTHER = "Other wall quantities"


def _wall_group(name):
    return next((g for g, pattern in WALL_GROUPS if re.fullmatch(
        pattern, name)), WALL_OTHER)


def wall_quantities(categories):
    """Quantities of the wall stack (b2plot wall labels) in their groups,
    in the order of WALL_GROUPS."""
    order = [g for g, _ in WALL_GROUPS] + [WALL_OTHER]
    out = [Quantity(n.strip(), describe.WALL.get(n.strip()) or d.strip()
                    or n.strip(), _wall_group(n.strip()), "wall")
           for n, d, _ in dict(categories).get("Wall quantities", [])
           if n.strip()]
    return sorted(out, key=lambda q: order.index(q.group))


def chord_quantities(layers, eirene):
    """Contribution maps of every chord of the chord sets of the run (b2plot
    chmf on the cells, echmf on the EIRENE triangles)."""
    out = []
    sets = [k.split(": ", 1)[1] for k in layers if k.startswith("chords: ")]
    for i, label in enumerate(sets, 1):
        n = len(layers["chords: " + label]) // (CHORD_POINTS - 1)
        for j in range(1, n + 1):
            for fn, where in (("chmf", "cells"), ("echmf", "triangles"))[
                    :1 + bool(eirene)]:
                out.append(Quantity(
                    "%d %d %s" % (i, j, fn), "Contribution of chord %d of %s "
                    "to the %s" % (j, label, where), CHORDS, "matrix" if fn ==
                    "chmf" else "eirene", expr="%s(%d, %d)" % (fn, i, j)))
    return out


# groups of the B2.5 and EIRENE quantities of the movie files and of the
# chord files (the same variables), by name in this order; EIRENE ones on
# its triangles one group; vectors: the plasma and the neutral fluxes
SOLPS_GROUPS = (("Plasma state", r"na|ne|ua|te|ti|po"),
                ("Plasma fluxes", r"f(na|he|hi|ch)[xy]"),
                ("Plasma sources",
                 r"r(sa|ra|cx)(na|hi|hisum)|rqahe(sum)?|rqrad(sum)?|"
                 r"eirene_\w+|eneutrad(sum)?|emolrad(sum)?"),
                ("Transport coefficients", r"dna|dpa|hc[ei]|vla[xy]|vsa"),
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
          "Transport coefficients": ("dna", "dpa", "vlax", "vlay", "vsa",
                                     "hce", "hci"),
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


def _movie_text(v):
    text = v.long or v.name
    return "%s (%s)" % (text, units_tex(v.units)) if v.units else text


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
