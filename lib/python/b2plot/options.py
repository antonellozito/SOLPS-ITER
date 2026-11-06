"""Command-line options of the Python graphics of b2plot (any Python 3,
standard library only)."""

import argparse
import os
import sys

from .. import requirements

DESCRIPTION = """\
Python graphics of b2plot and of the B2 post-processors. In a B2.5 build
with the Python graphics (the default), b2plot and b2run start it for the
programs b2pl and b2yg ... b2yr, carre2 for carre.exe of Carre2, and
b2plot_gui starts it with --gui. As
for the NCAR program, the b2plot commands come from stdin: typed at a
terminal, each line is run at once; piped or redirected, all of them. All
values are computed by the Fortran b2plot (b2pl.exe)."""

EPILOG = """\
B2PLOT_DEV chooses the output as for the NCAR b2plot: x11 page windows, ps
the file b2plot.ps in the run directory (both when unset). -o writes one
more file. A B2 post-processor writes PROGRAM.pdf in the run directory,
carre.exe (with the terminal of its caller) carre.pdf.
See the SOLPS-ITER manual, chapter "b2plot manual", section "Python
graphics"."""

# The B2 post-processors that draw (they read their own input files)
PROGRAMS = ("b2yg", "b2yi", "b2ym", "b2yn", "b2yp", "b2yq", "b2yr")
# The grid generator of Carre2 (carre.exe), started by --exec only
CARRE = "carre"


def name(argv=None):
    """Name in messages: the script the user started."""
    argv = sys.argv[1:] if argv is None else argv
    if any(os.path.basename(w) == CARRE + ".exe" for w in argv):
        return "carre2"
    return "b2plot_gui" if "--gui" in argv else "b2plot"


def parser(prog="b2plot"):
    ap = argparse.ArgumentParser(
        prog=prog, description=DESCRIPTION, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default="b2pl", metavar="TARGET",
                    help="b2pl (b2plot, default) or a B2 post-processor "
                    "(%s)" % ", ".join(PROGRAMS))
    ap.add_argument("--gui", action="store_true",
                    help="open the GUI on the run directory (b2plot_gui)")
    ap.add_argument("--exec", nargs=argparse.REMAINDER, metavar="COMMAND",
                    help="used by the run targets: run the rest of the "
                    "line (the executable with its prefix, such as time or "
                    "a debugger) in the current directory")
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
                    help="do not open the page windows")
    ap.add_argument("--dpi", type=int, default=150,
                    help="resolution of raster output (default 150)")
    ap.add_argument("--record", metavar="FILE",
                    help="save the raw message stream of the executable")
    ap.add_argument("--replay", metavar="FILE",
                    help="render a recorded stream, without an executable")
    ap.add_argument("--info", action="store_true",
                    help="print versions, paths and the build to be used")
    ap.add_argument("--exe", metavar="EXE",
                    help="development: run EXE in the run directory "
                    "instead of the run target")
    return ap


def program(args):
    """b2pl or the B2 post-processor: the executable of --exec, or TARGET."""
    for word in args.exec or []:
        if word.endswith(".exe"):
            return os.path.basename(word)[:-len(".exe")]
    return args.target


def parse(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = parser(name(argv))
    args = ap.parse_args(argv)
    prog = program(args)
    if args.exec is not None and not args.exec:
        ap.error("--exec needs a command")
    if prog == CARRE and not args.exec:
        ap.error("carre.exe runs through --exec only")
    if prog not in ("b2pl", CARRE) and prog not in PROGRAMS:
        ap.error("TARGET must be b2pl or one of " + ", ".join(PROGRAMS))
    if args.replay and (args.exe or args.record or args.dry_run
                        or args.exec or args.debugger is not None):
        ap.error("--replay runs no executable: no --exe, --record, "
                 "--exec, -n or -d")
    if args.dry_run and (args.exe or args.exec):
        ap.error("-n shows the commands of the wrapper: no --exe or --exec")
    if args.gui and (prog != "b2pl" or args.exec or args.output
                     or args.no_show or args.replay):
        ap.error("--gui opens the GUI on b2pl: no other TARGET, "
                 "--exec, -o, --no-show or --replay")
    if (prog in PROGRAMS or prog == CARRE) and args.replay:
        ap.error("a B2 post-processor reads its own input: no --replay")
    return args


def devices():
    """B2PLOT_DEV read as the Fortran b2plot reads it: x11 or X11, ps or
    PS, cgm or CGM anywhere in the value; "x11 ps" when unset."""
    dev = os.environ.get("B2PLOT_DEV", "x11 ps")
    return {"x11": "x11" in dev or "X11" in dev,
            "ps": "ps" in dev or "PS" in dev,
            "cgm": "cgm" in dev or "CGM" in dev}


def windows(args):
    """True if the command line opens page windows for these options."""
    return (not args.gui and not args.no_show and program(args) == "b2pl"
            and not args.info and not args.dry_run and devices()["x11"]
            and requirements.display_available())
