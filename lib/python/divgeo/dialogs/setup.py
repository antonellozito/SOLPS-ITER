"""The Setup menu (x_setup.c): the warning before a change of the setup,
the list of the variable-set definitions with their create and edit
dialogs, the variable definitions (create, edit, help text), and Save
configuration. The core part of Save configuration is in the library
(src/py/py_vars.c)."""

import ctypes

from PySide6 import QtWidgets

from ..core import api, lib as corelib
from . import boxes, files
from . import vacreate as vc
from .base import (MessageDialog, TemplateDialog, XmDialog,
                   create_ok_cancel_dialog, find_dialog)
from .variables import group_list

DG_FNAME_LEN = 256


def _str(w, ptr):
    return w.lib.string_at(ptr)


def _strex(dlg, name, cls, fmt, *args):
    names, classes = dlg.path()
    return files.resource_string_ex(dlg.window_.application.db, names,
                                    classes, name, cls, fmt, *args)


def _title(dlg, name, descr):
    """The title of a definition dialog: dialogTitleEx with the name and
    the description."""
    dlg.setWindowTitle(_strex(dlg, "dialogTitleEx", "DialogTitle",
                              "$(NAME)%s$(DESCR)%s", name, descr))


def _changes_vardefs(w):
    from ..app.window import CHF_VARDEFS
    return w.changes & CHF_VARDEFS


def _one_word(s):
    """sscanf(s, "%s%s", name, name) == 1: the word, else None."""
    words = s.split()
    return words[0] if len(words) == 1 else None


def _scan_int(s):
    from .settings import scan_int
    return scan_int(s)


def _find_by_child(window, name, child):
    """XtNameToWidget(wMain, "*CHILD"): the dialog NAME whose child is
    named CHILD."""
    for d in window.findChildren(XmDialog, name):
        if not d.destroyed_ and d.findChild(QtWidgets.QWidget, child):
            return d
    return None


def _var_set_defs(w):
    return group_list(w, w.lib.get(w.app, "App.varSetDefs"))


# Setup warning ############################################################

def open_setup_warning_dlg(window, callback):
    """OpenSetupWarningDlg: None when the warning was answered before (the
    command goes on), else the warning, callback called after OK."""
    w = window
    dlg = find_dialog(w, "dlgSetupWarning")
    if dlg is not None:
        if dlg.user is None:
            return None
        dlg.user = callback
        dlg.popup()
    else:
        dlg = MessageDialog(w, "dlgSetupWarning", auto_unmanage=False,
                            dialog_type="dialog_warning")
        dlg.set_message(dlg.resource("messageString", "MessageString")
                        or "")
        dlg.user = callback
        dlg.callbacks["ok"].append(lambda: _setup_warning_ok(dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.wm_close = dlg.popdown
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        dlg.manage()
    return dlg


def _setup_warning_ok(dlg):
    """CbSetupWarningOk."""
    cb = dlg.user
    dlg.popdown()
    if cb is not None:
        dlg.user = None
        cb()


def cb_edit_var_set_defs(window):
    """CbEditVarSetDefs."""
    if open_setup_warning_dlg(window,
                              lambda: cb_edit_var_set_defs(window)) \
            is not None:
        return
    open_var_set_def_list_dlg(window)


def cb_save_config(window):
    """CbSaveConfig."""
    if open_setup_warning_dlg(window, lambda: cb_save_config(window)) \
            is not None:
        return
    open_save_config_dlg(window)


# Variable-set definitions #################################################

class VarSetDefListDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = TemplateDialog(w, "dlgVarSetDefList")
        r = {}
        vc.create_widget_system(
            dlg,
            "b?:add", "add",
            "b?\n:modify", "modify",
            "b?:remove", "remove",
            "b?\b:cancel", "cancel",
            refs=r)
        r["add"].clicked.connect(lambda: open_var_set_def_create_dlg(w))
        r["modify"].clicked.connect(self.modify)
        r["remove"].clicked.connect(self.remove)
        r["cancel"].clicked.connect(dlg.popdown)
        dlg.wm_close = dlg.popdown
        self.list = vc.ScrolledList(dlg, "list")
        dlg.xm_place(self.list)
        self.list.default_callbacks.append(self.modify)
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_NEWAPP, None,
                        self.dw_list)
        dlg.manage()

    def _selected(self, checked):
        """The definition of the one selected item (checked: the position
        tested against the list of definitions)."""
        pos = self.list.selected_positions()
        if len(pos) != 1:
            return None
        defs = self.w.lib.get(self.w.app, "App.varSetDefs")
        if checked and not 1 <= pos[0] <= self.w.dll.GetPyGroupCount(defs):
            return None
        return self.w.dll.GroupAt(defs, pos[0] - 1)

    def modify(self):
        """CbVarSetDefListModify."""
        w = self.w
        vsd = self._selected(True)
        if not vsd:
            return
        if w.dll.IsLocked(vsd):
            boxes.error_box(self.dlg, _str(w, w.dll.WhyLocked(w.view, vsd)))
            return
        open_var_set_def_edit_dlg(w, vsd)

    def remove(self):
        """CbVarSetDefListRemove."""
        w = self.w
        vsd = self._selected(False)
        if not vsd:
            return
        if w.dll.IsLocked(vsd):
            boxes.error_box(self.dlg, _str(w, w.dll.WhyLocked(w.view, vsd)))
            return
        w.dll.DelVarSetDef(w.app, vsd)
        w.dll.UndoMark(w.app)
        w.pump()

    def dw_list(self, widget, kind, obj, user=None):
        """DwVarSetDefList."""
        w = self.w
        if kind == api.N_ALT and not _changes_vardefs(w):
            return
        self.list.set_items([_str(w, w.lib.get(v, "VarSetDef.name"))
                             for v in _var_set_defs(w)])
        self.list.select_pos(1, True)


def open_var_set_def_list_dlg(window):
    """OpenVarSetDefListDlg."""
    dlg = find_dialog(window, "dlgVarSetDefList")
    if dlg is not None:
        dlg.popup()
    else:
        dlg = VarSetDefListDlg(window).dlg
    return dlg


class VarSetDefCreateDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgVarSetDefCreate")
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "l@:nameLabel", 0x0101,
            "x?@:name", "name", 0x0201,
            refs=self.r)
        vc.form2table(form)
        dlg.manage()

    def ok(self):
        """CbVarSetDefCreateOk."""
        w = self.w
        name = _one_word(vc.text_of(self.r["name"]))
        if name is None:
            boxes.error_box(self.dlg, w.str_(api.ERR_BADNAME))
            return
        for vsd in _var_set_defs(w):
            if _str(w, w.lib.get(vsd, "VarSetDef.name")) == name:
                boxes.error_box(self.dlg, w.str_(api.ERR_DUPNAME))
                return
        w.dll.AddVarSetDef(w.app, corelib.cstr(name), b"CLASSIFIED", 0, 1)
        w.dll.UndoMark(w.app)
        w.pump()
        self.dlg.popdown()


def open_var_set_def_create_dlg(window):
    """OpenVarSetDefCreateDlg."""
    dlg = find_dialog(window, "dlgVarSetDefCreate")
    if dlg is not None:
        dlg.popup()
    else:
        dlg = VarSetDefCreateDlg(window).dlg
    return dlg


class VarSetDefEditDlg:
    def __init__(self, window, vsd):
        w = window
        self.w = w
        self.vsd = vsd
        name = _str(w, w.lib.get(vsd, "VarSetDef.name"))
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgVarSetDefEdit")
        dlg.data = self
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, "dlgVarSetDefEdit_" + name)
        dlg.xm_place(form)
        form2 = vc.Form(form, "form2")
        form.xm_place(form2)
        self.r = {}
        vc.create_widget_system(
            form2,
            "l@:descrLabel", 0x0101,
            "x?@:descr", "descr", 0x0201,
            "l@:minLabel", 0x0102,
            "x?@:min", "min", 0x0202,
            "l@:maxLabel", 0x0103,
            "x?@:max", "max", 0x0203,
            refs=self.r)
        vc.form2table(form2)
        outer = vc.Form(form, "outerForm")
        form.xm_place(outer)
        self.frame = vc.Frame(outer, "frame")
        outer.xm_place(self.frame)
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_DEL |
                        api.N_NEWAPP, None, self.dw_edit)
        self.reset()
        dlg.manage()

    def reset(self):
        """ResetVarSetDefEditDlg."""
        w = self.w
        g = w.lib.get
        name = _str(w, g(self.vsd, "VarSetDef.name"))
        descr = _str(w, g(self.vsd, "VarSetDef.descr"))
        _title(self.dlg, name, descr)
        vc.set_text(self.r["descr"], descr or "")
        vc.set_text(self.r["min"], "%d" % g(self.vsd, "VarSetDef.minVarSets"))
        vc.set_text(self.r["max"], "%d" % g(self.vsd, "VarSetDef.maxVarSets"))

    def dw_edit(self, widget, kind, obj, user=None):
        """DwVarSetDefEdit: the grid of the variable definitions (a new
        one after each change; the old one stays, as in Motif)."""
        w = self.w
        if self.vsd is None:
            return
        if kind == api.N_DEL and obj != self.vsd:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.vsd = None
            w.del_dependent(self.dlg)
            self.dlg.destroy_()
            return
        if kind == api.N_ALT and not _changes_vardefs(w):
            return
        vds = group_list(w, w.lib.get(self.vsd, "VarSetDef.varDefs"))
        pos = [(w.lib.get(vd, "VarDef.row"), w.lib.get(vd, "VarDef.col"),
                vd) for vd in vds]
        rows = max([p[0] + 1 for p in pos] + [0]) + 1
        cols = max([p[1] + 1 for p in pos] + [0]) + 1
        cols = max(cols, 3)
        rows = max(rows, 3)
        grid = vc.Form(self.frame, "varDefs")
        self.frame.xm_place(grid)
        for i in range(rows):
            for j in range(cols):
                vd = next((p[2] for p in pos if p[0] == i and p[1] == j),
                          None)
                bn = vc.PushButton(grid, "varDef")
                grid.xm_place(bn, j + 1, i + 1)
                if vd is not None:
                    bn.set_label(_str(w, w.lib.get(vd, "VarDef.name")))
                bn.clicked.connect(lambda checked=False, v=vd, r=i, c=j:
                                   self.edit_var_def(v, r, c))

    def edit_var_def(self, vd, row, col):
        """CbEditVarDef."""
        if vd is None:
            open_var_def_create_dlg(self.w, self.vsd, row, col)
        else:
            open_var_def_edit_dlg(self.w, vd)

    def ok(self):
        """CbVarSetDefEditOk."""
        w = self.w
        vs_min = _scan_int(vc.text_of(self.r["min"]))
        if vs_min is None:
            boxes.error_box(self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        vs_max = _scan_int(vc.text_of(self.r["max"]))
        if vs_max is None:
            boxes.error_box(self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        if vs_min > vs_max:
            boxes.error_box(self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        i = w.dll.GetPyGroupCount(w.lib.get(self.vsd, "VarSetDef.varSets"))
        if i < vs_min or i > vs_max:
            boxes.error_box(self.dlg, w.str_(api.ERR_MINMAXVARSETS))
            return
        if vs_max > 1:
            for vd in group_list(w, w.lib.get(self.vsd,
                                              "VarSetDef.varDefs")):
                if w.lib.get(vd, "VarDef.varType") & api.VTF_SINGLE:
                    boxes.error_box(self.dlg, w.str_(api.ERR_SINGLE))
                    return
        descr = vc.text_of(self.r["descr"])
        w.dll.ChangeVarSetDef(w.app, self.vsd, w.lib.get(
            self.vsd, "VarSetDef.name"), corelib.cstr(descr or "CLASSIFIED"),
            vs_min, vs_max, None)
        w.dll.UndoMark(w.app)
        w.pump()
        self.dlg.popdown()


def open_var_set_def_edit_dlg(window, vsd):
    """OpenVarSetDefEditDlg: one dialog per definition."""
    w = window
    name = _str(w, w.lib.get(vsd, "VarSetDef.name"))
    dlg = _find_by_child(w, "dlgVarSetDefEdit", "dlgVarSetDefEdit_" + name)
    if dlg is not None:
        dlg.data.reset()
        dlg.popup()
    else:
        dlg = VarSetDefEditDlg(w, vsd).dlg
    return dlg


# Variable definitions #####################################################

_TYPES = (("int", api.VT_INT), ("float", api.VT_FLOAT),
          ("text", api.VT_TEXT), ("filename", api.VT_FILENAME), None,
          ("elem", api.VT_ELEM), ("elems", api.VT_ELEMS),
          ("target1", api.VT_TARGET1), ("target2", api.VT_TARGET2),
          ("structure", api.VT_STRUCTURE),
          ("structPart", api.VT_STRUCTPART), ("chords", api.VT_CHORDS),
          ("topView", api.VT_TOPVIEW), None,
          ("meshCells", api.VT_MESH_CELLS),
          ("meshElems", api.VT_MESH_ELEMENTS),
          ("meshHElems", api.VT_MESH_H_ELEMENTS),
          ("meshVElems", api.VT_MESH_V_ELEMENTS))


def _pointer_name(prefix, ptr):
    """The name of a widget with an address (%p)."""
    return "%s_0x%x" % (prefix, ptr)


class VarDefEditDlg:
    def __init__(self, window, vd):
        w = window
        self.w = w
        self.vd = vd
        self.dlg = dlg = TemplateDialog(w, "dlgVarDefEdit")
        dlg.data = self
        vc.create_widget_system(
            dlg,
            "bA\n:ok", lambda wg, d: self.ok(), None,
            "bA\b:cancel", lambda wg, d: dlg.popdown(), None,
            "bA:editHelp", lambda wg, d: self.edit_help(), None,
            "bA:remove", lambda wg, d: self.remove(), None)
        dlg.wm_close = dlg.popdown
        form = vc.Form(dlg, _pointer_name("dlgVarDefEdit", vd))
        dlg.xm_place(form)
        spec = ["l@:descrLabel", 0x0101,
                "x?@:descr", "descr", 0x0201,
                "l@:typeLabel", 0x0102,
                "*:typeMenu"]
        for item in _TYPES:
            if item is None:
                spec += ["s:separator"]
            else:
                spec += ["b@A:" + item[0], item[1],
                         lambda wg, d: self.sensitive(), None]
        spec += ["-:",
                 "o?@:type", "type", 0x0202,
                 "l@:orgLabel", 0x0103,
                 "*:orgMenu",
                 "b?:withVarSet", "orgVarSet",
                 "b?:withElems", "orgElems",
                 "b?:withSources", "orgSources",
                 "b?:withChords", "orgChords",
                 "-:",
                 "o?@:origin", "origin", 0x0203,
                 "l?@:defLabel", "defLabel", 0x0104,
                 "x?@:def", "def", 0x0204,
                 "t?@:noExport", "noExport", 0x0205,
                 "t?@:layerIndex", "layerIndex", 0x0206]
        self.r = {}
        vc.create_widget_system(form, *spec, refs=self.r)
        self.reset()
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_DEL |
                        api.N_NEWAPP, None, self.dw_edit)
        vc.form2table(form)
        dlg.manage()

    def reset(self):
        """ResetVarDefEditDlg."""
        w = self.w
        g = w.lib.get
        r = self.r
        vd = self.vd
        _title(self.dlg, _str(w, g(vd, "VarDef.name")),
               _str(w, g(vd, "VarDef.descr")))
        vc.set_text(r["descr"], _str(w, g(vd, "VarDef.descr")) or "")
        var_type = g(vd, "VarDef.varType")
        vc.set_option_menu_value(r["type"], var_type)
        flags = g(vd, "VarDef.flags")
        org = {api.VF_FORELEMS: "orgElems", api.VF_FORSOURCES: "orgSources",
               api.VF_FORCHORDS: "orgChords"}.get(flags & api.VFM_MULTIPLE,
                                                  "orgVarSet")
        r["origin"].set_history(r[org])
        r["noExport"].set_state(flags & api.VF_NOEXPORT, False)
        r["layerIndex"].set_state(flags & api.VF_LAYERINDEX, False)
        vc.set_text(r["def"], "" if var_type & api.VTM_HASGROUP else (_str(
            w, w.dll.GetVar(g(vd, "VarDef.varSetDef"), vd, None)) or ""))
        self.sensitive()

    def dw_edit(self, widget, kind, obj, user=None):
        """DwVarDefEdit."""
        if self.vd is None:
            return
        if kind == api.N_DEL and obj != self.vd:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.vd = None
            self.w.del_dependent(self.dlg)
            self.dlg.destroy_()

    def sensitive(self):
        """CbVarDefEditSensitive."""
        t = vc.get_option_menu_value(self.r["type"])
        self.r["def"].setEnabled(not t & api.VTM_HASGROUP)
        self.r["defLabel"].setEnabled(not t & api.VTM_HASGROUP)

    def ok(self):
        """CbVarDefEditOk."""
        w = self.w
        g = w.lib.get
        r = self.r
        dlg = self.dlg
        var_type = vc.get_option_menu_value(r["type"])
        opt = 0
        hist = r["origin"]._history
        if hist is r["orgElems"]:
            opt |= api.VF_FORELEMS
        if hist is r["orgSources"]:
            opt |= api.VF_FORSOURCES
        if hist is r["orgChords"]:
            opt |= api.VF_FORCHORDS
        if r["noExport"].isChecked():
            opt |= api.VF_NOEXPORT
        if r["layerIndex"].isChecked():
            opt |= api.VF_LAYERINDEX
        if opt & api.VFM_MULTIPLE and var_type & api.VTM_HASGROUP:
            boxes.error_box(dlg, w.str_(api.ERR_MULTGROUP))
            return
        if var_type & api.VTF_SINGLE:
            if opt & api.VFM_MULTIPLE:
                boxes.error_box(dlg, w.str_(api.ERR_SINGLE))
                return
            for vd in group_list(w, g(w.app, "App.varDefs")):
                if vd != self.vd and g(vd, "VarDef.varType") == var_type:
                    boxes.error_box(dlg, w.str_(api.ERR_SINGLE))
                    return
        vsd = g(self.vd, "VarDef.varSetDef")
        if opt & api.VF_LAYERINDEX:
            if opt & api.VFM_MULTIPLE:
                boxes.error_box(dlg, vc.resource_string(dlg,
                                                        "errIndexMultiple"))
                return
            if var_type & api.VTM_HASGROUP:
                boxes.error_box(dlg, vc.resource_string(dlg,
                                                        "errIndexGroup"))
                return
            for vd in group_list(w, g(vsd, "VarSetDef.varDefs")):
                if vd == self.vd:
                    continue
                if g(vd, "VarDef.flags") & api.VF_LAYERINDEX:
                    names, classes = dlg.path()
                    boxes.error_box(dlg, files.resource_string_ex(
                        w.application.db, names, classes, "errIndex2nd",
                        None, "$(NAME)%s$(DESCR)%s",
                        _str(w, g(vd, "VarDef.name")),
                        _str(w, g(vd, "VarDef.descr"))))
                    return
        descr = vc.text_of(r["descr"])
        err = w.dll.ChangeVarDef(w.app, self.vd, vsd,
                                 g(self.vd, "VarDef.name"),
                                 corelib.cstr(descr or "CLASSIFIED"),
                                 var_type, opt, g(self.vd, "VarDef.col"),
                                 g(self.vd, "VarDef.row"))
        w.pump()
        if err and err != api.STR_VARSLOST:
            w.dll.Cancel(w.app)
            w.pump()
            boxes.error_box(dlg, w.str_(err))
            return
        if not var_type & api.VTM_HASGROUP:
            err = w.dll.SetVar(w.app, vsd, self.vd, None,
                               corelib.cstr(vc.text_of(r["def"])))
            w.pump()
            if err:
                w.dll.Cancel(w.app)
                w.pump()
                boxes.error_box(dlg, w.str_(err))
                return
        w.dll.UndoMark(w.app)
        w.pump()
        dlg.popdown()

    def remove(self):
        """CbVarDefEditRemove."""
        w = self.w
        w.dll.DelVarDef(w.app, self.vd)
        w.dll.UndoMark(w.app)
        w.pump()

    def edit_help(self):
        """CbVarDefEditHelpStr."""
        if self.vd is None:
            return
        open_help_edit_dlg(self.w, self.vd)


def open_var_def_edit_dlg(window, vd):
    """OpenVarDefEditDlg: one dialog per definition."""
    w = window
    dlg = _find_by_child(w, "dlgVarDefEdit",
                         _pointer_name("dlgVarDefEdit", vd))
    if dlg is not None:
        dlg.data.reset()
        dlg.popup()
    else:
        dlg = VarDefEditDlg(w, vd).dlg
    return dlg


class HelpEditDlg:
    def __init__(self, window, vd):
        w = window
        self.w = w
        self.vd = vd
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgHelpEdit")
        dlg.data = self
        dlg.callbacks["ok"].append(self.accept)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        self.text = vc.ScrolledText(dlg, _pointer_name("dlgHelpEdit", vd))
        dlg.xm_place(self.text)
        self.reset()
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_DEL |
                        api.N_NEWAPP, None, self.dw_edit)
        dlg.manage()

    def reset(self):
        """ResetHelpEditDlg."""
        w = self.w
        self.text.setPlainText(_str(w, w.lib.get(self.vd, "VarDef.help"))
                               or "")

    def dw_edit(self, widget, kind, obj, user=None):
        """DwHelpEdit: the title from the definition."""
        w = self.w
        if self.vd is None:
            return
        if kind == api.N_DEL and obj != self.vd:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.vd = None
            w.del_dependent(self.dlg)
            self.dlg.destroy_()
            return
        if kind == api.N_ALT and not _changes_vardefs(w):
            return
        _title(self.dlg, _str(w, w.lib.get(self.vd, "VarDef.name")),
               _str(w, w.lib.get(self.vd, "VarDef.descr")))

    def accept(self):
        """CbHelpEditDlgAccept."""
        w = self.w
        w.dll.ChangeHelpString(w.app, self.vd,
                               corelib.cstr(self.text.toPlainText()))
        w.dll.UndoMark(w.app)
        w.pump()
        self.dlg.popdown()


def open_help_edit_dlg(window, vd):
    """OpenHelpEditDlg."""
    w = window
    dlg = _find_by_child(w, "dlgHelpEdit", _pointer_name("dlgHelpEdit", vd))
    if dlg is not None:
        dlg.data.reset()
        dlg.popup()
    else:
        dlg = HelpEditDlg(w, vd).dlg
    return dlg


class VarDefCreateDlg:
    def __init__(self, window, vsd):
        w = window
        self.w = w
        self.vsd = vsd
        self.row = self.col = 0
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgVarDefCreate")
        dlg.data = self
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, _pointer_name("dlgVarDefCreate", vsd))
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "l@:nameLabel", 0x0101,
            "x?@:name", "name", 0x0201,
            refs=self.r)
        vc.form2table(form)
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_DEL |
                        api.N_NEWAPP, None, self.dw_create)
        dlg.manage()

    def dw_create(self, widget, kind, obj, user=None):
        """DwVarDefCreate: the title from the variable-set definition."""
        w = self.w
        if self.vsd is None:
            return
        if kind == api.N_DEL and obj != self.vsd:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.vsd = None
            w.del_dependent(self.dlg)
            self.dlg.destroy_()
            return
        if kind == api.N_ALT and not _changes_vardefs(w):
            return
        _title(self.dlg, _str(w, w.lib.get(self.vsd, "VarSetDef.name")),
               _str(w, w.lib.get(self.vsd, "VarSetDef.descr")))

    def ok(self):
        """CbVarDefCreateOk."""
        w = self.w
        name = _one_word(vc.text_of(self.r["name"]))
        if name is None:
            boxes.error_box(self.dlg, w.str_(api.ERR_BADNAME))
            return
        for vd in group_list(w, w.lib.get(self.vsd, "VarSetDef.varDefs")):
            if _str(w, w.lib.get(vd, "VarDef.name")) == name:
                boxes.error_box(self.dlg, w.str_(api.ERR_DUPNAME))
                return
        vd = w.dll.AddVarDef(w.app, self.vsd, corelib.cstr(name),
                             b"CLASSIFIED", api.VT_FLOAT, 0, self.col,
                             self.row)
        w.dll.UndoMark(w.app)
        w.pump()
        open_var_def_edit_dlg(w, vd)
        self.dlg.popdown()


def open_var_def_create_dlg(window, vsd, row, col):
    """OpenVarDefCreateDlg."""
    w = window
    dlg = _find_by_child(w, "dlgVarDefCreate",
                         _pointer_name("dlgVarDefCreate", vsd))
    if dlg is not None:
        d = dlg.data
        dlg.popup()
    else:
        d = VarDefCreateDlg(w, vsd)
        dlg = d.dlg
    d.row = row
    d.col = col
    return dlg


# Save configuration #######################################################

def open_save_config_dlg(window):
    """OpenSaveConfigDlg: the question, with the file of the
    configuration."""
    w = window
    dlg = find_dialog(w, "dlgSaveConfig")
    if dlg is None:
        dlg = MessageDialog(w, "dlgSaveConfig", auto_unmanage=False,
                            dialog_type="dialog_question")
        dlg.callbacks["ok"].append(lambda: _save_config_ok(w, dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.wm_close = dlg.popdown
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
    buf = ctypes.create_string_buffer(DG_FNAME_LEN)
    w.dll.PyConfigFileName(w.view, buf)
    dlg.user = buf.value.decode("latin-1")
    dlg.set_message(_strex(dlg, "messageStringEx", "MessageString",
                           "$(FILENAME)%s", dlg.user))
    dlg.manage()
    dlg.popup()
    return dlg


def _save_config_ok(w, dlg):
    """CbSaveConfigDlgOk."""
    a = w.app
    if not a:
        return
    if w.dll.PyAppHasGeometry(a):
        w.pump()
        if boxes.warning_box(dlg, w.str_(api.QUE_WITHGEOMETRY)):
            return
    err = w.dll.PySaveConfig(w.view, corelib.cstr(dlg.user))
    w.pump()
    if err:
        w.error_box(w.str_(err))
        return
    if w.dll.PyOtherApps(w.view):
        if not boxes.question_box(dlg, w.str_(api.QUE_UPDATEAPPS)):
            w.dll.PyUpdateOtherApps(w.view)
            w.pump()
    dlg.popdown()
