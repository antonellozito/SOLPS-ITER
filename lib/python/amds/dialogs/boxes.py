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


def _find(owner, name):
    for d in owner.findChildren(XmDialog, name):
        if not d.destroyed_:
            return d
    return None


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
