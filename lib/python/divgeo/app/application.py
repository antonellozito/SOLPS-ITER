"""DivGeo with the Python interface: the start (x_main.c), the XApp with
the checks of the Motif front end (x_xapp.c, ConfigureXApp), the views.

The resources are those the Motif version reads: the fallback resources
compiled into the library (x_~fbr.c), then the command line."""

import ctypes
import os
import sys

from PySide6 import QtWidgets

from ..core import api, lib as corelib, options, prefs, resources
from ..view import records
from . import window

USAGE = ("DivGeo version %s\n"
         "Usage: %s [-display [Host]{:Number}] [-nores] [-nocfg] [-nohelp]"
         " [-cfg CfgFile] [filename] ...\n"
         "-display      Specifies display to use\n"
         "-wid          Embed first DivGeo view into window ID\n"
         "-nores        Do not check resource file version\n"
         "-nocfg        Do not load configuration file\n"
         "-cfg          Specifies configuration file\n"
         "-nohelp       Do not require the help file\n"
         "filename...   Files to load\n\n"
         "Default configuration file is %s\n")


class Application:
    def __init__(self, library, argv, qt_app=None):
        self.lib = library
        self.dll = library.dll
        self.qt = qt_app or QtWidgets.QApplication.instance() or \
            QtWidgets.QApplication(["DivGeo"])
        rest, self.name, cmdline = options.parse(list(argv))
        self.db = resources.Database()
        for line in library.resources():
            self.db.put_line(line)
        self.db.merge(cmdline)
        self.argv = rest
        self.pump = records.Pump(library)
        self.windows = []
        self.help_text = None
        self.geometry = self._geometry()
        self.canvas_size = None
        self.wid = 0

    # Resources of the program (application resources of the Motif shell)

    def app_resource(self, name, cls=None):
        return self.db.get([self.name, name], ["DivGeo", cls or name])

    def _app_int(self, name, cls, default):
        value = self.app_resource(name, cls)
        number = resources.to_int(value) if value is not None else None
        return default if number is None else number

    def _geometry(self):
        value = self.db.get(["DivGeo", "geometry"], ["DivGeo", "Geometry"])
        try:
            w, h = value.lower().split("+")[0].split("-")[0].split("x")
            return int(w), int(h)
        except (AttributeError, ValueError):
            return 700, 400

    def _install_strings(self):
        """The values of the core messages (XAppGetStringProc)."""
        for k in range(self.dll.GetPyMsgCount()):
            name = self.dll.GetPyMsgName(k).decode("latin-1")
            if name.startswith("\r"):
                continue
            value = self.db.get([self.name, name], ["DivGeo", "DivGeoMsg"])
            if value is not None:
                self.dll.SetPyMsgValue(k, corelib.cstr(value))

    def _configure(self, xap):
        """End of ConfigureXApp: usage, resource version, help file."""
        if self._app_int("displayHelp", "DisplayHelp", 0):
            cfg = self.lib.string_at(self.lib.get(xap, "XApp.configFileName"))
            version = self.lib.string_at(self.dll.GetPyVersionStr(
                self.dll.GetPyVersion()))
            sys.stdout.flush()
            sys.stderr.write(USAGE % (version, os.path.basename(
                self.argv[0]), cfg))
            sys.stderr.flush()
            os._exit(10)
        if self._app_int("checkResources", "CheckResources", 1):
            found = self._app_int("resourceFileVersion",
                                  "ResourceFileVersion", -1)
            if found < 0:
                self.dll.PyFatalError(b"DivGeo: no resources")
            elif found != self.dll.GetPyVersion():
                self.dll.PyFatalError2(
                    b"DivGeo: invalid resource file version\n"
                    b"DivGeo version:        %s\n"
                    b"Resource file version: %s\n",
                    ctypes.string_at(self.dll.GetPyVersionStr(
                        self.dll.GetPyVersion())),
                    ctypes.string_at(self.dll.GetPyVersionStr(found)))
        help_name = self.lib.string_at(self.dll.GetPyHelpFileName(xap))
        try:
            with open(help_name, "rb") as f:
                self.help_text = f.read().decode("latin-1")
        except OSError:
            if self._app_int("checkHelpFile", "CheckHelpFile", 1):
                self.dll.PyFatalError(b"\rDivGeo: error opening help file\n")

    # Start (x_main.c) ######################################################

    def start(self):
        dll = self.dll
        cfg = self.app_resource("configFileName") or ""
        load_cfg = self._app_int("loadConfig", "LoadConfig", 1)
        self.wid = options.strtol(self.app_resource("embedWID") or "")
        dll.SetPyXAppConfig(corelib.cstr(cfg), load_cfg, self.wid)
        self._install_strings()
        self._configure_proc = api.CONFIGUREPROC(self._configure)
        dll.SetPyConfigureProc(self._configure_proc)

        self._argc = ctypes.c_int(len(self.argv))
        self._argv = (ctypes.c_char_p * (len(self.argv) + 1))(
            *[corelib.cstr(a) for a in self.argv], None)
        self.xap = dll.CreateXApp(ctypes.byref(self._argc), self._argv)

        a = dll.AddApp(self.xap)
        if not a:
            sys.stderr.write("Error opening configuration file")
            sys.stderr.flush()
            os._exit(1)
        files = self.argv[1:]
        if not files:
            self.create_view(a)
            dll.FreeUndoInfo(a)
        else:
            dll.FreeApp(a)
            for name in files:
                msg = ctypes.c_void_p()
                err = ctypes.c_int()
                a = dll.LoadNormalApp(self.xap, corelib.cstr(name),
                                      ctypes.byref(msg), ctypes.byref(err))
                if err.value != 0:
                    sys.stderr.write("%s:\n" % name)
                    sys.stderr.write("%s\n" % self.lib.string_at(
                        dll.XAppStr(self.xap, err.value)))
                    sys.stderr.flush()
                    os._exit(1)
                if msg.value:
                    sys.stdout.write(self.lib.string_at(msg.value) + "\n")
                    sys.stdout.flush()
                    dll.Free(msg.value)
                self.create_view(a)
                dll.FreeUndoInfo(a)
                self.pump.process()
                if a:
                    fname = self.lib.get(a, "App.fName")
                    prefs.add_recent_file(self, self.lib.string_at(fname))

        w = self.windows[-1]
        self.new_prefs_file(w)
        self.new_version(w)

    # Start checks of the preferences file (x_verdlg.c) #####################

    def new_prefs_file(self, w):
        """OpenNewPrefsFileDlg(w, True)."""
        lib = self.lib
        if prefs.get_string(lib, "DG.Signature") == "XDivGeo":
            return
        prefs.set_string(lib, "DG.Signature", "XDivGeo")
        if prefs.get_string(lib, "DG.Signature") != "XDivGeo":
            fn = prefs.file_name()
            # the message of the Motif version, file name in single quotes
            sys.stderr.write("Failure to initialize the preferences file "
                             "\x27%s\x27\n" % ("(null)" if fn is None
                                                  else fn))
            sys.stderr.flush()
            os._exit(1)
        w.message_dialog("dlgNewPrefsFile")

    def new_version(self, w):
        """OpenNewVersionDlg(w, True)."""
        lib = self.lib
        new = self.dll.GetPyVersion()
        if new % 10:
            sys.stderr.write("OpenNewVersionDlg:Interim version\n")
            sys.stderr.flush()
        buf = "%d" % new
        s = prefs.get_string(lib, "DG.LastUsedVersion")
        prefs.set_string(lib, "DG.LastUsedVersion", buf)
        if s == buf:
            return
        w.message_dialog("dlgNewVersion")

    def create_view(self, app):
        w = window.ViewWindow(self, len(self.windows) + 1)
        self.windows.append(w)
        if self.canvas_size is not None:
            w.canvas_size = self.canvas_size
        w.create(self.xap, app)
        return w

    def quit(self):
        os._exit(0)


def main(argv, library_path=None):
    """Runs DivGeo: argv as the command line of the Motif program."""
    path = library_path or corelib.default_path()
    if not os.path.exists(path):
        sys.stderr.write(
            "DivGeo: library %s not found; build DivGeo (make in "
            "modules/DivGeo, without USE_MOTIF)\n" % path)
        return 1
    qt = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
        ["DivGeo"])
    application = Application(corelib.Library(path), argv, qt)
    application.start()
    return qt.exec()

