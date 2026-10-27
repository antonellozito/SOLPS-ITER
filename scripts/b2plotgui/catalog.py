"""Quantities of the 2D tab from the b2plot command catalogue (CATALOG).

Matrix quantities are B2.5 cell fields, Eirene quantities are fields on
the EIRENE triangles. A poloidal and a radial quantity with otherwise the
same description form a vector quantity. The groups only sort the list
for the user; the names are the b2plot labels.
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
ORDER = ["Plasma state", VECTORS, "Fluxes", "Velocities",
         "Sources and sinks", "Transport coefficients", NEUTRALS,
         "Geometry and magnetic field", OTHER]


@dataclass
class Quantity:
    name: str                   # b2plot label, "pol rad" for vectors
    description: str
    group: str
    source: str                 # "matrix", "eirene" or "vector"
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


def _pairs(entries):
    """(poloidal, radial, description) for matching component labels."""
    radial = {}
    for name, desc, _ in entries:
        key = re.sub(r"(?i)\bradial\b", "#", desc, count=1)
        if key != desc:
            radial[key.lower()] = name
    out = []
    for name, desc, _ in entries:
        key = re.sub(r"(?i)\bpoloidal\b", "#", desc, count=1)
        if key != desc and key.lower() in radial:
            text = re.sub(r"(?i)\bpoloidal\s+", "", desc, count=1)
            out.append((name, radial[key.lower()], text[:1].upper()
                        + text[1:]))
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
    out.sort(key=lambda q: (ORDER.index(q.group), q.name.lower()))
    return out
