"""The error box of the widget helpers (vacreate.c, ErrorBox) and the
About box (aminfo.c). Both are modeless, as in the Motif version: an
error box is made once per window or dialog, a second error is added to
its text after a line "---" and the box is shown again; OK destroys it."""

from ...divgeo.dialogs.base import MessageDialog, XmDialog

DLG_ERROR_BOX = "errorBox"
DLG_ABOUT = "dlgAbout"


def _owner(parent):
    """(window, dialog) of a widget an error box is made on."""
    if isinstance(parent, XmDialog):
        return parent.window_, parent
    return parent, None


def find_dialog(owner, name):
    """XtNameToWidget(owner, "*NAME"): a dialog of a view window (not one
    of its subset windows), or a dialog made on a dialog; None if none."""
    for d in owner.findChildren(XmDialog, name):
        if d.destroyed_:
            continue
        if isinstance(owner, XmDialog) or d.window_ is owner:
            return d
    return None


_find = find_dialog


def error_box(parent, text):
    """ErrorBox(w, name): name is the text."""
    window, dialog = _owner(parent)
    dlg = _find(parent, DLG_ERROR_BOX)
    if dlg is None:
        dlg = MessageDialog(window, DLG_ERROR_BOX, text, auto_unmanage=False,
                            parent=dialog, dialog_type="dialog_error")
        dlg.cancel.hide()
        dlg.help.hide()
        dlg.callbacks["ok"].append(dlg.destroy_)
        dlg.wm_close = dlg.destroy_
        dlg.manage()
    else:
        dlg.set_message(dlg.message_text() + "\n---\n" + text)
        dlg.popup()
    return dlg


def show_about_dlg(w):
    """ShowAboutDlg."""
    dlg = _find(w, DLG_ABOUT)
    if dlg is None:
        dlg = MessageDialog(w, DLG_ABOUT, auto_unmanage=False,
                            dialog_type="dialog_information")
        dlg.set_message(dlg.resource("messageString", "MessageString") or "")
        dlg.callbacks["ok"].append(dlg.popdown)
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.cancel.hide()
        dlg.help.hide()
        dlg.manage()
    else:
        dlg.popup()
    return dlg
