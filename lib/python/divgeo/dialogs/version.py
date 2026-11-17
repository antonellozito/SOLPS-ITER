"""The dialogs of the first start and of a new version (x_verdlg.c): the
signature and the version last used in the preferences file, a message
dialog when either is new."""

import os
import re
import sys

from ..core import prefs
from . import files, helpwin
from .base import MessageDialog

PSTR_PREFSPRESENT = "DG.Signature"
PSTR_DGVERSION = "DG.LastUsedVersion"
PVAL_PREFSPRESENT = "XDivGeo"


def _message_dialog(window, name, no_cancel):
    """CreateDialogEx with CDLG_MESSAGE: a message dialog that is not
    unmanaged by its buttons; Cancel and the close button pop it down."""
    dlg = MessageDialog(window, name, auto_unmanage=False)
    dlg.callbacks["cancel"].append(dlg.popdown)
    dlg.wm_close = dlg.popdown
    if no_cancel:
        dlg.cancel.hide()
    return dlg


def _set_message(dlg, fmt, *args):
    """SetMessageString with GetResourceStringEx of messageStringEx."""
    names, classes = dlg.path()
    dlg.set_message(files.resource_string_ex(
        dlg.window_.application.db, names, classes, "messageStringEx", None,
        fmt, *args))


def open_new_prefs_file_dlg(window, use_prefs_file):
    """OpenNewPrefsFileDlg: None when the file is known."""
    lib = window.lib
    if use_prefs_file:
        if prefs.get_string(lib, PSTR_PREFSPRESENT) == PVAL_PREFSPRESENT:
            return None
        prefs.set_string(lib, PSTR_PREFSPRESENT, PVAL_PREFSPRESENT)
        if prefs.get_string(lib, PSTR_PREFSPRESENT) != PVAL_PREFSPRESENT:
            fn = prefs.file_name()
            # the message of the Motif version, file name in single quotes
            sys.stderr.write("Failure to initialize the preferences file "
                             "\x27%s\x27\n" % ("(null)" if fn is None
                                                 else fn))
            sys.stderr.flush()
            os._exit(1)
    dlg = window.findChild(MessageDialog, "dlgNewPrefsFile")
    if dlg is None:
        dlg = _message_dialog(window, "dlgNewPrefsFile", True)
        dlg.callbacks["ok"].append(dlg.popdown)
        dlg.callbacks["help"].append(lambda: window.help_on(dlg))
        fn = prefs.file_name()
        _set_message(dlg, "$(PATH)%s", "(null)" if fn is None else fn)
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def open_new_version_dlg(window, only_if_needed):
    """OpenNewVersionDlg."""
    lib = window.lib
    last = 0
    new = 0
    if only_if_needed:
        new = window.dll.GetPyVersion()
        if new % 10:
            sys.stderr.write("OpenNewVersionDlg:Interim version\n")
            sys.stderr.flush()
        buf = "%d" % new
        s = prefs.get_string(lib, PSTR_DGVERSION)
        m = re.match(r"\s*([+-]?\d+)", s)
        last = int(m.group(1)) if m else 0
        prefs.set_string(lib, PSTR_DGVERSION, buf)
        if s == buf:
            return None
    dlg = window.findChild(MessageDialog, "dlgNewVersion")
    if dlg is None:
        dlg = _message_dialog(window, "dlgNewVersion", False)
        dlg.callbacks["ok"].append(lambda: _new_version_ok(window, dlg))
        dlg.callbacks["help"].append(lambda: window.help_on(dlg))
        v = lambda k: lib.string_at(window.dll.GetPyVersionStr(k))
        _set_message(dlg, "$(OLDVERSION)%s$(VERSION)%s", v(last), v(new))
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def _new_version_ok(window, dlg):
    """CbNewVersionOk: the topic of helpToDisplay of the dialog (CbHelpMenu
    with the dialog), then the dialog popped down."""
    topic = dlg.resource("helpToDisplay", "HelpToDisplay")
    if topic is not None:
        helpwin.display_help_topic(window, topic)
    dlg.popdown()
