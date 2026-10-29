#!/usr/bin/env python3
"""b2plot.py: Qt/matplotlib front end of b2plot, the B2.5 post-processor.

Used as b2plot: plot commands on stdin (echo "phys te surf" | b2plot.py,
b2plot.py < cmds), one matplotlib window per page. With stdin a terminal
the GUI opens. All values are computed by the Fortran b2plot
(b2pl_gui.exe); b2plot.py -h lists the options.

Any Python 3 syntax up to the requirements check, so that an old
interpreter still prints the requirements message.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from b2plotpy import options, requirements  # noqa: E402


def _version(name):
    try:
        import importlib.metadata
        return importlib.metadata.version(name)
    except Exception:
        return "missing"


def info(args):
    """--info: versions, paths and the build b2plot.py would use."""
    import b2plotpy
    v = sys.version_info
    rows = [("b2plot.py", "%s (protocol %d)" % (b2plotpy.__version__,
                                                b2plotpy.PROTOCOL_VERSION)),
            ("Python", "%d.%d.%d  %s" % (v[0], v[1], v[2], sys.executable))]
    for name, minimum in requirements.REQUIRED:
        rows.append((name, "%s (need >= %s)" % (_version(name), minimum)))
    found = requirements.problems(False)
    rows.append(("Requirements", "; ".join(found) if found else "complete"))
    for name in ("SOLPSTOP", "HOST_NAME", "COMPILER", "MAKE", "PYTHON"):
        rows.append((name, os.environ.get(name, "(not set)")))
    if os.environ.get("SOLPSTOP"):
        wrapper = os.path.join(os.environ["SOLPSTOP"], "scripts", "b2plot")
        rows.append(("Wrapper", wrapper + ("" if os.path.isfile(wrapper)
                                           else " (not found)")))
        build = requirements.build_dir(args.standalone,
                                       args.debugger is not None)
        rows.append(("Build", build))
        for target in args.targets:
            exe = os.path.join(build, target + ".exe")
            rows.append((target + ".exe", "found" if os.path.isfile(exe)
                         else "not built (run make in modules/B2.5)"))
    rows.append(("Run directory", os.path.abspath(args.rundir)))
    rows.append(("Mode", "GUI" if sys.stdin.isatty() and not args.output
                 and not args.no_show else "CLI"))
    width = max(len(key) for key, _ in rows)
    for key, value in rows:
        print("%-*s  %s" % (width, key, value))
    return 0


def dry_run(args):
    """-n: the make commands of the wrapper, nothing is run."""
    import subprocess
    from b2plotpy import backend
    cmd = backend.wrapper_command(args.standalone, args.targets,
                                  args.debugger, dry_run=True)
    return subprocess.call(cmd, cwd=args.rundir)


def main(argv=None):
    requirements.reexec_with_session_python()
    args = options.parse(argv)
    if args.info:
        return info(args)
    gui = options.gui_mode(args)
    requirements.check(gui)
    if args.debugger == "":
        args.debugger = os.environ.get("DBX", "")
        if not args.debugger:
            requirements.fail_environment(["-d: no debugger given and DBX "
                                           "is not set"])
    if not args.replay and not args.exe:
        found = requirements.environment_problems(
            args.standalone, args.debugger is not None, args.targets,
            built=not args.dry_run)
        if found:
            requirements.fail_environment(found)
    if not args.replay and not os.path.isdir(args.rundir):
        requirements.fail_environment(["run directory %s not found"
                                       % args.rundir])
    if args.dry_run:
        return dry_run(args)
    if gui:
        from b2plotpy.gui import app
        return app.main(args)
    from b2plotpy import batch
    return batch.main(args)


if __name__ == "__main__":
    sys.exit(main())
