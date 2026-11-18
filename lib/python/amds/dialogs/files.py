"""File dialogs of a view (amfio.c): File > Open and File > Save as with
the file selection box of Motif (directory mask from AMDSLOADMASK and
AMDSSAVEMASK, else the resources), File > Output (a question with the
name of the output file), and Unsaved work when a changed document is
closed."""

import os

from ...divgeo.dialogs.base import MessageDialog
from ...divgeo.dialogs.files import FileSelectionDialog, resource_string_ex
from ..core import lib as corelib
from . import boxes
from .boxes import find_dialog

DLG_FILE_OPEN = "dlgFileOpen"
DLG_FILE_SAVE = "dlgFileSave"
DLG_FILE_UNSAVED = "dlgFileUnsaved"
DLG_FILE_OUTPUT = "dlgFileOutput"
ENV_LOADMASK = "AMDSLOADMASK"
ENV_SAVEMASK = "AMDSSAVEMASK"


def _error(w, name):
    """ErrorBox on the main window with GetResourceStringEx(name, error)."""
    boxes.error_box(w, w.main_resource_ex(name, "error"))


def _file_dialog(w, name, ok, env):
    dlg = find_dialog(w, name)
    if dlg is None:
        dlg = FileSelectionDialog(w, name)
        dlg.callbacks["ok"].append(lambda: ok(w, dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.findChild(type(dlg.ok_button), "Help").hide()
        mask = os.environ.get(env)
        if mask is not None:
            dlg.set_dir_mask(mask)
        dlg.manage()
    else:
        dlg.do_search()
        dlg.popup()
    return dlg


def open_file_open_dlg(w):
    """OpenFileOpenDlg."""
    return _file_dialog(w, DLG_FILE_OPEN, cb_open, ENV_LOADMASK)


def open_file_save_dlg(w, at_exit):
    """OpenFileSaveDlg."""
    dlg = _file_dialog(w, DLG_FILE_SAVE, cb_save, ENV_SAVEMASK)
    dlg.at_exit = at_exit
    name = w.lib.string(w.subset, "Doc.fileName")
    if name:
        dlg.text.setText(name)
    return dlg


def _output_name(name):
    """The file name with the extension .amo (GetFileExt)."""
    k = max(name.rfind("/"), name.rfind("\\"), name.rfind(":")) + 1
    dot = name.rfind(".", k)
    return (name[:dot] if dot >= 0 else name) + ".amo"


def _question(w, name):
    dlg = MessageDialog(w, name, auto_unmanage=False,
                        dialog_type="dialog_question")
    dlg.set_message(dlg.resource("messageString", "MessageString") or "")
    dlg.callbacks["cancel"].append(dlg.popdown)
    dlg.wm_close = dlg.popdown
    dlg.help.hide()
    return dlg


def open_file_output_dlg(w):
    """OpenFileOutputDlg."""
    name = w.lib.string(w.subset, "Doc.fileName")
    if not name:
        boxes.error_box(w, "No filename")
        return None
    fn = _output_name(name)
    dlg = find_dialog(w, DLG_FILE_OUTPUT)
    if dlg is None:
        dlg = _question(w, DLG_FILE_OUTPUT)
        dlg.callbacks["ok"].append(lambda: cb_output(w, dlg))
    names, classes = dlg.path()
    dlg.set_message(resource_string_ex(
        w.application.db, names, classes, "messageStringEx", "MessageString",
        "$(FILENAME)%s", fn))
    dlg.manage()
    dlg.popup()
    dlg.file_name = fn
    return dlg


def open_file_unsaved_dlg(w):
    """OpenFileUnsavedDlg."""
    dlg = find_dialog(w, DLG_FILE_UNSAVED)
    if dlg is None:
        dlg = _question(w, DLG_FILE_UNSAVED)
        dlg.callbacks["ok"].append(lambda: cb_unsaved_save(w, dlg))
        dlg.add_button("discard", lambda: cb_unsaved_discard(w))
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def cb_open(w0, dlg):
    """CbOpen: the file in a new main window (or a new subset window of
    the main window when opened from a subset)."""
    dll = w0.dll
    lib = w0.lib
    s = dlg.text.text()
    xap = w0.application.xap
    ss = dll.CreateDoc(lib.get(xap, "XApp.db"))
    err = dll.LoadDoc(ss, corelib.cstr(s))
    if err:
        _error(w0, "errFileOpen")
        dll.FreeDoc(ss)
    else:
        config = lib.get(xap, "XApp.config")
        if config:
            dll.UpdateVarDefs(ss, config)
        w0.application.create_view(ss, w0.main_view)
        dlg.popdown()


def cb_save(w, dlg):
    """CbSave."""
    s = dlg.text.text()
    err = w.dll.SaveDoc(w.subset, corelib.cstr(s))
    if err:
        _error(w, "errFileSave")
    else:
        dlg.popdown()
        if getattr(dlg, "at_exit", False):
            w.dll.PyCloseView(w.view, 1)


def cb_unsaved_save(w, dlg):
    """CbUnsavedSave."""
    open_file_save_dlg(w, True)
    dlg.popdown()


def cb_unsaved_discard(w):
    """CbUnsavedDiscard."""
    w.dll.PyCloseView(w.view, 0)


def cb_output(w, dlg):
    """CbOutput."""
    s = dlg.file_name
    err = w.dll.OutputDoc(w.subset, corelib.cstr(s))
    if err:
        _error(w, "errFileOutput")
    else:
        dlg.popdown()
        dlg.file_name = None
