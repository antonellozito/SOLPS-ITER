"""The help window of DivGeo (x_help.c): one window for the program
(helpSystemShell with the main window dlgHelpSystem), a Window menu with
Close, and the text of a topic of the help file: the text after the line
of the topic, up to a line ---."""

from PySide6 import QtGui, QtWidgets

ERR_NOHELP, ERR_NOTOPIC = 63, 64


class HelpWindow(QtWidgets.QMainWindow):
    def __init__(self, application):
        super().__init__()
        self.application = application
        self.setObjectName("helpSystemShell")
        main = QtWidgets.QWidget(self)
        main.setObjectName("dlgHelpSystem")
        self.setCentralWidget(main)
        lay = QtWidgets.QVBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        db = application.db
        names = ["DivGeo", "helpSystemShell", "dlgHelpSystem",
                 "helpMainMenu"]
        classes = ["DivGeo", "TopLevelShell", "XmMainWindow", "XmRowColumn"]
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        bar.setObjectName("helpMainMenu")
        title = db.get(names + ["window", "labelString"],
                       classes + ["XmCascadeButton", "LabelString"])
        menu = bar.addMenu(title or "window")
        menu.setObjectName("helpWindowMenu")
        pnames = names + ["popup_helpWindowMenu", "helpWindowMenu"]
        pclasses = classes + ["XmMenuShell", "XmRowColumn"]
        label = db.get(pnames + ["close", "labelString"],
                       pclasses + ["XmPushButton", "LabelString"])
        close = QtGui.QAction(label or "close", menu)
        close.setObjectName("close")
        close.setShortcut(QtGui.QKeySequence("Esc"))
        close.triggered.connect(self.popdown)
        menu.addAction(close)
        menu.addSeparator().setObjectName("separator")
        self.text = QtWidgets.QPlainTextEdit(main)
        self.text.setObjectName("helptext")
        self.text.setReadOnly(True)
        self.text.setFont(QtGui.QFontDatabase.systemFont(
            QtGui.QFontDatabase.FixedFont))
        lay.addWidget(self.text)
        self.resize(500, 400)
        self.managed = False

    def _trace(self, kind):
        pass

    def popup(self):
        if not self.managed:
            self.managed = True
            self._trace("manage")
        self._trace("popup")
        self.show()
        self.raise_()

    def popdown(self):
        self.hide()

    def closeEvent(self, event):
        event.ignore()
        self.popdown()


def display_help_text(window, text, title=None):
    """DisplayHelpText (and the title of DisplayHelpTitle)."""
    application = window.application
    hw = getattr(application, "help_window", None)
    if hw is None:
        hw = application.help_window = HelpWindow(application)
    if title is not None:
        hw.setWindowTitle(title)
    if text is not None:
        hw.text.setPlainText(text)
        hw.text.moveCursor(QtGui.QTextCursor.Start)
    hw.popup()


def display_help_topic(window, topic):
    """DisplayHelpTopic."""
    display_help_text(window, None, topic)
    help_text = window.application.help_text
    if help_text is None:
        display_help_text(window, window.str_(ERR_NOHELP))
        return
    key = "\n" + topic + "\n"
    k = help_text.find(key)
    if k < 0:
        display_help_text(window, window.str_(ERR_NOTOPIC))
        return
    end = help_text.find("\n---\n", k)
    body = help_text[k + len(key):] if end < 0 else \
        help_text[k + len(key):end]
    display_help_text(window, body)
