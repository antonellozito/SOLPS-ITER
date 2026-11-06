"""2dt, 2dt_av, 2d, 2da, 2d_plots and 2d_plots_av: time traces of
b2time.nc (b2batch.nc for the averaged ones).

The pages carry the quantities of the old scripts, in the same order and
on linear axes unless -lx or -ly; species pages follow groups_species,
NREG and the species come from the helper scripts (helpers.py). Labels:
what all curves of a page share goes to the title, the rest to the
legend (quantities.Trace).
"""

import os
import sys

import numpy as np

from . import averaging, helpers, ncdata, quantities
from .pages import Curve, Page, stamp


class Traces:
    def __init__(self, name, avg, batch=False, path=None, nreg=None):
        self.name, self.avg = name, avg
        if path:
            import netCDF4
            self.data, self.timevar = netCDF4.Dataset(path), "timesa"
        else:
            self.data, self.timevar = ncdata.source(name, batch)
        self.batch = batch and self.timevar == "batchsa"
        self.fluids = helpers.solps_fluids()
        self.neutrals = helpers.neutral_names(self.fluids)
        if nreg is None:
            nreg = helpers.nreg_file()
        self.config = quantities.Configuration(nreg)
        if self.config.single_null() and self.data is not None:
            from . import geometry
            ref = (self.data if "cvlistl" in self.data.variables
                   else ncdata.open_file("b2time.nc"))
            self.config.swapped = geometry.first_target_outer(ref)

    def variable(self, name):
        """The name to read (the _av one in b2batch.nc), or None with a
        message when the file has neither."""
        if self.batch:
            name = ncdata.batch_name(self.data, name)
        if name in self.data.variables or ncdata.species_name(name,
                                                               self.data):
            return name
        ncdata.warn(self.name + ".py", "%s not in %s" % (
            name, os.path.basename(self.data.filepath())))
        return None

    def time(self):
        return np.asarray(self.data.variables[self.timevar][:], dtype=float)

    def items(self, names, x=None):
        """(Trace, x, y) for every row of the names, against time or x."""
        out = []
        t = self.time() if x is None else x
        for given in names:
            name = self.variable(given)
            if name is None:
                continue
            try:
                rows = ncdata.rows(self.data, name)
            except ValueError as err:
                ncdata.warn(self.name + ".py", str(err))
                continue
            found = ncdata.species_name(name, self.data)
            base, index = found if found else (name, None)
            species = (quantities.species_of(base, index, self.fluids,
                                             self.neutrals)
                       if found else "")
            long_name = getattr(self.data.variables[base], "long_name", "")
            for r, y in enumerate(rows):
                label = quantities.trace(base, self.config, r, len(rows),
                                         species, long_name)
                n = min(len(t), len(y))
                xs, ys = self._average(t[:n], y[:n], x is not None)
                out.append((label, xs, ys))
        return out

    def _average(self, x, y, both):
        if self.avg.rolling_n and both:
            return averaging.rolling(x, self.avg.rolling_n), \
                averaging.rolling(y, self.avg.rolling_n)
        return self.avg.apply(x, y)

    def footer(self, path):
        text = "%s    %s" % (path, stamp())
        if self.avg:
            text += "    " + self.avg.describe()
        if self.batch:
            text += "    b2batch.nc"
        return text


def _title(items):
    """Title from the label parts shared by all curves."""
    parts = [it[0].parts() for it in items]
    common = [p for k, p in enumerate(parts[0])
              if p and all(q[k] == p for q in parts)]
    return ", ".join(common) if common else "Time traces"


def _shared_words(texts):
    """Leading words that all texts share ("poloidal, into the" of
    "poloidal, into the inner target" and "... outer target")."""
    words = [t.split(" ") for t in texts]
    n = 0
    while all(len(w) > n + 1 for w in words) and \
            all(w[n] == words[0][n] for w in words):
        n += 1
    return n


def _legends(items):
    """Legend texts: the label parts that differ between the curves,
    without the leading words they all share."""
    parts = [it[0].parts() for it in items]
    if len(parts) == 1:
        return [""]
    vary = [k for k in range(3) if any(q[k] != parts[0][k] for q in parts)]
    for k in vary:
        n = _shared_words([p[k] for p in parts])
        for p in parts:
            p[k] = " ".join(p[k].split(" ")[n:])
    return [", ".join(p[k] for k in vary if p[k]) for p in parts]


def _ylabel(items):
    symbols, units = [], set()
    for trace, _, _ in items:
        if trace.symbol and trace.symbol not in symbols:
            symbols.append(trace.symbol)
        units.add(trace.unit)
    unit = units.pop() if len(units) == 1 else None
    if unit is None:
        return ""
    text = ", ".join(symbols)
    return "%s [%s]" % (text, unit) if unit else text


def page(traces, tab, names, title=None, xlabel="Time [s]", x=None,
         logx=False, logy=False, footer_path=None):
    items = traces.items(names, x)
    if not items:
        return None
    curves = [Curve(xs, ys, label)
              for (_, xs, ys), label in zip(items, _legends(items))]
    return Page(tab, title or _title(items), xlabel, _ylabel(items), curves,
                logx=logx, logy=logy,
                footer=traces.footer(footer_path or helpers.chop_pwd(60)))


def species_groups(traces, location):
    """The species names of one location, grouped as groups_species does:
    EIRENE atoms (dab) in coupled runs, fluid neutrals otherwise."""
    data, names, k = traces.data, [], -1
    coupled = "dabsepm" in data.variables or "dabsepm_av" in data.variables
    ns = len(data.dimensions["ns"]) if "ns" in data.dimensions else \
        len(traces.fluids)
    for i in range(min(ns, len(traces.fluids))):
        if traces.fluids[i] in traces.neutrals:
            if coupled:
                k += 1
                names.append("dabsep%s%d" % (location, k))
            elif "nasep" + location in data.variables or traces.batch:
                names.append("nasep%s%d" % (location, i))
        elif "nasep" + location in data.variables or traces.batch:
            names.append("nasep%s%d" % (location, i))
    groups, start = [], 0
    for count in helpers.groups_species():
        groups.append(names[start:start + count])
        start += count
    return [g for g in groups if g]


def _element(group, traces):
    """Element of a species group (D for D0 D+1): the species of its last
    name, an index into the species (nasep) or the neutrals (dabsep)."""
    import re
    m = re.match(r"^(.*?)([0-9]+)$", group[-1])
    pool = traces.neutrals if m.group(1).startswith("dab") else traces.fluids
    index = int(m.group(2))
    return re.sub(r"[+0-9].*$", "", pool[index]) if index < len(pool) else ""


def plots_pages(traces, nreg):
    """The pages of 2d_plots, in its order."""
    c = traces.config
    mid, ti, ta = c.midplane(), c.target("i"), c.target("a")
    spec = [("Midplane ne", None, ["nesepm"])]
    for g in species_groups(traces, "m"):
        e = _element(g, traces)
        spec.append(("Midplane %s" % e, "%s densities, separatrix, %s"
                     % (e, mid), g))
    spec += [("Midplane T", "Temperatures, separatrix, %s" % mid,
              ["tesepm", "tisepm"]),
             ("Target ne", "Electron density at the targets",
              ["nesepi", "nemxip", "nesepa", "nemxap"])]
    for loc, where in (("i", ti), ("a", ta)):
        for g in species_groups(traces, loc):
            e = _element(g, traces)
            spec.append(("%s %s" % (e, where), "%s densities, separatrix, %s"
                         % (e, where), g))
    spec += [("Target Te", "Electron temperature at the targets",
              ["tesepi", "temxip", "tesepa", "temxap"]),
             ("Target Ti", "Ion temperature at the targets",
              ["tisepi", "timxip", "tisepa", "timxap"]),
             ("Particle flux", "Poloidal particle flux into the targets",
              ["fnixip", "fnixap"]),
             ("Electron energy flux", "Poloidal electron energy flux into "
              "the targets", ["feexip", "feexap"]),
             ("Ion energy flux", "Poloidal ion energy flux into the targets",
              ["feixip", "feixap"])]
    n = quantities.Configuration(nreg).n
    radial = [("Radial particle flux", "Radial particle flux", "fniy"),
              ("Radial electron flux", "Radial electron energy flux", "feey"),
              ("Radial ion flux", "Radial ion energy flux", "feiy")]
    if n in (4, 5, 7, 8):
        spec += [(t, h, [v + "ip", v + "ap"]) for t, h, v in radial]
    elif n in (1, 2):
        spec += [(t, h, [v + "ip"]) for t, h, v in radial]
    else:
        print("Unusual number of regions: Not sure what to do!")
        print("NREG = ", nreg)
    spec += [("Peak power flux", "Maximum total power flux density on the "
              "targets", ["pwmxip", "pwmxap"]),
             ("Particles", None, ["tmne"]),
             ("Energy content", "Total electron and ion energy",
              ["tmte", "tmti"])]
    pages = [page(traces, tab, names, title) for tab, title, names in spec]
    return [p for p in pages if p is not None]


def table(traces, arguments):
    """The text of 2da: a column per row of each argument."""
    lines, header = [], ""
    for arg in arguments:
        if "(" in arg:
            if traces.avg:
                ncdata.warn(traces.name + ".py", "%s: no averaging of an "
                            "index expression" % arg)
            try:
                lines += ncdata.transpose(ncdata.nc2text(traces.data, arg))
            except (KeyError, IndexError, ValueError) as err:
                ncdata.warn(traces.name + ".py", "%s: %s" % (arg, err))
                continue
            header += " " + arg
            continue
        name = traces.variable(arg)
        if name is None:
            continue
        rows = ncdata.rows(traces.data, name)
        found = ncdata.species_name(name, traces.data)
        label = name
        if found:
            label = "%s(%s)" % (found[0], (traces.neutrals if found[0][:3] in
                                           ("dab", "dmb", "tab", "tmb")
                                           else traces.fluids)[found[1]])
        if traces.avg or found:
            t = traces.time()
            for y in rows:
                n = min(len(t), len(y))
                _, ys = traces.avg.apply(t[:n], y[:n])
                lines.append("".join("%18s" % ncdata.fortran_e(v)
                                     for v in ys))
        elif name.startswith("tm") and not name.startswith("tmb"):
            lines += ncdata.nc2text(traces.data, name)
        else:
            lines += ncdata.transpose(ncdata.nc2text(traces.data, name))
        if len(rows) == 1:
            header += " " + label
        else:
            header += "".join(" %s.%d" % (label, k)
                              for k in range(1, len(rows) + 1))
    print("# " + header)
    for line in ncdata.transpose(lines):
        print(line)
    return 0


def names_of(arguments):
    """The names of the calls, also several in one argument (2dt.py
    "nesepm tesepm")."""
    return [n for a in arguments for n in a.split()]
