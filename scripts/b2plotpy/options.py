"""Command-line options of b2plot.py (any Python 3, standard library only)."""

import argparse
import os
import sys

DESCRIPTION = """\
Qt/matplotlib front end of b2plot. As for b2plot, the plot commands are
read from stdin (echo "phys te surf" | b2plot.py, b2plot.py < cmds) and
every page opens in a matplotlib window. With stdin a terminal, the GUI
opens on the run directory instead. All values are computed by the
Fortran b2plot (b2pl_py.exe)."""

EPILOG = """\
B2PLOT_DEV chooses the output as for b2plot: x11 page windows, ps the file
b2plot.ps in the run directory (both when unset). -o writes one more file.
A B2 post-processor given with --program writes PROGRAM.pdf. See the
SOLPS-ITER manual, chapter "b2plot manual", section "b2plot.py"."""

# The B2 post-processors that draw (they read their own input files)
PROGRAMS = ("b2yg", "b2yi", "b2ym", "b2yn", "b2yp", "b2yq", "b2yr")


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
    ap.add_argument("--program", choices=PROGRAMS,
                    help="run this B2 post-processor instead of b2plot; "
                    "its pages go to PROGRAM.pdf (or to -o), no windows")
    ap.add_argument("--cli", action="store_true",
                    help="with stdin a terminal: type b2plot commands as "
                    "in b2plot instead of opening the GUI")
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
    if args.program and (args.cli or args.replay):
        ap.error("--program runs a post-processor: no --cli or --replay")
    return args


def gui_mode(args):
    """GUI with stdin a terminal, unless only files are asked for."""
    return (sys.stdin.isatty() and not args.output and not args.no_show
            and not args.dry_run and not args.info and not args.replay
            and not args.cli and not args.program)


def devices():
    """B2PLOT_DEV read as the Fortran b2plot reads it: x11 or X11, ps or
    PS, cgm or CGM anywhere in the value; "x11 ps" when unset."""
    dev = os.environ.get("B2PLOT_DEV", "x11 ps")
    return {"x11": "x11" in dev or "X11" in dev,
            "ps": "ps" in dev or "PS" in dev,
            "cgm": "cgm" in dev or "CGM" in dev}


def display_available():
    """A screen for the page windows (on Linux an X11 or Wayland display)."""
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY")
                    or os.environ.get("WAYLAND_DISPLAY"))
    return True


def windows(args):
    """True if the CLI opens page windows for these options."""
    return (not args.no_show and not args.program and not args.info
            and not args.dry_run and devices()["x11"]
            and display_available())
