"""The helper scripts of scripts/ that know the run, called as they are.

The run plots use climb_and_look_for, get_solps_fluids, chop_pwd and resopt
(with resmod, ave.awk and blank) exactly as the old scripts do; the folder
of the scripts comes first on PATH, since they call each other by name.
"""

import os
import subprocess

from .. import requirements

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir,
                                     os.pardir, os.pardir))
SCRIPTS = os.path.join(ROOT, "scripts")


def _environment():
    env = requirements.child_environment()
    env["PATH"] = SCRIPTS + os.pathsep + env.get("PATH", "")
    env.setdefault("SOLPSTOP", ROOT)
    return env


def run(name, args=(), stdin=None):
    """Standard output of the helper script name, run in the current
    folder; its error output goes to the terminal."""
    done = subprocess.run([os.path.join(SCRIPTS, name)] + list(args),
                          input=stdin, stdout=subprocess.PIPE,
                          env=_environment(), universal_newlines=True,
                          encoding="latin-1")
    return done.stdout


def shell(command):
    """Standard output of a pipeline of helper scripts (run by sh)."""
    done = subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                          env=_environment(), universal_newlines=True,
                          encoding="latin-1")
    return done.stdout


def _nonempty(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def _first_field(path):
    with open(path, encoding="latin-1") as stream:
        return stream.readline().strip().split(" ")[0]


def nreg_file():
    """First number of the NREG file found by climb_and_look_for, or
    None (no run.log reading)."""
    path = run("climb_and_look_for", ["NREG"]).strip()
    return _first_field(path) if _nonempty(path) else None


def nreg():
    """NREG as 2d_plots finds it, with its messages: the NREG file, else
    the nnreg line of run.log (pipe_run.log); None when they disagree."""
    path = run("climb_and_look_for", ["NREG"]).strip()
    log = shell("pipe_run.log | grep -a ^nnreg | head -1").split()
    if _nonempty(path):
        value, where = _first_field(path), path
    else:
        value, where = (log[1] if len(log) > 1 else "4"), "log file"
    print("Set NREG to %s (based on %s)" % (value, where), flush=True)
    if len(log) > 1 and value != log[1]:
        print("NREG in file (%s) does not match %s" % (log[1], value))
        return None
    return value


def groups_species():
    """Number of species of each isonuclear sequence (groups_species)."""
    return [int(n) for n in run("groups_species").split()]


def solps_fluids(message=False):
    """Species names: the SOLPS_FLUIDS file found by climb_and_look_for,
    else get_solps_fluids (run.log); message as resco prints it."""
    path = run("climb_and_look_for", ["SOLPS_FLUIDS"]).strip()
    if _nonempty(path):
        with open(path, encoding="latin-1") as stream:
            names, where = stream.read().split(), path
    else:
        names, where = run("get_solps_fluids").split(), "log file"
    if message:
        print("Set SOLPS_FLUIDS to %s (based on %s)" % (" ".join(names),
                                                        where), flush=True)
    return names


def neutral_names(names):
    """Neutral species: the name ends in 0, not after another digit."""
    return [n for n in names
            if n.endswith("0") and not (len(n) > 1 and n[-2].isdigit())]


def isonuclear_names(names):
    """Element names of the neutral species (D0 gives D)."""
    return [n[:-1] for n in neutral_names(names)]


def chop_pwd(width=60):
    """The current folder shortened by chop_pwd, as in the page titles."""
    return run("chop_pwd", [str(width)]).strip()


def resopt(text, args):
    """The residual records filtered by resopt with the options args."""
    return run("resopt", args, stdin=text)
