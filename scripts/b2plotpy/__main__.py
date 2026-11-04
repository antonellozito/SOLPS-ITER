"""Entry point of the Python graphics of b2plot.

Started by the run targets of b2plot and b2run (b2pl, b2yg ... b2yr) in a
B2.5 build with the Python graphics (--exec), and by b2plot_gui (--gui);
run it as
python $SOLPSTOP/scripts/b2plotpy or python -m b2plotpy. All values are
computed by the Fortran b2plot (b2pl.exe); -h lists the options.

Any Python 3 syntax up to the requirements check, so that an old
interpreter still prints the requirements message.
"""

import os
import sys

if not __package__:
    # run as a directory or file: import the package from its parent, and
    # not its modules as top-level modules
    _here = os.path.dirname(os.path.realpath(__file__))
    sys.path = [p for p in sys.path
                if os.path.realpath(p or ".") != _here]
    sys.path.insert(0, os.path.dirname(_here))

from b2plotpy import options, requirements  # noqa: E402


def _version(name):
    try:
        import importlib.metadata
        return importlib.metadata.version(name)
    except Exception:
        return "missing"


def info(args):
    """--info: versions, paths and the build that would be used."""
    import b2plotpy
    v = sys.version_info
    prog = options.program(args)
    rows = [("b2plotpy", "%s (protocol %d)" % (b2plotpy.__version__,
                                               b2plotpy.PROTOCOL_VERSION)),
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
        build = requirements.build_dir(args.standalone,
                                       args.debugger is not None)
        rows.append(("Build", build))
        kind = requirements.graphics(build)
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
    from b2plotpy import backend
    prog = options.program(args)
    cmd = backend.wrapper_command(args.standalone, [prog], args.debugger,
                                  dry_run=True, tool="b2plot"
                                  if prog == "b2pl" else "b2run")
    return subprocess.call(cmd, cwd=args.rundir)


def main(argv=None):
    requirements.NAME = options.name(argv)
    requirements.reexec_with_session_python()
    args = options.parse(argv)
    if args.info:
        return info(args)
    prog = options.program(args)
    requirements.check(args.gui or options.windows(args))
    if args.debugger == "":
        args.debugger = os.environ.get("DBX", "")
        if not args.debugger:
            requirements.fail_environment(["-d: no debugger given and DBX "
                                           "is not set"])
    if not args.replay and not args.exe and not args.exec:
        found = requirements.environment_problems(
            args.standalone, args.debugger is not None, [prog],
            built=not args.dry_run,
            tool="b2plot" if prog == "b2pl" else "b2run")
        if found:
            requirements.fail_environment(found)
    if not args.replay and not os.path.isdir(args.rundir):
        requirements.fail_environment(["run directory %s not found"
                                       % args.rundir])
    if args.dry_run:
        return dry_run(args)
    if args.gui:
        from b2plotpy.gui import app
        return app.main(args)
    from b2plotpy import batch
    if prog != "b2pl":
        return batch.run_program(args)
    if sys.stdin.isatty() and not args.replay:
        return batch.interactive(args)
    return batch.main(args)


if __name__ == "__main__":
    sys.exit(main())
