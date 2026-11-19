"""Settings of a model and of the program: Save interval (x_view.c),
Output mode and Mesh options (x_setup.c)."""

import ctypes
import re

from ..core import api, prefs
from . import boxes
from . import vacreate as vc
from .base import create_ok_cancel_dialog, find_dialog


def scan_int(s):
    """sscanf(s, "%d", ...): None when no number is read."""
    m = re.match(r"[ \t\n\v\f\r]*([+-]?[0-9]+)", s)
    if m is None:
        return None
    value = int(m.group(1)) & 0xFFFFFFFF
    return value - (1 << 32) if value >= 1 << 31 else value


# Save interval ############################################################

class SaveIntervalDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgSaveInterval")
        dlg.callbacks["ok"].append(self.set_interval)
        dlg.help.hide()
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "l@:saveLabel", 0x0101,
            "x?@:interval", "interval", 0x0102,
            refs=self.r)
        vc.form2table(form)
        vc.set_text(self.r["interval"], "%d" % prefs.get_int(
            w.lib, prefs.PSTR_AUTOSAVE_INTERVAL))
        dlg.manage()

    def set_interval(self):
        """CbSetSaveInterval."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        minutes = scan_int(vc.text_of(self.r["interval"]))
        if minutes is None:
            w.error_box(w.str_(api.ERR_INVNUMBERS))
            return
        prefs.set_int(w.lib, prefs.PSTR_AUTOSAVE_INTERVAL, minutes)
        self.dlg.popdown()
        w.dll.UndoMark(w.app)
        w.pump()


def open_autosave_dlg(window):
    """OpenAutosaveDlg."""
    w = window
    dlg = find_dialog(w, "dlgSaveInterval")
    if dlg is None:
        dlg = SaveIntervalDlg(w).dlg
    else:
        dlg.popup()
    w.dll.UndoMark(w.app)
    w.pump()
    return dlg


# Output mode ##############################################################

class OutputModeDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgOutputMode")
        dlg.data = self
        dlg.callbacks["ok"].append(self.accept)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        r = self.r = {}
        vc.create_widget_system(
            dlg,
            "#:form",
            "$+8#:mode", vc.radio_box, {"orientation": "horizontal"}, 0, 1,
            "t?:sonnet", "sonnet",
            "t?:carre", "carre",
            "t?:goat", "goat",
            "-:",
            "s-#:sep", 0, 2,
            "t#?:vars", 1, 3, "vars",
            "t#?:structure", 1, 4, "structure",
            "t#?:targets", 1, 5, "targets",
            "t#?:surfaces", 1, 6, "surfaces",
            "t#?:gpoints", 1, 7, "gpoints",
            "-#:",
            refs=r)
        self.reset()
        dlg.manage()

    def reset(self):
        """ResetOutputModeDlg."""
        w = self.w
        f = w.lib.get(w.app, "App.outputFlags")
        mode = w.lib.get(w.app, "App.outputMode")
        r = self.r
        r["vars"].set_state(not f & api.OF_NC_VARS, False)
        r["structure"].set_state(not f & api.OF_NC_STRUCTURE, False)
        r["targets"].set_state(not f & api.OF_NC_TARGETS, False)
        r["surfaces"].set_state(not f & api.OF_NC_SURFACES, False)
        r["gpoints"].set_state(not f & api.OF_NC_GPOINTS, False)
        r["sonnet"].set_state(mode == api.OUTPUTMODE_SONNET, False)
        r["carre"].set_state(mode == api.OUTPUTMODE_CARRE, False)
        r["goat"].set_state(mode == api.OUTPUTMODE_GOAT, False)

    def accept(self):
        """AcceptOutputModeDlg."""
        w = self.w
        r = self.r
        flags = 0
        if not r["vars"].isChecked():
            flags |= api.OF_NC_VARS
        if not r["structure"].isChecked():
            flags |= api.OF_NC_STRUCTURE
        if not r["targets"].isChecked():
            flags |= api.OF_NC_TARGETS
        if not r["surfaces"].isChecked():
            flags |= api.OF_NC_SURFACES
        if not r["gpoints"].isChecked():
            flags |= api.OF_NC_GPOINTS
        app = w.app
        w.dll.SetOutputFlags(app, flags)
        w.pump()
        mode = api.OUTPUTMODE_SONNET
        if r["carre"].isChecked():
            print("output mode is Carre")
            mode = api.OUTPUTMODE_CARRE
        elif r["sonnet"].isChecked():
            print("output mode is Sonnet")
        elif r["goat"].isChecked():
            print("output mode is GOAT")
            mode = api.OUTPUTMODE_GOAT
        w.dll.SetOutputFlags(app, flags)
        w.pump()
        w.dll.SetAppOutputMode(app, mode)
        w.pump()
        w.dll.UndoMark(app)
        w.pump()
        self.dlg.popdown()


def open_output_mode_dlg(window):
    """OpenOutputModeDlg."""
    dlg = find_dialog(window, "dlgOutputMode")
    if dlg is None:
        dlg = OutputModeDlg(window).dlg
    else:
        dlg.data.reset()
        dlg.popup()
    return dlg


# Mesh options #############################################################

class MeshOptionsDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgMeshOptions")
        dlg.data = self
        dlg.callbacks["ok"].append(self.accept)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        r = self.r = {}
        vc.create_widget_system(
            dlg,
            "#:form",
            "l#:modeLabel", 1, 1,
            "*:modeMenu",
            "b@:surfaces", api.MSM_SURFACE,
            "b@:splines", api.MSM_SPLINE,
            "-:",
            "o?#:mode", "mode", 2, 1,
            "s#:separator", 0, 2,
            "l#:slideLabel", 1, 3,
            "x?#:slide", "slide", 2, 3,
            "t?#:border", "border", 2, 4,
            "-#:",
            refs=r)
        self.reset()
        dlg.manage()

    def reset(self):
        """ResetMeshOptionsDlg."""
        w = self.w
        mode, threshold, border = ctypes.c_int(), ctypes.c_double(), \
            ctypes.c_int()
        w.dll.PyMeshOptions(w.app, ctypes.byref(mode),
                            ctypes.byref(threshold), ctypes.byref(border))
        vc.set_option_menu_value(self.r["mode"], mode.value)
        vc.set_text(self.r["slide"], "%g" % threshold.value)
        self.r["border"].set_state(border.value, True)

    def accept(self):
        """AcceptMeshOptionsDlg."""
        w = self.w
        app = w.app
        d = vc.get_text_double(self.r["slide"])
        if d == vc.MAXDOUBLE or d <= 0:
            w.dll.Cancel(app)
            w.pump()
            boxes.error_box(self.dlg, vc.resource_string(
                self.dlg, "errBadSlidingThreshold"))
            return
        w.dll.SetMeshSlidingThreshold(app, d)
        w.pump()
        w.dll.SetDoubleMeshBorderFlag(app, self.r["border"].isChecked())
        w.pump()
        w.dll.SetMeshSlidingMode(app, vc.get_option_menu_value(
            self.r["mode"]))
        w.pump()
        w.dll.UndoMark(app)
        w.pump()
        self.dlg.popdown()


def open_mesh_options_dlg(window):
    """OpenMeshOptionsDlg."""
    dlg = find_dialog(window, "dlgMeshOptions")
    if dlg is None:
        dlg = MeshOptionsDlg(window).dlg
    else:
        dlg.data.reset()
        dlg.popup()
    return dlg
