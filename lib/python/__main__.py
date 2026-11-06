"""Entry point of the Python tools of SOLPS-ITER, run as
python $SOLPSTOP/lib/python OPTIONS:

    --run-plot NAME ARGS   the run plot scripts scripts/NAME.py (run_plots)
    --gui ...              b2plot_gui (b2plot_gui, on the checks of b2plot)
    anything else          b2plot, b2run (b2pl, b2yg ... b2yr) and carre2
                           (carre.exe) with the Python graphics (b2plot)

-h lists the options of b2plot. All b2plot values are computed by the
Fortran b2plot (b2pl.exe).

Any Python 3 syntax up to the requirements check, so that an old
interpreter still prints the requirements message.
"""

import os
import sys

if not __package__:
    # run as a directory or file: load this directory as the package
    # solpspy, and not its modules as top-level modules
    import importlib.util
    _here = os.path.dirname(os.path.realpath(__file__))
    sys.path = [p for p in sys.path
                if os.path.realpath(p or ".") != _here]
    _spec = importlib.util.spec_from_file_location(
        "solpspy", os.path.join(_here, "__init__.py"),
        submodule_search_locations=[_here])
    sys.modules["solpspy"] = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(sys.modules["solpspy"])

from solpspy import requirements  # noqa: E402


def main(argv=None):
    words = sys.argv[1:] if argv is None else list(argv)
    if words[:1] == ["--run-plot"]:
        requirements.NAME = (words[1:2] or ["run_plots"])[0] + ".py"
        requirements.reexec_with_session_python()
        from solpspy import run_plots
        return run_plots.main(words[1:])
    from solpspy.b2plot import command
    args = command.prepare(argv)
    if isinstance(args, int):
        return args
    if args.gui:
        from solpspy.b2plot_gui import app
        return app.main(args)
    return command.run(args)


if __name__ == "__main__":
    sys.exit(main())
