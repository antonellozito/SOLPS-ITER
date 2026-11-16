"""X resources as the Motif DivGeo reads them: a resource database with the
syntax and the matching rules of the X resource manager, and the conversions
of the X toolkit for the types DivGeo uses.

The database holds entries "binding component binding component ...: value"
(binding "." tight or "*" loose, component a name, a class or "?"). A query
gives the names and the classes of a widget path down to the resource; of
the entries that match, the most specific one wins, compared level by level
from the left: a matched level beats a skipped one, a name beats a class
beats "?", and a tight binding beats a loose one.
"""

import re

from . import xcms, xcolors

_NAME = re.compile(r"[A-Za-z0-9_\-?]+")


def _parse_value(text):
    """The value of a resource line with the escapes of the X resource
    manager: \\n, \\\\, \\ followed by space or tab, octal \\nnn, and a
    backslash at the end of a line continuing it."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            break
        if c != "\\" or i + 1 >= n:
            out.append(c)
            i += 1
            continue
        d = text[i + 1]
        if d == "\n":
            i += 2
        elif d == "n":
            out.append("\n")
            i += 2
        elif d == "\\":
            out.append("\\")
            i += 2
        elif d in " \t":
            out.append(d)
            i += 2
        elif (d in "01234567" and i + 3 < n and text[i + 2] in "01234567"
              and text[i + 3] in "01234567"):
            out.append(chr(int(text[i + 1:i + 4], 8) & 255))
            i += 4
        else:
            out.append("\\")
            i += 1
    return "".join(out)


def _parse_spec(spec):
    """Components of a resource specification as (tight, component) pairs,
    None if the specification is not valid."""
    comps = []
    i = 0
    n = len(spec)
    tight = True
    while i < n:
        if spec[i] in ".*":
            loose = False
            while i < n and spec[i] in ".*":
                loose = loose or spec[i] == "*"
                i += 1
            tight = not loose
            continue
        m = _NAME.match(spec, i)
        if m is None:
            return None
        comps.append((tight, m.group(0)))
        tight = True
        i = m.end()
    if not comps or comps[-1][1] == "?":
        return None
    return tuple(comps)


class Database:
    """Resource database: entries keyed by their specification, so that a
    later entry with the same specification replaces an earlier one (as
    the X resource manager merges databases)."""

    def __init__(self):
        self.entries = {}
        self.by_last = {}

    def put(self, comps, value):
        if comps not in self.entries:
            self.by_last.setdefault(comps[-1][1], []).append(comps)
        self.entries[comps] = value

    def put_line(self, line):
        """One resource line ("name: value"); comments ("!"), directives
        ("#") and lines without a colon are ignored."""
        i = 0
        while i < len(line) and line[i] in " \t":
            i += 1
        if i >= len(line) or line[i] in "!#\n":
            return
        colon = line.find(":", i)
        if colon < 0:
            return
        comps = _parse_spec(line[i:colon].rstrip(" \t"))
        if comps is None:
            return
        j = colon + 1
        while j < len(line) and line[j] in " \t":
            j += 1
        self.put(comps, _parse_value(line[j:]))

    def put_text(self, text):
        """A resource file: lines, with a backslash at the end of a line
        continuing it."""
        lines = []
        cur = ""
        for line in text.split("\n"):
            if line.endswith("\\") and not line.endswith("\\\\"):
                cur += line[:-1]
                continue
            lines.append(cur + line)
            cur = ""
        if cur:
            lines.append(cur)
        for line in lines:
            self.put_line(line)

    def merge(self, other):
        for comps, value in other.entries.items():
            self.put(comps, value)

    def get(self, names, classes):
        """Value of the most specific matching entry, None if no entry
        matches. names and classes: lists of the same length, the last
        element the resource."""
        best = None
        best_value = None
        n = len(names)
        candidates = (self.by_last.get(names[-1], [])
                      + (self.by_last.get(classes[-1], [])
                         if classes[-1] != names[-1] else [])
                      )
        for comps in candidates:
            score = _match(comps, names, classes, n)
            if score is not None and (best is None or score > best):
                best = score
                best_value = self.entries[comps]
        return best_value


def _match(comps, names, classes, n):
    """Score of the best way comps matches the levels (None: no match): per
    level (3 name, 2 class, 1 "?", 0 skipped; 1 tight, 0 loose)."""
    m = len(comps)
    memo = {}

    def level(c, k):
        comp = comps[c][1]
        if comp == names[k]:
            return 3
        if comp == classes[k]:
            return 2
        if comp == "?":
            return 1
        return 0

    def best(c, k):
        key = (c, k)
        if key in memo:
            return memo[key]
        result = None
        if c == m:
            result = () if k == n else None
        elif k < n and n - k >= m - c:
            tight = comps[c][0]
            kind = level(c, k)
            if kind:
                rest = best(c + 1, k + 1)
                if rest is not None:
                    result = ((kind, 1 if tight else 0),) + rest
            if not tight:
                rest = best(c, k + 1)
                if rest is not None:
                    skipped = ((0, 0),) + rest
                    if result is None or skipped > result:
                        result = skipped
        memo[key] = result
        return result

    return best(0, 0)


# Conversions of the X toolkit ##############################################

def to_int(text):
    """Integer as the X toolkit converts it (sign, digits, blanks around);
    None if the text is not an integer."""
    m = re.match(r"^[ \t]*([+-]?)([0-9]+)[ \t]*$", text)
    if m is None:
        return None
    value = int(m.group(2))
    return -value if m.group(1) == "-" else value


def to_bool(text):
    """Boolean as the X toolkit converts it; None if not a boolean."""
    t = text.strip().lower()
    if t in ("true", "yes", "on"):
        return True
    if t in ("false", "no", "off"):
        return False
    value = to_int(text)
    if value is not None:
        return value != 0
    return None


def _scale16(digits):
    """Hex digits of an rgb: colour scaled to 16 bits."""
    return int(int(digits, 16) * 65535 / (16 ** len(digits) - 1) + 0.5)


def to_pixel(text):
    """Pixel 0xRRGGBB of a colour on a 24-bit display, as the X server
    allocates it: colour names, #RGB forms, rgb: and RGBi: specifications;
    None if the colour is not known."""
    t = text.strip()
    low = t.lower()
    if low in xcolors.NAMES:
        return xcolors.NAMES[low]
    if low == "xtdefaultforeground":
        return 0x000000
    if low == "xtdefaultbackground":
        return 0xffffff
    m = re.match(r"^#([0-9a-f]+)$", low)
    if m and len(m.group(1)) in (3, 6, 9, 12):
        k = len(m.group(1)) // 3
        parts = [m.group(1)[i * k:(i + 1) * k] for i in range(3)]
        values = [int(p, 16) << (16 - 4 * k) for p in parts]
        return _pack(values)
    m = re.match(r"^rgb:([0-9a-f]{1,4})/([0-9a-f]{1,4})/([0-9a-f]{1,4})$",
                 low)
    if m:
        return _pack([_scale16(g) for g in m.groups()])
    m = re.match(r"^rgbi:\s*([^/]+)/([^/]+)/([^/]+)$", low)
    if m:
        try:
            values = [float(g) for g in m.groups()]
        except ValueError:
            return None
        if any(v < 0 or v > 1 for v in values):
            return None
        r, g, b = (xcms.channel(k, v) for k, v in enumerate(values))
        return (r << 16) | (g << 8) | b
    return None


def _pack(values16):
    r, g, b = (v >> 8 for v in values16)
    return (r << 16) | (g << 8) | b
