"""The SOLPS-ITER session of the GUI: which folders are run directories,
and the runs opened in the session. A session starts with each source of
setup.csh (or setup.ksh), which sets SOLPS_SESSION; every b2viewer
started from it shares one list of runs, kept in a file of the temporary
folder. Without SOLPS_SESSION the list is that of the window only."""

import getpass
import os
import re
import tempfile

RUN_FILES = ("b2mn.dat", "b2fstate", "b2fstati")
STATE = ("b2fstate", "b2fplasma")   # written at the end of a run
SLACK = 600.0               # seconds between a file of a run and its state


def is_run(path):
    """A run directory: b2mn.dat or a plasma state file in it."""
    return bool(path) and any(os.path.exists(os.path.join(path, f))
                              for f in RUN_FILES)


def of_state(rundir, path):
    """"" if the file at path was written by the run of the present state
    (within SLACK of the newer of b2fstate and b2fplasma), else why not."""
    name = os.path.basename(path)
    times = [os.path.getmtime(p) for p in (os.path.join(rundir, n)
                                           for n in STATE)
             if os.path.isfile(p)]
    if not times:
        return "No b2fstate or b2fplasma next to %s" % name
    gap = abs(os.path.getmtime(path) - max(times))
    if gap > SLACK:
        return "%s is %s older or newer than b2fstate and b2fplasma: it " \
            "is not from the run of this state" % (name, _age(gap))
    return ""


def _age(seconds):
    for unit, size in (("days", 86400.0), ("hours", 3600.0),
                       ("minutes", 60.0)):
        if seconds >= 2 * size:
            return "%.0f %s" % (seconds / size, unit)
    return "%.0f seconds" % seconds


def runs_folder():
    """Where the runs of the session are ($SOLPSWORK, else
    $SOLPSTOP/runs), or None."""
    if os.environ.get("SOLPSWORK"):
        return os.environ["SOLPSWORK"]
    if os.environ.get("SOLPSTOP"):
        return os.path.join(os.environ["SOLPSTOP"], "runs")
    return None


def shown(path):
    """The run directory as the run line shows it: without the runs
    folder of the session when it is in there."""
    top = runs_folder()
    if top:
        for f in (os.path.abspath, os.path.realpath):
            base, p = f(top), f(path)
            if p.startswith(base + os.sep):
                return p[len(base) + 1:]
    return path


class Recent:
    """The runs opened in the session, newest first."""

    def __init__(self):
        self.mine = []
        sid = os.environ.get("SOLPS_SESSION", "")
        self.path = None
        if sid:
            folder = os.path.join(tempfile.gettempdir(),
                                  "b2viewer-" + getpass.getuser())
            self.path = os.path.join(
                folder, "runs-" + re.sub(r"[^\w.-]", "_", sid))

    def runs(self):
        if self.path is not None:
            try:
                with open(self.path) as f:
                    return [p.rstrip("\n") for p in f if p.strip()]
            except OSError:
                pass
        return list(self.mine)

    def add(self, path):
        self.mine = [path] + [p for p in self.runs() if p != path]
        if self.path is None:
            return
        try:
            os.makedirs(os.path.dirname(self.path), mode=0o700,
                        exist_ok=True)
            part = "%s.%d" % (self.path, os.getpid())
            with open(part, "w") as f:
                f.write("".join(p + "\n" for p in self.mine))
            os.replace(part, self.path)
        except OSError:
            pass
