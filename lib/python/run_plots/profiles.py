"""2dds, 2d_profiles and 2d_profiles_extended: b2time.nc profiles against
the ds coordinate of their location, means over the last time slices.

The numbers follow the old pipelines (nc2text, ave.awk, paste, awk), so
the .last10 files are the same text and the pages the same values: means
with 6 significant digits, the ds coordinate of b2time.nc rounded so and
written as % .16E, temperatures te and ti divided by e, fluxes divided by
the target area (dsXT) and, when the run folder has the contact areas
(dsXP), by those. Which files the old scripts test (dsl, dsL, dsLP,
fort.1, ...) decides as before.
"""

import math
import os
import re
import sys

import numpy as np

from . import averaging, geometry, helpers, ncdata, quantities, timetraces
from .pages import Curve, Page, stamp
from .tracefiles import run_file

E_CHARGE = 1.602176634e-19
_NUMBER = re.compile(r"^[0-9]+$")


def _whole(limit, fmt):
    def style(v):
        if v == int(v) and abs(v) < 2.0 ** 63 and \
                (limit is None or abs(v) < limit):
            return "%d" % int(v)
        if v == int(v) and limit is None:
            return fmt % v
        return "%.6g" % v
    return style


# How awks print a whole number (others: %.6g): %d up to 2^63 and all
# digits above (macOS awk), %d up to 2^63 (gawk), 2^53, 2^31 (older mawk);
# %d also turns -0 into 0
_STYLES = (_whole(None, "%.30g"), _whole(2.0 ** 63, "%d"),
           _whole(2.0 ** 53, "%d"), _whole(2.0 ** 31, "%d"))
_PROBES = (123.0, 2.0 ** 40, 2.0 ** 60, 2767835482401008517120.0, 1e300, 0.5,
           1234567.0)
_style = []


def _awk_style():
    """The style of the awk on PATH, found once from probe numbers."""
    if not _style:
        out = helpers.shell("printf '%s\\n' " + " ".join(
            "%.17g" % v for v in _PROBES) + " | awk '{print $1+0}'").split()
        found = [s for s in _STYLES
                 if out == [s(v) for v in _PROBES]]
        _style.append(found[0] if found else _STYLES[1])
    return _style[0]


def awk_str(v):
    """A number as awk prints it (print, printf %s): whole numbers as the
    awk on PATH writes them, else %.6g."""
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    return _awk_style()(v)


def awk_num(text):
    try:
        return float(text)
    except ValueError:
        return 0.0


def ave_awk(lines):
    """ave.awk without argument: the column means of the lines."""
    sums, count, width = {}, 0, 0
    for line in lines:
        if not line or line[0] == "#":
            continue
        fields = line.split()
        for j, f in enumerate(fields):
            sums[j] = sums.get(j, 0.0) + awk_num(f)
        count, width = count + 1, len(fields)
    if count == 0:
        return []
    return [awk_str(sums.get(j, 0.0) / count) for j in range(width)]


def paste(*columns):
    """paste: the lines side by side, separated by tabs."""
    n = max((len(c) for c in columns), default=0)
    return ["\t".join(c[i] if i < len(c) else "" for c in columns)
            for i in range(n)]


def divide(lines, name):
    """awk '{print $1,$2/$3}'; a zero divisor stops awk, as it does."""
    out = []
    for line in lines:
        f = line.split()
        x, v, d = (f + ["", "", ""])[:3]
        if awk_num(d) == 0.0:
            sys.stderr.write("%s.py: division by zero (as awk), output cut "
                             "here\n" % name)
            break
        out.append("%s %s" % (x, awk_str(awk_num(v) / awk_num(d))))
    return out


def _lines_of(path):
    with open(path, encoding="latin-1") as stream:
        return stream.read().splitlines()


def split_name(name, data):
    """(base, species index from 1 or None, prefix, pr2fix, suffix) as
    2dds cuts the name (dab, dmb, tab, tmb: one letter later)."""
    found = ncdata.species_name(name, data)
    base, index = (found[0], found[1] + 1) if found else (name, None)
    if found and base[:3] in ("dab", "dmb", "tab", "tmb"):
        return base, index, base[1], base[2], base[5:]
    return base, index, base[0:1], base[1:2], base[4:]


class Profiles:
    def __init__(self, name, avg, nreg=None):
        self.name, self.avg = name, avg
        self.data = ncdata.open_file("b2time.nc")
        if self.data is None:
            raise OSError("b2time.nc not found")
        self.fluids = helpers.solps_fluids()
        self.neutrals = helpers.neutral_names(self.fluids)
        self.config = quantities.Configuration(
            nreg if nreg is not None else helpers.nreg_file())
        if self.config.single_null():
            self.config.swapped = geometry.first_target_outer(self.data)
        t = np.asarray(self.data.variables["timesa"][:], dtype=float)
        if avg.batch_n and len(t) % avg.batch_n:
            ncdata.warn(name + ".py", "batch average: last %d time slice(s) "
                        "dropped (incomplete block)" % (len(t) % avg.batch_n))
        self.time = self._average(t)
        self.nt = (len(self.time) if avg.batch_n
                   else int(float(self.data.variables["ntstep"][...])))

    def _average(self, a):
        """The rolling or batch average along time (first axis)."""
        a = np.asarray(a, dtype=float)
        if self.avg.rolling_n:
            return np.apply_along_axis(averaging.rolling, 0, a,
                                       self.avg.rolling_n)
        if self.avg.batch_n:
            n = self.avg.batch_n
            m = a.shape[0] // n
            return a[:m * n].reshape((m, n) + a.shape[1:]).mean(axis=1)
        return a

    def means(self, var, subscripts):
        """ave.awk of nc2text var(subscripts): the strings of the means."""
        a = self._average(self.data.variables[var][:])
        return ave_awk(ncdata.nc2text_array(a, subscripts))

    def from_file(self, key):
        """The lines nc2text, ave.awk and printf "  % .16E" make of a ds
        variable of b2time.nc (rounded to awk precision), or None."""
        if key not in self.data.variables:
            return None
        a = np.asarray(self.data.variables[key][:], dtype=float)
        return ["  % .16E" % awk_num(s)
                for s in ave_awk(ncdata.nc2text_array(a))]

    def window(self, num, end):
        """NUM:END as 2dds and 2d_profiles clamp it."""
        if self.nt + num < 0:
            num = -self.nt + 1
        if self.nt + end > self.nt:
            end = 0
        return num, end

    def describe(self, num, end):
        """Footer text of a NUM:END time window."""
        n = len(self.time)
        lo, hi = [k if k > 0 else n + k for k in (num, end)]
        lo, hi = sorted((lo, hi))
        text = "mean of time slices %d-%d of %d" % (lo, hi, n)
        if 1 <= lo <= hi <= n:
            text += " (%.6g-%.6g s)" % (self.time[lo - 1], self.time[hi - 1])
        if self.avg:
            text += ", after a " + self.avg.describe()
        return text


class Areas:
    """The ds coordinate and areas of a location, as the old scripts find
    them: b2time.nc first, else the run folder files (folder: the folder
    of the copies, None for 2dds which uses the run folder itself)."""

    def __init__(self, prof, folder=None):
        self.prof, self.folder, self.cache = prof, folder, {}

    def _copy(self, key, source):
        target = os.path.join(self.folder or "", key)
        if os.path.isfile(target) and os.path.getsize(target) > 0:
            return _lines_of(target)
        path = run_file(source)
        return _lines_of(path) if path else []

    def get(self, key, source):
        """Lines of the ds file key: b2time.nc, else the copy of source."""
        if key not in self.cache:
            lines = self.prof.from_file(key)
            self.cache[key] = lines if lines is not None else \
                self._copy(key, source)
        return self.cache[key]

    def coordinate(self, suffix):
        return self.get("ds" + suffix, "ds" + suffix)

    def target(self, suffix):
        return self.get("ds%sT" % suffix.upper(), "ds" + suffix.upper())

    def contact(self, suffix):
        return self.get("ds%sP" % suffix.upper(), "ds%sP" % suffix.upper())


def profile_lines(prof, areas, base, index, prefix, pr2fix, suffix, num,
                  end, contact=False):
    """The lines of a .last10 file (2d_profiles), the data of a 2dds
    curve: ds TAB value, or ds value for divided fluxes."""
    if index is None:
        values = prof.means(base, ":,%d:%d" % (num, end))
    else:
        values = prof.means(base, ":,%d,%d:%d" % (index, num, end))
    ds = areas.coordinate(suffix)
    flux = prefix == "f"
    if flux and contact:
        return divide(paste(ds, values, areas.contact(suffix)), prof.name)
    if flux and run_file("ds" + suffix.upper()):
        return divide(paste(ds, values, areas.target(suffix)), prof.name)
    if prefix == "t" and pr2fix != "p" and index is None:
        values = [awk_str(awk_num(v) / E_CHARGE) for v in values]
    return paste(ds, values)


def dds_curve(prof, areas, name, num, end):
    """(Trace, x, y) of one 2dds name, or None with a message."""
    base, index, prefix, pr2fix, suffix = split_name(name, prof.data)
    if base not in prof.data.variables:
        ncdata.warn(prof.name + ".py", "%s not in b2time.nc" % name)
        return None
    shape = prof.data.variables[base].shape
    if len(shape) != (2 if index is None else 3):
        ncdata.warn(prof.name + ".py", "%s: give a species index (%s0, "
                    "%s1, ...)" % (name, name, name) if index is None
                    else "%s: no species index for %s" % (name, base))
        return None
    lines = profile_lines(prof, areas, base, index, prefix, pr2fix, suffix,
                          num, end)
    contact = prefix == "f" and run_file("ds%sP" % suffix.upper())
    if contact:
        lines = profile_lines(prof, areas, base, index, prefix, pr2fix,
                              suffix, num, end, contact=True)
    rows = [l.split() for l in lines]
    rows = [r for r in rows if len(r) == 2]
    x = np.array([awk_num(r[0]) for r in rows])
    y = np.array([awk_num(r[1]) for r in rows])
    stem = base.split("3d")[0]
    species = (quantities.species_of(base, index - 1, prof.fluids,
                                     prof.neutrals)
               if index is not None else "")
    divided = prefix == "f" and bool(run_file("ds" + suffix.upper()))
    label = quantities.profile(stem, suffix, prof.config, species, divided,
                               getattr(prof.data.variables[base],
                                       "long_name", ""))
    return label, x, y, suffix


def dds_page(prof, names, num, end, logx=False, logy=False, title=None,
             tab="Profiles"):
    """One 2dds page: the names against the ds of the first one."""
    num, end = prof.window(1 + end - num, end)
    found = [c for c in (dds_curve(prof, Areas(prof), n, num, end)
                         for n in names) if c is not None]
    if not found:
        return None
    items = [(label, x, y) for label, x, y, _ in found]
    x0 = found[0][1]
    curves = [Curve(x0[:len(y)] if len(x0) >= len(y) else x[:len(x0)], y
                    if len(x0) >= len(y) else y[:len(x0)], legend)
              for (_, x, y), legend in zip(items, timetraces._legends(items))]
    xlabel = quantities.profile_xlabel(found[0][3])
    footer = "%s    %s    %s" % (helpers.chop_pwd(60), stamp(),
                                 prof.describe(num, end))
    return Page(tab, title or timetraces._title(items), xlabel,
                timetraces._ylabel(items), curves, logx=logx, logy=logy,
                footer=footer)


def dds_arguments(words):
    """Names and the trailing NUM [END] of 2dds (defaults 10 and 0)."""
    num, end = 10, 0
    if len(words) >= 2 and _NUMBER.match(words[-1]) \
            and _NUMBER.match(words[-2]):
        num, end, words = int(words[-2]), int(words[-1]), words[:-2]
    elif words and _NUMBER.match(words[-1]):
        num, words = int(words[-1]), words[:-1]
    return words, num, end


# .last10 files of 2d_profiles: by the ds files found in the run folder
_USUAL = {
    "l": ("ne te ti po an fe fi fc fl fo ft", "fn na"),
    "i": ("ne te ti po an ke ki", "na dn dp vx vy vs"),
    "a": ("ne te ti po an ke ki", "na dn dp vx vy vs"),
    "r": ("ne te ti po an fe fi fc fl fo ft", "fn na"),
}
_EXTRA = ("fe3dtl fi3dtl fc3dtl fl3dtl fo3dtl ft3dtl ne3dtl te3dtl ti3dtl "
          "po3dtl an3dtl ne3dtr te3dtr ti3dtr po3dtr an3dtr fe3dtr fi3dtr "
          "fc3dtr fl3dtr fo3dtr ft3dtr tp3dtl tp3dtr")
_EXTRA_MULTI = "fn3dtl na3dtl fn3dtr na3dtr"


def _nonempty(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def last10_names(nreg):
    """(single, multi) names of 2d_profiles: per ds file of the run folder
    (dsl, dsi, dsa, dsr), mn with fort.1, tl/tr for NREG 7 or 8."""
    single, multi = [], []
    fort1 = _nonempty("fort.1")
    for s in ("l", "i", "a", "r"):
        if _nonempty("ds" + s):
            single += [q + "3d" + s for q in _USUAL[s][0].split()]
            multi += [q + "3d" + s for q in _USUAL[s][1].split()]
            if fort1:
                single.append("mn3d" + s)
    if quantities.Configuration(nreg).n in (7, 8):
        single += _EXTRA.split()
        multi += _EXTRA_MULTI.split()
        if fort1:
            single += ["mn3dtl", "mn3dtr"]
    return single, multi


def write_last10(prof, nreg, num, end, folder):
    """The .last10 files of 2d_profiles in folder (and the ds copies)."""
    os.makedirs(folder, exist_ok=True)
    areas = Areas(prof, folder)
    single, multi = last10_names(nreg)
    ns = len(prof.data.dimensions["ns"]) if "ns" in prof.data.dimensions \
        else len(prof.fluids)
    for name in single + multi:
        if name not in prof.data.variables:
            continue
        base, _, prefix, pr2fix, suffix = split_name(name, prof.data)
        keys = [("ds" + suffix, areas.coordinate)]
        if suffix not in ("a", "i"):
            keys += [("ds%sT" % suffix.upper(), areas.target),
                     ("ds%sP" % suffix.upper(), areas.contact)]
        for key, get in keys:
            lines = get(suffix)
            if lines:
                with open(os.path.join(folder, key), "w") as out:
                    out.write("".join(l + "\n" for l in lines))
        flux = prefix == "f"
        indices = [None] if name in single else list(range(1, ns + 1))
        for index in indices:
            tag = "" if index is None else str(index - 1)
            outputs = [("", False)]
            if flux and run_file("ds%sP" % suffix.upper()):
                outputs.append(("P", True))
            for extra, contact in outputs:
                lines = profile_lines(prof, areas, base, index, prefix,
                                      pr2fix, suffix, num, end, contact)
                path = os.path.join(folder, "%s%s%s.last10"
                                    % (name, extra, tag))
                with open(path, "w") as out:
                    out.write("".join(l + "\n" for l in lines))


def species_groups(prof, location):
    """The species names of one profile location, grouped as 2d_profiles
    groups them (EIRENE atoms in coupled runs)."""
    data, names, k = prof.data, [], -1
    coupled = "dabsepm" in data.variables
    ns = len(data.dimensions["ns"]) if "ns" in data.dimensions else \
        len(prof.fluids)
    var = "na3d" + location
    for i in range(min(ns, len(prof.fluids))):
        if prof.fluids[i] in prof.neutrals:
            if coupled:
                k += 1
                names.append("dab3d%s%d" % (location, k))
            elif var in data.variables:
                names.append("%s%d" % (var, i))
        elif var in data.variables:
            names.append("%s%d" % (var, i))
    groups, start = [], 0
    for count in helpers.groups_species():
        groups.append(names[start:start + count])
        start += count
    return [g for g in groups if g]


def profile_pages(prof, nreg, num, end):
    """The pages of 2d_profiles (2dds calls), in its order."""
    c = prof.config
    spec = []
    for s in ("a", "l", "r"):
        where = quantities.profile_location(s, c)
        short = where[0].upper() + where[1:]
        spec.append((short + " ne", None, ["ne3d" + s]))
        for g in species_groups(prof, s):
            e = _element(prof, g)
            spec.append(("%s %s" % (short, e), "%s densities, %s" % (e, where),
                         g))
        spec.append((short + " T", "Temperatures, " + where,
                     ["te3d" + s, "ti3d" + s]))
    for s in ("l", "r"):
        where = quantities.profile_location(s, c)
        short = where[0].upper() + where[1:]
        spec.append((short + " ion flux", None, ["fo3d" + s]))
        spec.append((short + " energy flux", None, ["ft3d" + s]))
    if c.n in (7, 8):
        for s in ("tl", "tr"):
            where = quantities.profile_location(s, c)
            short = where[0].upper() + where[1:]
            spec.append((short + " ion flux", None, ["fo3d" + s]))
            spec.append((short + " energy flux", None, ["ft3d" + s]))
    pages = [dds_page(prof, names, num, end, title=title, tab=tab)
             for tab, title, names in spec]
    return [p for p in pages if p is not None]


def _element(prof, group):
    """Element of a group of profile species names (D for dab3da0 na3da1)."""
    m = re.match(r"^(.*?)([0-9]+)$", group[-1])
    pool = prof.neutrals if m.group(1).startswith("dab") else prof.fluids
    index = int(m.group(2))
    return re.sub(r"[+0-9].*$", "", pool[index]) if index < len(pool) else ""


_EXTENDED = {
    "l": "fn fe fi fc fl fo ft ne te ti po an tp",
    "i": "ne te ti po an dn dp ke ki vx vy vs",
    "a": "ne te ti po an dn dp ke ki vx vy vs",
    "r": "ne te ti po an fn fe fi fc fl fo ft tp",
}
_EXTENDED_EXTRA = ("fn3dtl fe3dtl fi3dtl fc3dtl fl3dtl fo3dtl ft3dtl ne3dtl "
                   "te3dtl ti3dtl po3dtl an3dtl ne3dtr te3dtr ti3dtr po3dtr "
                   "an3dtr fn3dtr fe3dtr fi3dtr fc3dtr fl3dtr fo3dtr ft3dtr "
                   "tp3dtl tp3dtr")


def write_extended(prof, nreg, num):
    """The .last10 files of 2d_profiles_extended in the run folder: run
    folder ds files only, the names read as one array each."""
    names = []
    fort1 = _nonempty("fort.1")
    for s in ("l", "i", "a", "r"):
        if _nonempty("ds" + s):
            names += [q + "3d" + s for q in _EXTENDED[s].split()]
            if fort1:
                names.append("mn3d" + s)
    if quantities.Configuration(nreg).n in (7, 8):
        names += _EXTENDED_EXTRA.split()
        if fort1:
            names += ["mn3dtl", "mn3dtr"]
    if prof.nt + num < 0:
        num = -prof.nt + 1
    for name in names:
        if name not in prof.data.variables:
            ncdata.warn(prof.name + ".py", "%s not in b2time.nc" % name)
            continue
        prefix, pr2fix, suffix = name[0:1], name[1:2], name[4:]
        ds_path = run_file("ds" + suffix)
        ds = _lines_of(ds_path) if ds_path else []
        values = prof.means(name, ":,%d:0" % num)
        big, big_p = run_file("ds" + suffix.upper()), \
            run_file("ds%sP" % suffix.upper())
        if prefix == "f" and big:
            lines = divide(paste(ds, values, _lines_of(big)), prof.name)
        elif prefix == "t" and pr2fix != "p":
            lines = paste(ds, [awk_str(awk_num(v) / E_CHARGE)
                               for v in values])
        else:
            lines = paste(ds, values)
        with open(name + ".last10", "w") as out:
            out.write("".join(l + "\n" for l in lines))
        if prefix == "f" and big_p:
            lines = divide(paste(ds, values, _lines_of(big_p)), prof.name)
            with open(name + "P.last10", "w") as out:
                out.write("".join(l + "\n" for l in lines))
