"""File dialogs of a view (x_fileio.c): File > Open and File > Save with
the file selection box of Motif (directory mask from the DG_*MASK
variables, filter, directory and file lists, selection text), opening a
recent file, and the questions for an unsaved model or mesh when a view
closes. Also the filling of resource templates ($(NAME) placeholders) of
GetResourceStringEx (vacreate.c)."""

import ctypes
import fnmatch
import os

from PySide6 import QtWidgets

from ..core import api, lib as corelib, prefs
from . import boxes
from .base import MessageDialog, XmDialog, gadget

MAKESTREX_CHR = "\x01"
# Message ids (msg.h) and the file type of a configuration (calc.h)
ENV_LOADMASK, ENV_SAVEMASK, ENV_LOADMASK2, ENV_SAVEMASK2 = (6001, 6002,
                                                            6007, 6008)
MSG_FILEOPENED, MSG_FILESAVED = 1009, 1010
ERR_NOSAVECONFIG, ERR_BADMASK = 36, 65
FT_DG_CONFIG = 11


def make_str_va_ex(s, formatted):
    """MakeStrVaEx: the $(NAME) placeholders of s replaced with the values
    after the same names in formatted (the format with $ as \\x01, filled);
    None when a name is missing. A copy of the C loop, quirks included."""
    s = list(s)
    buf = formatted
    i = 0
    while i < len(s):
        if s[i] == "$" and i + 1 < len(s) and s[i + 1] == "(":
            s[i] = MAKESTREX_CHR
            j = 0
            while j < len(s):
                j += 1
                if i + j - 1 < len(s) and s[i + j - 1] == ")":
                    break
            key = "".join(s[i:i + j])
            ps = 0
            while ps >= 0:
                if buf[ps:ps + j] == key:
                    break
                ps = buf.find(MAKESTREX_CHR, ps + 1)
            if ps < 0:
                return None
            ps1 = buf.find(MAKESTREX_CHR, ps + j)
            value = buf[ps + j:] if ps1 < 0 else buf[ps + j:ps1]
            s[i:i + j] = list(value)
            # C goes on from i + len(value) - j + 1; before the start of the
            # string it reads other text, without a placeholder
            i = max(i + len(value) - j, -1)
        i += 1
    return "".join(s)


def resource_string_ex(db, names, classes, name, cls, fmt, *args):
    """GetResourceStringEx: the resource (default its name) with the
    placeholders filled from fmt % args."""
    value = db.get(names + [name], classes + [cls or name])
    s = name if value is None else value
    formatted = (fmt or "").replace("$", MAKESTREX_CHR) % args
    r = make_str_va_ex(s, formatted)
    return "(BadString1)" if r is None else r


# The item of the file list when no file matches (noMatchString)
NO_MATCH = " [    ] "


class FileSelectionDialog(XmDialog):
    """XmFileSelectionBox in a dialog shell, children in the Motif order:
    file list, selection text, OK, Filter, Cancel, Help, filter text and
    directory list. A search lists the folders (hidden ones and links to
    folders too) and the regular files matching the pattern (hidden ones
    and links to files too, case kept), each in byte order, with full
    paths; the selection text then holds the folder."""

    widget_class = "XmFileSelectionBox"

    def __init__(self, window, name):
        super().__init__(window, name)
        self.callbacks = {"ok": [], "cancel": [], "help": []}
        self.pattern = "*"
        self.no_match = False
        self.items_label = self._label("Items", "fileListLabelString",
                                       "Files")
        self.items_list = self._list("ItemsList", self._item_selected,
                                     self._item_activated)
        self.selection_label = self._label("Selection",
                                           "selectionLabelString",
                                           "Selection")
        self.text = QtWidgets.QLineEdit(self)
        self.text.setObjectName("Text")
        self.text.returnPressed.connect(lambda: self.activate("ok"))
        self.separator = gadget(QtWidgets.QFrame(self), "XmSeparatorGadget")
        self.separator.setObjectName("Separator")
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        row = QtWidgets.QHBoxLayout()
        for bname, res, default, which in (
                ("OK", "okLabelString", "OK", "ok"),
                ("Apply", "applyLabelString", "Filter", "filter"),
                ("Cancel", "cancelLabelString", "Cancel", "cancel"),
                ("Help", "helpLabelString", "Help", "help")):
            b = gadget(QtWidgets.QPushButton(
                self.resource(res, res[0].upper() + res[1:]) or default,
                self), "XmPushButtonGadget")
            b.setObjectName(bname)
            b.setAutoDefault(False)
            b.clicked.connect(lambda checked=False, w=which:
                              self.activate(w))
            row.addWidget(b)
        self.filter_label = self._label("FilterLabel", "filterLabelString",
                                        "Filter")
        self.dir_label = self._label("Dir", "dirListLabelString",
                                     "Directories")
        self.filter_text = QtWidgets.QLineEdit(self)
        self.filter_text.setObjectName("FilterText")
        self.filter_text.returnPressed.connect(
            lambda: self.activate("filter"))
        self.dir_list = self._list("DirList", self._dir_selected,
                                   self._dir_activated)
        lay = QtWidgets.QGridLayout(self)
        lay.addWidget(self.filter_label, 0, 0, 1, 2)
        lay.addWidget(self.filter_text, 1, 0, 1, 2)
        lay.addWidget(self.dir_label, 2, 0)
        lay.addWidget(self.items_label, 2, 1)
        lay.addWidget(self.dir_list, 3, 0)
        lay.addWidget(self.items_list, 3, 1)
        lay.addWidget(self.selection_label, 4, 0, 1, 2)
        lay.addWidget(self.text, 5, 0, 1, 2)
        lay.addWidget(self.separator, 6, 0, 1, 2)
        lay.addLayout(row, 7, 0, 1, 2)
        self.dir_mask = self.qualify(self.resource("dirMask", "DirMask")
                                     or "*")
        self.do_search()

    def _label(self, name, res, default):
        label = gadget(QtWidgets.QLabel(self.resource(
            res, res[0].upper() + res[1:]) or default, self),
            "XmLabelGadget")
        label.setObjectName(name)
        return label

    def _list(self, name, selected, activated):
        lst = QtWidgets.QListWidget(self)
        lst.setObjectName(name)
        lst.itemSelectionChanged.connect(selected)
        lst.itemActivated.connect(activated)
        return lst

    @staticmethod
    def qualify(mask):
        """The directory mask as the file selection box keeps it: an
        absolute directory (relative to the working folder) ending in /, a
        pattern (default *)."""
        if not mask:
            mask = "*"
        directory, _, pattern = mask.rpartition("/")
        if not mask.count("/"):
            directory, pattern = "", mask
        directory = os.path.normpath(os.path.join(os.getcwd(), directory))
        if not directory.endswith("/"):
            directory += "/"
        return directory + (pattern or "*")

    def set_dir_mask(self, mask):
        """XmNdirMask: False if the box keeps another mask (the qualified
        one, or the old one when the folder cannot be read)."""
        q = self.qualify(mask)
        directory = q.rpartition("/")[0] or "/"
        if not os.path.isdir(directory):
            return False
        self.dir_mask = q
        self.do_search()
        return q == mask

    @staticmethod
    def _fill(lst, items, select_first):
        lst.blockSignals(True)
        lst.clear()
        lst.addItems(items)
        if select_first and items:
            lst.item(0).setSelected(True)
        lst.blockSignals(False)

    def do_search(self):
        """XmFileSelectionDoSearch with the directory mask."""
        directory, _, pattern = self.dir_mask.rpartition("/")
        directory += "/"
        self.pattern = pattern
        self.filter_text.setText(self.dir_mask)
        try:
            names = os.listdir(directory)
        except OSError:
            names = []
        dirs = [".", ".."] + [n for n in names
                              if os.path.isdir(directory + n)]
        files = [n for n in names if os.path.isfile(directory + n) and
                 fnmatch.fnmatchcase(n, pattern)]
        order = lambda n: os.fsencode(n)  # noqa: E731 (strcmp)
        self._fill(self.dir_list, [directory + n for n in
                                   sorted(dirs, key=order)], True)
        self.no_match = not files
        self._fill(self.items_list,
                   [directory + n for n in sorted(files, key=order)]
                   or [self.resource("noMatchString", "NoMatchString")
                       or NO_MATCH], False)
        self.text.setText(directory)

    def select_file(self, name):
        """XmListSelectItem of the file list, without its callback."""
        self.items_list.blockSignals(True)
        self.items_list.clearSelection()
        for k in range(self.items_list.count()):
            if not self.no_match and self.items_list.item(k).text() == name:
                self.items_list.item(k).setSelected(True)
        self.items_list.blockSignals(False)

    def _item_selected(self):
        items = self.items_list.selectedItems()
        if items and not self.no_match:
            self.text.setText(items[0].text())

    def _item_activated(self, item):
        if self.no_match:
            return
        self.text.setText(item.text())
        self.activate("ok")

    def _dir_mask_of(self, item):
        return self.qualify(item.text() + "/" + self.pattern)

    def _dir_selected(self):
        items = self.dir_list.selectedItems()
        if items:
            self.filter_text.setText(self._dir_mask_of(items[0]))

    def _dir_activated(self, item):
        self.dir_mask = self._dir_mask_of(item)
        self.do_search()

    def activate(self, which):
        if which == "filter":
            self.dir_mask = self.qualify(self.filter_text.text())
            self.do_search()
            return
        callbacks = list(self.callbacks.get(which, []))
        if which == "help" and not callbacks:
            # no help callback of its own: the one of the main window
            self.window_.help_on(self)
        for cb in callbacks:
            cb()

    def wm_close(self):
        """The close button: CbUnmap."""
        self.popdown()


def _file_dialog(window, name, ok, mask_ids):
    """The file selection box of a view, created once."""
    dlg = window.findChild(FileSelectionDialog, name)
    if dlg is None:
        dlg = FileSelectionDialog(window, name)
        env2, env1 = (window.str_(i) for i in mask_ids)
        mask = os.environ.get(env2)
        if mask is None:
            mask = os.environ.get(env1)
        dlg.callbacks["ok"].append(lambda: ok(dlg))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.manage()
        if mask is not None and not dlg.set_dir_mask(mask):
            window.error_box(window.str_(ERR_BADMASK))
    else:
        dlg.do_search()
        dlg.popup()
    return dlg


def open_file_open_dlg(window):
    """OpenFileOpenDlg."""
    return _file_dialog(window, "dlgFileOpen",
                        lambda dlg: cb_file_open_name(window, dlg.text.text(),
                                                      dlg),
                        (ENV_LOADMASK2, ENV_LOADMASK))


def open_file_save_dlg(window, at_exit):
    """OpenFileSaveDlg."""
    dlg = _file_dialog(window, "dlgFileSave",
                       lambda d: cb_file_save(window, d),
                       (ENV_SAVEMASK2, ENV_SAVEMASK))
    dlg.at_exit = at_exit
    dlg.select_file(None)
    fname = window.lib.get(window.app, "App.fName")
    if fname:
        name = window.lib.string_at(fname)
        dlg.text.setText(name)
        dlg.select_file(name)
    return dlg


def cb_file_open_name(window, name, dlg=None):
    """CbFile_Open: the file of the selection box or of a recent entry."""
    application = window.application
    dll = window.dll
    lib = window.lib
    expanded = lib.string_at(dll.ExpandFilename(corelib.cstr(name)))
    w2 = application.find_view(expanded)
    if w2 is not None:
        w2.popup()
        dll.PyViewMsg(w2.view, corelib.cstr(application.db.get(
            ["DivGeo", "main", "msgFileAlreadyLoaded"],
            ["DivGeo", "XmMainWindow", "msgFileAlreadyLoaded"])))
        w2.pump()
        return
    msg = ctypes.c_void_p()
    err = ctypes.c_int()
    a = dll.LoadNormalApp(application.xap, corelib.cstr(name),
                          ctypes.byref(msg), ctypes.byref(err))
    window.pump()
    if err.value:
        boxes.error_box(dlg if dlg is not None else window,
                        window.str_(err.value))
        return
    if dlg is not None:
        dlg.popdown()
    app = window.app
    if app and not lib.get(app, "App.fName") and not dll.IsAppUnsaved(app):
        dll.SetViewApp(window.view, a)
        window.pump()
        window.commands.create_autosave_info()
        if not dll.GetPyGroupCount(lib.get(app, "App.views")):
            dll.FreeApp(app)
            window.pump()
        w2 = window
    else:
        w2 = application.create_view(a)
    if msg.value:
        boxes.message_box(w2, lib.string_at(msg.value))
        dll.Free(msg.value)
    dll.PyViewMsg(w2.view, corelib.cstr(window.str_(MSG_FILEOPENED)))
    w2.pump()
    dll.FreeUndoInfo(a)
    w2.pump()
    prefs.add_recent_file(application, lib.string_at(lib.get(a,
                                                             "App.fName")))


def cb_file_save(window, dlg):
    """CbFile_Save."""
    dll = window.dll
    s = dlg.text.text()
    if dll.DetectFileType(corelib.cstr(s)) == FT_DG_CONFIG:
        boxes.error_box(dlg, window.str_(ERR_NOSAVECONFIG))
        return
    err = dll.SaveApp(window.app, corelib.cstr(s), api.DGFM_APP)
    window.pump()
    if err:
        boxes.error_box(dlg, window.str_(err))
        return
    dlg.popdown()
    dll.PyViewMsg(window.view, corelib.cstr(window.str_(MSG_FILESAVED)))
    window.pump()
    app = window.app
    dll.SetAppFName(app, corelib.cstr(s))
    window.pump()
    dll.UndoMark(app)
    window.pump()
    window.lib.set(app, "App.alt", 0)
    dll.UndoMark(app)
    window.pump()
    prefs.add_recent_file(window.application,
                          window.lib.string_at(window.lib.get(app,
                                                              "App.fName")))
    if getattr(dlg, "at_exit", False):
        window.close_view(-1)


def _unsaved_dlg(window, name, save, discard):
    """OpenAppUnsavedDlg, OpenMeshUnsavedDlg: a question box with Save,
    Discard, Cancel and Help, created once."""
    window.popup()
    dlg = window.findChild(MessageDialog, name)
    if dlg is None:
        dlg = MessageDialog(window, name, auto_unmanage=False,
                            dialog_type="dialog_question")
        dlg.set_message(dlg.resource("messageString", "MessageString")
                        or "")
        dlg.callbacks["ok"].append(lambda: (dlg.popdown(), save()))
        dlg.callbacks["cancel"].append(dlg.popdown)
        dlg.callbacks["help"].append(lambda: window.help_on(dlg))
        dlg.add_button("discard", lambda: (dlg.popdown(), discard()))
        dlg.wm_close = dlg.popdown
        dlg.manage()
    else:
        dlg.popup()
    return dlg


def open_app_unsaved_dlg(window):
    def discard():
        window.discard_flags |= 1
        window.close_view(-1)
    return _unsaved_dlg(window, "dlgAppUnsaved",
                        lambda: open_file_save_dlg(window, True), discard)


def open_mesh_unsaved_dlg(window):
    def discard():
        window.discard_flags |= 2
        window.close_view(-1)
    return _unsaved_dlg(window, "dlgMeshUnsaved",
                        lambda: window.commands.cm_export_mesh(None),
                        discard)
