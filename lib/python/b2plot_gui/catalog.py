"""Quantities of the 2D tab from the b2plot command catalogue (CATALOG).

Matrix quantities are B2.5 cell fields, Eirene quantities are fields on
the EIRENE triangles. A poloidal and a radial quantity with otherwise the
same description form a vector quantity, and so do EIRENE quantities
whose labels differ only by x and y (Cartesian R and Z components). The
groups only sort the list for the user; the names are the b2plot labels.
"""

import re
from dataclasses import dataclass

from ..b2plot import labels
from .expression import ExpressionError, Translator, names_of

VECTORS = "Fluxes and velocities (vectors)"
GROUPS = [
    ("Geometry and magnetic field",
     ("flux function", "volume", "area", "length", "coordinate", "metric",
      "magnetic", "angle", "pitch", "b_{", "connection")),
    ("Fluxes", ("flux", "current")),
    ("Sources and sinks",
     ("source", "sink", "rate", "loss", "power", "heating", "radiat")),
    ("Velocities", ("velocity", "mach", "speed")),
    ("Transport coefficients",
     ("coefficient", "diffusiv", "conductiv", "viscosit", "resistiv")),
    ("Plasma state",
     ("density", "temperature", "pressure", "potential", "energy",
      "charge", "z_{eff}", "zeff")),
]
# Labels with an integer argument (masks): written ixeq(10) as derived
INTEGER = re.compile(r"i[xysc](lt|le|eq|ne|ge|gt)|nreg|freg|clbl|flbl|tlbl|"
                     r"ifeq|iveq|fteq")
# Families of labels, checked before the description keywords of GROUPS
FAMILIES = [
    ("Convergence (residuals, corrections)",
     r"r(co|mo|mt|ee|ei|po|en|kt|zt)|c(pa|ua|ut|te|ti|po|kt|zt|tn)"),
    ("Previous time step", r"(na|ne|ni|te|ti|ua|po|tn|kt|zt)0"),
    ("Balances", r"ebld|ebls|ebal|pbal"),
    ("Sources by origin",
     r"(br|bc|bm|ex)(na|ne|mo|he|hi|ch|hn|kt|zt)|s(na|ne|he|hi|ch|hn|kt|zt)"),
    ("Atomic physics and radiation", r"rqae|rsa[inm]|rra[nim]|rcx[nim]|"
     r"b2br|b2ra|[am]hal|neutrad|molrad|ionrad|srcml|edissml"),
    ("Momentum terms", r"sm(pr|pt|fr|p|o|q|af|ag|av|th|cf)"),
    ("Heating terms", r"dvue|dvua|exbe|exba|visa|joul|fraa|str"),
    ("Transport coefficients",
     r"d|dp|ky[ei]|kyi0|kyn0|vla[xy]|visc|sig|alf|dkt|dzt"),
    ("Flux limiters", r"fle|fli|nflf..x?y?|flvisc|fluc.|flk.|flalc?"),
    ("Neoclassical, collisionality, plasma frequencies",
     r"dnneo|chineo|vnneo|vwneo|lnn|ltt|nuab|nua|nustar|vth|rhol|deltal|wb|"
     r"deltaw[nt]?|omega|deltab|deltapar|chhichii|colle|colli|lnlam|wpe|wce|"
     r"wci|vthe|vthi|valfven"),
    ("Cell masks and indices (integer argument: ixeq(10))", INTEGER.pattern
     + r"|rlcl|gdcl|bdcl|npcl|iimp|iomp|ix|iy|iix|iiy|ic|ift|xymap|bc|rc"),
]
OTHER = "Other matrix quantities"
NEUTRALS = "Neutrals (EIRENE)"
NEUTRAL_VECTORS = "Neutral fluxes and velocities (EIRENE vectors)"
DERIVED = "Derived quantities"
CHORDS = "Chord contributions (*.chords files)"
EQUILIBRIUM = "Magnetic equilibrium (derived)"
CHORD_POINTS = 33               # points of each chord sent by guigeom
ORDER = [DERIVED, "Plasma state", VECTORS, "Fluxes", "Velocities",
         "Sources and sinks", "Sources by origin", "Atomic physics and "
         "radiation", "Momentum terms", "Heating terms", "Transport "
         "coefficients", "Neoclassical, collisionality, plasma frequencies",
         "Flux limiters", "Balances", "Convergence (residuals, corrections)",
         "Previous time step", NEUTRALS, NEUTRAL_VECTORS, "Geometry and "
         "magnetic field", EQUILIBRIUM, FAMILIES[-1][0], OTHER, CHORDS]


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


# Component pairs whose descriptions differ by more than the direction
EXTRA_PAIRS = [("fcxviskt", "fcyviskt")]


def _key(name, desc, word):
    """Description without its own label name and with word replaced."""
    d = re.sub(r"\s*[\[(]%s[\])]" % re.escape(name), "", desc, flags=re.I)
    key = re.sub(r"(?i)\b%s\b" % word, "#", d, count=1)
    return (" ".join(key.lower().split()), d) if key != d else (None, d)


def _pairs(entries):
    """(poloidal, radial, description) for matching component labels."""
    radial = {}
    for name, desc, _ in entries:
        key, _ = _key(name, desc, "radial")
        if key is not None:
            radial[key] = name
    out, seen = [], set()
    for name, desc, _ in entries:
        key, d = _key(name, desc, "poloidal")
        if key is not None and key in radial:
            text = re.sub(r"(?i)\bpoloidal\s+", "", d, count=1)
            out.append((name, radial[key], text[:1].upper() + text[1:]))
            seen.add(name)
    descs = {n: d for n, d, _ in entries}
    for p, r in EXTRA_PAIRS:
        if p in descs and r in descs and p not in seen:
            text = re.sub(r"(?i)\bpoloidal\s+", "", descs[p], count=1)
            out.append((p, r, text[:1].upper() + text[1:]))
    return out


def _epairs(entries):
    """(R, Z, description) for EIRENE labels differing by x and y."""
    descs = {n: d for n, d, _ in entries}
    out = []
    for name, desc, _ in entries:
        if "x" not in name:
            continue
        partner = name.replace("x", "y", 1)
        if partner in descs:
            text = re.sub(r"(?i)\bcartesian\s+x-", "", desc, count=1)
            text = re.sub(r"\bX-", "", text, count=1)
            out.append((name, partner, text[:1].upper() + text[1:]))
    return out


def quantities(categories, maps=()):
    """List of Quantity from the categories of the CATALOG message, and
    the 2D maps of the derived equilibrium quantities (name, label: the
    GUI computes them from the geometry files, source "equilibrium")."""
    cats = dict(categories)
    matrix = [e for e in cats.get("Matrix quantities", []) if e[0].strip()]
    eirene = [e for e in cats.get("Eirene quantities", []) if e[0].strip()]
    out = [Quantity(n.strip(), d.strip() or n.strip(),
                    _group(n.strip(), d), "matrix") for n, d, _ in matrix]
    out += [Quantity(p + " " + r, d, VECTORS, "vector", p.strip(),
                     r.strip()) for p, r, d in _pairs(matrix)]
    out += [Quantity(n.strip(), d.strip() or n.strip(), NEUTRALS, "eirene")
            for n, d, _ in eirene]
    out += [Quantity(x + " " + y, d, NEUTRAL_VECTORS, "evector", x, y)
            for x, y, d in _epairs(eirene)]
    out.sort(key=lambda q: (ORDER.index(q.group), q.name.lower()))
    out += [Quantity(n, d, EQUILIBRIUM, "equilibrium") for n, d in maps]
    out.sort(key=lambda q: ORDER.index(q.group))       # maps in their order
    return out


def wall_quantities(categories):
    """Quantities of the wall stack (b2plot wall labels), for the strip."""
    return [Quantity(n.strip(), d.strip() or n.strip(), "Wall", "wall")
            for n, d, _ in dict(categories).get("Wall quantities", [])
            if n.strip()]


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


MOVIE_GROUPS = {(1, 1): "Movie: B2.5 cells", (1, 2): "Movie: B2.5 faces "
                "(at the cells)", (2, 3): "Movie: EIRENE"}
MOVIE_VECTORS = {1: "Movie: B2.5 vectors", 2: "Movie: EIRENE vectors"}
MOVIE_ORDER = [MOVIE_GROUPS[1, 1], MOVIE_GROUPS[1, 2], MOVIE_VECTORS[1],
               MOVIE_GROUPS[2, 3], MOVIE_VECTORS[2], "Movie"]


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


def movie_quantities(movies, derived_quantities=()):
    """Quantities of the movie files (data.MovieFile per file): every
    variable, x/y component pairs as vectors, and the derived quantities
    whose operands are all variables of one file."""
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
            out.append(Quantity(v.name, _movie_text(v), MOVIE_GROUPS.get(
                (f, v.location), "Movie"), "eirene" if f == 2 else
                "matrix", movie=f))
            y = _movie_partner(v, names)
            w = names.get(y)
            if w is None or (w.location, w.ncol) != (v.location, v.ncol):
                continue
            desc = re.sub(r"(?i)\b(poloidal|x-directed)\s+", "",
                          _movie_text(v), count=1)
            vectors.append(Quantity(
                "%s %s" % (v.name, y), desc[:1].upper() + desc[1:],
                MOVIE_VECTORS[f], "evector" if f == 2 else "vector",
                v.name, y, movie=f))
    out += vectors
    out.sort(key=lambda q: -1 if q.group == DERIVED else
             MOVIE_ORDER.index(q.group))                    # stable
    return out
