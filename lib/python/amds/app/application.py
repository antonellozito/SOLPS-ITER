"""AMDS with the Python interface: the start (ammain.c), the XApp with the
checks of the Motif front end (amxapp.c, CreateXApp), the views and the
notifications of the core.

The resources are those the Motif version reads (core/options.py): the
fallback resources compiled into the library (x_~fbr.c), the user
resource files, the command line."""

import ctypes
import os
import sys
import traceback

from PySide6 import QtWidgets

from ...b2viewer import scaling
from ...divgeo.core import resources
from ...divgeo.view import themes
from ..core import api, lib as corelib, options
from . import window

ENV_DBFILE = "AMDSDATABASEFILE"
ENV_CFGFILE = "AMDSCONFIGFILE"
VERSION = 104
USAGE = ("Atomic & Molecular Data Selector v%g\n"
         "Syntax: amds [-help] [-nocfg] [<file.amd>] [<file.amd>] ...\n"
         "  -help          Display this help text\n"
         "  -nocfg         Do not load configuration\n"
         "  <file.amd>     AMD files to load. If none specified, a new "
         "document\n"
         "                 will be displayed.\n"
         "amds is an X Windows application. A proper DISPLAY setting may "
         "be needed\n")


def out(fd, text):
    """Text on standard output (1) or error (2) in order with what the C
    library of the core has buffered (printf of the core)."""
    sys.stdout.flush()
    sys.stderr.flush()
    ctypes.CDLL(None).fflush(None)
    os.write(fd, text.encode("latin-1"))


class Application:
    def __init__(self, library, argv):
        self.lib = library
        self.dll = library.dll
        rest, self.name, cmdline = options.parse(list(argv))
        self.db = options.database(library.resources(), cmdline)
        self.argv = rest
        self.windows = {}           # View address -> window
        self.order = []             # windows in the order of creation
        self._procs = (api.NOTIFYPROC(self._notify),
                       api.VIEWPROC(self._free_view),
                       api.VIEWPROC(self._unsaved),
                       api.EXITPROC(self.exit))
        self.dll.SetPyProcs(*self._procs)
        # the look of b2viewer, in the theme of the resource theme
        qt = QtWidgets.QApplication.instance()
        themes.install_style(qt)
        scaling.guard_wheel(qt)
        start = (self.app_resource("theme", "Theme") or "light").strip()
        self.set_theme(start.lower() if start.lower() in themes.NAMES
                       else "light")

    def set_theme(self, name):
        """Options > Theme (the Python interface only): every window in
        the theme; in the classic one the menu bars and the lists in the
        colours of the resources."""
        self.theme = name
        themes.current = name
        sheet = themes.stylesheet(name, self.db, self.name, options.CLASS)
        if name == "classic":
            value = self.db.get([self.name, "primaryShell", "main", "listSW",
                                 "list", "background"],
                                [options.CLASS, "ApplicationShell",
                                 "XmMainWindow", "XmScrolledWindow",
                                 "XmList", "Background"])
            pixel = resources.to_pixel(value) if value else None
            if pixel is not None:
                sheet += "QListWidget#list { background-color: #%06x; }\n" \
                    % pixel
        QtWidgets.QApplication.instance().setStyleSheet(sheet)
        for w in self.order:
            if not w.freed:
                w.check_theme(name)

    # Resources of the application shell (GetResource* on xap->wShell)

    def app_resource(self, name, cls):
        return self.db.get([self.name, name], [options.CLASS, cls])

    def app_int(self, name, cls, default):
        value = self.app_resource(name, cls)
        return default if value is None else resources.to_int(value)

    def app_string(self, name, cls, default):
        value = self.app_resource(name, cls)
        return default if value is None else value

    # The start (CreateXApp, main)

    def exit(self, code):
        """exit() of the Motif program: everything written, then the end."""
        self.lib.exit(code)

    def create_xapp(self):
        dll = self.dll
        lib = self.lib
        if self.app_int("displayHelp", "DisplayHelp", 0):
            out(1, USAGE % (VERSION / 100.))
            self.exit(10)
        argc = len(self.argv)
        self._argc = ctypes.c_int(argc)
        self._argv = (ctypes.c_char_p * (argc + 1))(
            *[corelib.cstr(a) for a in self.argv] + [None])
        xap = dll.PyCreateXApp(ctypes.byref(self._argc), self._argv)
        self.xap = xap
        if self.app_int("checkResources", "CheckResources", 1):
            i = self.app_int("resourceFileVersion", "ResourceFileVersion", 0)
            if i != VERSION:
                out(2, "amds: Bad resource file version\n"
                       "amds version:           %g\n"
                       "Resource file version: %g\n" % (VERSION / 100.,
                                                        i / 100.))
                self.exit(1)
        s = os.environ.get(ENV_DBFILE, "")
        if not s:
            s = self.app_string("databaseFile", "DatabaseFile", "")
        if not s:
            s = self.argv[0] + ".rpd"
        lib.set(xap, "XApp.db", dll.CreateDatabase(corelib.cstr(s)))
        if self.app_int("loadConfig", "LoadConfig", 1):
            ps = os.environ.get(ENV_CFGFILE)
            if ps is None:
                ps = self.app_string("configFile", "ConfigFile", "")
                if not ps:
                    ps = self.argv[0] + ".rpc"
            config = dll.CreateDoc(lib.get(xap, "XApp.db"))
            lib.set(xap, "XApp.config", config)
            if dll.LoadDoc(config, corelib.cstr(ps)):
                out(2, "amds: Error reading configuration from %s\n" % ps)
                self.exit(1)
        else:
            lib.set(xap, "XApp.config", None)
        lib.set(xap, "XApp.clipboard",
                dll.CreateDoc(lib.get(xap, "XApp.db")))

    def start(self):
        """main of ammain.c."""
        dll = self.dll
        lib = self.lib
        self.create_xapp()
        xap = self.xap
        files = self.argv[1:]
        for name in files:
            d = dll.CreateDoc(lib.get(xap, "XApp.db"))
            if dll.LoadDoc(d, corelib.cstr(name)):
                dll.FreeDoc(d)
                out(2, "amds: Error loading %s\n" % name)
                self.exit(1)
            config = lib.get(xap, "XApp.config")
            if config:
                dll.UpdateVarDefs(d, config)
            self.create_view(d, None)
        if not files:
            self.new_view()

    # Views

    def create_view(self, doc, main_view):
        """CreateView: a main window (main_view None) or a subset window."""
        w = window.ViewWindow(self, doc, main_view)
        return w

    def new_view(self):
        """NewView."""
        d = self.dll.PyNewViewDoc(self.xap)
        return self.create_view(d, None)

    def window_of(self, view):
        return self.windows.get(view)

    def register(self, w):
        self.windows[w.view] = w
        self.order.append(w)

    # Callbacks of the library

    def _guard(self, f, *args):
        try:
            f(*args)
        except Exception:
            traceback.print_exc()

    def _notify(self, view, msg, obj):
        w = self.windows.get(view)
        if w is not None:
            self._guard(w.notify, msg, obj)

    def _free_view(self, view):
        w = self.windows.pop(view, None)
        if w is not None:
            self._guard(w.free)

    def _unsaved(self, view):
        from ..dialogs import files
        w = self.windows.get(view)
        if w is not None:
            self._guard(files.open_file_unsaved_dlg, w)


def main(argv, library_path=None):
    """Runs AMDS: argv as the command line of the Motif program."""
    path = library_path or corelib.default_path()
    if library_path is None:
        found = corelib.build_problems(path)
    else:
        found = [] if os.path.exists(path) else [path + " not found"]
    if found:
        for line in found:
            sys.stderr.write("amds: " + line + "\n")
        return 2
    qt = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
        ["amds"])
    qt.setQuitOnLastWindowClosed(False)
    application = Application(corelib.Library(path), argv)
    application.start()
    return qt.exec()
