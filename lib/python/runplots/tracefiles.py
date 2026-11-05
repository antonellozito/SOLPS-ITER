"""Text files of a run: b2ftrace and the tracing files tracing/*.trc.

Both are read from b2mn.exe.dir first (run in progress), as the old
scripts do.
"""

import gzip
import os
import re

import numpy as np

TRACING = ("blnn_SPb.trc", "blne.trc")

# Columns by file, as 2dt_tracing finds them (species suffix removed)
BLNN_STEMS = ("ion_core ntr_targ_tot ntr_targ_rec ntr_targ_spt ntr_targ_pmp "
              "ion_wall ntr_wall_tot ntr_wall_rec ntr_wall_spt ntr_wall_pmp "
              "src_ioniz ntr_puff flux_tot src_ext ion_dn/dt ntr_core "
              "ion_targ").split()
BLNE_STEMS = ("pwr_totl pwr_tscl tot_core tot_targ tot_wall tot_rad heat_cor "
              "ptnt_cor ntrl_cor plsm_trg ntrl_trg plsm_wll ntrl_wll brms_rad "
              "ntrl_rad imp_rad tot_enrg tot_enre tot_enri").split()
BLNE_STEMS += ["pwr_%s_%s" % (q, s) for s in ("il", "ol", "iu", "ou", "wl")
               for q in ("totl", "plsm", "neut", "ionz", "diss")]

_FORTRAN_EXPONENT = re.compile(r"(?<=[0-9.])([+-][0-9]{3})$")


def run_file(name):
    """b2mn.exe.dir/name if not empty, else name; None if both are empty
    or missing."""
    for path in (os.path.join("b2mn.exe.dir", name), name):
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def number(text):
    """A number as Fortran writes it (D or missing E exponent); nan for
    anything else, which gnuplot leaves out as well."""
    text = text.replace("D", "E").replace("d", "E")
    try:
        return float(text)
    except ValueError:
        try:
            return float(_FORTRAN_EXPONENT.sub(r"E\1", text))
        except ValueError:
            return float("nan")


def _text_lines(path):
    with open(path, "rb") as stream:
        gzipped = stream.read(2) == b"\x1f\x8b"
    opener = gzip.open if gzipped else open
    with opener(path, "rt", encoding="latin-1") as stream:
        return stream.read().splitlines()


def b2ftrace_records(path):
    """The data records of b2ftrace, one line each, as the record joiner of
    resco makes them (no newline after the last record)."""
    out, state = [], 0
    for line in _text_lines(path):
        if "data" in line:
            if state == 0:
                state = 1
            elif state == 2:
                out.append("\n")
        if state > 0 and line and line[0] != "*":
            state = 2
            out.append(line)
    return "".join(out)


class TraceFile:
    """A tracing file: column names from its third line, values below."""

    def __init__(self, path):
        lines = _text_lines(path)
        header = lines[2] if len(lines) > 2 else ""
        self.path = path
        self.names = re.sub(r"^# *", "", header).split()
        self._rows = [line.split() for line in lines[3:]]

    def has(self, name):
        return name in self.names

    def column(self, name):
        """The values of a column; rows too short for it are left out."""
        k = self.names.index(name)
        return np.array([number(r[k]) for r in self._rows if len(r) > k])

    def series(self, name):
        """(time, values) of a column, both from this file."""
        t, v = self.column("time"), self.column(name)
        n = min(len(t), len(v))
        return t[:n], v[:n]


def stem(name, elements):
    """The column name without its element suffix (ion_core_D gives
    ion_core), as 2dt_tracing finds the file of a column."""
    for element in elements:
        if name.endswith("_" + element):
            return name.replace("_" + element, "")
    return name


def tracing_files():
    """The tracing files present, by name."""
    found = {}
    for name in TRACING:
        path = run_file(os.path.join("tracing", name))
        if path is not None:
            found[name] = TraceFile(path)
    return found
