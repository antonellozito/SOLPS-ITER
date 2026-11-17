"""Dialogs as the Motif front end handles them: a dialog is created once
and kept; it is shown by managing it (the first time) or popping up its
shell, hidden by unmanaging it or popping its shell down (Xt); a modal
dialog runs a nested event loop until it is unmanaged and is then
destroyed (ProcessModalDialog, x_dlg.c).

Widgets carry the names of the Motif widgets; resources are read with the
path of the Motif widget: the window, the dialog shell NAME_popup and the
dialog NAME."""

from PySide6 import QtCore, QtWidgets

MAIN_NAMES = ["DivGeo", "main"]
MAIN_CLASSES = ["DivGeo", "XmMainWindow"]


class XmDialog(QtWidgets.QDialog):
    """A dialog of a view: name, resource path, Xt-like visibility."""

    widget_class = "XmBulletinBoard"

    def __init__(self, window, name, parent=None):
        super().__init__(parent or window)
        self.window_ = window
        self.parent_dialog = parent
        self.setObjectName(name)
        self.name = name
        self.managed = False
        self.destroyed_ = False
        self._loop = None
        # dialogTitle of the box, else the title of its shell (default: the
        # name of the shell)
        names, classes = self.path()
        self.setWindowTitle(
            self.resource("dialogTitle", "DialogTitle") or
            window.application.db.get(names[:-1] + ["title"],
                                      classes[:-1] + ["Title"]) or
            name + "_popup")

    # Resources of the dialog

    def path(self, *names):
        """The widget path of the dialog: under the main window, or under
        the dialog it was created on."""
        if self.parent_dialog is not None:
            pn, pc = self.parent_dialog.path()
        else:
            pn, pc = list(MAIN_NAMES), list(MAIN_CLASSES)
        return (pn + [self.name + "_popup", self.name] + list(names),
                pc + ["XmDialogShell", self.widget_class])

    def resource(self, name, cls, *children):
        """Value of resource name of the dialog (or of a child given as
        (name, class) pairs), None if not set."""
        names, classes = self.path()
        for child, child_class in children:
            names.append(child)
            classes.append(child_class)
        return self.window_.application.db.get(names + [name],
                                               classes + [cls])

    # Xt visibility (_trace: a hook for tracing the calls, empty here)

    def _trace(self, kind):
        pass

    def manage(self):
        if self.managed:
            return
        self._trace("manage")
        self.managed = True
        self.show()
        self.raise_()

    def unmanage(self, trace=True):
        if not self.managed:
            return
        if trace:
            self._trace("unmanage")
        self.managed = False
        self.hide()
        if self._loop is not None:
            self._loop.quit()

    def popup(self):
        self._trace("popup")
        self.show()
        self.raise_()

    def popdown(self):
        self.hide()

    def destroy_(self):
        self.destroyed_ = True
        self.hide()
        self.deleteLater()

    def run_modal(self):
        """ProcessModalDialog: manage, wait until unmanaged, destroy."""
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.manage()
        self._loop = QtCore.QEventLoop()
        if self.managed:
            self._loop.exec()
        self._loop = None
        self.destroy_()

    def closeEvent(self, event):
        """The close button of the window manager (deleteResponse): as
        Motif XmDO_NOTHING, unless a subclass handles it."""
        event.ignore()
        self.wm_close()

    def wm_close(self):
        pass

    def reject(self):
        """Escape: as the close button."""
        self.wm_close()


def find_dialog(window, name):
    """XtNameToWidget(wMain, "*NAME"): the dialog of the view, None if it
    was not made or is destroyed."""
    for d in window.findChildren(XmDialog, name):
        if not d.destroyed_:
            return d
    return None


# The symbol of a message box (dialogType)
SYMBOLS = {
    "dialog_error": QtWidgets.QStyle.SP_MessageBoxCritical,
    "dialog_information": QtWidgets.QStyle.SP_MessageBoxInformation,
    "dialog_question": QtWidgets.QStyle.SP_MessageBoxQuestion,
    "dialog_warning": QtWidgets.QStyle.SP_MessageBoxWarning,
    "dialog_working": QtWidgets.QStyle.SP_MessageBoxInformation}


def gadget(widget, xm_class):
    """A child drawn by its parent in Motif (no window of its own): the
    Help key starts at the parent."""
    widget.xm_class = xm_class
    widget.xm_gadget = True
    return widget


class MessageDialog(XmDialog):
    """XmMessageBox in a dialog shell: symbol, message, OK, Cancel, Help
    (gadgets, in the Motif order); OK and Cancel unmanage the dialog after
    their callbacks (autoUnmanage)."""

    widget_class = "XmMessageBox"

    def __init__(self, window, name, text="", auto_unmanage=True,
                 parent=None, dialog_type="dialog_message"):
        super().__init__(window, name, parent)
        self.auto_unmanage = auto_unmanage
        self.callbacks = {"ok": [], "cancel": [], "help": []}
        lay = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        lay.addLayout(top)
        self.symbol = gadget(QtWidgets.QLabel(self), "XmLabelGadget")
        self.symbol.setObjectName("Symbol")
        kind = (self.resource("dialogType", "DialogType") or
                dialog_type).lower()
        kind = kind if kind.startswith("dialog_") else "dialog_" + kind
        if kind in SYMBOLS:
            icon = self.style().standardIcon(SYMBOLS[kind])
            self.symbol.setPixmap(icon.pixmap(32, 32))
        top.addWidget(self.symbol, 0, QtCore.Qt.AlignTop)
        self.message = gadget(QtWidgets.QLabel(self), "XmLabelGadget")
        self.message.setObjectName("Message")
        self.message.setTextFormat(QtCore.Qt.PlainText)
        top.addWidget(self.message, 1)
        self.extra = QtWidgets.QVBoxLayout()
        lay.addLayout(self.extra)
        self.separator = gadget(QtWidgets.QFrame(self), "XmSeparatorGadget")
        self.separator.setObjectName("Separator")
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        lay.addWidget(self.separator)
        self.buttons = QtWidgets.QHBoxLayout()
        lay.addLayout(self.buttons)
        self.ok = self._button("OK", "okLabelString", "OkLabelString", "ok")
        self.cancel = self._button("Cancel", "cancelLabelString",
                                   "CancelLabelString", "cancel")
        self.help = self._button("Help", "helpLabelString",
                                 "HelpLabelString", "help")
        self.set_message(text)

    def _button(self, name, res, cls, which):
        label = self.resource(res, cls) or name
        b = gadget(QtWidgets.QPushButton(label, self), "XmPushButtonGadget")
        b.setObjectName(name)
        b.setAutoDefault(False)
        b.clicked.connect(lambda: self.activate(which))
        self.buttons.addWidget(b)
        return b

    def add_button(self, name, callback):
        """A push button of the message box (as children created on it)."""
        label = self.resource("labelString", "LabelString",
                              (name, "XmPushButton")) or name
        b = QtWidgets.QPushButton(label, self)
        b.setObjectName(name)
        b.setAutoDefault(False)
        b.clicked.connect(callback)
        self.xm_place(b)
        return b

    def xm_place(self, w, x=None, y=None, attach=None):
        """A child created on the message box: a push button in the row of
        buttons, after OK and the buttons added before; anything else in
        the work area."""
        if isinstance(w, QtWidgets.QPushButton):
            self.added = getattr(self, "added", 0) + 1
            self.buttons.insertWidget(self.added, w)
        else:
            self.extra.addWidget(w)

    def set_message(self, text):
        self.message.setText(text)

    def message_text(self):
        return self.message.text()

    def activate(self, which):
        callbacks = list(self.callbacks[which])
        if which == "help" and not callbacks:
            # no help callback of its own: the one of the main window
            self.window_.help_on(self)
        for cb in callbacks:
            cb()
        if which in ("ok", "cancel") and self.auto_unmanage:
            # done inside Motif (autoUnmanage), not by DivGeo
            self.unmanage(trace=False)


class FormDialog(XmDialog):
    """XmCreateFormDialog: an XmForm in a dialog shell, its children one
    below the other."""

    widget_class = "XmForm"

    def __init__(self, window, name, parent=None):
        super().__init__(window, name, parent)
        self.lay = QtWidgets.QVBoxLayout(self)

    def message_text(self):
        return ""

    def xm_place(self, w, x=None, y=None, attach=None):
        self.lay.addWidget(w)


def create_dialog_ex(window, name, no_label=False, no_ok=False,
                     no_cancel=False, no_help=False, parent=None):
    """CreateDialogEx with CDLG_MESSAGE (CreateOkCancelDialog: no_label):
    a message dialog not unmanaged by its buttons; Cancel and the close
    button pop it down (CbUnmap)."""
    dlg = MessageDialog(window, name, auto_unmanage=False, parent=parent)
    dlg.callbacks["cancel"].append(dlg.popdown)
    dlg.wm_close = dlg.popdown
    for flag, w in ((no_label, dlg.message), (no_ok, dlg.ok),
                    (no_cancel, dlg.cancel), (no_help, dlg.help)):
        if flag:
            w.hide()
    return dlg


def create_ok_cancel_dialog(window, name):
    """CreateOkCancelDialog."""
    return create_dialog_ex(window, name, no_label=True)


class TemplateDialog(XmDialog):
    """CreateMessageDialog (XmCreateTemplateDialog): a message box with a
    separator only; push buttons created on it go below the separator,
    other children above."""

    widget_class = "XmMessageBox"

    def __init__(self, window, name, parent=None):
        super().__init__(window, name, parent)
        lay = QtWidgets.QVBoxLayout(self)
        self.extra = QtWidgets.QVBoxLayout()
        self.separator = gadget(QtWidgets.QFrame(self), "XmSeparatorGadget")
        self.separator.setObjectName("Separator")
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.buttons = QtWidgets.QHBoxLayout()
        lay.addLayout(self.extra)
        lay.addWidget(self.separator)
        lay.addLayout(self.buttons)
        self.callbacks = {"ok": [], "cancel": [], "help": []}

    def message_text(self):
        return ""

    def xm_place(self, w, x=None, y=None, attach=None):
        if isinstance(w, QtWidgets.QPushButton):
            self.buttons.addWidget(w)
        else:
            self.extra.addWidget(w)
