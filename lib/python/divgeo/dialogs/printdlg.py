"""File > Print (x_fileio.c): the picture of the view as PostScript, to a
file or into the standard input of a command."""

import os
import subprocess

from ..core import api, lib as corelib
from . import vacreate as vc
from .base import create_ok_cancel_dialog, find_dialog

CMT_CMD, CMT_FILE = 1, 2

# The command as system() runs it, its input then read to the end so that
# DivGeo never writes into a closed pipe
_SHELL = 'sh -c "$1"; cat > /dev/null'


class FilePrintDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgPrint")
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        r = self.r = {}
        vc.create_widget_system(
            form,
            "*:cmdTypeMenu",
            "b@:file", CMT_FILE,
            "b@:cmd", CMT_CMD,
            "-:",
            "o@?:cmdType", 0x0101, "cmdType",
            "x@?:command", 0x0201, "command",
            "s@:separator", 0x0002,
            "l@:widthLabel", 0x0103,
            "x@?:width", 0x0203, "width",
            "l@:heightLabel", 0x0104,
            "x@?:height", 0x0204, "height",
            "l@:marginLabel", 0x0105,
            "x@?:margin", 0x0205, "margin",
            "t@?:fit", 0x0006, "fit",
            refs=r)
        vc.form2table(form)
        dlg.manage()

    def _number(self, name):
        n, value = vc.scan_double(vc.text_of(self.r[name]))
        return value if n == 1 else None

    def ok(self):
        """CbFilePrintOk."""
        w = self.w
        dll = w.dll
        dll.SetActiveView(w.view)
        w.pump()
        values = []
        for name in ("width", "height", "margin"):
            v = self._number(name)
            if v is None:
                w.error_box(w.str_(api.ERR_INVNUMBERS))
                return
            values.append(v)
        width, height, margin = values
        ps = dll.CreatePsView(w.app, width * 72, height * 72, margin * 72)
        w.pump()
        if not ps:
            w.error_box(w.str_(api.ERR_PSVIEWSIZE))
            return
        w.lib.set(ps, "View.bEditTopology",
                  w.lib.get(w.view, "View.bEditTopology"))
        if self.r["fit"].isChecked():
            dll.ShowPicture(ps)
            w.pump()
        s = vc.text_of(self.r["command"])
        r = 0
        if vc.get_option_menu_value(self.r["cmdType"]) == CMT_FILE:
            r = dll.PsViewOutput(ps, corelib.cstr(s), -1, None)
        else:
            r = self._to_command(ps, s)
        w.pump()
        if r is not None:
            if r:
                w.error_box(w.str_(r))
            else:
                self.dlg.popdown()
                dll.PyViewMsgId(w.view, api.MSG_FILEPRINTED)
                w.pump()
        dll.SetViewApp(ps, None)
        dll.FreeView(ps)
        w.pump()

    def _to_command(self, ps, s):
        """The PostScript into a pipe read by the command (the error code,
        None when the command cannot be started: no box then)."""
        try:
            fd = os.pipe()
        except OSError:
            return api.ERR_PIPECREATE
        try:
            subprocess.Popen(["/bin/sh", "-c", _SHELL, "sh", s],
                             stdin=fd[0], close_fds=True)
        except OSError:
            os.close(fd[0])
            os.close(fd[1])
            return None
        os.close(fd[0])
        r = self.w.dll.PsViewOutput(ps, None, fd[1], None)
        if r:
            os.close(fd[1])
        return r


def open_file_print_dlg(window):
    """CbFilePrint, OpenFilePrintDlg."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    dlg = find_dialog(w, "dlgPrint")
    if dlg is not None:
        dlg.popup()
    else:
        dlg = FilePrintDlg(w).dlg
    return dlg
