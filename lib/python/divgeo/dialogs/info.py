"""About and Statistics (x_info.c), the mesh header (x_mesh.c)."""

import ctypes

from ..core import api, lib as corelib
from . import boxes, files
from . import vacreate as vc
from .base import (MessageDialog, TemplateDialog, create_ok_cancel_dialog,
                   find_dialog)


# About ####################################################################

def open_about_dlg(window):
    """OpenAboutDlg: a message dialog with the version, OK only."""
    w = window
    dlg = find_dialog(w, "dlgAbout")
    if dlg is None:
        dlg = MessageDialog(w, "dlgAbout")
        names, classes = dlg.path()
        dlg.set_message(files.resource_string_ex(
            w.application.db, names, classes, "messageStringEx",
            "MessageStringEx", "$(VERSION)%s",
            w.lib.string_at(w.dll.GetVersionStr(api.DG_VERSION))))
        dlg.cancel.hide()
        dlg.help.hide()
        dlg.manage()
    else:
        dlg.popup()
    return dlg


# Statistics ###############################################################

class InfoDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.alt = 0
        self.dlg = dlg = TemplateDialog(w, "dlgInfo")
        close = vc.PushButton(dlg, "close")
        dlg.xm_place(close)
        close.clicked.connect(dlg.popdown)
        dlg.wm_close = dlg.popdown
        self.r = {}
        vc.create_widget_system(
            dlg,
            "#:form",
            "#4:table",
            "l#:nodesLabel", 1, 1,
            "l#:elemsLabel", 1, 2,
            "l#:unusedLabel", 1, 3,
            "l#:sourcesLabel", 1, 4,
            "l#:surfacesLabel", 1, 5,
            "l#:gridPointsLabel", 1, 6,
            "l#:separatorsLabel", 1, 7,
            "l#:chordsLabel", 1, 8,
            "-#:",
            "#5:values",
            "l#?:nodes", 2, 1, "nodes",
            "l#?:elems", 2, 2, "elems",
            "l#?:unused", 2, 3, "unused",
            "l#?:sources", 2, 4, "sources",
            "l#?:surfaces", 2, 5, "surfaces",
            "l#?:gridPoints", 2, 6, "gridPoints",
            "l#?:separators", 2, 7, "separators",
            "l#?:chords", 2, 8, "chords",
            "-#:",
            "-:",
            refs=self.r)
        w.add_dependent(dlg, api.N_NOW | api.N_NEWAPP | api.N_ALT, None,
                        lambda *a: self.update())

    def update(self):
        """UpdateInfoDlg."""
        w = self.w
        app = w.app
        if not app:
            return
        self.alt = w.lib.get(app, "App.alt")
        counts = (ctypes.c_uint * 6)()
        w.dll.PyInfoCounts(app, counts)
        r = self.r
        r["nodes"].set_label("%u" % counts[0])
        r["elems"].set_label("%u" % counts[1])
        r["sources"].set_label("%u" % counts[2])
        r["unused"].set_label("%u" % counts[3])
        r["surfaces"].set_label(w.lib.string_at(
            w.dll.GetSurfacesStatsStr(app)))
        r["gridPoints"].set_label(w.lib.string_at(
            w.dll.GetGridPointStatsStr(app)))
        r["separators"].set_label("%u" % counts[4])
        r["chords"].set_label("%u" % counts[5])


def open_info_dlg(window):
    """OpenInfoDlg."""
    dlg = find_dialog(window, "dlgInfo")
    if dlg is None:
        dlg = InfoDlg(window).dlg
        dlg.manage()
    else:
        dlg.popup()
    return dlg


# Mesh header ##############################################################

class MeshHeaderDlg:
    def __init__(self, window, mesh):
        w = window
        self.w = w
        self.mesh = mesh
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgEditMeshHeader")
        dlg.data = self
        dlg.callbacks["ok"].append(self.accept)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        self.text = vc.ScrolledText(dlg, "text")
        dlg.xm_place(self.text)
        self.text.textChanged.connect(self.input)
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_DEL |
                        api.N_NEWAPP, None, self.dw_mesh_edit)
        self.reset()
        dlg.manage()

    def reset(self):
        """ResetMeshHeaderDlg."""
        w = self.w
        header = w.lib.string_at(w.dll.PyMeshHeader(self.mesh))
        self.text.setPlainText(header if header is not None else "")
        self.dlg.ok.setEnabled(False)

    def dw_mesh_edit(self, widget, kind, obj, user):
        """DwMeshEdit: the dialog destroyed with its mesh or model."""
        if kind == api.N_DEL and obj != self.mesh:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.w.del_dependent(self.dlg)
            self.dlg.destroy_()

    def accept(self):
        """CbMeshHeaderDlgAccept."""
        w = self.w
        s = corelib.cstr(self.text.toPlainText())
        r = w.dll.CheckMeshHeaderString(self.mesh, s)
        w.pump()
        if r:
            boxes.error_box(w, w.str_(r))
        else:
            w.dll.SetMeshHeaderString(self.mesh, s)
            w.dll.UndoMark(w.app)
            w.pump()
            self.dlg.popdown()

    def input(self):
        """CbMeshHeaderDlgInput."""
        if not self.dlg.ok.isEnabled():
            self.dlg.ok.setEnabled(True)


def open_edit_mesh_header_dlg(window, mesh):
    """OpenEditMeshHeaderDlg."""
    dlg = find_dialog(window, "dlgEditMeshHeader")
    if dlg is not None:
        dlg.data.reset()
        dlg.popup()
    else:
        dlg = MeshHeaderDlg(window, mesh).dlg
    return dlg
