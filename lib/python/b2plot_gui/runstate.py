"""Where a run directory stands, from what runs/Makefile does around b2mn:
at the start it deletes b2fstate, b2fplasma, b2fparam, b2ftrack, b2mn.prt
and balance.nc and runs b2mn in b2mn.exe.dir with a copy of b2fstati
(the movie files are written in the run directory, or in b2mn.exe.dir
when older ones are there); at the end, also after a crash, it moves the
outputs back and removes the folder when it is empty.

finished: b2fstate passes the test of scripts/b2fstate_OK (at least as
long as b2fstati) and b2fplasma was written with it; crashed: b2fstate
empty or absent, and the b2fplasma B2.5 writes when an error stops it
(b2plot shows that plasma with the species of b2fstati); running:
b2mn.exe.dir of a run started after any final state (in progress, or
stopped before the end of the Makefile); stopped: no complete final state
(crashed before b2mn wrote b2fplasma on errors). Running or stopped,
b2plot runs in a folder of links to the run directory, with b2fstati as
its state."""

import os
import shutil
import tempfile
import time

from .session import SLACK, _age, of_state

EXE = "b2mn.exe.dir"
MOVIES = ("b2movies.nc", "eirenemovies.nc", "b2tallies.nc")
_COUNTS = {}                        # (path, size, date) -> counts


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _first(*paths):
    return next((p for p in paths if os.path.isfile(p)), None)


def _initial(rundir):
    """b2fstati as scripts/b2fstate_OK finds it: the run directory, else
    ../baserun."""
    return _first(os.path.join(rundir, "b2fstati"),
                  os.path.join(rundir, "..", "baserun", "b2fstati"))


def _counts(path):
    """Lines, bytes and *cf records of a formatted state file."""
    st = os.stat(path)
    key = (path, st.st_size, st.st_mtime)
    if key not in _COUNTS:
        lines = cf = 0
        tail = b""
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 23), b""):
                lines += chunk.count(b"\n")
                cf += (tail + chunk).count(b"*cf")
                tail = chunk[-2:]
        _COUNTS[key] = (lines, st.st_size, cf)
    return _COUNTS[key]


def complete(rundir):
    """The test of scripts/b2fstate_OK: b2fstate with at least the lines,
    bytes and *cf records of b2fstati, and more than 10 records (without
    any b2fstati only the latter)."""
    state, ref = os.path.join(rundir, "b2fstate"), _initial(rundir)
    if not os.path.isfile(state) or (
            ref is not None and os.path.getsize(state) <
            os.path.getsize(ref)):
        return False
    lines, size, cf = _counts(state)
    lines0, size0, cf0 = _counts(ref) if ref is not None else (0, 0, 0)
    return lines >= lines0 and size >= size0 and cf >= cf0 and cf > 10


def _start(rundir):
    """When the run in b2mn.exe.dir started (its copy of b2fstati), or
    None."""
    exe = os.path.join(rundir, EXE)
    if not os.path.isdir(exe):
        return None
    return _mtime(os.path.join(exe, "b2fstati")) or _mtime(exe)


def state(rundir):
    """("finished" | "crashed" | "running" | "stopped", why: empty when
    finished)."""
    path = os.path.join(rundir, "b2fstate")
    t_state = _mtime(path) if os.path.isfile(path) and \
        os.path.getsize(path) > 0 else None
    start = _start(rundir)
    plasma = os.path.join(rundir, "b2fplasma")
    begun = _mtime(path) or start   # an empty b2fstate: the run start
    if t_state is None and os.path.isfile(plasma) and (
            begun is None or _mtime(plasma) >= begun - SLACK):
        return "crashed", (
            "plasma of b2fplasma, written when an error stopped B2.5 (%s): "
            "that of the start of the failing time step; no b2fstate" %
            time.strftime("%Y-%m-%d %H:%M", time.localtime(
                _mtime(plasma))))
    if start is not None and (t_state is None or start > t_state + SLACK):
        exe = os.path.join(rundir, EXE)
        last = max([_mtime(e.path) or start for e in os.scandir(exe)] +
                   [start])
        return "running", (
            "A run is in progress in b2mn.exe.dir (started %s, last "
            "written %s ago), or it stopped before its end: no final state"
            % (time.strftime("%Y-%m-%d %H:%M", time.localtime(start)),
               _age(max(time.time() - last, 0.0))))
    if t_state is None:
        return "stopped", "No b2fstate%s: the latest run stopped before " \
            "its end" % (" (empty)" if os.path.isfile(path) else "")
    if not complete(rundir):
        return "stopped", "b2fstate is shorter than b2fstati (the test of " \
            "scripts/b2fstate_OK): the latest run stopped before its end"
    if not os.path.isfile(plasma):
        return "stopped", "No b2fplasma: the latest run stopped before " \
            "its end"
    gap = abs(_mtime(plasma) - t_state)
    if gap > SLACK:
        return "stopped", "b2fplasma and b2fstate are %s apart: not " \
            "written by the same run" % _age(gap)
    return "finished", ""


def movies(rundir, kind, names=MOVIES):
    """{name: (path, why)} of the movie files (or of other files the run
    writes as them: names): those of the latest run (why empty) and why
    the others are left out. Finished run: written with its final state
    (as balance.nc); otherwise written since its start (b2mn.exe.dir;
    ended: its empty b2fstate, else b2fstati), those b2mn writes in
    b2mn.exe.dir first."""
    exe = os.path.join(rundir, EXE)
    st = os.path.join(rundir, "b2fstate")
    begun = _mtime(st) if os.path.isfile(st) and \
        os.path.getsize(st) == 0 else None
    start = _start(rundir) if kind == "running" else begun or _mtime(
        _initial(rundir) or "")
    out = {}
    for name in names:
        local = os.path.join(exe, name)
        if kind == "running" and os.path.isfile(local) and \
                not os.path.islink(local):
            out[name] = (local, "")
            continue
        path = os.path.join(rundir, name)
        if not os.path.isfile(path):
            continue
        if kind == "finished":
            why = of_state(rundir, path)
        elif start is not None and _mtime(path) < start - SLACK:
            why = "%s is %s older than the start of the latest run: from " \
                "an earlier run" % (name, _age(start - _mtime(path)))
        else:
            why = ""
        out[name] = (path, why)
    return out


def view_folder(rundir, kind):
    """A folder of links to the run directory for b2plot when there is no
    final state: b2fstate the initial state of the latest run (its copy in
    b2mn.exe.dir, else b2fstati), b2fparam its default parameters
    (b2fpardf: b2plot adds those of b2mn.dat), the movie files of the
    latest run, no b2fplasma or b2ftrack; the files of the folder above
    (baserun) beside it. remove_view removes it."""
    rundir = os.path.abspath(rundir)
    parent = os.path.dirname(rundir)
    base = tempfile.mkdtemp(prefix="b2plot-view-")
    for name in os.listdir(parent):
        if os.path.join(parent, name) != rundir:
            os.symlink(os.path.join(parent, name), os.path.join(base, name))
    run = os.path.join(base, os.path.basename(rundir))
    os.mkdir(run)
    skip = {"b2fstate", "b2fplasma", "b2ftrack", "b2fparam", EXE,
            "b2pl.exe.dir"} | set(MOVIES)
    for name in os.listdir(rundir):
        if name not in skip:
            os.symlink(os.path.join(rundir, name), os.path.join(run, name))
    links = {"b2fstate": _first(os.path.join(rundir, EXE, "b2fstati"),
                                os.path.join(rundir, "b2fstati"),
                                os.path.join(parent, "baserun", "b2fstati")),
             "b2fparam": _first(os.path.join(rundir, "b2fpardf"),
                                os.path.join(parent, "baserun", "b2fpardf"))}
    links.update((name, path) for name, (path, why) in
                 movies(rundir, kind).items() if not why)
    for name, path in links.items():
        if path is not None:
            os.symlink(path, os.path.join(run, name))
    return run


def remove_view(run):
    """Remove a folder of view_folder (only links and b2plot files)."""
    base = os.path.dirname(run)
    if os.path.basename(base).startswith("b2plot-view-"):
        shutil.rmtree(base, ignore_errors=True)
