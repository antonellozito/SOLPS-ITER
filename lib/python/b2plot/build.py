"""The B2.5 build that b2plot, b2run and carre2 use: its folder, its
graphics and the executables and wrapper scripts they need (any Python 3,
standard library only)."""

import os
import sys

from .. import requirements


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
        sys.stderr.write(requirements.NAME + ": " + line + "\n")
    sys.exit(2)
