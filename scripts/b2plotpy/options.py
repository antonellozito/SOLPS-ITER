"""Command-line options of b2plot.py (any Python 3, standard library only)."""

import argparse
import sys

DESCRIPTION = """\
Qt/matplotlib front end of b2plot. As for b2plot, the plot commands are
read from stdin (echo "phys te surf" | b2plot.py, b2plot.py < cmds) and
every page opens in a matplotlib window. With stdin a terminal, the GUI
opens on the run directory instead. All values are computed by the
Fortran b2plot (b2pl_py.exe)."""

EPILOG = """\
Files are written only with -o. B2PLOT_DEV is ignored. See the
SOLPS-ITER manual, chapter "b2plot manual", section "b2plot.py"."""


def parser():
    ap = argparse.ArgumentParser(
        prog="b2plot.py", description=DESCRIPTION, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", metavar="TARGET",
                    help="runs/Makefile.plot targets, as for b2plot "
                    "(default b2pl_py)")
    ap.add_argument("-s", action="store_true", dest="standalone",
                    help="stand-alone build (without Eirene), as for b2plot")
    ap.add_argument("-n", action="store_true", dest="dry_run",
                    help="dry run: show the commands b2plot would run, as "
                    "for b2plot")
    ap.add_argument("-d", nargs="?", const="", dest="debugger",
                    metavar="DEBUGGER", help="run under DEBUGGER (default "
                    "$DBX), as for b2plot")
    ap.add_argument("-r", "--run", dest="rundir", default=".",
                    metavar="DIR", help="run directory (default .)")
    ap.add_argument("-o", dest="output", metavar="OUT",
                    help="also write the pages to OUT (.pdf or .ps "
                    "multipage, or numbered .png/.svg/.eps)")
    ap.add_argument("--no-show", action="store_true",
                    help="do not open the page windows (with -o)")
    ap.add_argument("--dpi", type=int, default=150,
                    help="resolution of raster output (default 150)")
    ap.add_argument("--record", metavar="FILE",
                    help="save the raw message stream of b2pl_py.exe")
    ap.add_argument("--replay", metavar="FILE",
                    help="CLI: render a recorded stream, without "
                    "b2pl_py.exe")
    ap.add_argument("--info", action="store_true",
                    help="print versions, paths and the build to be used")
    ap.add_argument("--exe", metavar="EXE",
                    help="development: run EXE in the run directory "
                    "instead of the scripts/b2plot wrapper")
    return ap


def parse(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    if not args.targets:
        args.targets = ["b2pl_py"]
    if args.replay and (args.exe or args.record or args.dry_run
                        or args.debugger is not None):
        ap.error("--replay runs no b2pl_py.exe: no --exe, --record, -n "
                 "or -d")
    if args.dry_run and args.exe:
        ap.error("-n shows the commands of the wrapper: no --exe")
    return args


def gui_mode(args):
    """GUI with stdin a terminal, unless only files are asked for."""
    return (sys.stdin.isatty() and not args.output and not args.no_show
            and not args.dry_run and not args.info and not args.replay)
