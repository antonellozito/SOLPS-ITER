"""Vectors drawn as their components, arrows of their own: their poloidal
and radial components (horizontal and vertical for the EIRENE vectors);
the total fluxes of the vector table as their physical components (each a
vector quantity of the table, by name): the parts
add up to the total (checked on runs without and with drifts), but for
the particle flux with drifts, whose parts B2.5 adds up to fna_mdf +
fnaPSch and not to fna; the rest (total minus the parts) is drawn as a
part of its own when it is not negligible."""

import numpy as np

from ..model import split_unit
from ...b2plot import labels

SPLITS = {
    "fnax fnay": ("fnaxpll fnaypll", "fnaxnanm fnaynanm",
                  "fnaxpanm fnaypanm", "fnaxpnch fnaypnch",
                  "fnaxecrb fnayecrb", "fnaxdia fnaydia", "fnaxch fnaych"),
    "fmox fmoy": ("fmoxflua fmoyflua", "fmoxcvsa fmoycvsa",
                  "fmoxhybr fmoyhybr"),
    "fhtx fhty": ("fhex fhey", "fhix fhiy", "fhnx fhny", "fhjx fhjy",
                  "fhpx fhpy", "fhmx fhmy", "fntx fnty", "fktx fkty"),
    "fhex fhey": ("fhexconv fheyconv", "fhexcond fheycond",
                  "fhexthj fheythj", "fhexdia fheydia", "fhexstr fheystr"),
    "fhix fhiy": ("fhixconv fhiyconv", "fhixcond fhiycond",
                  "fhixdia fhiydia", "fhixstr fhiystr", "fhixinrt fhiyinrt",
                  "fhixvspa fhiyvspa", "fhixvspe fhiyvspe",
                  "fhixvisq fhiyvisq", "fhixanml fhiyanml",
                  "fhixvskt fhiyvskt", "fhixvzh fhiyvzh"),
    "fchx fchy": ("fchp 0", "fchxdia fchydia", "fchxanml fchyanml",
                  "fchxinrt fchyinrt", "fchxvspa fchyvspa",
                  "fchxvspe fchyvspe", "fchxvisq fchyvisq",
                  "fcxviskt fcyviskt", "fchxn fchyn"),
}
# the wall fluxes as the same parts (wall labels of b2plot: the face
# fluxes of the parts on the wall elements), the total energy flux as the
# wall fluxes it adds up, the net deposited energy flux as its terms; a
# minus: the part subtracted
WALL_SPLITS = {
    "wallflux": ("wnapll", "wnananm", "wnapanm", "wnapnch", "wnaecrb",
                 "wnadia", "wnach"),
    "wallfmo": ("wmoflua", "wmocvsa", "wmohybr"),
    "wallfhe": ("wheconv", "whecond", "whethj", "whedia", "whestr"),
    "wallfhi": ("whiconv", "whicond", "whidia", "whistr", "whiinrt",
                "whivspa", "whivspe", "whivisq", "whianml", "whivskt",
                "whivzh"),
    "wallfch": ("wchp", "wchdia", "wchanml", "wchinrt", "wchvspa",
                "wchvspe", "wchvisq", "wchvskt", "wchn"),
    "wallhflx": ("wallfhe", "wallfhi", "wallfhn", "wallfhp", "wallfhm",
                 "wallfnt", "wallfkt"),
    "walldep": ("wallhflx", "wallrad", "ewldt", "-ewldrp"),
}
WALL_TEXTS = {"ewldrp": "Energy released by recycled ions"}   # shorter
REST = "rest"                   # name of the rest
REST_MIN = 1e-4                 # drawn above this rms fraction of the total
ZERO = 1e-6                     # a part this small (of the total) is zero


def parts_of(q, quantities):
    """The vector quantities (of the list quantities) the vector quantity
    q splits into, in order; None if it does not split."""
    names = SPLITS.get(getattr(q, "name", None))
    if names is None:
        return None
    by = {p.name: p for p in quantities if p.source == "vector"}
    return [by[n] for n in names if n in by]


def label(q):
    """Short text of a part: its description without the unit."""
    return labels.any_to_plain(split_unit(q.description)[0])


def wall_label(run, name):
    """Short text of a part of a wall flux: its description without the
    unit and the word Wall (a minus before it when subtracted)."""
    from .. import describe
    sign, name = ("\u2212", name[1:]) if name.startswith("-") else ("", name)
    text = WALL_TEXTS.get(name) or describe.WALL.get(name) or dict(
        (n.strip(), d) for n, d, _ in dict(run.catalog).get(
            "Wall quantities", [])).get(name, name)
    text = labels.any_to_plain(split_unit(text)[0]).strip()
    text = text[5:] if text.startswith("Wall ") else text
    return sign + text[:1].upper() + text[1:]


def wall_parts(total, parts):
    """[(name, label, values)] of the parts [(name, label, values)] of the
    wall flux total (values) but those zero everywhere, and of the rest
    when not negligible."""
    total = np.asarray(total, float)
    norm = np.sqrt(np.nansum(total * total)) or 1.0
    rest = total - sum(np.nan_to_num(v) for _, _, v in parts)
    size = np.sqrt(np.nansum(rest * rest)) / norm
    big = np.nanmax(np.abs(total), initial=0.0)
    return [p for p in parts if np.nanmax(np.abs(p[2]), initial=0.0) >
            ZERO * big] + ([(REST, "rest (total minus the parts, %.0f %%)"
                            % (100.0 * size), rest)] if size > REST_MIN
                          else [])


def _cells(tab, data, like):
    """(vr, vz) per cell of a part, with the species chosen for the total
    (data like) when it has the same species, else all summed."""
    if list(data.columns) == list(like.columns):
        d, col = tab.summed_vector(data)
        return np.asarray(d.vr[col], float), np.asarray(d.vz[col], float)
    return (np.asarray(data.vr, float).sum(0),
            np.asarray(data.vz, float).sum(0))


def combine(tab, total, col, parts):
    """[(name, label, vr, vz)] of the parts arrived [(Quantity, data)] and
    of the rest (if not negligible), each with a flag zero; for the
    vector total (column col, the species chosen)."""
    tr = np.asarray(total.vr[col], float)
    tz = np.asarray(total.vz[col], float)
    norm = np.sqrt(np.nansum(tr * tr + tz * tz)) or 1.0
    out, sr, sz = [], np.zeros_like(tr), np.zeros_like(tz)
    for q, d in parts:
        vr, vz = _cells(tab, d, tab.vector_data)
        if vr.shape != tr.shape:
            continue
        sr, sz = sr + np.nan_to_num(vr), sz + np.nan_to_num(vz)
        size = np.sqrt(np.nansum(vr * vr + vz * vz)) / norm
        out.append((q.name, label(q), vr, vz, size < ZERO))
    rr, rz = tr - sr, tz - sz
    rest = np.sqrt(np.nansum(rr * rr + rz * rz)) / norm
    if rest > REST_MIN:
        out.append((REST, "rest (total minus the parts, %.0f %%)"
                    % (100.0 * rest), rr, rz, False))
    return out


def geometric(tab, v, col):
    """[(name, label, vr, vz, zero)] of the poloidal and radial components
    of the vector v (column col; the poloidal one along the poloidal field
    of each cell, the radial one the rest), of the horizontal and vertical
    ones for a vector on the EIRENE triangles."""
    vr = np.asarray(v.vr[col], float)
    vz = np.asarray(v.vz[col], float)
    zero = np.zeros_like(vr)
    if v.location == "triangles":
        return [("horizontal", "Horizontal component", vr, zero, False),
                ("vertical", "Vertical component", zero, vz, False)]
    from . import fieldlines
    g = tab.run.geometry
    b = fieldlines.cell_field(tab.run)
    er, ez = np.full(len(vr), np.nan), np.full(len(vr), np.nan)
    if b is not None:
        n = np.hypot(b[0], b[1])
        with np.errstate(invalid="ignore", divide="ignore"):
            er[g.cells - 1], ez[g.cells - 1] = b[0] / n, b[1] / n
    else:
        tab.status.emit("No poloidal field direction in b2fgmtry: no "
                        "poloidal and radial components")
    p = vr * er + vz * ez
    return [("poloidal", "Poloidal component", p * er, p * ez, False),
            ("radial", "Radial component", vr - p * er, vz - p * ez,
             False)]
