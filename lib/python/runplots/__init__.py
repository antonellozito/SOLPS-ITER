"""Python versions of run plot scripts of scripts/: the same calls and the
same pages as resco, resmo, reshe, reshi, plot_residuals, 2dt_tracing,
particle_balance_tracing, energy_balance_tracing, 2dt, 2dt_av, 2d,
2d_plots and 2d_plots_av, drawn by matplotlib instead of gnuplot, and the
same text as 2da. The pages open in one window with a tab
each and go to the PostScript file of the old script; b2time.nc and
b2batch.nc are read with netCDF4.

Started by the launchers scripts/NAME.py through the package entry
(--run-plot NAME ARGUMENTS). The helper scripts that know the run
(climb_and_look_for, get_solps_fluids, pipe_run.log, groups_species,
chop_pwd, resopt) are called as they are (helpers.py).

Standard library only up to the requirements check, so that a missing
module gives the requirements message.
"""

import argparse
import sys

from .. import requirements

RESIDUALS = {"resco": "co", "resmo": "mo", "reshe": "he", "reshi": "hi"}
TRACING = ("2dt_tracing", "particle_balance_tracing",
           "energy_balance_tracing")
NETCDF = ("2dt", "2dt_av", "2d", "2da", "2d_plots", "2d_plots_av")
TEXT = ("2da",)
EXTRA = [("netCDF4", "1.6")]
USAGE = {
    "resco": "continuity residuals per species against the iteration",
    "resmo": "parallel momentum residuals per species",
    "reshe": "residual of the electron energy equation",
    "reshi": "residual of the ion energy equation",
    "plot_residuals": "the four residual pages, also in residuals.ps",
    "2dt_tracing": "columns of tracing/*.trc against time",
    "particle_balance_tracing": "particle balance of each element from "
                                "tracing/blnn_SPb.trc, also in "
                                "particle_balance.ps",
    "energy_balance_tracing": "energy balance from tracing/blne.trc, also "
                              "in energy_balance.ps",
    "2dt": "b2time.nc time traces (species as nasepm1, dabsepm0)",
    "2dt_av": "averaged time traces of b2batch.nc (b2time.nc without it)",
    "2d": "b2time.nc quantities against the first one given",
    "2da": "table of b2time.nc quantities on standard output",
    "2d_plots": "the b2time.nc time traces, also in "
                "b2time2d_time_traces.ps",
    "2d_plots_av": "the b2batch.nc averaged time traces, also in "
                   "b2time2d_time_traces_av.ps",
}


def _parser(name):
    p = argparse.ArgumentParser(
        prog=name + ".py", allow_abbrev=False,
        description="%s, as %s, drawn by the Python graphics of "
                    "SOLPS-ITER: the pages open in a window with a tab "
                    "each (on a display, with PySide6)." % (USAGE[name],
                                                            name))
    p.add_argument("--no-show", action="store_true",
                   help="no window, files only")
    return p


def _averaging_options(p):
    group = p.add_mutually_exclusive_group()
    group.add_argument("--rolling", type=int, metavar="N",
                       help="rolling average: mean over N//2 slices on "
                            "either side (cut at the ends)")
    group.add_argument("--batch", type=int, metavar="N",
                       help="batch average: means of consecutive blocks "
                            "of N slices from the first one")


def _parse(name, argv):
    p = _parser(name)
    if name in RESIDUALS or name == "plot_residuals":
        if name in RESIDUALS:
            p.epilog = ("-m MOD (every MOD-th record), -l LAST (the last "
                        "LAST records), -a AVE (means of AVE records) go "
                        "to resopt, as for %s." % name)
        args, rest = p.parse_known_args(argv)
        args.resopt = rest if name in RESIDUALS else []
        if name == "plot_residuals" and rest:
            sys.stderr.write("plot_residuals.py: ignored: %s\n"
                             % " ".join(rest))
        return args
    _averaging_options(p)
    if name in ("2dt_tracing", "2dt", "2dt_av", "2d"):
        p.add_argument("-lx", action="store_true",
                       help="logarithmic abscissa")
        p.add_argument("-ly", action="store_true", help="logarithmic values")
    if name == "2dt_tracing":
        p.add_argument("columns", nargs="*", metavar="NAME",
                       help="tracing columns (e.g. ion_core_D tot_rad)")
    elif name == "2da":
        p.add_argument("-s", metavar="FILE", dest="source",
                       help="netCDF file instead of b2time.nc")
    if name in ("2dt", "2dt_av", "2d", "2da"):
        p.add_argument("names", nargs="*", metavar="NAME",
                       help="b2time.nc names (species: nasepm1, dabsepm0)")
    args = p.parse_args(argv)
    for n in (args.rolling, args.batch):
        if n is not None and n < 1:
            p.error("the averaging length must be at least 1")
    return args


def main(argv):
    if not argv:
        sys.stderr.write("--run-plot: no script name\n")
        return 2
    name, argv = argv[0], argv[1:]
    if name not in USAGE:
        sys.stderr.write("--run-plot: unknown script %s\n" % name)
        return 2
    requirements.NAME = name + ".py"
    requirements.GRAPHICS_OF = name + ".py"
    args = _parse(name, argv)
    extra = EXTRA if name in NETCDF else []
    if name in TEXT:
        found = requirements.problems(False, extra)
        if found:
            requirements.fail(found, extra)
        return _netcdf(name, args, None)
    one_page = name in RESIDUALS or name in ("2dt_tracing", "2dt", "2dt_av",
                                             "2d")
    from .output import Output
    out = Output(name, args, one_page, extra)
    if name in RESIDUALS or name == "plot_residuals":
        return _residuals(name, args, out)
    if name in NETCDF:
        return _netcdf(name, args, out)
    return _tracing(name, args, out)


def _residuals(name, args, out):
    from . import residuals
    kinds = [RESIDUALS[name]] if name in RESIDUALS else ["co", "mo", "he",
                                                          "hi"]
    pages = [residuals.page(k, args.resopt, name) for k in kinds]
    pages = [p for p in pages if p is not None]
    title = pages[0].footer.split("    ")[0] if pages else ""
    return out.deliver(title, pages,
                       "residuals.ps" if name == "plot_residuals" else None)


def _tracing(name, args, out):
    from . import averaging, tracing
    avg = averaging.Averaging(args.rolling, args.batch, name + ".py")
    if name == "2dt_tracing":
        if not args.columns:
            sys.stderr.write("Error: You must provide at least one argument "
                             "(1st, 2nd, etc. arguments will be plotted vs. "
                             "time).\n")
            return 1
        trc = tracing.Tracing(name, avg)
        page = trc.page("tracing", "Tracing data: " + ", ".join(args.columns),
                        args.columns, logx=args.lx, logy=args.ly)
        return out.deliver(trc.footer, [page] if page else [])
    trc = tracing.Tracing(name, avg)
    if name == "particle_balance_tracing":
        return out.deliver(trc.footer, tracing.particle_pages(trc),
                           "particle_balance.ps")
    if "blne.trc" not in trc.files:
        print("No blne.trc tracing file found. Cannot proceed.")
        return 0
    return out.deliver(trc.footer, tracing.energy_pages(trc),
                       "energy_balance.ps")


def _netcdf(name, args, out):
    import os
    from . import averaging, helpers, timetraces
    avg = averaging.Averaging(args.rolling, args.batch, name + ".py")
    names = timetraces.names_of(getattr(args, "names", []))
    if name in ("2dt", "2dt_av") and not names:
        sys.stderr.write("Error: You must provide at least one argument "
                         "(1st, 2nd, etc. arguments will be plotted vs. "
                         "time).\n")
        return 1
    if name == "2d" and len(names) < 2:
        sys.stderr.write("Error: You must provide at least two arguments "
                         "(2nd, 3rd, etc. arguments will be plotted vs. the "
                         "1st one).\n")
        return 1
    nreg = None
    if name in ("2d_plots", "2d_plots_av"):
        nreg = helpers.nreg()
        if nreg is None:
            return 1
    source = getattr(args, "source", None)
    try:
        traces = timetraces.Traces(name, avg, name in ("2dt_av",
                                                       "2d_plots_av"),
                                   source, nreg)
    except (OSError, AttributeError):
        sys.stderr.write("%s.py: %s not found\n"
                         % (name, source or "b2time.nc"))
        return 1
    if traces.data is None:
        sys.stderr.write("%s.py: b2time.nc not found\n" % name)
        return 1
    if name == "2da":
        return timetraces.table(traces, names)
    if name in ("2dt", "2dt_av"):
        page = timetraces.page(traces, "Time traces", names, logx=args.lx,
                               logy=args.ly)
        return out.deliver(helpers.chop_pwd(60), [page] if page else [])
    if name == "2d":
        x_name = traces.variable(names[0])
        if x_name is None:
            return 1
        x = timetraces.ncdata.rows(traces.data, x_name)[0]
        xt = timetraces.quantities.trace(x_name, traces.config)
        xlabel = ", ".join(p for p in (xt.quantity, xt.location) if p)
        if xt.unit:
            xlabel += " [%s]" % xt.unit
        page = timetraces.page(traces, "Against " + names[0], names[1:],
                               xlabel=xlabel, x=x, logx=args.lx,
                               logy=args.ly, footer_path=os.getcwd())
        return out.deliver(os.getcwd(), [page] if page else [])
    pages = timetraces.plots_pages(traces, nreg)
    ps = ("b2time2d_time_traces_av.ps" if name == "2d_plots_av"
          else "b2time2d_time_traces.ps")
    return out.deliver(helpers.chop_pwd(60), pages, ps)
