"""Options > Setup (amxvars.c): the warning shown before the first use,
the Setup dialog, the list of variable definitions with Add, Change and
Delete, the dialog that creates a definition and the dialog that edits
one."""

from ...divgeo.dialogs import vacreate as vc
from ...divgeo.dialogs.base import FormDialog, MessageDialog
from ..core import api, lib as corelib
from . import boxes
from .boxes import find_dialog
from .lists import scrolled_list

DLG_SETUPWARNING = "dlgSetupWarning"
DLG_SETUP = "dlgSetup"
DLG_VARDEFLIST = "dlgVarDefList"
DLG_VARDEFCREATE = "dlgVarDefCreate"
DLG_VARDEFEDIT = "dlgVarDefEdit"
VDS_DESCR = b"VDS_DESCR"
SPACES = " \t\n\v\f\r"


def _message_dialog(w, name, kind="dialog_message"):
    dlg = MessageDialog(w, name, auto_unmanage=False, dialog_type=kind)
    dlg.help.hide()
    return dlg


def open_setup_warning_dlg(w):
    """OpenSetupWarningDlg: after its first Proceed, Setup at once."""
    dlg = find_dialog(w, DLG_SETUPWARNING)
    if dlg is None:
        dlg = _message_dialog(w, DLG_SETUPWARNING, "dialog_warning")
        dlg.set_message(dlg.resource("messageString", "MessageString") or "")
        dlg.proceeded = False
        dlg.callbacks["ok"].append(lambda: cb_setup_warning_ok(w, dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.wm_close = dlg.popdown
        dlg.manage()
    elif dlg.proceeded:
        cb_setup_warning_ok(w, dlg)
    else:
        dlg.popup()
    return dlg


def cb_setup_warning_ok(w, dlg):
    """CbSetupWarningOk."""
    dlg.proceeded = True
    open_setup_dlg(w)
    dlg.popdown()


def open_setup_dlg(w):
    """OpenSetupDlg."""
    dlg = find_dialog(w, DLG_SETUP)
    if dlg is None:
        from . import variables
        dlg = FormDialog(w, DLG_SETUP)
        dlg.wm_close = dlg.popdown
        form = dlg
        for name, user, cb in (
                ("close", 0x0101, dlg.popdown), ("separ", 0x0103, None),
                ("varDefs", 0x0105, lambda: open_var_def_list_dlg(w)),
                ("reactionVars", 0x0107,
                 lambda: variables.open_vars_edit_dlg(w, False)),
                ("particleVars", 0x0109,
                 lambda: variables.open_vars_edit_dlg(w, True))):
            if cb is None:
                b = vc.Separator(form, name)
            else:
                b = vc.PushButton(form, name)
                b.clicked.connect(cb)
            b.xm_user = user
            form.xm_place(b)
        dlg.manage()
    else:
        dlg.popup()
    return dlg


# Variable definitions ##################################################

def open_var_def_list_dlg(w):
    """OpenVarDefListDlg."""
    dlg = find_dialog(w, DLG_VARDEFLIST)
    if dlg is None:
        dlg = _message_dialog(w, DLG_VARDEFLIST)
        dlg.ok.hide()
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.wm_close = dlg.popdown
        dlg.list = scrolled_list(dlg, "list", "browse_select")
        dlg.list.default_callbacks.append(
            lambda pos: _edit_at(w, pos))
        w.add_dependent(dlg.list, api.N_NOW | api.N_VARDEFS,
                        lambda *a: dw_var_def_list(w, dlg))
        for name, cb in (("add", lambda: open_var_def_create_dlg(w)),
                         ("change", lambda: cb_var_def_list_edit(w, dlg)),
                         ("delete", lambda: cb_var_def_list_del(w, dlg))):
            dlg.add_button(name, cb)
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def _var_defs(w):
    return w.lib.group(w.lib.get(w.subset, "Doc.varDefs"))


def dw_var_def_list(w, dlg):
    """DwVarDefList."""
    dlg.list.set_items([corelib.text(w.dll.PyVarDefName(vd))
                        for vd in _var_defs(w)])


def _edit_at(w, pos):
    """CbVarDefListEdit from a double click (item position pos)."""
    open_var_def_edit_dlg(w, _var_defs(w)[pos - 1])


def cb_var_def_list_edit(w, dlg):
    """CbVarDefListEdit (Change)."""
    pos = dlg.list.positions()
    if len(pos) == 1:
        open_var_def_edit_dlg(w, _var_defs(w)[pos[0] - 1])


def cb_var_def_list_del(w, dlg):
    """CbVarDefListDel."""
    pos = dlg.list.positions()
    if len(pos) == 1:
        w.dll.DelVarDef(w.subset, _var_defs(w)[pos[0] - 1])
        w.dll.UndoMark(w.subset)


def open_var_def_create_dlg(w):
    """OpenVarDefCreateDlg."""
    dlg = find_dialog(w, DLG_VARDEFCREATE)
    if dlg is None:
        dlg = _message_dialog(w, DLG_VARDEFCREATE)
        dlg.callbacks["ok"].append(lambda: cb_var_def_create(w, dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.wm_close = dlg.popdown
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        lab = vc.Label(form, "nameLabel")
        lab.xm_user = 0x0101
        form.xm_place(lab)
        dlg.name_ = vc.Text(form, "name")
        dlg.name_.xm_user = 0x0201
        form.xm_place(dlg.name_)
        vc.form2table(form)
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def cb_var_def_create(w, dlg):
    """CbVarDefCreate: one word, not the name of a definition."""
    words = [x for x in _split(dlg.name_.text()) if x]
    if len(words) != 1:
        boxes.error_box(w, w.main_resource_ex("errBadName", "error"))
        return
    name = words[0]
    for vd in _var_defs(w):
        if corelib.text(w.dll.PyVarDefName(vd)) == name:
            boxes.error_box(w, w.main_resource_ex("errDuplicateName",
                                                  "error"))
            return
    vd = w.dll.AddVarDef(w.subset, corelib.cstr(name))
    w.dll.UndoMark(w.subset)
    open_var_def_edit_dlg(w, vd)
    dlg.name_.setText("")
    dlg.popdown()


def _split(s):
    """The words of s as sscanf %s reads them (separated by C spaces)."""
    out = []
    word = ""
    for c in s:
        if c in SPACES:
            if word:
                out.append(word)
            word = ""
        else:
            word += c
    if word:
        out.append(word)
    return out


class VarDefEditDialog(MessageDialog):
    """CreateVarDefEditDlg: one per definition, its form named after the
    address of the definition."""

    def __init__(self, w, vd):
        super().__init__(w, DLG_VARDEFEDIT, auto_unmanage=False)
        self.w = w
        self.vd = vd
        self.help.hide()
        self.callbacks["ok"].append(self.cb_accept)
        self.callbacks["cancel"].append(self.popdown)
        self.wm_close = self.popdown
        w.add_dependent(self, api.N_DEL, self.dw_track_delete, vd)
        form = vc.Form(self, "0x%x" % vd)
        self.xm_place(form)
        items = []

        def add(kind, name, user, ref=None):
            if kind == "l":
                x = vc.Label(form, name)
            elif kind == "x":
                x = vc.Text(form, name)
            else:
                x = vc.ToggleButton(form, name)
            x.xm_user = user
            form.xm_place(x)
            items.append(x)
            return x
        add("l", "descrLabel", 0x0101)
        self.descr = add("x", "descr", 0x0201)
        add("l", "typeLabel", 0x0102)
        self.type_ = self._option(form, "typeMenu", "type", 0x0202, (
            ("string", api.VDT_STRING), ("float", api.VDT_FLOAT),
            ("int", api.VDT_INT)))
        add("l", "useForLabel", 0x0103)
        self.use_for = self._option(form, "useForMenu", "useFor", 0x0203, (
            ("reactions", api.VDF_REACTIONS),
            ("particles", api.VDF_PARTICLES)))
        self.no_export = add("t", "noExport", 0x0104)
        vc.form2table(form)
        self.reset()
        self.manage()

    @staticmethod
    def _option(form, menu, name, user, entries):
        pd = vc.Pulldown(form, menu)
        for item, value in entries:
            act = pd.add_item(item)
            act.xm_user = value
        om = vc.OptionMenu(form, name, pd)
        om.xm_user = user
        form.xm_place(om)
        return om

    def reset(self):
        """ResetVarDefEditDlg."""
        lib = self.w.lib
        vd = self.vd
        self.setWindowTitle(corelib.text(self.w.dll.PyVarDefName(vd)))
        self.descr.setText(corelib.text(self.w.dll.PyVarDefDescr(vd)))
        vc.set_option_menu_value(self.type_, lib.get(vd, "VarDef.type"))
        flags = lib.get(vd, "VarDef.flags")
        vc.set_option_menu_value(self.use_for, flags & api.VDFM_APPLY)
        self.no_export.set_state(bool(flags & api.VDF_NOEXPORT), False)

    def cb_accept(self):
        """CbVarDefEditAccept."""
        dll = self.w.dll
        ss = self.w.subset
        dll.SetVarDefStr(ss, self.vd, VDS_DESCR,
                         corelib.cstr(self.descr.text()))
        f = vc.get_option_menu_value(self.use_for)
        if self.no_export.isChecked():
            f |= api.VDF_NOEXPORT
        dll.ChangeVarDef(ss, self.vd, vc.get_option_menu_value(self.type_),
                         f)
        dll.UndoMark(ss)
        self.popdown()

    def dw_track_delete(self, widget, evt, obj, vd):
        """DwTrackDelete: the dialog destroyed with its definition."""
        if evt == api.N_DEL and obj == vd:
            self.w.del_dependent(self)
            self.destroy_()


def open_var_def_edit_dlg(w, vd):
    """OpenVarDefEditDlg."""
    for d in w.findChildren(VarDefEditDialog):
        if d.vd == vd and not d.destroyed_ and d.window_ is w:
            d.reset()
            d.popup()
            return d
    return VarDefEditDialog(w, vd)
