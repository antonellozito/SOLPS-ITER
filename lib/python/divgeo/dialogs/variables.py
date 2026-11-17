"""The dialogs of the variables (x_vars.c): the Variables dialog of a
variable set, a grid of its variables from their definitions, with Set
all, Reset all, Hold, a menu per field (reset, compare, display) and the
file selection for file-name variables; the list of invalid variables.
The core part of the callbacks is in the library (src/py/py_vars.c)."""

import ctypes
import os

from PySide6 import QtCore, QtWidgets

from ..core import api, lib as corelib
from . import boxes, files, helpwin
from . import vacreate as vc
from .base import FormDialog, create_ok_cancel_dialog, find_dialog
from .files import FileSelectionDialog

# What ResetVarsDlgField updates
RF_NEWVAL, RF_OLDVAL, RF_SEL, RF_SENS = 0x1, 0x2, 0x4, 0x8
RF_VALUE, RF_CLEARVAL, RF_HOLD = 0x10, 0x20, 0x40
# What the message line shows (its userData)
XT_VEF, XT_NEWVAL, XT_COMP = 0x65438953, 0x23490834, 0x53190783
CV_MARK_EQUAL, CV_MARK_NOT_EQUAL, CV_MARK_GT, CV_MARK_GE, CV_MARK_LT, \
    CV_MARK_LE = range(1, 7)
COL_W = 8


def group_list(w, group):
    """The members of a core group."""
    n = w.dll.PyGroupList(group, None, 0)
    items = (ctypes.c_void_p * max(n, 1))()
    w.dll.PyGroupList(group, items, n)
    return [items[k] for k in range(n)]


def _str(w, ptr):
    return w.lib.string_at(ptr)


def _strex(widget, name, cls, fmt, *args):
    names, classes = vc.path_of(widget)
    return files.resource_string_ex(vc._db(widget), names, classes, name,
                                    cls, fmt, *args)


class VarsEditField:
    """A variable of the dialog: its definition and its widgets."""

    def __init__(self, dlg, vd):
        self.dlg = dlg
        self.vd = vd
        lib = dlg.w.lib
        self.var_type = lib.get(vd, "VarDef.varType")
        self.flags = lib.get(vd, "VarDef.flags")
        self.def_type = lib.get(vd, "VarDef.type")
        self.descr = _str(dlg.w, lib.get(vd, "VarDef.descr")) or ""
        self.help = _str(dlg.w, lib.get(vd, "VarDef.help"))
        self.row = lib.get(vd, "VarDef.row")
        self.col = lib.get(vd, "VarDef.col")
        self.new_value = None
        self.bn_set = None
        self.sensitive = False


class VarsEditDlg:
    def __init__(self, window, obj):
        w = window
        self.w = w
        self.a = w.app
        self.obj = obj
        self.keep_hold = 0
        self.popup_field = None
        self.n_sensitive = 0
        self.view_destroyed = False
        self.fields = []
        self.dlg = dlg = FormDialog(w, "dlgVarsEdit")
        dlg.data = self
        dlg.wm_close = self.close
        dlg.setWindowTitle(_str(w, w.dll.GetObjDescription(w.view, obj)))
        self.vsd = w.lib.get(obj, "VarSet.def")
        row = vc.row_column(dlg, "rowcol")
        dlg.xm_place(row)
        self.bn_collapse = vc.ArrowButton(row, "collapse", "up")
        row.xm_place(self.bn_collapse)
        self.bn_collapse.clicked.connect(
            lambda: self.collapse(not self.collapsed()))
        vds = group_list(w, w.lib.get(self.vsd, "VarSetDef.varDefs"))
        fields = [VarsEditField(self, vd) for vd in vds]
        i = sum(1 for f in fields if f.var_type & api.VTM_HASGROUP)
        j = len(fields) - i
        k = sum(1 for f in fields if f.flags & api.VFM_MULTIPLE)
        self.bn_accept_all = self.bn_reset_all = None
        if j and not i:
            self.bn_accept_all = vc.PushButton(row, "setAll")
            row.xm_place(self.bn_accept_all)
            self.bn_accept_all.clicked.connect(self.accept_all)
            self.bn_reset_all = vc.PushButton(row, "resetAll")
            row.xm_place(self.bn_reset_all)
            self.bn_reset_all.clicked.connect(self.reset_all)
        self.sw_hold = None
        if k:
            self.sw_hold = vc.ToggleButton(row, "hold")
            self.sw_hold.set_state(False, False)
            row.xm_place(self.sw_hold)
        close = vc.PushButton(row, "close")
        row.xm_place(close)
        close.clicked.connect(self.close)
        bn_help = vc.PushButton(row, "help")
        row.xm_place(bn_help)
        bn_help.clicked.connect(
            lambda: w.help_on_widget(bn_help))
        self.main_form = form1 = vc.Form(dlg, "form1")
        dlg.xm_place(form1)
        r = {}
        vc.create_widget_system(
            form1,
            "s8:separ",
            "l2?:message", "message",
            "s2:separ",
            "$5?:varsFrame", vc.scrolled_window, None, "varsFrame",
            refs=r)
        self.message = r["message"]
        self.vars_frame = r["varsFrame"]
        self._popup_menu()
        self.vars_form = form = vc.Form(self.vars_frame, "vars")
        self.vars_frame.set_work_window(form)
        for f in fields:
            self.fields.append(f)
            self._field_widgets(f)
        self.popup_field = None
        w.add_dependent(dlg, api.N_NEWAPP | api.N_ALT | api.N_DEL |
                        api.N_DESTROYVIEW, None, self.dw_notify)
        dlg.manage()
        w.vars_dialogs.append(self)

    # Creation

    def _menu_res(self, menu, name, res, default=None):
        """A resource of an entry of the menu of the fields: the menu is a
        popup of a widget foo of the dialog shell, the compare menu a
        pulldown in its shell."""
        names, classes = self.dlg.path()
        names = names[:-1] + ["foo", "popup_varsPopupMenu"]
        classes = classes[:-1] + ["Core", "XmMenuShell"]
        names += [menu, name, res]
        classes += ["XmRowColumn", "XmPushButton", res[0].upper() + res[1:]]
        value = self.w.application.db.get(names, classes)
        return default if value is None else value

    def _popup_menu(self):
        """The menu of a field (third button): reset, compare, display;
        the help line of an entry in the message line."""
        m = self.menu = QtWidgets.QMenu(self.dlg)

        def entry(menu, qmenu, name):
            act = qmenu.addAction(vc.mnemonic_free(self._menu_res(
                menu, name, "labelString", name)))
            act.hovered.connect(lambda: self.message.set_label(
                self._menu_res(menu, name, "helpLine", "")))
            return act

        entry("varsPopupMenu", m, "reset").triggered.connect(
            self.reset_var_n)
        m.addSeparator()
        self.mb_compare = m.addMenu(vc.mnemonic_free(self._menu_res(
            "varsPopupMenu", "compare", "labelString", "compare")))
        for name, mode in (("equal", CV_MARK_EQUAL),
                           ("not_equal", CV_MARK_NOT_EQUAL),
                           ("gt", CV_MARK_GT), ("ge", CV_MARK_GE),
                           ("lt", CV_MARK_LT), ("le", CV_MARK_LE)):
            entry("compareMenu", self.mb_compare, name).triggered.connect(
                lambda checked=False, md=mode: self.compare(md))
        self.mb_display = entry("varsPopupMenu", m, "display")
        self.mb_display.triggered.connect(self.display)
        m.aboutToHide.connect(lambda: self.message.set_label(""))

    def _field_widgets(self, f):
        form = self.vars_form

        def add(wg, dx):
            form.xm_place(wg, f.col * COL_W + dx + 1, f.row + 1)
            wg.xm_user = f
            wg.installEventFilter(self.filter)

        name = vc.Label(form, "varName")
        name.set_label(f.descr)
        name.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        add(name, 1)
        if f.help is not None:
            bn = vc.PushButton(form, "varHelp")
            bn.clicked.connect(lambda: self.vd_help(f))
            self._arm(bn, f)
            add(bn, 2)
        if not f.var_type & api.VTM_HASGROUP:
            f.new_value = t = vc.Text(form, "newValueText")
            if f.var_type & api.VTF_FILENAME:
                t.returnPressed.connect(lambda: self.open_file_set_dlg(f))
            t.textChanged.connect(lambda *a: self.input(f))
            add(t, 3)
        else:
            bn = vc.PushButton(form, "resetVar")
            bn.clicked.connect(lambda: self.reset_var(f))
            self._arm(bn, f)
            add(bn, 3)
        f.bn_set = bn = vc.PushButton(form, "set")
        bn.clicked.connect(lambda: self.accept_var(f))
        self._arm(bn, f)
        add(bn, 5)

    def _arm(self, bn, f):
        """The arm and disarm callbacks (CbVarsEditFocus)."""
        bn.pressed.connect(lambda: self.reset_field(f, RF_OLDVAL))
        bn.released.connect(lambda: self.reset_field(f, RF_CLEARVAL))

    @property
    def filter(self):
        if not hasattr(self, "_filter"):
            self._filter = _FieldEvents(self)
        return self._filter

    # The fields

    def reset_field(self, f, flags):
        """ResetVarsDlgField."""
        w = self.w
        dll = w.dll
        p = dll.GetVarEx(w.app, self.obj, f.vd)
        kind = dll.PyVarValueKind(p)
        if flags & (RF_NEWVAL | RF_OLDVAL):
            s = _str(w, dll.PyVarValueDescr(w.view, p, f.vd)) or ""
            s = _strex(self.dlg, "strOldVal" if flags & RF_OLDVAL
                       else "strNewVal", "StrVal", "$(VAR)%s$(VALUE)%s",
                       f.descr, s)
            if self.message.xm_user == XT_COMP:
                self.message.xm_user = None
            else:
                self.message.set_label(s)
                self.message.xm_user = XT_NEWVAL if flags & RF_NEWVAL \
                    else XT_VEF
        if flags & RF_CLEARVAL:
            if self.message.xm_user == XT_VEF:
                self.message.set_label("")
                self.message.xm_user = None
        if flags & RF_VALUE:
            self.keep_hold += 1
            if f.new_value is not None:
                vc.set_text(f.new_value, "" if kind else (_str(w, p) or ""))
            self.keep_hold -= 1
        if flags & RF_SEL:
            if f.var_type & api.VTM_HASGROUP:
                dll.MarkGroup(self.a, p, 10)
                w.pump()
        if flags & RF_SENS:
            b = -1
            if not f.var_type & api.VTM_HASGROUP and \
                    f.new_value is not None and f.bn_set is not None:
                s = vc.text_of(f.new_value)
                if kind == 1:
                    b = 0
                elif kind == 2:
                    b = int(bool(s))
                else:
                    b = int((_str(w, p) or "") != s)
            elif f.var_type & api.VTM_HASGROUP and f.bn_set is not None:
                b = 1
            if b >= 0:
                if (not b) != (not f.sensitive):
                    self.n_sensitive += 1 if b else -1
                    f.sensitive = bool(b)
                if flags & RF_HOLD and self.sw_hold is not None:
                    if not self.n_sensitive:
                        self.sw_hold.set_state(False, False)
                _sensitive(f.bn_set, f.sensitive)
                if self.bn_accept_all is not None:
                    _sensitive(self.bn_accept_all, self.n_sensitive)
                if self.bn_reset_all is not None:
                    _sensitive(self.bn_reset_all, self.n_sensitive or (
                        self.sw_hold is not None and
                        self.sw_hold.isChecked()))

    def accept_field(self, f):
        """AcceptVarsDlgField: 0 or the error code."""
        w = self.w
        text = None if f.var_type & api.VTM_HASGROUP else \
            corelib.cstr(vc.text_of(f.new_value))
        r = w.dll.PyAcceptVarsField(w.view, self.obj, f.vd, text)
        w.pump()
        return r

    def _error_text(self, f, i):
        w = self.w
        if i != api.ERR_USEDBY:
            return w.str_(i)
        return _str(w, w.dll.WhyLockedEx(w.view, self.obj, f.vd))

    def is_empty_field(self, f):
        """IsEmptyField (the test of the object type, never a group, kept
        as it is)."""
        if f.def_type & api.VTM_HASGROUP:
            return False
        if f.new_value is None:
            return False
        return not vc.text_of(f.new_value).split()

    # Callbacks

    def input(self, f):
        """CbVarsDlgInput."""
        if self.sw_hold is not None and not self.keep_hold:
            if not self.sw_hold.isChecked():
                self.sw_hold.set_state(True, True)
        self.reset_field(f, RF_SENS)

    def accept_var(self, f):
        """CbVarsDlgAcceptVar."""
        i = self.accept_field(f)
        if i:
            boxes.error_box(self.dlg, self._error_text(f, i))
        else:
            self.w.dll.UndoMark(self.a)
            self.w.pump()
            self.reset_field(f, RF_NEWVAL | RF_SENS | RF_HOLD)

    def reset_var(self, f):
        """CbVarsDlgResetVar."""
        self.reset_field(f, RF_VALUE | RF_SEL | RF_SENS | RF_HOLD)
        self.w.dll.UndoMark(self.a)
        self.w.pump()

    def reset_var_n(self):
        """CbVarsDlgResetVar_n (from the menu of a field)."""
        if self.popup_field is None:
            return
        self.reset_var(self.popup_field)

    def accept_all(self):
        """CbVarsDlgAccept."""
        w = self.w
        failed = False
        for f in list(self.fields):
            if f.flags & api.VFM_MULTIPLE and self.is_empty_field(f):
                continue
            i = self.accept_field(f)
            if i:
                w.dll.Cancel(self.a)
                w.pump()
                boxes.error_box(self.dlg, "%s : %s" % (
                    f.descr, self._error_text(f, i)))
                failed = True
                break
        if failed:
            w.dll.Cancel(self.a)
            w.pump()
        else:
            for f in self.fields:
                self.reset_field(f, RF_SENS | RF_HOLD)
            if self.sw_hold is not None:
                self.sw_hold.set_state(False, False)
            w.dll.UndoMark(self.a)
            w.pump()

    def reset_all(self):
        """CbVarsDlgReset."""
        w = self.w
        for f in self.fields:
            self.reset_field(f, RF_SEL | RF_VALUE | RF_SENS | RF_HOLD)
        w.dll.UndoMark(self.a)
        w.pump()
        if self.sw_hold is not None:
            self.sw_hold.set_state(False, False)
        w.dll.UndoMark(self.a)
        w.pump()

    def close(self):
        """CbVarsDlgClose."""
        self.dlg.popdown()

    def vd_help(self, f):
        """CbVarsEditDlgVDHelp."""
        helpwin.display_help_text(self.w, None, f.descr)
        helpwin.display_help_text(self.w, f.help)

    def compare(self, mode):
        """CbVarsEditCompare_p."""
        w = self.w
        f = self.popup_field
        if f is None or f.new_value is None:
            return
        if not f.flags & api.VFM_MULTIPLE:
            boxes.error_box(self.dlg, vc.resource_string(self.dlg,
                                                         "errBadScope"))
            return
        n = w.dll.PyVarsCompare(w.view, self.obj, f.vd, mode, corelib.cstr(
            vc.text_of(f.new_value)))
        w.pump()
        if n == -2:
            return
        if n == -1:
            boxes.error_box(self.dlg, vc.resource_string(self.dlg,
                                                         "errBadNumber"))
            return
        self.message.set_label(_strex(self.dlg, "msgObjectsMatching", None,
                                      "$(COUNT)%d", n))
        self.message.xm_user = XT_COMP

    def display(self):
        """CbVarsEditDisplay_p."""
        w = self.w
        f = self.popup_field
        if f is None:
            return
        if not f.flags & api.VFM_MULTIPLE:
            boxes.error_box(self.dlg, vc.resource_string(self.dlg,
                                                         "errBadScope"))
            return
        w.dll.PyVarsDisplay(w.view, self.obj, f.vd)
        w.pump()

    def popup_menu(self, f, pos):
        """ActVarsDlgPopupMenu."""
        self.popup_field = f
        multiple = bool(f.flags & api.VFM_MULTIPLE)
        self.mb_compare.setEnabled(multiple)
        self.mb_display.setEnabled(multiple)
        self.menu.popup(pos)

    # Collapse

    def collapsed(self):
        return self.main_form.isHidden()

    def collapse(self, state):
        """CollapseVarsDlg."""
        if state and not self.collapsed():
            self.main_form.hide()
            self.bn_collapse.set_direction("down")
        elif not state and self.collapsed():
            self.main_form.show()
            self.bn_collapse.set_direction("up")

    # Notifications

    def destroy(self):
        """The dialog destroyed (CbDestroyVarsEditDlg)."""
        w = self.w
        w.del_dependent(self.dlg)
        if not self.view_destroyed and self in w.vars_dialogs:
            w.vars_dialogs.remove(self)
        self.dlg.destroy_()

    def dw_notify(self, widget, kind, obj, user=None):
        """DwNotifyVarsDlg."""
        from ..app.window import CHF_MARK, CHF_VARDEFS, CHF_VARS
        w = self.w
        if kind == api.N_DESTROYVIEW:
            self.view_destroyed = True
            return
        if kind == api.N_DEL and obj != self.obj:
            return
        if kind in (api.N_DEL, api.N_NEWAPP):
            self.destroy()
            return
        if kind == api.N_ALT:
            if w.changes & CHF_VARDEFS:
                self.destroy()
                return
            if not self.dlg.isVisible():
                return
        if w.changes & CHF_VARS or kind == api.N_USER:
            self.dlg.setWindowTitle(_str(w, w.dll.GetObjDescription(
                w.view, self.obj)))
        if w.changes & (CHF_VARS | CHF_MARK) or kind == api.N_USER:
            hold = self.sw_hold is not None and self.sw_hold.isChecked()
            for f in list(self.fields):
                self.reset_field(f, RF_SENS | (0 if hold else RF_VALUE))

    # File names

    def open_file_set_dlg(self, f):
        """CbVarsDlgOpenFileSetDlg."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        open_vars_file_set_dlg(w, f)


def _sensitive(widget, state):
    """SetSensitiveEx."""
    if widget.isEnabled() != bool(state):
        widget.setEnabled(bool(state))


class _FieldEvents(QtCore.QObject):
    """The translations of the fields: the third button opens the menu of
    the field; the focus of a text shows its value in the message line."""

    def __init__(self, dlg):
        super().__init__(dlg.dlg)
        self.dlg = dlg

    def eventFilter(self, obj, event):
        f = getattr(obj, "xm_user", None)
        if not isinstance(f, VarsEditField):
            return False
        t = event.type()
        if t == QtCore.QEvent.MouseButtonPress and \
                event.button() == QtCore.Qt.RightButton:
            self.dlg.popup_menu(f, event.globalPosition().toPoint())
            return True
        if isinstance(obj, QtWidgets.QLineEdit):
            if t == QtCore.QEvent.FocusIn:
                self.dlg.reset_field(f, RF_OLDVAL)
            elif t == QtCore.QEvent.FocusOut:
                self.dlg.reset_field(f, RF_CLEARVAL)
        return False


def open_vars_edit_dlg(window, obj):
    """OpenVarsEditDlg."""
    for d in list(window.vars_dialogs):
        if d.obj == obj:
            d.dw_notify(None, api.N_USER, None)
            d.dlg.popup()
            d.collapse(False)
            return d.dlg
    d = VarsEditDlg(window, obj)
    d.dw_notify(None, api.N_USER, None)
    return d.dlg


def open_vars_file_set_dlg(window, f):
    """OpenVarsFileSetDlg: the callback keeps the field of the first
    call, as in Motif."""
    w = window
    dlg = find_dialog(w, "dlgVarsFileSet")
    if dlg is None:
        dlg = FileSelectionDialog(w, "dlgVarsFileSet")
        dlg.manage()
        s = os.environ.get(w.str_(api.ENV_VARSFILESETMASK))
        if s is not None and not dlg.set_dir_mask(s):
            w.error_box(w.str_(api.ERR_BADMASK))
        dlg.callbacks["ok"].append(lambda: _vars_file_set(w, dlg, f))
        dlg.callbacks["cancel"].append(dlg.popdown)
    else:
        dlg.do_search()
        dlg.popup()
    return dlg


def _vars_file_set(w, dlg, f):
    """CbVarsFileSet."""
    w.dll.SetActiveView(w.view)
    w.pump()
    vc.set_text(f.new_value, dlg.text.text())
    dlg.popdown()


# Invalid variables ########################################################

class InvalidVarsDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgInvalidVars")
        dlg.data = self
        dlg.callbacks["ok"].append(self.where)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        self.list = vc.ScrolledList(dlg, "list")
        dlg.xm_place(self.list)
        self.list.default_callbacks.append(self.where)
        w.add_dependent(dlg, api.N_NOW | api.N_ALT | api.N_NEWAPP, None,
                        self.dw_invalid_vars)
        self.reset()
        dlg.manage()

    def reset(self):
        """ResetInvalidVarsDlg."""
        w = self.w
        items = []
        proc = api.ITEMPROC(lambda label, value: items.append(
            label.decode("latin-1")))
        state = w.dll.PyInvalidVarsItems(w.view, proc)
        self.list.set_items([])
        self.dlg.ok.setEnabled(bool(state))
        self.list.set_items(items)
        self.list.select_pos(1, True)

    def dw_invalid_vars(self, widget, kind, obj, user=None):
        """DwInvalidVars."""
        if not self.dlg.isVisible():
            return
        self.reset()

    def where(self):
        """CbInvalidVarsWhere."""
        w = self.w
        pos = self.list.selected_positions()
        if not pos:
            return
        reset = ctypes.c_int()
        vs = w.dll.PyInvalidVarsWhere(w.view, pos[0] if len(pos) == 1
                                      else 0, ctypes.byref(reset))
        w.pump()
        if reset.value:
            self.reset()
            return
        if not vs:
            return
        open_vars_edit_dlg(w, vs)
        w.dll.UndoMark(w.app)
        w.pump()


def open_invalid_vars_dlg(window):
    """OpenInvalidVarsDlg."""
    dlg = find_dialog(window, "dlgInvalidVars")
    if dlg is not None:
        dlg.data.reset()
        dlg.popup()
    else:
        dlg = InvalidVarsDlg(window).dlg
    return dlg
