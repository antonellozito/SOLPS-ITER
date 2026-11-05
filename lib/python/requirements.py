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

# Qt platforms without windows, to which Qt falls back when it cannot use
# the display
WINDOWLESS = ("offscreen", "minimal", "minimalegl", "linuxfb", "eglfs",
              "vkkhrdisplay")
_PROBE = ("from PySide6.QtWidgets import QApplication; "
          "a = QApplication(['b2plot']); "
          "print('B2PLOT_QT_PLATFORM=' + a.platformName())")

# Linux: system libraries for the Qt windows that the system lacks, put
# there by install_python (provide_qt_libraries)
QT_LIBS = os.path.join(sys.prefix, "qtlibs", "lib")

# conda-forge package of each system library the Qt windows may need,
# by start of the library name (more specific names first)
CONDA_PACKAGES = (
    ("libxcb-cursor.", "xcb-util-cursor"), ("libxcb-image.", "xcb-util-image"),
    ("libxcb-keysyms.", "xcb-util-keysyms"),
    ("libxcb-render-util.", "xcb-util-renderutil"),
    ("libxcb-icccm.", "xcb-util-wm"), ("libxcb-ewmh.", "xcb-util-wm"),
    ("libxcb-util.", "xcb-util"), ("libxcb", "libxcb"),
    ("libxkbcommon", "libxkbcommon"), ("libX11", "xorg-libx11"),
    ("libXau.", "xorg-libxau"), ("libXdmcp.", "xorg-libxdmcp"),
    ("libXext.", "xorg-libxext"), ("libXrender.", "xorg-libxrender"),
    ("libSM.", "xorg-libsm"), ("libICE.", "xorg-libice"),
    ("libEGL.", "libegl"), ("libGLX.", "libglx"), ("libGLdispatch.", "libglvnd"),
    ("libOpenGL.", "libopengl"), ("libGL.", "libgl"),
    ("libfontconfig.", "fontconfig"), ("libfreetype.", "freetype"),
    ("libdbus-1.", "dbus"), ("libglib-2.0.", "libglib"),
    ("libgthread-2.0.", "libglib"), ("libpng16.", "libpng"),
    ("libz.", "libzlib"), ("libzstd.", "zstd"), ("libexpat.", "libexpat"),
    ("libbz2.", "bzip2"), ("liblzma.", "liblzma"), ("libuuid.", "libuuid"),
    ("libpcre2-8.", "pcre2"), ("libbrotli", "brotli"),
    ("libstdc++.", "libstdcxx"), ("libgcc_s.", "libgcc"))
MICROMAMBA = ("https://micro.mamba.pm/api/micromamba/%s/latest",
              "https://github.com/mamba-org/micromamba-releases/releases/"
              "latest/download/micromamba-%s")


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
    wheel, then the system libraries of provide_qt_libraries, and without the
    library folders of other Python installations."""
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
    first = [d for d in first + [QT_LIBS] if os.path.isdir(d)]
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
        if name == "PySide6" and not gui:
            continue   # Qt only for windows: files need numpy and matplotlib
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
        else:
            problem = window_problem()
            if problem:
                found.append("Qt for matplotlib (" + problem + ")")
    return found


def missing_qt_libraries(library_path=None):
    """System libraries that the Qt of PySide6 needs for windows and that
    the library loader cannot find (Linux, from ldd, with library_path as
    LD_LIBRARY_PATH; the current one if None)."""
    if not sys.platform.startswith("linux") or shutil.which("ldd") is None:
        return []
    import importlib.util
    import subprocess
    try:
        spec = importlib.util.find_spec("PySide6")
        root = os.path.join(list(spec.submodule_search_locations)[0], "Qt")
    except Exception:
        return []
    env = dict(os.environ)
    if library_path is not None:
        env["LD_LIBRARY_PATH"] = library_path
    missing = []
    for pattern in ("plugins/platforms/libqxcb.so", "lib/libQt6XcbQpa.so.*",
                    "lib/libQt6Gui.so.*", "lib/libQt6Widgets.so.*"):
        for path in glob.glob(os.path.join(root, pattern)):
            try:
                out = subprocess.run(["ldd", path], stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, env=env,
                                     universal_newlines=True,
                                     timeout=60).stdout
            except Exception:
                continue
            for line in out.splitlines():
                if "not found" in line and line.split()[0] not in missing:
                    missing.append(line.split()[0])
    return missing


def _conda_package(name):
    for start, package in CONDA_PACKAGES:
        if name.startswith(start):
            return package
    return None


def _micromamba(folder):
    """A private micromamba (one static binary) in folder/bin, downloaded
    from conda-forge for this machine; None if not possible."""
    import platform
    import tarfile
    exe = os.path.join(folder, "bin", "micromamba")
    if os.access(exe, os.X_OK):
        return exe
    arch = {"x86_64": "linux-64", "aarch64": "linux-aarch64",
            "arm64": "linux-aarch64", "ppc64le": "linux-ppc64le"}.get(
                platform.machine())
    if arch is None:
        print("No prebuilt libraries for the machine type " + platform.machine())
        return None
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    archive = os.path.join(folder, "micromamba.download")
    for url in MICROMAMBA:
        if _download(url % arch, archive):
            try:
                if tarfile.is_tarfile(archive):
                    with tarfile.open(archive, "r:bz2") as tar:
                        src = tar.extractfile(tar.getmember("bin/micromamba"))
                        with open(exe, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                else:
                    shutil.move(archive, exe)
                os.chmod(exe, 0o755)
                return exe
            except Exception:
                pass
            finally:
                if os.path.exists(archive):
                    os.remove(archive)
    print("The download of micromamba failed (no internet access?)")
    return None


def _download(url, path):
    """url into path, with urllib or else curl; True if it worked."""
    import subprocess
    try:
        import urllib.request
        urllib.request.urlretrieve(url, path)
        return True
    except Exception:
        return subprocess.call(["curl", "-fsSL", "-o", path, url]) == 0


def provide_qt_libraries():
    """install_python on Linux: the system libraries that the Qt windows of
    PySide6 need and that the system lacks, prebuilt from conda-forge by a
    private micromamba (no root, no compiler, no conda of the user) and
    copied into QT_LIBS: only the missing ones, so that the system libraries
    are used where they exist. Returns 0 if nothing is missing any more."""
    import subprocess
    if not sys.platform.startswith("linux"):
        return 0
    folder = os.path.dirname(QT_LIBS)
    env_dir = os.path.join(folder, "env")
    path = os.pathsep.join([QT_LIBS] + [
        d for d in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        if d and not _other_python_lib(d)])
    missing = missing_qt_libraries(path)
    if not missing:
        print("All system libraries needed by the Qt windows are present.")
        return 0
    print("System libraries needed by the Qt windows and not found: "
          + ", ".join(missing))
    env = dict((k, v) for k, v in os.environ.items()
               if not k.startswith(("CONDA", "MAMBA", "_CONDA", "_MAMBA",
                                    "PYTHON")))
    env["MAMBA_ROOT_PREFIX"] = os.path.join(folder, "root")
    tried = set()
    try:
        for _ in range(6):
            packages = sorted(set(p for p in map(_conda_package, missing)
                                  if p and p not in tried))
            if not packages:
                break
            exe = _micromamba(folder)
            if exe is None:
                break
            print("Fetching from conda-forge: " + " ".join(packages))
            action = "install" if os.path.isdir(env_dir) else "create"
            if subprocess.call([exe, action, "-y", "-q", "--no-rc",
                                "-r", env["MAMBA_ROOT_PREFIX"], "-p", env_dir,
                                "-c", "conda-forge", "--override-channels"]
                               + packages, env=env) != 0:
                print("micromamba could not fetch " + " ".join(packages))
                break
            tried.update(packages)
            os.makedirs(QT_LIBS, exist_ok=True)
            for name in missing:
                source = os.path.join(env_dir, "lib", name)
                if os.path.exists(source):
                    shutil.copy2(os.path.realpath(source),
                                 os.path.join(QT_LIBS, name))
            missing = missing_qt_libraries(path)
            if not missing:
                break
    finally:
        for d in ("env", "root", "bin"):
            shutil.rmtree(os.path.join(folder, d), ignore_errors=True)
    if missing:
        print("Still not found: " + ", ".join(missing)
              + " (install them with the package manager of the system)")
        return 1
    print("The missing system libraries are in " + QT_LIBS)
    return 0


def window_problem():
    """None if Qt can open windows here, else the reason. Checked in a
    separate process: Qt stops a process that cannot use the display, or
    falls back to a platform without windows (WINDOWLESS)."""
    import subprocess
    try:
        r = subprocess.run([sys.executable, "-I", "-c", _PROBE],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=120)
    except Exception as err:
        return "Qt could not be started (%s)" % err
    platform = ""
    for line in r.stdout.splitlines():
        if line.startswith("B2PLOT_QT_PLATFORM="):
            platform = line.split("=", 1)[1].strip()
    wanted = os.environ.get("QT_QPA_PLATFORM", "")
    if r.returncode == 0 and platform and (platform not in WINDOWLESS
                                           or wanted.startswith(platform)):
        return None
    text = "Qt cannot open windows on this display"
    if platform:
        text += " (it fell back to its %s platform)" % platform
    reasons = [l.strip() for l in r.stderr.splitlines()
               if l.startswith("qt.") or "platform plugin" in l][:3]
    if reasons:
        text += ": " + " ".join(reasons)
    missing = missing_qt_libraries()
    if missing:
        text += "; system libraries not found: " + ", ".join(missing)
    return text


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
    if found and "cannot open windows" in found[0]:
        lines += ["The windows need a display that Qt can use (DISPLAY on "
                  "Linux) and the system",
                  "  libraries listed above; on Linux run install_python "
                  "again, it provides the",
                  "  missing ones. B2PLOT_DEV=ps writes the pages to "
                  "b2plot.ps without windows."]
    elif found and all(f.startswith("Qt for matplotlib") for f in found):
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
