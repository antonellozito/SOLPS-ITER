"""The window of a view (Motif: CreateXmView and the callbacks of
x_view.c and x_menu.c): menu bar, command row with the tool slots, drawing
area and status line. Widgets carry the names of the Motif widgets.

Every callback keeps the order of the core calls of the Motif one."""

import os
import sys

from PySide6 import QtCore, QtWidgets

from ..core import api, lib as corelib
from ..view import canvas, modes

# The tools of the option menus of the command row (widget name, tool)
TOOL_ITEMS = (
    ("zoom", "TlZoom"), ("mark", "TlMark"), ("examine", "TlExamine"),
    None,
    ("rotate", "TlRotate"), ("stretch", "TlStretch"),
    None,
    ("move", "TlMoveObject"), ("remove", "TlRemoveObject"),
    None,
    ("addElem", "TlAddElem"), ("addSource", "TlAddSource"),
    ("addChord", "TlAddChord"), ("addSurf", "TlAddSurface"),
    ("addGP", "TlAddGridPoint"),
    None,
    ("moveMeshPoint", "TlMoveMeshPoint"),
    None,
    ("splitElem", "TlSplitElem"), ("joinElem", "TlJoinElems"),
    ("ctPts", "TlConnectPoints"), ("chElem", "TlRepositionElem"),
    ("chNormals", "TlMirrorNormals"),
    None,
    ("extChord", "TlExtChord"), ("adjChord", "TlAdjustChord"),
)

# Object types (view.h) and change flags of NotifyXmView
T_ELEM, T_NODE, T_EQUIL, T_TEMPLATE, T_VARSETDEF, T_VARDEF, T_VARSET, \
    T_VAR = 1, 2, 3, 7, 8, 9, 10, 11
T_APP, T_VIEW, T_SONNET, T_SEPARATOR, T_SOURCE, T_CHORD = (14, 16, 18, 19,
                                                           21, 22)
T_XPOINTTEST, T_XPOINTSEG, T_MESH, T_MESHCELL, T_MESHPOINT, \
    T_MESHELEMENT = 23, 24, 26, 27, 28, 29
T_GRIDPOINTSEG, T_GRIDPOINTEX, T_SURFACEZONE, T_SURFACEEX = 31, 32, 33, 34
CHF_GEOMETRY, CHF_FILES, CHF_VARS, CHF_VARDEFS, CHF_VARSMENU, CHF_APPVIEW, \
    CHF_TOPOLOGY, CHF_MESH, CHF_APP, CHF_MARK = (1 << k for k in range(10))
_CHANGE_OF_TYPE = {}
for _t in (T_ELEM, T_NODE, T_SEPARATOR, T_SOURCE, T_CHORD, T_GRIDPOINTEX,
           T_SURFACEEX):
    _CHANGE_OF_TYPE[_t] = CHF_GEOMETRY
for _t in (T_EQUIL, T_TEMPLATE, T_SONNET):
    _CHANGE_OF_TYPE[_t] = CHF_FILES
for _t in (T_VARSETDEF, T_VARDEF, T_VARSET):
    _CHANGE_OF_TYPE[_t] = CHF_VARDEFS | CHF_VARSMENU
for _t in (T_APP, T_VIEW):
    _CHANGE_OF_TYPE[_t] = CHF_APPVIEW
for _t in (T_XPOINTTEST, T_XPOINTSEG, T_GRIDPOINTSEG, T_SURFACEZONE):
    _CHANGE_OF_TYPE[_t] = CHF_TOPOLOGY
for _t in (T_MESH, T_MESHCELL, T_MESHELEMENT, T_MESHPOINT):
    _CHANGE_OF_TYPE[_t] = CHF_MESH

NMASK_HASOBJECT = (api.N_ADD | api.N_ADDED | api.N_CHANGE | api.N_CHANGED
                   | api.N_DEL | api.N_DELETED | api.N_MARK
                   | api.N_EXAMINE)


class ViewWindow(QtWidgets.QMainWindow):
    """One view: created by Application.create_view (CreateXmView)."""

    def __init__(self, application, number):
        super().__init__()
        self.application = application
        self.lib = application.lib
        self.dll = application.lib.dll
        self.number = number
        self.view = None
        self.changes = 0
        self.tools = [None, None, None]
        self.dependents = []
        self.setObjectName("DivGeo")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

    # Creation (CreateXmView) ###############################################

    def create(self, xap, app):
        dll = self.dll
        self.view = dll.CreatePyView(xap, self.number)
        self.application.pump.views[self.number] = self
        db = self.application.db
        self.res = modes.read_view_resources(db)
        dll.SetPyViewSquares(self.view, self.res["bUseSquares"])

        main = QtWidgets.QWidget(self)
        main.setObjectName("main")
        self.setCentralWidget(main)
        lay = QtWidgets.QVBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._create_menus()
        self._create_command(main, lay)
        self.canvas = canvas.Canvas(self, self.res, self.res["renderer"])
        if getattr(self, "canvas_size", None):
            self.canvas.setFixedSize(*self.canvas_size)
        lay.addWidget(self.canvas, 1)
        form = QtWidgets.QWidget(main)
        form.setObjectName("msgForm")
        fl = QtWidgets.QHBoxLayout(form)
        fl.setContentsMargins(2, 2, 2, 2)
        self.msg = QtWidgets.QLabel(form)
        self.msg.setObjectName("msg")
        self.msg.setTextFormat(QtCore.Qt.PlainText)
        fl.addWidget(self.msg)
        lay.addWidget(form)
        self.resize(*self.application.geometry)

        # realize and show: the drawing area gets its size
        dll.SetPyViewRealized(self.view, 1)
        self.show()
        size = self.canvas.size()
        if self.application.wid:
            sys.stdout.write("DivGeo WID: %d\nDivGeo PID: %d\n"
                             % (int(self.winId()), os.getpid()))
            sys.stdout.flush()

        # user resources of the drawing area
        for field, *_ in modes.CONFIG:
            self.lib.set(self.view, "View." + field, self.res[field])
        dll.SetPyViewSize(self.view, size.width(), size.height())

        self.canvas.start_update_timer()

        tools = self.lib.tools
        self.tools = [tools["TlExamine"], tools["TlMark"], tools["TlZoom"]]
        self.notify_view(api.N_NEWTOOL)

        self.update_title()

        dll.SetViewApp(self.view, app)
        self.pump()
        dll.SetActiveView(self.view)
        self.pump()

        self.dependents.append((self.command, api.N_NOW | api.N_NEWTOOL,
                                None, self._dw_update_toolbar))

        dll.PyViewMsgVersion(self.view)
        self.pump()
        return self.view

    def _label(self, path_names, path_classes, default):
        value = self.application.db.get(
            ["DivGeo", "main"] + path_names + ["labelString"],
            ["DivGeo", "XmMainWindow"] + path_classes + ["LabelString"])
        return default if value is None else value

    def _create_menus(self):
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        bar.setObjectName("menu")
        self.actions_ = {}
        menus = (
            ("file", "fileMenu", (("quit", self.cb_quit),)),
            ("edit", "editMenu", (("undo", self.cb_undo),
                                  ("redo", self.cb_redo),
                                  ("redoAll", self.cb_redo_all))),
            ("view", "viewMenu", (("zoomIn", self.cb_zoom_in),
                                  ("zoomOut", self.cb_zoom_out))),
        )
        for cascade, pulldown, items in menus:
            title = self._label(["menu", cascade], ["XmRowColumn",
                                                    "XmCascadeButton"],
                                cascade)
            m = bar.addMenu(title)
            m.setObjectName(pulldown)
            for name, cb in items:
                label = self._label(
                    ["menu", "popup_" + pulldown, pulldown, name],
                    ["XmRowColumn", "XmMenuShell", "XmRowColumn",
                     "XmPushButton"], name)
                act = m.addAction(label)
                act.setObjectName(name)
                act.triggered.connect(cb)
                self.actions_[name] = act
        for name, value in (("undo", 0), ("redo", 1), ("redoAll", 1)):
            self.dependents.append((self.actions_[name], api.N_NOW
                                    | api.N_ALT | api.N_NEWAPP, None,
                                    self._dw_undo_button(value)))

    def _create_command(self, main, lay):
        self.command = QtWidgets.QWidget(main)
        self.command.setObjectName("command")
        row = QtWidgets.QHBoxLayout(self.command)
        row.setContentsMargins(2, 2, 2, 2)
        self.tool_menus = []
        for i in range(3):
            label = QtWidgets.QLabel(self._label(
                ["command", "tool%d" % i], ["XmRowColumn", "XmRowColumn"],
                "tool%d" % i), self.command)
            box = QtWidgets.QComboBox(self.command)
            box.setObjectName("tool%d" % i)
            box.items = []
            for item in TOOL_ITEMS:
                if item is None:
                    box.insertSeparator(box.count())
                    box.items.append(None)
                    continue
                name, tool = item
                box.addItem(self._label(["command", "toolMenu%d" % i, name],
                                        ["XmRowColumn", "XmRowColumn",
                                         "XmPushButton"], name), tool)
                box.items.append(name)
            box.activated.connect(lambda k, i=i: self.cb_change_tool(i, k))
            row.addWidget(label)
            row.addWidget(box)
            self.tool_menus.append(box)
        row.addStretch(1)
        lay.addWidget(self.command)

    # Core state ############################################################

    @property
    def app(self):
        return self.lib.get(self.view, "View.app") if self.view else None

    def pump(self):
        self.application.pump.process()

    def update_flag(self):
        return self.lib.get(self.view, "View.updateFlag")

    def set_update_flag(self, value):
        self.lib.set(self.view, "View.updateFlag", value)

    def repaint_view(self):
        self.dll.RepaintView(self.view)
        self.pump()

    def resized(self, width, height):
        """CbResizeView."""
        if self.view is None:
            return
        self.dll.ResizePyView(self.view, width, height)
        self.pump()

    def notify_view(self, kind, obj=None):
        self.dll.PyNotifyView(self.view, kind, obj)
        self.pump()

    # Records ###############################################################

    def draw_records(self, recs, text, view_id):
        self.canvas.draw_records(recs, text, view_id)

    def set_message(self, text):
        self.msg.setText(text or "")

    def flush(self):
        pass

    def unconfigured(self):
        self.application.pump.views.pop(self.number, None)
        self.view = None
        self.canvas.update_timer.stop()
        self.canvas.expose_timer.stop()
        self.hide()
        self.deleteLater()

    def notify(self, kind, obj, obj_type):
        """NotifyXmView: dependent widgets, change flags, the reactions of
        the window."""
        if self.app is not None or kind == api.N_DESTROYVIEW:
            for widget, mask, dep_obj, proc in list(self.dependents):
                if not mask & kind:
                    continue
                if kind & NMASK_HASOBJECT and dep_obj is not None \
                        and dep_obj != obj:
                    continue
                proc(widget, kind, obj)
        if kind != api.N_EXAMINE and obj is not None:
            if obj_type == T_VAR:
                self.changes |= CHF_VARS
            elif obj_type in _CHANGE_OF_TYPE:
                self.changes |= _CHANGE_OF_TYPE[obj_type]
            else:
                self.dll.PyFatalError(b"NotifyXmView: object type")
        if kind == api.N_NEWAPP:
            self.changes |= ~0
        elif kind == api.N_ALT:
            if self.changes & CHF_APP:
                self.update_title()
            self.changes = 0
        elif kind == api.N_ADDED:
            if obj_type == T_APP:
                self.update_title()
        elif kind == api.N_CHANGED:
            if obj_type == T_VIEW:
                self.update_title()
            elif obj_type == T_APP:
                self.changes |= CHF_APP
        elif kind == api.N_MARK:
            self.changes |= CHF_MARK
        elif kind in (api.N_ADD, api.N_CHANGE, api.N_DEL, api.N_DELETED,
                      api.N_EXAMINE, api.N_NEWTOOL, api.N_RECENTFILES,
                      api.N_DESTROYVIEW):
            pass
        else:
            self.dll.PyFatalError2(b"NotifyView()-unknown event %s%s",
                                   str(kind).encode(), b" : fatal error 1")
        if kind == api.N_NEWAPP:
            self.dll.PyNotifyView(self.view, api.N_ALT, None)

    def update_title(self):
        """UpdateXViewTitle."""
        argv0 = self.application.argv[0].encode("latin-1")
        s = self.lib.string_at(self.dll.GetShortFName(argv0))
        s1 = s
        app = self.app
        if app:
            fname = self.lib.get(app, "App.fName")
            if fname:
                short = self.lib.string_at(
                    self.dll.GetShortFName(corelib.cstr(
                        self.lib.string_at(fname))))
                s = s + " " + short
                s1 = short
        self.setWindowTitle(s)
        self.setWindowIconText(s1)

    # Dependent widgets (x_notify.c) ########################################

    def _dw_undo_button(self, which):
        def proc(widget, kind, obj):
            app = self.app
            if app is None:
                return
            stack = self.lib.get(app, "App.undoStack" if which == 0
                                 else "App.redoStack")
            widget.setEnabled(bool(self.dll.GetPyGroupCount(stack)))
        return proc

    def _dw_update_toolbar(self, widget, kind, obj):
        for i, box in enumerate(self.tool_menus):
            name = self.lib.tool_names.get(self.tools[i])
            for k in range(box.count()):
                if box.itemData(k) == name:
                    box.setCurrentIndex(k)

    # Callbacks #############################################################

    def cb_change_tool(self, slot, index):
        """CbChangeTool."""
        name = self.tool_menus[slot].itemData(index)
        if name is None:
            return
        self.tools[slot] = self.lib.tools[name]
        self.notify_view(api.N_NEWTOOL)

    def use_tool(self, what, slot, x, y, shift=False):
        """XtActUseTool."""
        if self.view is None:
            return
        tool = None
        if what == "press":
            self.dll.SetActiveView(self.view)
            self.pump()
            event = api.TL_DBLCLK if shift else api.TL_PRESS
            tool = self.tools[slot]
        elif what == "motion":
            if not self.canvas.mouse_inside:
                return
            event = api.TL_MOTION
        elif what == "release":
            event = (api.TL_RELEASE if self.canvas.mouse_inside
                     else api.TL_CANCEL)
        elif what == "enter":
            self.canvas.mouse_inside = True
            event = api.TL_ENTER
        else:
            self.canvas.mouse_inside = False
            event = api.TL_LEAVE
        if tool is None:
            tool = self.lib.get(self.view, "View.activeTool")
        if not tool:
            return
        self.dll.CallToolProc(self.view, tool, event, x, y)
        self.pump()

    def cb_undo(self):
        if not self.app:
            return
        self.dll.SetActiveView(self.view)
        self.pump()
        self.dll.Undo(self.app)
        self.pump()

    def cb_redo(self):
        if not self.app:
            return
        self.dll.SetActiveView(self.view)
        self.pump()
        self.dll.Redo(self.app)
        self.pump()

    def cb_redo_all(self):
        if not self.app:
            return
        self.dll.SetActiveView(self.view)
        self.pump()
        while self.dll.GetPyGroupCount(self.lib.get(self.app,
                                                    "App.redoStack")):
            self.dll.Redo(self.app)
            self.pump()

    def _zoom(self, factor):
        self.dll.SetActiveView(self.view)
        self.pump()
        if not self.app:
            return
        g = self.lib.get
        v = self.view
        self.dll.SetViewFactor(v, g(v, "View.centerX"), g(v, "View.centerY"),
                               g(v, "View.zoomX") * factor,
                               g(v, "View.zoomY") * factor)
        self.pump()
        self.dll.UndoMark(self.app)
        self.pump()

    def cb_zoom_in(self):
        self._zoom(2.0)

    def cb_zoom_out(self):
        self._zoom(0.5)

    def message_dialog(self, name):
        """A modeless message dialog with the text of its resources (the
        dialogs come with the Python dialogs of the next phase)."""
        text = self.application.db.get(
            ["DivGeo", "main", name + "_popup", name, "messageString"],
            ["DivGeo", "XmMainWindow", "XmDialogShell", "XmMessageBox",
             "MessageString"]) or name
        box = QtWidgets.QMessageBox(self)
        box.setObjectName(name)
        box.setText(text)
        box.setModal(False)
        box.show()

    def cb_quit(self):
        self.application.quit()
