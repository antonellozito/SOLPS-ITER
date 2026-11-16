"""The command line of DivGeo as the Motif version reads it: the options
of the X toolkit and of DivGeo become resource entries of the program (its
name: -name, else RESOURCE_NAME, else the file name of argv[0]); the other
words stay as the files to open.

An option may be given by any prefix that is not the prefix of another
option; an exact name always wins."""

import os

from . import resources

NOARG, SEPARG, RESARG = 0, 1, 2

# The options of the X toolkit (XtOpenApplication)
XT_OPTIONS = (
    ("+rv", "*reverseVideo", NOARG, "off"),
    ("+synchronous", "*synchronous", NOARG, "off"),
    ("-background", "*background", SEPARG, None),
    ("-bd", "*borderColor", SEPARG, None),
    ("-bg", "*background", SEPARG, None),
    ("-bordercolor", "*borderColor", SEPARG, None),
    ("-borderwidth", ".borderWidth", SEPARG, None),
    ("-bw", ".borderWidth", SEPARG, None),
    ("-display", ".display", SEPARG, None),
    ("-fg", "*foreground", SEPARG, None),
    ("-fn", "*font", SEPARG, None),
    ("-font", "*font", SEPARG, None),
    ("-foreground", "*foreground", SEPARG, None),
    ("-geometry", ".geometry", SEPARG, None),
    ("-iconic", ".iconic", NOARG, "on"),
    ("-name", ".name", SEPARG, None),
    ("-reverse", "*reverseVideo", NOARG, "on"),
    ("-rv", "*reverseVideo", NOARG, "on"),
    ("-selectionTimeout", ".selectionTimeout", SEPARG, None),
    ("-synchronous", "*synchronous", NOARG, "on"),
    ("-title", ".title", SEPARG, None),
    ("-xnllanguage", ".xnlLanguage", SEPARG, None),
    ("-xrm", None, RESARG, None),
    ("-xtsessionID", ".sessionID", SEPARG, None),
)

# The options of DivGeo (x_xapp.c, commandLineOptions)
DG_OPTIONS = (
    ("--help", "displayHelp", NOARG, "1"),
    ("-help", "displayHelp", NOARG, "1"),
    ("/help", "displayHelp", NOARG, "1"),
    ("-h", "displayHelp", NOARG, "1"),
    ("/h", "displayHelp", NOARG, "1"),
    ("-?", "displayHelp", NOARG, "1"),
    ("/?", "displayHelp", NOARG, "1"),
    ("?", "displayHelp", NOARG, "1"),
    ("-nocfg", "loadConfig", NOARG, "0"),
    ("-cfg", "configFileName", SEPARG, None),
    ("-wid", "embedWID", SEPARG, None),
    ("-nores", "checkResources", NOARG, "0"),
    ("-nohelp", "checkHelpFile", NOARG, "0"),
)


def _table():
    """The options of the toolkit, replaced by those of DivGeo with the same
    name."""
    table = dict((o[0], o) for o in XT_OPTIONS)
    for o in DG_OPTIONS:
        table[o[0]] = o
    return table


def _find(word, table):
    if word in table:
        return table[word]
    found = [name for name in table if name.startswith(word) and word]
    if len(found) == 1:
        return table[found[0]]
    return None


def app_name(argv):
    """Name of the program for its resources."""
    for k, word in enumerate(argv[1:-1], 1):
        if word == "-name":
            return argv[k + 1]
    if os.environ.get("RESOURCE_NAME"):
        return os.environ["RESOURCE_NAME"]
    return os.path.basename(argv[0])


def parse(argv):
    """(remaining argv with argv[0], name, resource database of the
    command line)."""
    name = app_name(argv)
    table = _table()
    db = resources.Database()
    rest = [argv[0]]
    k = 1
    while k < len(argv):
        word = argv[k]
        opt = _find(word, table)
        if opt is None:
            rest.append(word)
            k += 1
            continue
        _, spec, kind, value = opt
        if kind == NOARG:
            db.put_line("%s%s%s: %s" % (name, "" if spec[0] in ".*" else ".",
                                        spec, value))
            k += 1
        elif k + 1 < len(argv):
            if kind == RESARG:
                db.put_line(argv[k + 1])
            else:
                db.put_line("%s%s%s:%s" % (name, "" if spec[0] in ".*"
                                           else ".", spec,
                                           _escape(argv[k + 1])))
            k += 2
        else:
            rest.append(word)
            k += 1
    return rest, name, db


def _escape(value):
    """A value as a resource line keeps it: leading blanks, newlines and
    backslashes escaped."""
    out = value.replace("\\", "\\\\").replace("\n", "\\n")
    if out[:1] in (" ", "\t"):
        out = "\\" + out
    return out


def strtol(text):
    """The integer of a text as C strtol with base 0 reads it (0 when there
    is none)."""
    t = text.lstrip(" \t\n\r\f\v")
    sign = 1
    if t[:1] in ("+", "-"):
        sign = -1 if t[0] == "-" else 1
        t = t[1:]
    if t[:2].lower() == "0x" and t[2:3].lower() in "0123456789abcdef" \
            and t[2:3]:
        digits, base = t[2:], 16
    elif t[:1] == "0":
        digits, base = t, 8
    else:
        digits, base = t, 10
    valid = "0123456789abcdef"[:base]
    n = 0
    while n < len(digits) and digits[n].lower() in valid:
        n += 1
    return sign * int(digits[:n], base) if n else 0
