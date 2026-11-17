"""File > Import and File > Export (x_fileio.c, x_topo.c): the
equilibrium, the template, the mesh and the topology read, the mesh and
the elements as a template written, each with its file selection box
(directory mask from its DG_*MASK variables)."""

import os

from ..core import api, lib as corelib
from . import boxes
from . import vacreate as vc
from .base import find_dialog
from .files import FileSelectionDialog

ENV_EXPORT_TEMPLATE_MASK = "DG_EXPORT_TEMPLATE_MASK"
ENV_EXPORT_MESH_MASK = "DG_EXPORT_MESH_MASK"
ENV_IMPORT_TOPO_MASK = "DG_IMPORT_TOPOLOGY_MASK"
EEAT_ALL, EEAT_MARKED = 1, 2


def _mask(window, ids):
    """The first of the variables (message ids of their names) that is
    set."""
    for i in ids:
        s = os.environ.get(window.str_(i) if isinstance(i, int) else i)
        if s is not None:
            return s
    return None


def _create(window, name, mask_ids, ok, before_mask=None):
    """A file selection box made and managed; children made before the
    mask is set; a mask the box does not keep reported."""
    dlg = FileSelectionDialog(window, name)
    dlg.manage()
    dlg.wm_close = dlg.popdown
    if before_mask is not None:
        before_mask(dlg)
    s = _mask(window, mask_ids)
    if s is not None and not dlg.set_dir_mask(s):
        window.error_box(window.str_(api.ERR_BADMASK))
    dlg.callbacks["ok"].append(lambda: ok(dlg))
    dlg.callbacks["cancel"].append(dlg.popdown)
    return dlg


def _reopen(dlg):
    dlg.do_search()
    dlg.popup()


def _set_view_flags(w, flags):
    w.dll.SetViewFlags(w.view, w.lib.get(w.view, "View.showFlags") | flags)
    w.pump()


def _file_name(w, which):
    return w.lib.string_at(w.dll.PyAppFileName(w.app, which))


def _locked(w, obj):
    """The error box of a locked object; True if locked."""
    if obj and w.dll.IsLocked(obj):
        w.error_box(w.lib.string_at(w.dll.WhyLocked(w.view, obj)))
        return True
    return False


def _msg(w, text):
    w.dll.PyViewMsg(w.view, corelib.cstr(text))
    w.pump()


# Imports ##################################################################

def _load(w, dlg, call, flags, msg_id):
    """CbEquilLoad, CbTemplateLoad, CbSonnetLoad."""
    i = call(dlg.text.text())
    w.pump()
    if i:
        w.dll.Cancel(w.app)
        w.pump()
        boxes.error_box(dlg, w.str_(i))
        return
    dlg.popdown()
    _set_view_flags(w, flags)
    w.dll.PyViewMsgId(w.view, msg_id)
    w.pump()
    w.dll.UndoMark(w.app)
    w.pump()


def _open_import(w, name, mask_ids, ok, which, flags):
    dlg = find_dialog(w, name)
    if dlg is None:
        dlg = _create(w, name, mask_ids, ok)
    else:
        _reopen(dlg)
    fname = _file_name(w, which)
    if fname is not None:
        dlg.text.setText(fname)
    _set_view_flags(w, flags)
    w.dll.UndoMark(w.app)
    w.pump()
    return dlg


def open_equil_dlg(window):
    """OpenEquilDlg."""
    w = window

    def load(dlg):
        w.dll.SetActiveView(w.view)
        w.pump()
        _load(w, dlg, lambda s: w.dll.AddEquil(w.app, corelib.cstr(s)),
              api.SHW_EQUIL, api.MSG_EQUILLOADED)
    return _open_import(w, "dlgEquil", (api.ENV_EQUILMASK2,
                                        api.ENV_EQUILMASK), load, 1,
                        api.SHW_EQUIL)


def open_template_dlg(window):
    """OpenTemplateDlg."""
    w = window

    def load(dlg):
        _load(w, dlg, lambda s: w.dll.AddTemplate(w.app, corelib.cstr(s),
                                                  0, 0, 0, 1),
              api.SHW_TEMPLATE, api.MSG_TEMPLATELOADED)
    return _open_import(w, "dlgTemplate", (api.ENV_TEMPLATEMASK2,
                                           api.ENV_TEMPLATEMASK), load, 2,
                        api.SHW_TEMPLATE)


def open_sonnet_dlg(window):
    """OpenSonnetDlg."""
    w = window

    def load(dlg):
        _load(w, dlg, lambda s: w.dll.LoadMesh(w.app, corelib.cstr(s)),
              api.SHW_MESH, api.MSG_SONNETLOADED)
    return _open_import(w, "dlgSonnet", (api.ENV_SONNETMASK2,
                                         api.ENV_SONNETMASK), load, 3,
                        api.SHW_MESH)


def cb_equil(window):
    """CbEquil."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    if not w.app:
        return
    if not _locked(w, w.lib.get(w.app, "App.equil")):
        open_equil_dlg(w)


def cb_template(window):
    """CbTemplate."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    if not w.app:
        return
    if not _locked(w, w.lib.get(w.app, "App.template")):
        open_template_dlg(w)


def cb_sonnet(window):
    """CbSonnet."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    if not w.app:
        return
    if not _locked(w, w.lib.get(w.app, "App.sonnetData")):
        open_sonnet_dlg(w)


def open_import_topology_dlg(window):
    """CmImportTopology, OpenImportTopologyDlg."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    dlg = find_dialog(w, "dlgImportTopology")
    if dlg is None:
        def toggle(d):
            d.detect = vc.ToggleButton(d, "detectXPoints")
            d.xm_place(d.detect)

        dlg = _create(w, "dlgImportTopology", (ENV_IMPORT_TOPO_MASK,),
                      lambda d: _import_topology(w, d), toggle)
    else:
        # the search done again, the selection kept
        s = dlg.text.text()
        dlg.do_search()
        dlg.text.setText(s)
        dlg.select_file(s)
        dlg.popup()
    return dlg


def _import_topology(w, dlg):
    """CbImportTopo."""
    w.dll.SetActiveView(w.view)
    w.pump()
    i = w.dll.LoadTopology(w.app, corelib.cstr(dlg.text.text()),
                           dlg.detect.isChecked())
    w.pump()
    if i:
        w.dll.Cancel(w.app)
        w.pump()
        boxes.error_box(dlg, w.str_(i))
        return
    dlg.popdown()
    _msg(w, vc.resource_string(dlg, "msgTopoImported"))
    w.dll.UndoMark(w.app)
    w.pump()


# Exports ##################################################################

def open_export_mesh_dlg(window, at_exit):
    """OpenExportMeshDlg."""
    w = window
    mesh = w.lib.get(w.app, "App.mesh")
    if not mesh:
        w.error_box(w.str_(api.ERR_NOSONNET))
        return None
    dlg = find_dialog(w, "dlgExportMesh")
    if dlg is None:
        dlg = _create(w, "dlgExportMesh", (ENV_EXPORT_MESH_MASK,),
                      lambda d: _export_mesh(w, d))
        w.add_dependent_rule(dlg.ok_button, ("exists", api.T_MESH))
    else:
        _reopen(dlg)
    fname = _file_name(w, 3)
    if fname is not None:
        dlg.text.setText(fname)
        dlg.select_file(fname)
    dlg.at_exit = at_exit
    return dlg


def _export_mesh(w, dlg):
    """CbExportMesh."""
    w.dll.SetActiveView(w.view)
    w.pump()
    mesh = w.lib.get(w.app, "App.mesh")
    if not mesh:
        boxes.error_box(dlg, w.str_(api.ERR_NOSONNET))
        return
    i = w.dll.SaveMesh(mesh, corelib.cstr(dlg.text.text()))
    w.pump()
    if i:
        w.dll.Cancel(w.app)
        w.pump()
        boxes.error_box(dlg, w.str_(i))
        return
    dlg.popdown()
    _msg(w, vc.resource_string(dlg, "msgMeshSaved"))
    w.dll.UndoMark(w.app)
    w.pump()
    if dlg.at_exit:
        w.close_view(-1)


def open_export_elems_as_template_dlg(window):
    """OpenExportElemsAsTemplateDlg."""
    w = window
    dlg = find_dialog(w, "dlgExportElemsAsTemplate")
    if dlg is None:
        dlg = _create(w, "dlgExportElemsAsTemplate",
                      (ENV_EXPORT_TEMPLATE_MASK,),
                      lambda d: _export_elems(w, d))
        r = {}
        vc.create_widget_system(
            dlg,
            "*:optMenu",
            "b@:all", EEAT_ALL,
            "b@:marked", EEAT_MARKED,
            "-:",
            "o?:whichElems", "whichElems",
            refs=r)
        dlg.which = r["whichElems"]
        w.add_dependent_rule(dlg.ok_button, ("exists", api.T_ELEM))
    else:
        _reopen(dlg)
    return dlg


def _export_elems(w, dlg):
    """CbExportElemsAsTemplate."""
    w.dll.SetActiveView(w.view)
    w.pump()
    app = w.app
    group = w.lib.get(app, "App.elems" if vc.get_option_menu_value(
        dlg.which) == EEAT_ALL else "App.mark")
    check = w.dll.PyExportElemsCheck(w.view, group)
    w.pump()
    if check == 1:
        boxes.error_box(dlg, w.str_(api.ERR_NO_MARKED_ELEMS))
        return
    if check == 2:
        w.error_box(w.str_(api.ERR_BAD_OBJECT_TYPE))
        return
    i = w.dll.WriteElemsAsDgTemplate(group, corelib.cstr(dlg.text.text()))
    w.pump()
    if i:
        w.dll.Cancel(app)
        w.pump()
        boxes.error_box(dlg, w.str_(i))
        return
    dlg.popdown()
    _msg(w, vc.resource_string(dlg, "msgTemplateSaved"))
    w.dll.UndoMark(app)
    w.pump()
