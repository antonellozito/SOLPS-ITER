"""The preferences file of DivGeo (x_xapp.c): $DG_PREFS_FILE, else
$HOME/.dg-preferences, none with $DG_NO_PREFS_FILE; lines key=value, the
whole file written again on every change; and the list of recent files.

The file is read and written byte for byte as the Motif version does
(lines read in pieces of at most 1022 bytes, empty lines dropped when the
file is written again)."""

import os

from . import api, resources

PSTR_RECENTFILES_COUNT = "DG.RecentFilesCount"
PSTR_RECENTFILES_PREFIX = "DG.RecentFile_"
PSTR_AUTOSAVE_INTERVAL = "DG.AutosaveInterval"


def file_name():
    """GetUserPrefsFileName: None when there is no preferences file."""
    if os.environ.get("DG_NO_PREFS_FILE") is not None:
        return None
    s = os.environ.get("DG_PREFS_FILE")
    if s is not None:
        return s
    home = os.environ.get("HOME")
    if not home:
        return False
    home = home[:1024 - 100]
    if not home.endswith("/"):
        home += "/"
    return home + ".dg-preferences"


def _fgets_lines(data):
    """The pieces fgets(buf, 1023) reads: up to a newline or 1022 bytes."""
    k = 0
    n = len(data)
    while k < n:
        end = data.find(b"\n", k, k + 1022)
        if end < 0:
            piece = data[k:k + 1022]
        else:
            piece = data[k:end + 1]
        yield piece
        k += len(piece)


def get_string(lib, key):
    """GetUserPrefsString ("" when not found)."""
    fn = file_name()
    if fn is False:
        lib.dll.PyFatalError(b"The $HOME variable cannot be read")
    if fn is None:
        return ""
    try:
        with open(fn, "rb") as f:
            data = f.read()
    except OSError:
        return ""
    prefix = (key[:1022] + "=").encode("latin-1")
    for piece in _fgets_lines(data):
        if piece.startswith(prefix):
            if piece.endswith(b"\n"):
                piece = piece[:-1]
            return piece[len(prefix):].split(b"\0")[0].decode("latin-1")
    return ""


def set_string(lib, key, value):
    """SetUserPrefsString: 0, or the error code of the core."""
    if value is None:
        value = ""
    fn = file_name()
    if fn is False:
        lib.dll.PyFatalError(b"The $HOME variable cannot be read")
    if fn is None:
        return api.ERR_NOPREFS
    try:
        with open(fn, "rb") as f:
            old = f.read()
    except OSError:
        old = None
    try:
        f = open(fn, "wb")
    except OSError:
        return api.ERR_FWRITE
    prefix = (key[:1022] + "=").encode("latin-1")
    with f:
        if old is not None:
            for line in old.split(b"\0")[0].split(b"\n"):
                if line and not line.startswith(prefix):
                    f.write(line + b"\n")
        if value:
            f.write(prefix + value.encode("latin-1") + b"\n")
    return 0


def get_int(lib, key):
    """GetUserPrefsInt (atol)."""
    s = get_string(lib, key).lstrip(" \t\n\r\f\v")
    sign = 1
    if s[:1] in ("+", "-"):
        sign = -1 if s[0] == "-" else 1
        s = s[1:]
    n = 0
    while n < len(s) and s[n] in "0123456789":
        n += 1
    return sign * int(s[:n]) if n else 0


def set_int(lib, key, value):
    return set_string(lib, key, "%d" % value)


def recent_files(lib):
    """GetRecentFilesStack: the recent files, the latest first."""
    out = []
    count = get_int(lib, PSTR_RECENTFILES_COUNT)
    i = 0
    while i < count:
        s = get_string(lib, "%s%d" % (PSTR_RECENTFILES_PREFIX, i))
        i += 1
        if not s:
            break
        out.append(s)
    return out


def add_recent_file(application, name):
    """AddXAppRecentFile: the file first in the list, the list written with
    at most recentFilesCount entries, the views notified."""
    lib = application.lib
    files = [s for s in recent_files(lib) if s != name]
    files.insert(0, name)
    value = application.app_resource("recentFilesCount")
    count = resources.to_int(value) if value is not None else None
    if count is None:
        count = 4
    i = 0
    for s in files[:max(count, 0)]:
        set_string(lib, "%s%d" % (PSTR_RECENTFILES_PREFIX, i), s)
        i += 1
    set_int(lib, PSTR_RECENTFILES_COUNT, i)
    for w in application.windows:
        if w.view is not None:
            w.notify_view(api.N_RECENTFILES)

