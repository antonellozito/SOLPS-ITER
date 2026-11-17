"""The modal message boxes of the Motif front end (x_dlg.c): error,
message, question and warning boxes, each a new dialog run in a nested
event loop; a text of ten lines or more is shown in a scrolled label."""

from PySide6 import QtCore, QtWidgets

from .base import MessageDialog, XmDialog

MDLG_SCROLLMIN = 10


def _owner(parent):
    """The view window and the dialog a box is created on."""
    if isinstance(parent, XmDialog):
        return parent.window_, parent
    return parent, None


def _create(parent, name, text):
    """CreateMessageDlg: Help and Cancel hidden."""
    window, dialog = _owner(parent)
    dlg = MessageDialog(window, name, parent=dialog)
    dlg.help.hide()
    dlg.cancel.hide()
    if text.count("\n") < MDLG_SCROLLMIN:
        dlg.set_message(text)
    else:
        scroll = QtWidgets.QScrollArea(dlg)
        scroll.setObjectName("scroll")
        label = QtWidgets.QLabel(text)
        label.setObjectName("label")
        label.setTextFormat(QtCore.Qt.PlainText)
        scroll.setWidget(label)
        dlg.extra.addWidget(scroll)
        dlg.scrolled_label = label
    return dlg


def error_box(window, text):
    _create(window, "errBox", text).run_modal()


def message_box(window, text):
    _create(window, "messageBox", text).run_modal()


def _ask(window, name, text):
    dlg = _create(window, name, text)
    answer = []
    dlg.callbacks["ok"].append(lambda: answer.append(True))
    dlg.cancel.show()
    dlg.run_modal()
    return 0 if answer else 1


def question_box(window, text):
    """0 when answered with OK, as QuestionBox."""
    return _ask(window, "questionBox", text)


def warning_box(window, text):
    return _ask(window, "warningBox", text)
