"""The equation of a term of the balances, from the model equations of
B2.5 (simplified): text lines, each with words and $mathtext$. There is
none for boundary conditions and recycling, numerics and time
derivatives, discretisation corrections, residuals and EIRENE."""

from .termeqs import EQ
from .terms import BOUNDARY, EIRENE, NUMERICS, RADIAL

HEAT = ("elheat", "ionheat", "totheat", "toten")
NONE_GROUPS = {BOUNDARY, NUMERICS} | set(EIRENE.values())
NONE_KEYS = ("eirene_", "b2stbc_", "b2stbr_", "b2srdt_", "b2srsm_",
             "b2srst_", "b2scdt_", "b2smdt_", "b2shdt_", "b2nxdv_",
             "b2sigp_smogpgr_")
NONE_NAMES = ("Kinetic energy: cell to face", "u × EIRENE momentum",
              "-mu²/2 × EIRENE particle sources")


def _lookup(quantity, role, key, name):
    family = "heat" if quantity in HEAT and key != "kinetic" else quantity
    for k in ((family, role, key, name), (family, role, key, None)):
        if k in EQ:
            return EQ[k]
    if quantity == "force":
        return _lookup("momentum", role, key, name)
    if quantity == "totpress" and role == "source":
        eq = _lookup("momentum", role, key, name)
        if eq is not None:
            return eq + "\ndivided by the parallel area $A_\\parallel$"
    return None


def _none(t):
    return t.parts or t.group in NONE_GROUPS or t.name in NONE_NAMES or \
        t.key.startswith(NONE_KEYS)


def of_term(quantity, role, t):
    """Equation of the Term t of the balance of quantity (role "flux": a
    part of the flux along the tube, its poloidal component; "source": a
    source, the radial transport being the radial component of a flux
    through the sides of the tube), or None."""
    if _none(t):
        return None
    if role == "source" and t.group == RADIAL and t.key != "raddiv":
        flux = t.name.split(": ", 1)[-1]         # the name of the flux
        return _lookup(quantity, "radial", t.key,
                       flux[:1].upper() + flux[1:])
    return _lookup(quantity, role, t.key, t.name)


def of_series(quantity, term):
    """Equations of a line (its Series.term): [(None, equation)], for a
    group of sources [(name, equation)] of its terms; None if none."""
    if term is None:
        return None
    role, t = term
    if role != "group":
        eq = of_term(quantity, role, t)
        return None if eq is None else [(None, eq)]
    parts = [(m.name, of_term(quantity, "source", m)) for m in t]
    return [(n, eq) for n, eq in parts if eq is not None] or None
