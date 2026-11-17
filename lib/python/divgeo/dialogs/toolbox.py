"""The toolbox of a view (x_toolb.c): a grid of buttons; a tool button
puts its tool on the slot of the mouse button that pressed it; the
buttons of the tools in use show the colour of their slot."""

from PySide6 import QtCore, QtWidgets

from ..core import api
from .base import XmDialog

# (name, column, row, tool, enable rule of DwNotifyShowFlags or None);
# tool None: close, menu, undo, redo
BUTTONS = (
    ("close", 1, 1, None, None), ("menu", 2, 1, None, None),
    ("undo", 3, 1, None, None),
    ("move", 1, 2, "TlMoveObject", None), ("remove", 2, 2, "TlRemoveObject",
                                           None),
    ("redo", 3, 2, None, None),
    ("examine", 1, 3, "TlExamine", None), ("zoom", 2, 3, "TlZoom", None),
    ("mark", 3, 3, "TlMark", None),
    ("addElem", 1, 4, "TlAddElem", 1), ("addSrc", 2, 4, "TlAddSource", 1),
    ("addChord", 3, 4, "TlAddChord", None),
    ("extChord", 1, 5, "TlExtChord", None),
    ("addSurf", 2, 5, "TlAddSurface", 1), ("addGP", 3, 5, "TlAddGridPoint",
                                            1),
    ("splitElem", 1, 6, "TlSplitElem", 1), ("joinElem", 2, 6, "TlJoinElems",
                                             1),
    ("ctPts", 3, 6, "TlConnectPoints", 1),
    ("chElem", 1, 7, "TlRepositionElem", 1),
    ("chNormals", 2, 7, "TlMirrorNormals", None),
    ("moveMeshPt", 3, 7, "TlMoveMeshPoint", 1),
    ("rotate", 1, 8, "TlRotate", None), ("stretch", 2, 8, "TlStretch", 0),
    ("adjChord", 3, 8, "TlAdjustChord", 1),
)


class _Button(QtWidgets.QPushButton):
    """Remembers the mouse button that pressed it (EhToolSelInput)."""

    def __init__(self, label, parent, box):
        super().__init__(label, parent)
        self.box = box

    def mousePressEvent(self, event):
        self.box.slot = {QtCore.Qt.LeftButton: 0, QtCore.Qt.MiddleButton: 1,
                         QtCore.Qt.RightButton: 2}.get(event.button(), 0)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # every mouse button activates the button, as button 1
        if event.button() != QtCore.Qt.LeftButton and \
                self.rect().contains(event.position().toPoint()):
            self.setDown(False)
            self.click()
            return
        super().mouseReleaseEvent(event)


class ToolBox(XmDialog):
    """CreateToolBarDlg: the form dialog dlgToolBox with the form
    subForm."""

    widget_class = "XmForm"

    def __init__(self, window):
        super().__init__(window, "dlgToolBox")
        self.slot = 0
        lay = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QWidget(self)
        form.setObjectName("subForm")
        grid = QtWidgets.QGridLayout(form)
        lay.addWidget(form)
        self.form = form
        self.buttons = {}
        self.tool_buttons = []
        c = window.commands
        for name, col, row, tool, rule in BUTTONS:
            label = self.resource("labelString", "LabelString",
                                  ("subForm", "XmForm"),
                                  (name, "XmPushButton")) or name
            b = _Button(label, form, self)
            b.setObjectName(name)
            b.setAutoDefault(False)
            grid.addWidget(b, row - 1, col - 1)
            self.buttons[name] = b
            if tool is not None:
                b.tool = tool
                self.tool_buttons.append(b)
                b.clicked.connect(lambda checked=False, t=tool:
                                  self.set_tool(t))
                if rule is not None:
                    window.add_dependent_rule(b, ("showflags", rule))
            elif name == "close":
                b.clicked.connect(self.popdown)
            elif name == "menu":
                b.clicked.connect(c.options_menu_toggle)
            elif name == "undo":
                b.clicked.connect(lambda: c.cb_undo(None))
            elif name == "redo":
                b.clicked.connect(lambda: c.cb_redo(None))
        window.add_dependent_rule(self.buttons["undo"], ("undo", 0))
        window.add_dependent_rule(self.buttons["redo"], ("undo", 1))
        window.add_dependent(form, api.N_NOW | api.N_NEWTOOL, None,
                             self.update_colors)

    def set_tool(self, tool):
        """CbToolBarDlgSetTool."""
        w = self.window_
        w.tools[self.slot] = w.lib.tools[tool]
        w.notify_view(api.N_NEWTOOL)

    def update_colors(self, widget, kind, obj, user):
        """DwUpdateToolBox: the colour of the slot of each tool."""
        w = self.window_
        keys = ("pxTool[0]", "pxTool[1]", "pxTool[2]", "pxTool[3]")
        for b in self.tool_buttons:
            tool = w.lib.tools[b.tool]
            j = w.tools.index(tool) if tool in w.tools else 3
            b.setStyleSheet("background-color: #%06x;" % w.res[keys[j]])

    def wm_close(self):
        self.popdown()
