"""Interpreter and module check of the Python graphics of b2plot (no
fallbacks).

Runs on any Python 3 (no f-strings, standard library only), so that the
error message is printed even by an old interpreter. The module list must
match PYTHON_MODULES of scripts/install_python.
"""

import glob
import json
import os
import shutil
import sys

REQUIRED_PYTHON = (3, 9)
REQUIRED = [("PySide6", "6.4"), ("numpy", "1.21"), ("matplotlib", "3.8")]

# Name in messages, set from the command line (options.name)
NAME = "b2plot"

# Settings of other Python, Qt and matplotlib installations that would
# reach the Python graphics: removed for its Python, given back to the
# executables it starts (child_environment)
FOREIGN = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE",
           "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH",
           "QML2_IMPORT_PATH", "QML_IMPORT_PATH", "MPLBACKEND",
           "MATPLOTLIBRC", "LD_PRELOAD", "DYLD_LIBRARY_PATH",
           "DYLD_FRAMEWORK_PATH", "DYLD_FALLBACK_LIBRARY_PATH",
           "DYLD_FALLBACK_FRAMEWORK_PATH", "DYLD_INSERT_LIBRARIES")
SAVED = "B2PLOT_PY_ENV"
STAGE = "B2PLOT_PY_REEXEC"


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


def local_python():
    """The local SOLPS-ITER-specific Python of install_python, or None."""
    env = os.environ
    if not (env.get("SOLPSTOP") and env.get("HOST_NAME")
            and env.get("COMPILER")):
        return None
    path = os.path.join(env["SOLPSTOP"], "lib", "%s.%s" % (
        env["HOST_NAME"], env["COMPILER"]), "python", "bin", "python3")
    return path if os.access(path, os.X_OK) else None


def _saved():
    return json.loads(os.environ.get(SAVED, "{}"))


def _other_python_lib(folder):
    """True for the library folder of another Python installation (a conda
    environment, another interpreter), which holds its own Qt, ICU, ..."""
    real = os.path.realpath(folder)
    if real.startswith(os.path.realpath(sys.prefix) + os.sep):
        return False
    return bool(glob.glob(os.path.join(real, "python3*", "os.py"))
                or os.path.isdir(os.path.join(real, "..", "conda-meta")))


def _library_path(path):
    """LD_LIBRARY_PATH for the Python graphics on Linux: the libraries of
    PySide6 first, since LD_LIBRARY_PATH comes before the RUNPATH of its
    wheel, and without the library folders of other Python installations."""
    first = []
    try:
        import importlib.util
        for name, subs in (("PySide6", ("Qt/lib", "")), ("shiboken6", ("",))):
            spec = importlib.util.find_spec(name)
            if spec is not None and spec.submodule_search_locations:
                root = list(spec.submodule_search_locations)[0]
                first += [os.path.join(root, d) if d else root for d in subs]
    except Exception:
        pass
    first = [d for d in first if os.path.isdir(d)]
    rest = [d for d in path.split(os.pathsep)
            if d and d not in first and not _other_python_lib(d)]
    return os.pathsep.join(first + rest)


def reexec_with_session_python():
    """Run the Python graphics under the SOLPS-ITER Python, whatever other
    Python is installed: the local installation of install_python (else
    $PYTHON, else this interpreter) in isolated mode (no PYTHONPATH,
    PYTHONHOME or user site-packages), without the settings of FOREIGN and,
    on Linux, with the library path of _library_path. At most two re-runs;
    the executables started later get the original environment back."""
    env = os.environ
    stage = env.get(STAGE)
    if stage is None:
        target = local_python()
        if target is None and env.get("PYTHON"):
            target = shutil.which(env["PYTHON"])
            if target is None or not os.access(target, os.X_OK):
                fail(["PYTHON is set to " + env["PYTHON"]
                      + ", which is not executable"])
        target = target or sys.executable
        saved = dict((name, env.get(name)) for name in FOREIGN + ("QT_API",))
        for name in FOREIGN:
            env.pop(name, None)
        env["QT_API"] = "pyside6"
        env[SAVED] = json.dumps(saved)
        env[STAGE] = "1"
        os.execv(target, [target, "-I"] + sys.argv)
    if stage == "1" and sys.platform.startswith("linux"):
        path = env.get("LD_LIBRARY_PATH", "")
        new = _library_path(path)
        if new != path:
            saved = _saved()
            saved["LD_LIBRARY_PATH"] = path or None
            env[SAVED] = json.dumps(saved)
            env["LD_LIBRARY_PATH"] = new
            env[STAGE] = "2"
            os.execv(sys.executable, [sys.executable, "-I"] + sys.argv)


def child_environment(**extra):
    """Environment for the executables: the original one of the user, as
    before reexec_with_session_python, plus extra."""
    env = dict(os.environ)
    saved = json.loads(env.pop(SAVED, "{}"))
    env.pop(STAGE, None)
    for name, value in saved.items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    env.update(extra)
    return env


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
        os.environ["QT_API"] = "pyside6"
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
        "%s: the Python of this SOLPS-ITER session cannot run the Python "
        "graphics of b2plot." % NAME,
        "  Interpreter: %s (Python %d.%d.%d)" % (sys.executable, v[0], v[1],
                                                 v[2]),
        "  Missing or too old: " + "; ".join(found),
        "The Python graphics of b2plot need Python >= %d.%d with: %s"
        % (REQUIRED_PYTHON + (need,)),
    ]
    local = os.path.join(os.environ.get("SOLPSTOP", ""), "lib",
                         "%s.%s" % (os.environ.get("HOST_NAME", ""),
                                    os.environ.get("COMPILER", "")),
                         "python")
    if found and all(f.startswith("Qt for matplotlib") for f in found):
        lines += ["PySide6 is installed, but its Qt libraries cannot be "
                  "loaded: another Qt",
                  "  found first by the system library loader is the usual "
                  "cause; look for one",
                  "  in the library path (%s)." % (
                      "DYLD_LIBRARY_PATH" if sys.platform == "darwin"
                      else "LD_LIBRARY_PATH")]
    elif os.environ.get("SOLPSTOP") and os.path.realpath(
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
                 "section \"Python graphics\".")
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


def graphics(build):
    """Graphics of a B2.5 build from its stamp file (modules/B2.5/Makefile):
    "python", "ncar" or None (not built since the stamp exists)."""
    for kind in ("python", "ncar"):
        if os.path.isfile(os.path.join(build, ".graphics_" + kind)):
            return kind
    return None


def environment_problems(standalone, debug, programs, built=True,
                         tool="b2plot"):
    """SOLPS environment, wrapper script and Python graphics executables
    needed to run the programs through scripts/b2plot or scripts/b2run."""
    missing = [v for v in ("SOLPSTOP", "HOST_NAME", "COMPILER", "MAKE")
               if not os.environ.get(v)]
    if missing:
        return [", ".join(missing) + " not set: source setup.csh first"]
    found = []
    wrapper = os.path.join(os.environ["SOLPSTOP"], "scripts", tool)
    if not os.access(wrapper, os.X_OK):
        found.append(wrapper + " not found")
    if not built:
        return found
    build = build_dir(standalone, debug)
    kind = graphics(build)
    if kind == "ncar":
        return found + ["%s was built with NCAR Graphics (USE_NCAR): the "
                        "Python graphics need a build without USE_NCAR"
                        % build]
    for prog in programs:
        exe = os.path.join(build, prog + ".exe")
        if not os.path.isfile(exe):
            found.append("%s.exe not built: run make in modules/B2.5 "
                         "(no %s)" % (prog, exe))
    if kind is None and not found:
        found.append("%s has no Python graphics yet: run make in "
                     "modules/B2.5" % build)
    return found


def fail_environment(found):
    for line in found:
        sys.stderr.write(NAME + ": " + line + "\n")
    sys.exit(2)
