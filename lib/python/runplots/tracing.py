"""2dt_tracing, particle_balance_tracing and energy_balance_tracing: columns
of tracing/blnn_SPb.trc and tracing/blne.trc against time.

Each column is drawn against the time column of its own file (the two
files need not have the same time slices). A column found in neither file
is named in a message.
"""

import sys

from . import helpers, quantities, tracefiles
from .pages import Curve, Page, stamp

MISSING = {"blnn_SPb.trc": "No blnn_SPb.trc tracing file found.",
           "blne.trc": "No blne.trc tracing file found."}


def _first_target_outer():
    """il of blne.trc is the first target of b2time.nc: True when it is the
    outer one (geometry.py); without netCDF4 or b2time.nc the names of
    B2.5 (il inner) are kept, since only the labels depend on it."""
    try:
        from . import geometry, ncdata
        data = ncdata.open_file("b2time.nc")
    except (ImportError, OSError):
        return None
    return geometry.first_target_outer(data)


class Tracing:
    """The tracing files of the run and the elements of SOLPS_FLUIDS."""

    def __init__(self, name, averaging):
        self.name, self.averaging = name, averaging
        self.files = tracefiles.tracing_files()
        self.elements = helpers.isonuclear_names(helpers.solps_fluids())
        self._reported = set()
        blne = self.files.get("blne.trc")
        self.four_targets = bool(blne and blne.has("pwr_totl_iu"))
        self.swapped = False
        if blne is not None and not self.four_targets:
            self.swapped = bool(_first_target_outer())
        self.footer = helpers.chop_pwd(60)

    def _file_of(self, column):
        base = tracefiles.stem(column, self.elements)
        order = ("blne.trc", "blnn_SPb.trc") \
            if base in tracefiles.BLNE_STEMS else ("blnn_SPb.trc", "blne.trc")
        for name in order:
            trc = self.files.get(name)
            if trc is not None and trc.has(column):
                return trc
        wanted = order[0]
        if wanted not in self.files and wanted not in self._reported:
            self._reported.add(wanted)
            sys.stderr.write("%s.py: %s\n" % (self.name, MISSING[wanted]))
        elif wanted in self.files:
            sys.stderr.write("%s.py: %s not in %s\n"
                             % (self.name, column, self.files[wanted].path))
        return None

    def page(self, tab, title, columns, logx=False, logy=False,
             element=None, surface=None):
        """A page of columns; element and surface name what the title
        already says, which the legend leaves out."""
        curves = []
        for column in columns:
            trc = self._file_of(column)
            if trc is None:
                continue
            x, y = self.averaging.apply(*trc.series(column))
            curves.append(Curve(x, y, quantities.tracing_label(
                column, self.elements, self.four_targets, element,
                surface, self.swapped)))
        if not curves:
            return None
        footer = "%s    %s" % (self.footer, stamp())
        if self.averaging:
            footer += "    " + self.averaging.describe()
        return Page(tab, title, "time [s]", quantities.tracing_unit(columns),
                    curves, logx=logx, logy=logy, footer=footer)


def particle_pages(tracing):
    """Two pages per element, as particle_balance_tracing."""
    pages = []
    for e in tracing.elements:
        pages.append(tracing.page(
            "%s sources" % e, "Neutral sources and sinks, %s" % e,
            ["%s_%s" % (c, e) for c in ("ntr_puff", "ntr_core", "ion_core",
                                        "ntr_targ_pmp", "ntr_wall_pmp",
                                        "ntr_targ_spt", "ntr_wall_spt")],
            element=e))
        pages.append(tracing.page(
            "%s ions" % e, "Ion balance, %s" % e,
            ["%s_%s" % (c, e) for c in ("ion_core", "ion_targ", "ion_wall",
                                        "src_ioniz", "ion_dn/dt")],
            element=e))
    return [p for p in pages if p is not None]


def energy_pages(tracing):
    """Five pages, as energy_balance_tracing (impurities: the elements
    after the first)."""
    surfaces = quantities.surfaces(tracing.four_targets, tracing.swapped)
    spec = [("balance", "Total energy balance",
             ["tot_core", "pwr_totl_il", "pwr_totl_ol", "pwr_totl_wl",
              "tot_rad", "pwr_totl"]),
            ("radiation", "Radiated power",
             ["brms_rad", "ntrl_rad"]
             + ["imp_rad_%s" % e for e in tracing.elements[1:]])]
    pages = [tracing.page(*item) for item in spec]
    for s in ("il", "ol", "wl"):
        pages.append(tracing.page(
            surfaces[s], "Power onto the %s" % surfaces[s],
            ["pwr_%s_%s" % (q, s) for q in ("plsm", "neut", "ionz", "diss")],
            surface=s))
    return [p for p in pages if p is not None]
