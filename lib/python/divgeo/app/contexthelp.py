"""Context help (CbHelp, x_view.c): the Help button of a dialog and the
Help key (F1) show the topic of the first resource helpTopic found from the
widget up to its shell. The Help key starts at the widget with the
keyboard focus, or at the armed entry of a posted menu."""

from PySide6 import QtCore, QtWidgets

from ..dialogs import base, helpwin

_CLASSES = ((QtWidgets.QPushButton, "XmPushButton"),
            (QtWidgets.QCheckBox, "XmToggleButton"),
            (QtWidgets.QRadioButton, "XmToggleButton"),
            (QtWidgets.QLabel, "XmLabel"),
            (QtWidgets.QLineEdit, "XmTextField"),
            (QtWidgets.QPlainTextEdit, "XmText"),
            (QtWidgets.QTextEdit, "XmText"),
            (QtWidgets.QListWidget, "XmList"),
            (QtWidgets.QMenuBar, "XmRowColumn"),
            (QtWidgets.QMenu, "XmRowColumn"))


def _xm_class(widget):
    if isinstance(widget, base.XmDialog):
        return widget.widget_class
    if getattr(widget, "xm_class", None):
        return widget.xm_class
    for cls, name in _CLASSES:
        if isinstance(widget, cls):
            return name
    return "XmForm"


def show_topic(window, names, classes):
    """CbHelp from a resource path: the last value read (empty, the
    default of the resource) when no topic is set up to the shell."""
    db = window.application.db
    topic = ""
    for k in range(len(names), 0, -1):
        topic = db.get(names[:k] + ["helpTopic"],
                       classes[:k] + ["HelpTopic"]) or ""
        if topic:
            break
    helpwin.display_help_topic(window, topic)


def show_dialog_topic(window, dialog):
    """The Help button of a dialog (a gadget: the event is on the
    dialog)."""
    show_topic(window, *dialog.path())


def show_widget_topic(window, widget):
    """CbHelp from a widget of a dialog (a widget of its own: the event is
    on it)."""
    if hasattr(widget, "xm_names"):
        show_topic(window, list(widget.xm_names), list(widget.xm_classes))
    else:
        show_topic(window, *widget_path(window, widget))


def _window_of(widget):
    from .window import ViewWindow
    while widget is not None:
        if isinstance(widget, ViewWindow):
            return widget
        if isinstance(widget, base.XmDialog):
            return widget.window_
        widget = widget.parentWidget()
    return None


def _menu_path(window, menu):
    """The armed entry of a posted menu, else the pulldown itself."""
    action = menu.activeAction()
    entry = window.entry_of.get(action) if action is not None else None
    if entry is not None:
        return entry.names, entry.classes
    for pd in window.menus.pulldowns:
        if pd.qmenu is menu:
            return pd.names, pd.classes
    return ["DivGeo", "main"], ["DivGeo", "XmMainWindow"]


def widget_path(window, widget):
    """The resource path of a widget of a view or of one of its
    dialogs."""
    if isinstance(widget, QtWidgets.QMenu):
        return _menu_path(window, widget)
    names, classes = [], []
    w = widget
    while w is not None and w is not window:
        if isinstance(w, base.XmDialog):
            pn, pc = w.path()
            return pn + names, pc + classes
        name = w.objectName()
        if name and not name.startswith("qt_") and \
                not getattr(w, "xm_gadget", False):
            names.insert(0, name)
            classes.insert(0, _xm_class(w))
        if w is window.menuBar():
            names.insert(0, "main")
            classes.insert(0, "XmMainWindow")
            break
        w = w.parentWidget()
    if not names:
        # no widget of its own with the focus: the main window, where X
        # puts the keyboard focus of the shell
        return ["DivGeo", "main"], ["DivGeo", "XmMainWindow"]
    return ["DivGeo"] + names, ["DivGeo"] + classes


class HelpKey(QtCore.QObject):
    """The Help key in every window of the program."""

    def eventFilter(self, obj, event):
        if event.type() != QtCore.QEvent.KeyPress or \
                event.key() != QtCore.Qt.Key_F1 or \
                not isinstance(obj, QtWidgets.QWidget):
            return False
        window = _window_of(obj)
        if window is None or window.view is None:
            return False
        focus = obj if isinstance(obj, QtWidgets.QMenu) else \
            (QtWidgets.QApplication.focusWidget() or obj)
        show_topic(window, *widget_path(window, focus))
        return True
