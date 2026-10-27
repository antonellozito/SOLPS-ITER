"""Interpreter and module check of b2plot.py (no fallbacks).

Runs on any Python 3 (no f-strings, standard library only), so that the
error message is printed even by an old interpreter. The module list must
match PYTHON_MODULES of scripts/install_python.
"""

import os
import shutil
import sys

REQUIRED_PYTHON = (3, 9)
REQUIRED = [("PySide6", "6.4"), ("numpy", "1.21"), ("matplotlib", "3.8")]


def _tuple(version):
    out = []
    for part in version.split("."):
        digits = ""
        for c in part:
            if not c.isdigit():
                break
            digits += c
        out.append(int(digits or 0))
    return tuple(out)


def reexec_with_session_python():
    """Re-run under $PYTHON when it is another interpreter (once only)."""
    python = os.environ.get("PYTHON")
    if not python or os.environ.get("B2PLOT_PY_REEXEC"):
        return
    path = shutil.which(python)
    if path is None or not os.access(path, os.X_OK):
        fail(["PYTHON is set to " + python + ", which is not executable"])
    if os.path.realpath(path) != os.path.realpath(sys.executable):
        os.environ["B2PLOT_PY_REEXEC"] = "1"
        os.execv(path, [path] + sys.argv)


def problems(gui):
    """List of missing or too old requirements (empty if all is fine)."""
    found = []
    if sys.version_info < REQUIRED_PYTHON:
        return ["Python (need >= %d.%d)" % REQUIRED_PYTHON]
    import importlib
    import importlib.metadata
    for name, minimum in REQUIRED:
        try:
            version = importlib.metadata.version(name)
            importlib.import_module(name)
        except Exception:
            found.append("%s (need >= %s)" % (name, minimum))
            continue
        if _tuple(version) < _tuple(minimum):
            found.append("%s %s (need >= %s)" % (name, version, minimum))
    if gui and not found:
        os.environ.setdefault("QT_API", "pyside6")
        try:
            from PySide6 import QtCore, QtGui, QtWidgets  # noqa: F401
            import matplotlib.backends.backend_qtagg  # noqa: F401
        except Exception as err:
            found.append("Qt for matplotlib (" + str(err) + ")")
    return found


def fail(found):
    v = sys.version_info
    need = ", ".join("%s >= %s" % r for r in REQUIRED)
    lines = [
        "b2plot.py: the Python of this SOLPS-ITER session cannot run "
        "b2plot.py.",
        "  Interpreter: %s (Python %d.%d.%d)" % (sys.executable, v[0], v[1],
                                                 v[2]),
        "  Missing or too old: " + "; ".join(found),
        "b2plot.py needs Python >= %d.%d with: %s"
        % (REQUIRED_PYTHON + (need,)),
    ]
    local = os.path.join(os.environ.get("SOLPSTOP", ""), "lib",
                         "%s.%s" % (os.environ.get("HOST_NAME", ""),
                                    os.environ.get("COMPILER", "")),
                         "python")
    if os.environ.get("SOLPSTOP") and os.path.realpath(
            sys.executable).startswith(os.path.realpath(local) + os.sep):
        lines += ["The local SOLPS-ITER-specific Python installation is "
                  "incomplete:",
                  "  run install_python again; it adds the missing modules."]
    else:
        lines += ["Create the local SOLPS-ITER-specific Python installation, "
                  "which has all of them:",
                  "  1. run:  install_python   (also run by "
                  "install_dependencies)",
                  "     and answer y to \"Do you want to install a local "
                  "SOLPS-ITER-specific Python installation?\"",
                  "  2. close the shell, open a new one and source setup.csh "
                  "again."]
    lines.append("See the SOLPS-ITER manual, chapter \"b2plot manual\", "
                 "section \"b2plot.py\".")
    sys.stderr.write("\n".join(lines) + "\n")
    sys.exit(2)


def check(gui):
    """Re-exec under $PYTHON if needed, then stop on any missing module."""
    reexec_with_session_python()
    found = problems(gui)
    if found:
        fail(found)


def build_dir(standalone, debug):
    """B2.5 build directory used by runs/Makefile.plot (B2OBJ)."""
    env = os.environ
    ext = ""
    for name, suffix in (("SOLPS_OPENMP", ".openmp"), ("SOLPS_MPI", ".mpi"),
                         ("USE_IMPGYRO", ".ig")):
        if env.get(name):
            ext += suffix
    if debug or env.get("SOLPS_DEBUG"):
        ext += ".debug"
    kind = ("standalone" if standalone or env.get("STAND_ALONE")
            else "couple_SOLPS-ITER")
    return os.path.join(env.get("SOLPSTOP", ""), "modules", "B2.5", "builds",
                        "%s.%s.%s%s" % (kind, env.get("HOST_NAME", ""),
                                        env.get("COMPILER", ""), ext))


def environment_problems(standalone, debug, targets, built=True):
    """SOLPS environment and executables needed by scripts/b2plot."""
    missing = [v for v in ("SOLPSTOP", "HOST_NAME", "COMPILER", "MAKE")
               if not os.environ.get(v)]
    if missing:
        return [", ".join(missing) + " not set: source setup.csh first"]
    found = []
    wrapper = os.path.join(os.environ["SOLPSTOP"], "scripts", "b2plot")
    if not os.access(wrapper, os.X_OK):
        found.append(wrapper + " not found")
    build = build_dir(standalone, debug)
    for target in targets if built else []:
        exe = os.path.join(build, target + ".exe")
        if not os.path.isfile(exe):
            found.append("%s.exe not built: run make in modules/B2.5 "
                         "(no %s)" % (target, exe))
    return found


def fail_environment(found):
    for line in found:
        sys.stderr.write("b2plot.py: " + line + "\n")
    sys.exit(2)
