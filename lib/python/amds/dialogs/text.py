"""The text of a reaction (amtext.c): one window per data file (AMJUEL,
HYDHEL, ...) under the main window, the whole file read-only, shown from
the line of the reaction. The data folder is AMDSDATABASEDIR, else the
resource databaseDir, else the folder of the program."""

import os

from PySide6 import QtCore, QtWidgets

from ...divgeo.app.menus import key_sequences, mnemonic_label
from ..core import lib as corelib

DLG_REACTION_TEXT = "dlgReactionText_"
WG_TEXT = "text"
STR_BEGIN = "##BEGIN DATA HERE##"
ENV_DBPATH = "AMDSDATABASEDIR"
SPACES = " \t\n\v\f\r"


class ReactionTextWindow(QtWidgets.QMainWindow):
    """The shell dlgReactionText_shell with the main window
    dlgReactionText_FILE: Window menu, read-only text."""

    def __init__(self, w, name, path, content):
        super().__init__(w, QtCore.Qt.Window)
        self.setObjectName(name)
        self.view_window = w
        self.setWindowTitle(path)
        db = w.application.db
        names = [w.application.name, "primaryShell", "main",
                 DLG_REACTION_TEXT + "shell", name]
        classes = ["AMDS", "ApplicationShell", "XmMainWindow",
                   "TopLevelShell", "XmMainWindow"]
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        bar.setObjectName("textMenuBar")
        n = names + ["textMenuBar", "window"]
        c = classes + ["XmRowColumn", "XmCascadeButton"]
        menu = bar.addMenu(mnemonic_label(
            db.get(n + ["labelString"], c + ["LabelString"]) or "window",
            db.get(n + ["mnemonic"], c + ["Mnemonic"])))
        menu.setObjectName("textWindowMenu")
        menu.menuAction().setObjectName("window")
        n = names + ["textMenuBar", "popup_textWindowMenu", "textWindowMenu",
                     "close"]
        c = classes + ["XmRowColumn", "XmMenuShell", "XmRowColumn",
                       "XmPushButton"]
        close = menu.addAction(mnemonic_label(
            db.get(n + ["labelString"], c + ["LabelString"]) or "close",
            db.get(n + ["mnemonic"], c + ["Mnemonic"])))
        close.setObjectName("close")
        seqs = key_sequences(db.get(n + ["accelerator"], c + ["Accelerator"]))
        if seqs:
            close.setShortcuts(seqs)
            close.setShortcutContext(QtCore.Qt.WindowShortcut)
            self.addAction(close)
        close.triggered.connect(self.popdown)
        self.text = QtWidgets.QPlainTextEdit(self)
        self.text.setObjectName(WG_TEXT)
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text.setPlainText(content)
        self.content = content
        self.setCentralWidget(self.text)
        self.resize(600, 500)

    def closeEvent(self, event):
        """The window manager close: CbUnmap."""
        event.ignore()
        self.popdown()

    def popup(self):
        """XtPopup of the shell."""
        self.show()
        self.raise_()

    def popdown(self):
        """XtPopdown of the shell (CbUnmap)."""
        self.hide()

    def set_top_character(self, pos):
        """XmTextSetTopCharacter: the line of pos at the top."""
        def apply():
            block = self.text.document().findBlock(pos)
            self.text.verticalScrollBar().setValue(block.blockNumber())
        QtCore.QTimer.singleShot(0, apply)


def _find(w, name):
    for child in w.findChildren(ReactionTextWindow, name):
        return child
    return None


def _create(w, path):
    """CreateReactionTextDlg: None if the file cannot be read."""
    short = corelib.text(w.dll.GetShortFName(corelib.cstr(path)))
    try:
        with open(path, "rb") as f:
            content = f.read().decode("latin-1")
    except OSError:
        return None
    return ReactionTextWindow(w, DLG_REACTION_TEXT + short, path, content)


def _isspace(text, k):
    return k < len(text) and text[k] in SPACES


def display_reaction_text(w, r):
    """DisplayReactionText: 0, or -1 when the file or the reaction is not
    found (the searches as the C code makes them)."""
    dll = w.dll
    if w.main_view:
        w = w.application.window_of(w.main_view)
    s0 = corelib.text(dll.GetReactionDatabase(r))
    dlg = _find(w, DLG_REACTION_TEXT + s0)
    if dlg is None:
        s1 = os.environ.get(ENV_DBPATH, "")
        if not s1:
            s1 = w.application.app_string("databaseDir", "DatabaseDir", "")
        if not s1:
            argv0 = w.application.argv[0]
            k = max(argv0.rfind("/"), argv0.rfind("\\"), argv0.rfind(":"))
            s1 = argv0[:k + 1]
        if s1 and not s1.endswith("/"):
            s1 += "/"
        dlg = _create(w, s1 + s0)
        if dlg is None:
            return -1
        dlg.popup()
    text = dlg.content
    prefix = "\\section{" if text.startswith("\\") else ""
    str2 = text.find(STR_BEGIN)
    if str2 < 0:
        return -1
    s = "\n" + prefix + corelib.text(dll.GetReactionSection(r))
    while True:
        str2 = text.find(s, str2)
        if str2 < 0:
            return -1
        if _isspace(text, str2 + len(s)):
            break
    s = "Reaction " + corelib.text(dll.GetReactionNumber(r))
    s0 = "\n" + prefix + "H."
    while True:
        str3 = text.find(s0, str2 + 1)
        str2 = text.find(s, str2)
        if str2 < 0 or (str3 >= 0 and str2 > str3):
            return -1
        if _isspace(text, str2 + len(s)):
            break
    dlg.set_top_character(str2 + 1)
    dlg.popup()
    return 0
