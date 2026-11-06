"""The b2plot part of the package entry (__main__.py): checks of the
command line, of the Python and of the B2.5 build, --info and -n, then
b2plot, b2run or carre.exe with the Python graphics; b2plot_gui starts from
the same checks.

Any Python 3 syntax up to the requirements check, so that an old
interpreter still prints the requirements message.
"""

import os
import sys

from . import __version__, options
from . import build as b2build
from .. import requirements


def _version(name):
    try:
        import importlib.metadata
        return importlib.metadata.version(name)
    except Exception:
        return "missing"


def info(args):
    """--info: versions, paths and the build that would be used."""
    v = sys.version_info
    prog = options.program(args)
    rows = [("Python graphics", __version__),
            ("Python", "%d.%d.%d  %s" % (v[0], v[1], v[2], sys.executable))]
    for name, minimum in requirements.REQUIRED:
        rows.append((name, "%s (need >= %s)" % (_version(name), minimum)))
    found = requirements.problems(False)
    rows.append(("Requirements", "; ".join(found) if found else "complete"))
    for name in ("SOLPSTOP", "HOST_NAME", "COMPILER", "MAKE", "PYTHON"):
        rows.append((name, os.environ.get(name, "(not set)")))
    if os.environ.get("SOLPSTOP"):
        tool = "b2plot" if prog == "b2pl" else "b2run"
        wrapper = os.path.join(os.environ["SOLPSTOP"], "scripts", tool)
        rows.append(("Wrapper", wrapper + ("" if os.path.isfile(wrapper)
                                           else " (not found)")))
        build = b2build.build_dir(args.standalone,
                                       args.debugger is not None)
        rows.append(("Build", build))
        kind = b2build.graphics(build)
        rows.append(("Graphics", {"python": "Python", "ncar":
                                  "NCAR Graphics (USE_NCAR)"}.get(
                                      kind, "unknown (no stamp file)")))
        exe = os.path.join(build, prog + ".exe")
        rows.append((prog + ".exe", "found" if os.path.isfile(exe)
                     else "not built (run make in modules/B2.5)"))
    rows.append(("Run directory", os.path.abspath(args.rundir)))
    if args.gui:
        mode = "GUI"
    elif prog != "b2pl":
        mode = prog + ".pdf"
    else:
        mode = ("interactive" if sys.stdin.isatty() and not args.replay
                else "commands from stdin")
    rows.append(("Mode", mode))
    width = max(len(key) for key, _ in rows)
    for key, value in rows:
        print("%-*s  %s" % (width, key, value))
    return 0


def dry_run(args):
    """-n: the make commands of the wrapper, nothing is run."""
    import subprocess
    from . import backend
    prog = options.program(args)
    cmd = backend.wrapper_command(args.standalone, [prog], args.debugger,
                                  dry_run=True, tool="b2plot"
                                  if prog == "b2pl" else "b2run")
    return subprocess.call(cmd, cwd=args.rundir,
                           env=requirements.child_environment())


def prepare(argv=None):
    """The command line and the session checked: the options, or the exit
    status when nothing more is to run (--info, -n)."""
    requirements.NAME = options.name(argv)
    requirements.NO_WINDOW = ("B2PLOT_DEV=ps writes the pages to b2plot.ps "
                              "without windows.")
    requirements.reexec_with_session_python()
    args = options.parse(argv)
    if args.info:
        return info(args)
    prog = options.program(args)
    if prog == options.CARRE:
        found = requirements.problems(False)
        if found:
            # Carre2 runs without pictures rather than not at all
            print("carre2: Warning: no pictures, the Python graphics need "
                  + "; ".join(found) + ". install_python installs the "
                  "SOLPS-ITER Python with them (manual, section Python "
                  "graphics).")
            sys.stdout.flush()
            os.execvpe(args.exec[0], args.exec,
                       requirements.child_environment())
    requirements.check(args.gui or options.windows(args))
    if args.debugger == "":
        args.debugger = os.environ.get("DBX", "")
        if not args.debugger:
            b2build.fail_environment(["-d: no debugger given and DBX "
                                      "is not set"])
    if not args.replay and not args.exe and not args.exec:
        found = b2build.environment_problems(
            args.standalone, args.debugger is not None, [prog],
            built=not args.dry_run,
            tool="b2plot" if prog == "b2pl" else "b2run")
        if found:
            b2build.fail_environment(found)
    if not args.replay and not os.path.isdir(args.rundir):
        b2build.fail_environment(["run directory %s not found"
                                  % args.rundir])
    if args.dry_run:
        return dry_run(args)
    # matplotlib defaults, whatever matplotlibrc the user or the run
    # directory has
    import matplotlib
    matplotlib.rcdefaults()
    return args


def run(args):
    """b2plot, a B2 post-processor or carre.exe, with the checked options."""
    from . import batch
    prog = options.program(args)
    if prog == options.CARRE:
        return batch.run_carre(args)
    if prog != "b2pl":
        return batch.run_program(args)
    if sys.stdin.isatty() and not args.replay:
        return batch.interactive(args)
    return batch.main(args)
