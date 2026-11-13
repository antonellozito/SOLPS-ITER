"""The terms of the balances as the balance scripts take them from
balance.nc: flux parts on the faces (poloidal and radial component), cell
sources, residual, units; with readable names, the groups the sources are
shown in and, for EIRENE, the parts by stratum.

Quantities: particles and momentum (summed over the species chosen), total
pressure, electron, ion and total internal energy, total energy and the
potential equation (current)."""

from dataclasses import dataclass, field

import numpy as np

QUANTITIES = (("particles", "Particles"), ("momentum", "Parallel momentum"),
              ("force", "Parallel force"), ("totpress", "Total pressure"),
              ("elheat", "Electron heat"), ("ionheat", "Ion heat"),
              ("totheat", "Total heat"), ("toten", "Total energy"),
              ("potential", "Potential"))
SPECIES = ("particles", "momentum", "force")
MW = 1.0e6

RADIAL = "Radial transport"
ATOMIC = "Atomic processes (B2.5)"
FORCES = "Friction and thermal forces"
VISCOSITY = "Viscosity and other forces"
VISCOUS = "Viscous transport"
GRADIENTS = "Pressure gradients and electric field"
HEATING = "Heating and compression"
RADIATION = "Radiation, ionisation and recombination (B2.5)"
BOUNDARY = "Boundary conditions and recycling (B2.5)"
EXTERNAL = "External and user sources"
NUMERICS = "Numerics and time derivative"
KINETIC = "Kinetic energy of the ions"
EIRENE = {"a": "EIRENE: atom-plasma collisions",
          "m": "EIRENE: molecule-plasma collisions",
          "i": "EIRENE: test ion-plasma collisions",
          "p": "EIRENE: recombination"}

FLUX_NAMES = {
    "fna_pll": "Parallel convection", "fna_ecrb": "E×B drift",
    "fna_dia": "Diamagnetic drift",
    "fna_nanom": "Anomalous diffusion (density gradient)",
    "fna_panom": "Anomalous diffusion (pressure gradient)",
    "fna_pinch": "Anomalous pinch",
    "fna_ch": "Flux carried by the currents",
    "fna_pschused": "Pfirsch-Schlüter flux",
    "fmo_flua": "Convected momentum", "fmo_cvsa": "Viscous momentum flux",
    "fmo_hybr": "Hybrid correction of the momentum flux",
    "fhe_32": "Convection, 3/2 T part", "fhe_52": "Convection, 5/2 T part",
    "fhe_cond": "Conduction", "fhe_thermj": "Thermoelectric heat flux",
    "fhe_dia": "Diamagnetic heat flux", "fhe_ecrb": "E×B heat flux",
    "fhe_strange": "Anomalous heat convection",
    "fhe_pschused": "Pfirsch-Schlüter heat flux",
    "fhi_32": "Convection, 3/2 T part", "fhi_52": "Convection, 5/2 T part",
    "fhi_cond": "Conduction", "fhi_dia": "Diamagnetic heat flux",
    "fhi_ecrb": "E×B heat flux",
    "fhi_strange": "Anomalous heat convection",
    "fhi_pschused": "Pfirsch-Schlüter heat flux",
    "fhi_inert": "Heat with the inertia current",
    "fhi_vispar": "Heat with the parallel viscosity current",
    "fhi_anml": "Heat with the anomalous current",
    "fhi_kevis": "Heat with the Reynolds stress current",
    "fhi_visq": "Heat with the heat-flux viscosity current",
    "fhi_visper": "Heat with the perpendicular viscosity current",
    "fhi_vzh": "Zhdanov viscous heat flux",
    "fch_p": "Parallel current", "fch_in": "Ion-neutral current",
    "fch_dia": "Diamagnetic current",
    "fch_vispar": "Parallel viscosity current",
    "fch_visper": "Perpendicular viscosity current",
    "fch_visq": "Heat-flux viscosity current",
    "fch_inert": "Inertia current", "fch_anml": "Anomalous current",
    "fch_viskt": "Reynolds stress current"}

SOURCE_NAMES = {
    "b2stbc": ("Boundary conditions", BOUNDARY),
    "b2stbr_phys": ("Recycling model", BOUNDARY),
    "b2stbr_first_flight": ("Recycling model, first flight", BOUNDARY),
    "b2stbm": ("Application-specific sources", EXTERNAL),
    "ext": ("External source (source input)", EXTERNAL),
    "b2srdt": ("Implicit time discretisation", NUMERICS),
    "b2srsm": ("Source smoothing", NUMERICS),
    "b2srst": ("Numerical stabilisation", NUMERICS),
    "b2scdt": ("Time derivative", NUMERICS),
    "b2smdt": ("Time derivative", NUMERICS),
    "b2shdt": ("Time derivative", NUMERICS),
    "b2stcx": ("Charge exchange", ATOMIC),
    "b2stel_shi_ion": ("Ionisation", ATOMIC),
    "b2stel_shi_rec": ("Recombination", ATOMIC),
    "b2sifr_smoch": ("Ion-ion friction (b2sigp_style 1)", FORCES),
    "b2sifr_smotf_ehxp": ("Thermal force, E-hat part (b2sigp_style 1)",
                          FORCES),
    "b2sifr_smotf_cthe": ("Electron thermal force (b2sigp_style 1)", FORCES),
    "b2sifr_smotf_cthi": ("Ion thermal force (b2sigp_style 1)", FORCES),
    "b2sifr_smofrea": ("Electron-ion friction (b2sigp_style 2)", FORCES),
    "b2sifr_smofria": ("Ion-ion friction (b2sigp_style 2)", FORCES),
    "b2sifr_smotfea": ("Electron thermal force (b2sigp_style 2)", FORCES),
    "b2sifr_smotfia": ("Ion thermal force (b2sigp_style 2)", FORCES),
    "b2siav_smovh": ("Additional viscosity, smovh", VISCOSITY),
    "b2siav_smovv": ("Additional viscosity, smovv", VISCOSITY),
    "b2siav_smovi": ("Additional viscosity, smovi", VISCOSITY),
    "b2sicf": ("Centrifugal force", VISCOSITY),
    "b2sian": ("Force of the anomalous current", VISCOSITY),
    "b2nxdv": ("Correction for cancelling friction", VISCOSITY),
    "b2sigp_smogpi": ("Ion static pressure gradient", GRADIENTS),
    "b2sigp_smogpe": ("Electron static pressure gradient (b2sigp_style 1) "
                      "or potential gradient (2)", GRADIENTS),
    "b2sigp_smogpgr": ("Pressure gradient restriction", GRADIENTS),
    "b2sihs_diae": ("Diamagnetic heating, electrons", HEATING),
    "b2sihs_divue": ("Compression, electrons", HEATING),
    "b2sihs_exbe": ("E×B heating, electrons", HEATING),
    "b2sihs_joule": ("Joule heating", HEATING),
    "b2sihs_diaa": ("Diamagnetic heating, ions", HEATING),
    "b2sihs_divua": ("Compression, ions", HEATING),
    "b2sihs_exba": ("E×B heating, ions", HEATING),
    "b2sihs_visa": ("Viscous heating", HEATING),
    "b2sihs_fraa": ("Friction heating", HEATING),
    "b2npht_shei": ("Equipartition", HEATING),
    "b2stel_rqrad": ("Line radiation", RADIATION),
    "b2stel_rqbrm": ("Bremsstrahlung", RADIATION),
    "b2stel_iz": ("Ionisation energy", RADIATION),
    "b2stel_rc": ("Recombination energy", RADIATION)}
PROCESS_NAMES = {"a": "atom-plasma collisions",
                 "m": "molecule-plasma collisions",
                 "i": "test ion-plasma collisions", "p": "recombination"}
UNITS = {"particles": ("s^{-1}", "m^{-2} s^{-1}"),
         "momentum": ("N", "N m^{-2}"), "force": ("N/ion", "N/ion"),
         "totpress": ("N m^{-2}",
                                                     "N m^{-2}"),
         "elheat": ("MW", "MW m^{-2}"), "ionheat": ("MW", "MW m^{-2}"),
         "totheat": ("MW", "MW m^{-2}"), "toten": ("MW", "MW m^{-2}"),
         "potential": ("A", "A m^{-2}")}
SYMBOLS = {"particles": "Γ", "momentum": "Π", "force": "Π", "totpress": "p",
           "elheat": "Q", "ionheat": "Q", "totheat": "Q", "toten": "Q",
           "potential": "J"}


@dataclass
class Term:
    """One term: its B2.5 name, readable name, group (sources) and, for
    EIRENE, its parts by stratum [(part, (nCv, nstra) array)]."""
    key: str
    name: str
    group: str = ""
    parts: list = None


@dataclass
class Terms:
    """The terms of one balance (fluxes in fx, fy: (nFc, k); sources
    (nCv, m) besides the radial divergences of the fluxes)."""
    quantity: str
    fx: np.ndarray
    fy: np.ndarray
    fluxes: list
    src: np.ndarray
    sources: list
    res: np.ndarray
    ismom: bool = False
    hz: bool = False
    pressure: dict = None           # total pressure: what the end faces need
    ions: np.ndarray = None         # force: the number of ions per cell
    notes: list = field(default_factory=list)
    b2mndr_hz: float = 0.0

    @property
    def units(self):
        return UNITS[self.quantity]

    @property
    def symbol(self):
        return SYMBOLS[self.quantity]


def build(bf, grid, quantity, species=None):
    """Terms of quantity (a key of QUANTITIES) for the species chosen
    (indices, particles and momentum only)."""
    bf.missing = []
    t = {"particles": _particles, "momentum": _momentum, "force": _force,
         "totpress": _totpress, "elheat": _elheat, "ionheat": _ionheat,
         "totheat": _totheat, "toten": _toten,
         "potential": _potential}[quantity](bf, grid, species)
    t.notes = ["%s not in balance.nc (written by an older B2.5): taken as "
               "zero" % n for n in bf.missing]
    t.b2mndr_hz = bf.hz
    return t


def available(bf, quantity):
    """'' if balance.nc has what the quantity needs, else the reason."""
    if quantity == "potential" and not bf.has("respo"):
        return "balance.nc has no terms of the potential equation " \
            "(written by an older B2.5)"
    return ""


# ------------------------------------------------------------- helpers
def _source(key, label=None, group=None):
    base = key[:-4] if key.endswith("_bal") else key
    name, grp = SOURCE_NAMES.get(base, (None, None))
    if name is None:
        for k, (n, g) in SOURCE_NAMES.items():
            if base.startswith(k + "_"):
                name, grp = n, g
                break
    return Term(key, label or name or base, group or grp or EXTERNAL)


def _flux(key):
    return Term(key, FLUX_NAMES.get(key, key))


def _faces(bf, names, species=None, optional=()):
    fx = np.zeros((bf.dims["nFc"], len(names)))
    fy = np.zeros_like(fx)
    for k, n in enumerate(names):
        a = bf.face(n, species, optional=n in optional)
        fx[:, k], fy[:, k] = a[:, 0], a[:, 1]
    return fx, fy


def _eirene(bf, keys, species=None, scale=1.0, parts=None):
    """EIRENE terms by process (keys: process -> field or [(part, field)])
    with their strata."""
    out = []
    for proc, fields in keys.items():
        fields = fields if isinstance(fields, list) else [("", fields)]
        p = [(label, bf.strata(f, species) / scale) for label, f in fields]
        out.append((Term(fields[0][1], EIRENE[proc], EIRENE[proc], p),
                    sum(a.sum(axis=1) for _, a in p)))
    return out


def _assemble(quantity, bf, fx, fy, fluxes, columns, res, **kw):
    """Terms from a list of (Term, cell column)."""
    src = np.column_stack([c for _, c in columns]) if columns else \
        np.zeros((bf.dims["nCv"], 0))
    return Terms(quantity, fx, fy, fluxes, src, [t for t, _ in columns],
                 res, **kw)


def _cells(bf, keys, species=None, scale=1.0, optional=(), labels=None):
    return [(_source(k, (labels or {}).get(k)),
             bf.cell(k, species, optional=k in optional) / scale)
            for k in keys]


# ---------------------------------------------------------- particles
PART_FLUX = ("fna_pll", "fna_ecrb", "fna_dia", "fna_nanom", "fna_panom",
             "fna_pinch", "fna_ch", "fna_pschused")


def _charge_steps(bf, name):
    """The B2.5 ionisation or recombination source of each species split
    into the part from or to the previous charge state and the part from
    or to the next one (as balpart): (prev, next), (nCv, ns) each."""
    bal = bf.cell_species(name)
    za = bf.za
    high = [i for i in range(len(za) - 1) if za[i + 1] - za[i] < 1] + \
        [len(za) - 1]
    low = [0] + [h + 1 for h in high[:-1]]
    prev, nxt = np.zeros_like(bal), np.zeros_like(bal)
    for lo, hi in zip(low, high):
        for i in range(hi, lo - 1, -1):
            if i == hi:
                prev[:, i] = bal[:, i]
            else:
                nxt[:, i] = -prev[:, i + 1]
                prev[:, i] = bal[:, i] - nxt[:, i]
    return prev, nxt


def _particles(bf, grid, sp):
    sp = list(range(bf.ns)) if sp is None else list(sp)
    fx, fy = _faces(bf, PART_FLUX, sp, optional=("fna_ecrb", "fna_dia"))
    cols = []
    if bf.eirene:
        cols += _eirene(bf, {"a": "eirene_mc_papl_sna_bal",
                             "m": "eirene_mc_pmpl_sna_bal",
                             "i": "eirene_mc_pipl_sna_bal",
                             "p": "eirene_mc_pppl_sna_bal"}, sp)
        cols.append((Term("eirene_mc_core_sna_bal",
                          "EIRENE: core boundary source"),
                     bf.cell("eirene_mc_core_sna_bal", sp)))
    ion = _charge_steps(bf, "b2stel_sna_ion_bal")
    rec = _charge_steps(bf, "b2stel_sna_rec_bal")
    for key, name, a in (
            ("b2stel_sna_ion_bal", "Ionisation from the lower charge state",
             ion[0]),
            ("b2stel_sna_ion_bal", "Ionisation to the higher charge state",
             ion[1]),
            ("b2stel_sna_rec_bal", "Recombination to the lower charge state",
             rec[0]),
            ("b2stel_sna_rec_bal",
             "Recombination from the higher charge state", rec[1])):
        cols.append((Term(key, name, ATOMIC), a[:, sp].sum(axis=1)))
    cols += _cells(bf, ("b2stbc_sna_bal", "b2stbm_sna_bal", "b2stcx_sna_bal",
                        "ext_sna_bal", "b2srdt_sna_bal", "b2srsm_sna_bal",
                        "b2srst_sna_bal", "b2stbr_phys_sna_bal",
                        "b2stbr_first_flight_sna_bal", "b2scdt_sna_bal"),
                   sp, optional=("b2scdt_sna_bal",))
    return _assemble("particles", bf, fx, fy, [_flux(n) for n in PART_FLUX],
                     cols, bf.cell("resco", sp))


# ----------------------------------------------------------- momentum
MOM_FLUX = ("fmo_flua", "fmo_cvsa", "fmo_hybr")
MOM_EIRENE = {"a": "eirene_mc_mapl_smo_bal", "m": "eirene_mc_mmpl_smo_bal",
              "i": "eirene_mc_mipl_smo_bal", "p": "eirene_mc_mppl_smo_bal"}
MOM_ATOMIC = (("b2stel_smq_ion_bal", "Ionisation"),
              ("b2stel_smq_rec_bal", "Recombination"),
              ("b2stcx_smq_bal", "Charge exchange"))
MOM_FORCES = ("b2sifr_smoch_bal", "b2sifr_smotf_ehxp_bal",
              "b2sifr_smotf_cthe_bal", "b2sifr_smotf_cthi_bal",
              "b2sifr_smofrea_bal", "b2sifr_smofria_bal",
              "b2sifr_smotfea_bal", "b2sifr_smotfia_bal")
MOM_OTHER = ("b2siav_smovh_bal", "b2siav_smovv_bal", "b2siav_smovi_bal",
             "b2sicf_smo_bal", "b2sian_smo_bal", "b2nxdv_smo_bal")
MOM_GRAD = ("b2sigp_smogpi_bal", "b2sigp_smogpe_bal", "b2sigp_smogpgr_bal")
MOM_REST = ("b2stbr_phys_smo_bal", "b2stbm_smo_bal", "ext_smo_bal",
            "b2srsm_smo_bal", "b2srdt_smo_bal", "b2srst_smo_bal",
            "b2stbc_smo_bal", "b2smdt_smo_bal")


def _atomic(bf, pairs, sp, scale=1.0):
    return [(Term(k, n, ATOMIC), bf.cell(k, sp) / scale) for k, n in pairs]


def _momentum(bf, grid, sp):
    sp = list(range(bf.ns)) if sp is None else list(sp)
    fx, fy = _faces(bf, MOM_FLUX, sp)
    cols = _eirene(bf, MOM_EIRENE, sp) if bf.eirene else []
    cols += _atomic(bf, MOM_ATOMIC, sp)
    cols += _cells(bf, MOM_FORCES + MOM_OTHER + MOM_GRAD + MOM_REST, sp,
                   optional=("b2smdt_smo_bal",))
    return _assemble("momentum", bf, fx, fy, [_flux(n) for n in MOM_FLUX],
                     cols, bf.cell("resmo", sp), ismom=True, hz=True)


def _divergence(grid, flux):
    """Net inflow of the face flux into each cell."""
    out = np.zeros(grid.nCv)
    np.add.at(out, grid.fc[:, 0], -flux)
    np.add.at(out, grid.fc[:, 1], flux)
    return out


def _force(bf, grid, sp):
    """Force balance (the momentum balance per ion): the convected
    momentum is the only flux; the viscous and hybrid fluxes enter as
    their poloidal and radial divergences, with the other forces; calc
    divides every term by the number of ions n_a V of a cell."""
    sp = list(range(bf.ns)) if sp is None else list(sp)
    fx, fy = _faces(bf, MOM_FLUX, sp)
    cols = [(Term("viscous_pol", "Poloidal viscosity", VISCOUS),
             _divergence(grid, fx[:, 1] + fx[:, 2])),
            (Term("viscous_rad", "Radial viscosity", VISCOUS),
             _divergence(grid, fy[:, 1] + fy[:, 2]))]
    cols += _eirene(bf, MOM_EIRENE, sp) if bf.eirene else []
    cols += _atomic(bf, MOM_ATOMIC, sp)
    cols += _cells(bf, MOM_FORCES + MOM_OTHER + MOM_GRAD + MOM_REST, sp,
                   optional=("b2smdt_smo_bal",))
    t = _assemble("force", bf, fx[:, :1], fy[:, :1], [_flux("fmo_flua")],
                  cols, bf.cell("resmo", sp), ismom=True)
    t.ions = bf.cell_species("na")[:, sp].sum(axis=1) * grid.cvVol
    return t


# ------------------------------------------------------ total pressure
def _totpress(bf, grid, sp):
    """As baltotpress: momentum of the ions per parallel area (apll in the
    cells, apllf on the faces); fluxes: convected momentum over apllf and
    the electron and ion static pressures on the end faces (set by
    calc from the pressure-gradient sources); sources over apll."""
    ions = [i for i in range(bf.ns) if bf.za[i] > 0]
    g = grid
    hz = (1 - bf.hz) + bf.hz * g.cvHz
    apll = g.cvVol * hz / g.cvHx * g.cvBb[:, 0] / g.cvBb[:, 3]
    hzf = (1 - bf.hz) + bf.hz * g.fcHz
    apllf = g.fcS * np.abs(g.qalf) * hzf * g.fcBb[:, 0] / g.fcBb[:, 3]
    flua = bf.face("fmo_flua", ions)
    visc = bf.face("fmo_cvsa", ions)
    hybr = bf.face("fmo_hybr", ions)
    zero = np.zeros(g.nFc)
    # radial parts (radial component only) and poloidal divergences of the
    # viscous and hybrid fluxes: computed by calc as (x, y) flux pairs
    pairs = [("Net radial convected momentum", zero, flua[:, 1]),
             ("Net radial viscous flux", zero, visc[:, 1]),
             ("Net radial hybrid flux", zero, hybr[:, 1]),
             ("Viscous flux divergence", zero, visc[:, 0]),
             ("Hybrid flux divergence", zero, hybr[:, 0])]
    cols = []
    if bf.eirene:
        cols += [(t, c / apll) for t, c in _eirene(bf, MOM_EIRENE, ions)]
        for t, _ in cols:
            t.parts = [(p, a / apll[:, None]) for p, a in t.parts]
    cols += [(t, c / apll) for t, c in _atomic(bf, MOM_ATOMIC, ions)]
    one = sum(bf.cell(k, ions) for k in MOM_FORCES[:4])
    two = sum(bf.cell(k, ions) for k in MOM_FORCES[4:])
    cols += [(Term("b2sifr (b2sigp_style 1)",
                   "Friction and thermal forces (b2sigp_style 1)", FORCES),
              one / apll),
             (Term("b2sifr (b2sigp_style 2)",
                   "Friction and thermal forces (b2sigp_style 2)", FORCES),
              two / apll)]
    cols += [(t, c / apll) for t, c in _cells(
        bf, MOM_OTHER + ("b2sigp_smogpgr_bal",) + MOM_REST, ions,
        optional=("b2smdt_smo_bal",))]
    geom = np.zeros(g.nCv)
    ratio = 1.0 - apll[g.fc] / (apllf[:, None] + 1.0e-30)
    np.add.at(geom, g.fc[:, 0], -flua[:, 0] * ratio[:, 0])
    np.add.at(geom, g.fc[:, 1], flua[:, 0] * ratio[:, 1])
    cols.append((Term("geometric term", "Geometric term (change of the "
                      "parallel area)", VISCOSITY), geom / apll))
    ne, te = bf.cell("ne"), bf.cell("te")
    na, ti = bf.cell_species("na"), bf.cell("ti")
    pressure = dict(apll=apll, apllf=apllf, pairs=pairs,
                    pe=_intface(g, ne * te),
                    pi=_intface(g, ti * na[:, ions].sum(axis=1)),
                    gpe=bf.cell("b2sigp_smogpe_bal", ions) / apll,
                    gpi=bf.cell("b2sigp_smogpi_bal", ions) / apll,
                    flux=flua[:, 0] / (apllf + 1.0e-30))
    fluxes = [Term("fmo_flua", "Dynamic pressure (convected momentum)"),
              Term("pe", "Electron static pressure"),
              Term("pi", "Ion static pressure")]
    t = _assemble("totpress", bf, np.zeros((g.nFc, 3)),
                  np.zeros((g.nFc, 3)), fluxes, cols,
                  bf.cell("resmo", ions) / apll, ismom=True)
    t.pressure = pressure
    return t


def _intface(g, field):
    """Cell field on the faces, weighted by the volumes (intface)."""
    a, b = g.fc[:, 0], g.fc[:, 1]
    va, vb = g.cvVol[a], g.cvVol[b]
    return (va * field[b] + vb * field[a]) / (va + vb)


# ------------------------------------------------------------ energies
EL_FLUX = ("fhe_32", "fhe_52", "fhe_cond", "fhe_thermj", "fhe_dia",
           "fhe_ecrb", "fhe_strange", "fhe_pschused")
ION_FLUX = ("fhi_32", "fhi_52", "fhi_cond", "fhi_dia", "fhi_ecrb",
            "fhi_strange", "fhi_pschused", "fhi_inert", "fhi_vispar",
            "fhi_anml", "fhi_kevis", "fhi_visq", "fhi_visper", "fhi_vzh")
TOT_FLUX = ("fhe_32", "fhi_32", "fhe_52", "fhi_52", "fhe_cond", "fhi_cond",
            "fhe_thermj", "fhe_dia", "fhi_dia", "fhe_ecrb", "fhi_ecrb",
            "fhe_strange", "fhi_strange", "fhe_pschused", "fhi_pschused",
            "fhi_inert", "fhi_vispar", "fhi_anml", "fhi_kevis", "fhi_visq",
            "fhi_visper", "fhi_vzh")
EL_EIRENE = {"a": "eirene_mc_eael_she_bal", "m": "eirene_mc_emel_she_bal",
             "i": "eirene_mc_eiel_she_bal", "p": "eirene_mc_epel_she_bal"}
ION_EIRENE = {"a": "eirene_mc_eapl_shi_bal", "m": "eirene_mc_empl_shi_bal",
              "i": "eirene_mc_eipl_shi_bal", "p": "eirene_mc_eppl_shi_bal"}
STEL = ("b2stel_rqrad_bal", "b2stel_rqbrm_bal", "b2stel_iz_bal",
        "b2stel_rc_bal")


def _heat_flux_terms(names, both):
    """Flux terms; with both (total), electrons and ions in the names."""
    out = []
    for n in names:
        t = _flux(n)
        if both:
            t.name += ", %s" % ("electrons" if n.startswith("fhe")
                                else "ions")
        out.append(t)
    return out


def _stel(bf):
    """Electron energy of the atomic processes by part, all species."""
    return [(_source(k), bf.cell(k, optional=True) / MW) for k in STEL]


def _elheat(bf, grid, sp):
    fx, fy = _faces(bf, EL_FLUX)
    cols = _cells(bf, ("b2stbc_she_bal",), scale=MW)
    if bf.eirene:
        cols += _eirene(bf, EL_EIRENE, scale=MW)
    cols += _cells(bf, ("b2stbm_she_bal", "ext_she_bal", "b2srsm_she_bal",
                        "b2srdt_she_bal", "b2srst_she_bal",
                        "b2sihs_diae_bal", "b2sihs_divue_bal",
                        "b2sihs_exbe_bal", "b2sihs_joule_bal"), scale=MW)
    cols.append((_source("b2npht_shei_bal"),
                 -bf.cell("b2npht_shei_bal") / MW))
    cols += _cells(bf, ("b2stbr_phys_she_bal", "b2stbr_first_flight_she_bal",
                        "b2shdt_she_bal"), scale=MW,
                   optional=("b2shdt_she_bal",))
    cols += _stel(bf)
    return _assemble("elheat", bf, fx / MW, fy / MW,
                     _heat_flux_terms(EL_FLUX, False), cols,
                     bf.cell("reshe") / MW)


def _ionheat(bf, grid, sp):
    fx, fy = _faces(bf, ION_FLUX, optional=("fhi_vzh",))
    cols = _cells(bf, ("b2stbc_shi_bal",), scale=MW)
    if bf.eirene:
        cols += _eirene(bf, ION_EIRENE, scale=MW)
    cols += _cells(bf, ("b2stbm_shi_bal", "ext_shi_bal"), scale=MW)
    cols += _atomic(bf, (("b2stel_shi_ion_bal", "Ionisation"),
                         ("b2stel_shi_rec_bal", "Recombination"),
                         ("b2stcx_shi_bal", "Charge exchange")), None, MW)
    cols += _cells(bf, ("b2srsm_shi_bal", "b2srdt_shi_bal", "b2srst_shi_bal",
                        "b2sihs_diaa_bal", "b2sihs_divua_bal",
                        "b2sihs_exba_bal", "b2sihs_visa_bal",
                        "b2sihs_fraa_bal", "b2npht_shei_bal",
                        "b2stbr_phys_shi_bal", "b2stbr_first_flight_shi_bal",
                        "b2shdt_shi_bal"), scale=MW,
                   optional=("b2shdt_shi_bal",))
    return _assemble("ionheat", bf, fx / MW, fy / MW,
                     _heat_flux_terms(ION_FLUX, False), cols,
                     bf.cell("reshi") / MW)


def _both_eirene(bf):
    """EIRENE energy terms of electrons and ions, one per process."""
    keys = {p: [("electrons", EL_EIRENE[p]), ("ions", ION_EIRENE[p])]
            for p in "amip"}
    return _eirene(bf, keys, scale=MW)


def _part_names(cols, part):
    for t, _ in cols:
        t.name += ", " + part
    return cols


def _totheat_sources(bf):
    """Sources of the total internal energy, in the order of baltotht."""
    c = lambda keys, **kw: _cells(bf, keys, scale=MW, **kw)  # noqa: E731
    cols = _part_names(c(("b2stbc_she_bal",)), "electrons") + \
        _part_names(c(("b2stbc_shi_bal",)), "ions")
    if bf.eirene:
        cols += _both_eirene(bf)
    for k in ("b2stbm", "ext"):
        cols += _part_names(c((k + "_she_bal",)), "electrons") + \
            _part_names(c((k + "_shi_bal",)), "ions")
    cols += _atomic(bf, (("b2stel_shi_ion_bal", "Ionisation, ions"),
                         ("b2stel_shi_rec_bal", "Recombination, ions"),
                         ("b2stcx_shi_bal", "Charge exchange, ions")), None,
                    MW)
    for k in ("b2srsm", "b2srdt", "b2srst"):
        cols += _part_names(c((k + "_she_bal",)), "electrons") + \
            _part_names(c((k + "_shi_bal",)), "ions")
    cols += c(("b2sihs_diae_bal", "b2sihs_diaa_bal", "b2sihs_divue_bal",
               "b2sihs_divua_bal", "b2sihs_exbe_bal", "b2sihs_exba_bal",
               "b2sihs_visa_bal", "b2sihs_joule_bal", "b2sihs_fraa_bal"))
    cols += _part_names(c(("b2stbr_phys_she_bal",
                           "b2stbr_first_flight_she_bal")), "electrons")
    cols += _part_names(c(("b2stbr_phys_shi_bal",
                           "b2stbr_first_flight_shi_bal")), "ions")
    cols += _part_names(c(("b2shdt_she_bal",), optional=("b2shdt_she_bal",)),
                        "electrons")
    cols += _part_names(c(("b2shdt_shi_bal",), optional=("b2shdt_shi_bal",)),
                        "ions")
    cols += _stel(bf)
    return cols


def _totheat(bf, grid, sp):
    fx, fy = _faces(bf, TOT_FLUX, optional=("fhi_vzh",))
    return _assemble("totheat", bf, fx / MW, fy / MW,
                     _heat_flux_terms(TOT_FLUX, True),
                     _totheat_sources(bf),
                     (bf.cell("reshe") + bf.cell("reshi")) / MW)


# -------------------------------------------------------- total energy
MOM_SOURCES = ("b2stel_smq_ion_bal", "b2stel_smq_rec_bal", "b2stcx_smq_bal",
               "b2sifr_smoch_bal", "b2sifr_smotf_ehxp_bal",
               "b2sifr_smotf_cthe_bal", "b2sifr_smotf_cthi_bal",
               "b2sifr_smofrea_bal", "b2sifr_smofria_bal",
               "b2sifr_smotfea_bal", "b2sifr_smotfia_bal",
               "b2siav_smovh_bal", "b2siav_smovv_bal", "b2siav_smovi_bal",
               "b2sicf_smo_bal", "b2sian_smo_bal", "b2nxdv_smo_bal",
               "b2sigp_smogpi_bal", "b2sigp_smogpe_bal",
               "b2sigp_smogpgr_bal", "b2stbr_phys_smo_bal", "b2stbm_smo_bal",
               "ext_smo_bal", "b2srsm_smo_bal", "b2srdt_smo_bal",
               "b2srst_smo_bal", "b2stbc_smo_bal", "b2smdt_smo_bal")
MOM_GROUP = (1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 4, 4,
             4, 4, 4, 4, 4, 4)
PART_SOURCES = ("b2stbr_phys_sna_bal", "b2stbr_first_flight_sna_bal",
                "b2stbc_sna_bal", "b2stbm_sna_bal", "ext_sna_bal",
                "b2stel_sna_ion_bal", "b2stel_sna_rec_bal", "b2stcx_sna_bal",
                "b2srsm_sna_bal", "b2srdt_sna_bal", "b2srst_sna_bal",
                "b2scdt_sna_bal")
KINETIC_SOURCES = ("u × (ionisation, recombination, charge exchange)",
                   "u × (friction, thermal forces)",
                   "u × viscosity", "u × other momentum sources",
                   "u × (static pressure, electric field)",
                   "u × EIRENE momentum",
                   "-mu²/2 × B2.5 particle sources",
                   "-mu²/2 × EIRENE particle sources",
                   "Kinetic energy: cell to face")


def _kinetic_flux(g, flx, fly, uc, uf):
    """Kinetic energy flux on the faces (multiplier on the face times the
    flux) and the cell term, sum over the faces of (multiplier in the cell
    - multiplier on the face) times the inflow (baltoten)."""
    f = flx + fly
    a, b = g.fc[:, 0], g.fc[:, 1]
    cell = np.bincount(a, -(uc[a] - uf) * f, g.nCv) + \
        np.bincount(b, (uc[b] - uf) * f, g.nCv)
    return uf * flx, uf * fly, cell


def _toten(bf, grid, sp):
    """As baltoten: internal energy of electrons and ions plus, per ion
    species, u times the momentum equation and -mu^2/2 times the
    continuity equation."""
    g, nFc, ns = grid, bf.dims["nFc"], bf.ns
    hfx, hfy = _faces(bf, TOT_FLUX, optional=TOT_FLUX)
    cols = []
    names = ("b2stbc_she_bal", "b2stbc_shi_bal", "b2stbm_she_bal",
             "b2stbm_shi_bal", "ext_she_bal", "ext_shi_bal",
             "b2stel_shi_ion_bal", "b2stel_shi_rec_bal", "b2stcx_shi_bal",
             "b2srsm_she_bal", "b2srsm_shi_bal", "b2srdt_she_bal",
             "b2srdt_shi_bal", "b2srst_she_bal", "b2srst_shi_bal",
             "b2sihs_diae_bal", "b2sihs_diaa_bal", "b2sihs_divue_bal",
             "b2sihs_divua_bal", "b2sihs_exbe_bal", "b2sihs_exba_bal",
             "b2sihs_visa_bal", "b2sihs_joule_bal", "b2sihs_fraa_bal",
             "b2stbr_phys_she_bal", "b2stbr_first_flight_she_bal",
             "b2stbr_phys_shi_bal", "b2stbr_first_flight_shi_bal",
             "b2shdt_she_bal", "b2shdt_shi_bal")
    for k in names:
        t = _source(k)
        if "_she_" in k:
            t.name += ", electrons"
        elif "_shi_" in k:
            t.name += ", ions"
        cols.append((t, bf.cell(k, optional=k.startswith("b2shdt")) / MW))
    cols += _stel(bf)
    if bf.eirene:
        cols += _both_eirene(bf)
    # kinetic energy of the ions
    fmo = [bf.face_species(n) for n in MOM_FLUX]
    smom = [bf.cell_species(n, optional=n == "b2smdt_smo_bal")
            for n in MOM_SOURCES]
    group = list(MOM_GROUP)
    if bf.eirene:
        smom.append(sum(bf.raw(n).sum(axis=2) for n in MOM_EIRENE.values()))
        group.append(6)
    fna = sum(bf.face_species(n, optional=True) for n in PART_FLUX)
    spart = sum(bf.cell_species(n, optional=n == "b2scdt_sna_bal")
                for n in PART_SOURCES)
    spart_eir = np.zeros((g.nCv, ns))
    if bf.eirene:
        spart_eir = sum(bf.raw(n).sum(axis=2) for n in (
            "eirene_mc_papl_sna_bal", "eirene_mc_pmpl_sna_bal",
            "eirene_mc_pipl_sna_bal", "eirene_mc_pppl_sna_bal")) + \
            bf.cell_species("eirene_mc_core_sna_bal")
    resmo, resco = bf.cell_species("resmo"), bf.cell_species("resco")
    ua = bf.cell_species("ua")
    kfx, kfy = np.zeros((nFc, 3)), np.zeros((nFc, 3))
    ksrc, kres = np.zeros((g.nCv, 9)), np.zeros(g.nCv)
    for i in np.flatnonzero(bf.za > 0):
        m = bf.am[i] * bf.mp
        u = ua[:, i]
        uf = _intface(g, u)
        gk, gkf = -0.5 * m * u ** 2, -0.5 * m * uf ** 2
        for k in range(3):
            fx, fy, cell = _kinetic_flux(g, fmo[k][:, 0, i], fmo[k][:, 1, i],
                                         u, uf)
            kfx[:, k] += fx
            kfy[:, k] += fy
            ksrc[:, 8] += cell
        fx, fy, cell = _kinetic_flux(g, fna[:, 0, i], fna[:, 1, i], gk, gkf)
        kfx[:, 0] += fx
        kfy[:, 0] += fy
        ksrc[:, 8] += cell
        for k, s in enumerate(smom):
            ksrc[:, group[k] - 1] += u * s[:, i]
        ksrc[:, 6] += gk * spart[:, i]
        ksrc[:, 7] += gk * spart_eir[:, i]
        kres += u * resmo[:, i] + gk * resco[:, i]
    cols += [(Term("kinetic", n, KINETIC), ksrc[:, k] / MW)
             for k, n in enumerate(KINETIC_SOURCES)]
    fluxes = _heat_flux_terms(TOT_FLUX, True) + [
        Term("kinetic", "Kinetic energy, convected"),
        Term("kinetic", "Kinetic energy, viscous"),
        Term("kinetic", "Kinetic energy, hybrid")]
    return _assemble("toten", bf, np.column_stack((hfx, kfx)) / MW,
                     np.column_stack((hfy, kfy)) / MW, fluxes, cols,
                     (bf.cell("reshe") + bf.cell("reshi") + kres) / MW)


# ----------------------------------------------------------- potential
POT_FLUX = ("fch_p", "fch_in", "fch_dia", "fch_vispar", "fch_visper",
            "fch_visq", "fch_inert", "fch_anml", "fch_viskt")


def _potential(bf, grid, sp):
    fx, fy = _faces(bf, POT_FLUX)
    cols = [(Term(k, n, g), bf.cell(k)) for k, n, g in (
        ("b2stbc_sch_bal", "Boundary conditions", BOUNDARY),
        ("b2stbm_sch_bal", "Application-specific sources", EXTERNAL),
        ("ext_sch_bal", "External source (source input)", EXTERNAL),
        ("b2srdt_sch_bal", "Implicit time discretisation", NUMERICS),
        ("b2srst_sch_bal", "Numerical stabilisation", NUMERICS))]
    return _assemble("potential", bf, fx, fy, [_flux(n) for n in POT_FLUX],
                     cols, bf.cell("respo"))
