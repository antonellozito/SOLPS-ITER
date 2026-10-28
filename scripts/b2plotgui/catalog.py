"""Quantities of the 2D tab from the b2plot command catalogue (CATALOG).

Matrix quantities are B2.5 cell fields, Eirene quantities are fields on
the EIRENE triangles. A poloidal and a radial quantity with otherwise the
same description form a vector quantity, and so do EIRENE quantities
whose labels differ only by x and y (Cartesian R and Z components). The
groups only sort the list for the user; the names are the b2plot labels.
"""

import re
from dataclasses import dataclass

from . import labels

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
OTHER = "Other matrix quantities"
NEUTRALS = "Neutrals (EIRENE)"
NEUTRAL_VECTORS = "Neutral fluxes and velocities (EIRENE vectors)"
ORDER = ["Plasma state", VECTORS, "Fluxes", "Velocities",
         "Sources and sinks", "Transport coefficients", NEUTRALS,
         NEUTRAL_VECTORS, "Geometry and magnetic field", OTHER]


@dataclass
class Quantity:
    name: str                   # b2plot label, "pol rad" for vectors
    description: str
    group: str
    source: str                 # "matrix", "eirene", "vector", "evector"
    poloidal: str = ""
    radial: str = ""

    @property
    def text(self):
        return labels.tex_to_plain(self.description)


def _group(description):
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


def quantities(categories):
    """List of Quantity from the categories of the CATALOG message."""
    cats = dict(categories)
    matrix = [e for e in cats.get("Matrix quantities", []) if e[0].strip()]
    eirene = [e for e in cats.get("Eirene quantities", []) if e[0].strip()]
    out = [Quantity(n.strip(), d.strip() or n.strip(), _group(d), "matrix")
           for n, d, _ in matrix]
    out += [Quantity(p + " " + r, d, VECTORS, "vector", p.strip(),
                     r.strip()) for p, r, d in _pairs(matrix)]
    out += [Quantity(n.strip(), d.strip() or n.strip(), NEUTRALS, "eirene")
            for n, d, _ in eirene]
    out += [Quantity(x + " " + y, d, NEUTRAL_VECTORS, "evector", x, y)
            for x, y, d in _epairs(eirene)]
    out.sort(key=lambda q: (ORDER.index(q.group), q.name.lower()))
    return out
