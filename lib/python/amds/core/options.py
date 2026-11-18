"""The command line and the resources of AMDS as the Motif version reads
them (XtAppInitialize, class AMDS): the options of the X toolkit and of
AMDS (amxapp.c) become resource entries of the program; then the
resource database in the order of the X toolkit, without an X server:
the fallback resources compiled into the library (only when there is no
application defaults file AMDS), the user application defaults, the user
defaults (~/.Xdefaults), the environment file (XENVIRONMENT, else
~/.Xdefaults-HOST), the command line."""

import os
import socket

from ...divgeo.core import options, resources

NOARG, SEPARG = options.NOARG, options.SEPARG

# The options of AMDS (amxapp.c, commandLineOptions)
AMDS_OPTIONS = (
    ("-help", "displayHelp", NOARG, "1"),
    ("/help", "displayHelp", NOARG, "1"),
    ("-h", "displayHelp", NOARG, "1"),
    ("/h", "displayHelp", NOARG, "1"),
    ("-?", "displayHelp", NOARG, "1"),
    ("/?", "displayHelp", NOARG, "1"),
    ("?", "displayHelp", NOARG, "1"),
    ("-nocfg", "loadConfig", NOARG, "0"),
    ("-cfg", "configFile", SEPARG, None),
    ("-nores", "checkResources", NOARG, "0"),
    ("-nohelp", "checkHelpFile", NOARG, "0"),
)

CLASS = "AMDS"

# Folders of the application defaults when XFILESEARCHPATH is not set
APP_DEFAULTS = ("/opt/local/lib/X11/app-defaults",
                "/opt/X11/lib/X11/app-defaults",
                "/usr/X11R6/lib/X11/app-defaults", "/usr/lib/X11/app-defaults",
                "/etc/X11/app-defaults", "/usr/share/X11/app-defaults")


def parse(argv):
    """(remaining argv with argv[0], program name, command line database)."""
    return options.parse(argv, AMDS_OPTIONS)


def _read(path):
    try:
        with open(path, encoding="latin-1") as f:
            return f.read()
    except OSError:
        return None


def _search_path(spec, name, kind):
    """The first readable file of an X search path (%N name, %T type, the
    language and suffix parts empty)."""
    for part in spec.split(":"):
        path = (part.replace("%N", name).replace("%T", kind)
                .replace("%L", "").replace("%l", "").replace("%C", "")
                .replace("%S", "").replace("%%", "%").replace("//", "/"))
        if path and os.path.isfile(path):
            return path
    return None


def _app_defaults():
    spec = os.environ.get("XFILESEARCHPATH")
    if spec:
        return _search_path(spec, CLASS, "app-defaults")
    for folder in APP_DEFAULTS:
        path = os.path.join(folder, CLASS)
        if os.path.isfile(path):
            return path
    return None


def _user_app_defaults():
    home = os.environ.get("HOME", "")
    spec = os.environ.get("XUSERFILESEARCHPATH")
    if spec:
        return _search_path(spec, CLASS, "app-defaults")
    folder = os.environ.get("XAPPLRESDIR")
    path = os.path.join(folder or home, CLASS)
    return path if os.path.isfile(path) else None


def database(fallback, cmdline):
    """The resource database of the program."""
    db = resources.Database()
    home = os.environ.get("HOME", "")
    path = _app_defaults()
    if path is None:
        for line in fallback:
            db.put_line(line)
    files = [path, _user_app_defaults(), os.path.join(home, ".Xdefaults"),
             os.environ.get("XENVIRONMENT") or
             os.path.join(home, ".Xdefaults-" + socket.gethostname())]
    for f in files:
        text = _read(f) if f else None
        if text is not None:
            db.put_text(text)
    db.merge(cmdline)
    return db
