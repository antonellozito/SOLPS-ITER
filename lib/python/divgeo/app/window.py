"""The window of a view (Motif: CreateXmView and the view functions of
x_view.c, CloseXmView of x_fileio.c): menu bar, command row with the three
tool slots, drawing area and status line, with the names of the Motif
widgets. Every callback keeps the order of the core calls of the Motif
one."""

import ctypes
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import api, prefs, resources
from ..dialogs import boxes, files
from ..view import canvas, modes
from . import commands, contexthelp, menus

# The tools of the option menus of the command row: (widget name, tool,
# enable rule of DwNotifyShowFlags or None); None for a separator
TOOL_ITEMS = (
    ("zoom", "TlZoom", None), ("mark", "TlMark", None),
    ("examine", "TlExamine", None),
    None,
    ("rotate", "TlRotate", None), ("stretch", "TlStretch", 0),
    None,
    ("move", "TlMoveObject", None), ("remove", "TlRemoveObject", None),
    None,
    ("addElem", "TlAddElem", 1), ("addSource", "TlAddSource", 1),
    ("addChord", "TlAddChord", None), ("addSurf", "TlAddSurface", 1),
    ("addGP", "TlAddGridPoint", 1),
    None,
    ("moveMeshPoint", "TlMoveMeshPoint", 1),
    None,
    ("splitElem", "TlSplitElem", 1), ("joinElem", "TlJoinElems", 1),
    ("ctPts", "TlConnectPoints", 1), ("chElem", "TlRepositionElem", 1),
    ("chNormals", "TlMirrorNormals", None),
    None,
    ("extChord", "TlExtChord", None), ("adjChord", "TlAdjustChord", None),
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
DISCARD_DOC, DISCARD_MESH = 1, 2



class ToolOptionMenu(QtWidgets.QWidget):
    """An option menu of the command row (toolN with the pulldown
    toolMenuN): label, button with the current tool, entries."""

    xm_class = "XmRowColumn"

    def __init__(self, window, parent, slot):
        super().__init__(parent)
        self.setObjectName("tool%d" % slot)
        self.slot = slot
        self.history = None
        db = window.application.db
        names = ["DivGeo", "main", "command", "tool%d" % slot]
        classes = ["DivGeo", "XmMainWindow", "XmRowColumn", "XmRowColumn"]
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(
            db.get(names + ["labelString"], classes + ["LabelString"])
            or "", self)
        self.label.setObjectName("OptionLabel")
        self.button = QtWidgets.QToolButton(self)
        self.button.setObjectName("OptionButton")
        self.button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        color = db.get(names + ["foreground"], classes + ["Foreground"])
        pixel = resources.to_pixel(color) if color else None
        if pixel is not None:
            style = "color: #%06x;" % pixel
            self.label.setStyleSheet(style)
            self.button.setStyleSheet(style)
        menu_name = "toolMenu%d" % slot
        self.menu = QtWidgets.QMenu(self.button)
        self.menu.setObjectName(menu_name)
        self.button.setMenu(self.menu)
        self.entries = []
        pnames = ["DivGeo", "main", "command", "popup_" + menu_name,
                  menu_name]
        pclasses = ["DivGeo", "XmMainWindow", "XmRowColumn", "XmMenuShell",
                    "XmRowColumn"]
        self.pulldown = menus.Pulldown(menu_name, self.menu, 1, pnames,
                                       pclasses)
        for item in TOOL_ITEMS:
            if item is None:
                act = self.menu.addSeparator()
                act.setObjectName("separ")
                self.entries.append(menus.Entry("S", "separ", act, pnames,
                                                pclasses))
                continue
            name, tool, rule = item
            inames = pnames + [name]
            iclasses = pclasses + ["XmPushButton"]
            label = db.get(inames + ["labelString"],
                           iclasses + ["LabelString"]) or name
            act = self.menu.addAction(menus.mnemonic_label(
                label, db.get(inames + ["mnemonic"], iclasses + ["Mnemonic"])))
            act.setObjectName(name)
            entry = menus.Entry("B", name, act, inames, iclasses)
            entry.user = tool
            self.entries.append(entry)
            window.bind(act, lambda e, t=tool: window.cb_change_tool(slot, t),
                        entry)
            act.hovered.connect(lambda n=inames, c=iclasses:
                                window.display_help_line(n, c))
            if rule is not None:
                window.add_dependent_rule(act, ("showflags", rule))
        self.pulldown.entries = self.entries
        self.menu.aboutToHide.connect(window.clear_help_line)
        lay.addWidget(self.label)
        lay.addWidget(self.button)

    def set_history(self, tool):
        for e in self.entries:
            if e.kind == "B" and e.user == tool:
                self.button.setText(e.action.text().replace("&", ""))
                self.history = e.name


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
        self.discard_flags = 0
        self.tools = [None, None, None]
        self.dependents = []
        self.tool_box = None
        self.vars_entries = []
        self.recent_entries = []
        self.entry_of = {}
        self.msg_type = None
        self.autosave = None
        self.commands = commands.Commands(self)
        self.setObjectName("DivGeo")

    # Creation (CreateXmView) ###############################################

    def create(self, xap, app):
        dll = self.dll
        self.view = dll.CreatePyView(xap, self.number)
        self.application.pump.views[self.number] = self
        self.res = modes.read_view_resources(self.application.db)
        dll.SetPyViewSquares(self.view, self.res["bUseSquares"])

        main = QtWidgets.QWidget(self)
        main.setObjectName("main")
        main.xm_class = "XmMainWindow"
        self.setCentralWidget(main)
        lay = QtWidgets.QVBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        bar.setObjectName("menu")
        self.menus = menus.Builder(self, bar).build()

        self.command = QtWidgets.QWidget(main)
        self.command.setObjectName("command")
        self.command.xm_class = "XmRowColumn"
        row = QtWidgets.QHBoxLayout(self.command)
        row.setContentsMargins(2, 2, 2, 2)
        self.tool_menus = []
        for i in range(3):
            om = ToolOptionMenu(self, self.command, i)
            row.addWidget(om)
            self.tool_menus.append(om)
        row.addStretch(1)
        lay.addWidget(self.command)

        form = QtWidgets.QWidget(main)
        form.setObjectName("msgForm")
        fl = QtWidgets.QHBoxLayout(form)
        fl.setContentsMargins(2, 2, 2, 2)
        self.msg = QtWidgets.QLabel(form)
        self.msg.setObjectName("msg")
        self.msg.setTextFormat(QtCore.Qt.PlainText)
        fl.addWidget(self.msg)

        self.canvas = canvas.Canvas(self, self.res, self.res["renderer"])
        if getattr(self, "canvas_size", None):
            self.canvas.setFixedSize(*self.canvas_size)
        lay.addWidget(self.canvas, 1)
        lay.addWidget(form)
        self.menu_on = QtWidgets.QPushButton(self._res(
            ["draw", "menuOn"], ["XmDrawingArea", "XmPushButton"],
            "labelString", "LabelString") or "menuOn", self.canvas)
        self.menu_on.setObjectName("menuOn")
        self.menu_on.clicked.connect(self.commands.options_menu_toggle)
        self.menu_on.hide()
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

        self.update_show_flags()
        self.update_title()

        dll.SetViewApp(self.view, app)
        self.pump()
        dll.SetActiveView(self.view)
        self.pump()

        self.add_dependent(self.command, api.N_NOW | api.N_NEWTOOL, None,
                           self._dw_update_toolbar)
        self.add_dependent(self.mn_recent, api.N_NOW | api.N_RECENTFILES,
                           None, self._dw_notify_recent_files)

        self.commands.create_autosave_info()

        dll.PyViewMsgVersion(self.view)
        self.pump()
        return self.view

    def _res(self, names, classes, name, cls):
        return self.application.db.get(
            ["DivGeo", "main"] + names + [name],
            ["DivGeo", "XmMainWindow"] + classes + [cls])

    # Core state ############################################################

    @property
    def app(self):
        return self.lib.get(self.view, "View.app") if self.view else None

    def pump(self):
        self.application.pump.process()

    def str_(self, msg_id):
        return self.lib.string_at(self.dll.PyGetStr(self.view, msg_id))

    def error_box(self, text):
        self.pump()
        boxes.error_box(self, text)

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
        """SetXmViewMsg."""
        self.msg.setText(text or "")
        self.msg_type = "M"

    def flush(self):
        pass

    def unconfigured(self):
        """The end of the view (UnconfigureXmView): timers and dependent
        widgets gone, the window destroyed."""
        self.application.pump.views.pop(self.number, None)
        self.view = None
        self.dependents = []
        self.canvas.update_timer.stop()
        self.canvas.expose_timer.stop()
        if self.autosave is not None:
            self.autosave.stop()
        if self.tool_box is not None:
            self.tool_box.destroy_()
        self.hide()
        self.deleteLater()
        self.application.view_destroyed(self)

    # Dependent widgets (x_view.c, x_notify.c) ##############################

    def add_dependent(self, widget, mask, obj, proc, user=None):
        """AddDependentWidget: proc(widget, kind, obj, user) on the
        notifications of mask; evaluated at once with N_NOW."""
        self.dependents.append((widget, mask, obj, proc, user))
        if mask & api.N_NOW and self.app:
            proc(widget, api.N_NOW, None, user)

    def del_dependent(self, widget):
        self.dependents = [d for d in self.dependents if d[0] is not widget]

    def add_dependent_rule(self, action, rule):
        kind = rule[0]
        if kind == "rebuildCarre":
            self.add_dependent(action, api.N_ALT | api.N_NEWAPP, None,
                               self._dw_rebuild_carre)
            return
        func = {"undo": "PyDwUndoButton", "exists": "PyDwIfExists",
                "showflags": "PyDwShowFlags"}[kind]
        self.add_dependent(action, menus.DW_MASK, None,
                           self._dw_sensitive, (func, rule[1]))

    def _dw_sensitive(self, widget, kind, obj, user):
        func, value = user
        state = getattr(self.dll, func)(self.view, value)
        if state >= 0 and widget.isEnabled() != bool(state):
            widget.setEnabled(bool(state))

    def _dw_rebuild_carre(self, widget, kind, obj, user):
        state = bool(self.dll.PyDwRebuildCarreInfo(self.view))
        if widget.isEnabled() != state:
            widget.setEnabled(state)

    def _dw_update_toolbar(self, widget, kind, obj, user):
        for i, om in enumerate(self.tool_menus):
            om.set_history(self.lib.tool_names.get(self.tools[i]))

    def _dw_notify_recent_files(self, widget, kind, obj, user):
        """DwNotifyRecentFiles: the recent files, a separator first."""
        menu = self.mn_recent.menu()
        pd = [p for p in self.menus.pulldowns if p.qmenu is menu][0]
        for e in self.recent_entries:
            menu.removeAction(e.action)
            pd.entries.remove(e)
        self.recent_entries = []
        names_ = prefs.recent_files(self.lib)
        if names_:
            act = menu.addSeparator()
            act.setObjectName("separ")
            self.recent_entries.append(menus.Entry("S", "separ", act,
                                                   pd.names, pd.classes))
        for name in names_:
            names = pd.names + ["openRecentFile"]
            classes = pd.classes + ["XmPushButton"]
            short = self.lib.string_at(self.dll.GetShortFName(
                name.encode("latin-1")))
            res = ("labelStringRaise" if self.application.find_view(name)
                   else "labelStringOpen")
            label = files.resource_string_ex(self.application.db, names,
                                             classes, res, None,
                                             "$(SHORTNAME)%s", short)
            act = QtGui.QAction(label.replace("&", "&&"), menu)
            act.setObjectName("openRecentFile")
            menu.addAction(act)
            entry = menus.Entry("B", "openRecentFile", act, names, classes)
            entry.user = name
            act.triggered.connect(lambda checked=False, f=name:
                                  files.cb_file_open_name(self, f))
            act.hovered.connect(lambda f=name: self.display_data_line(f))
            self.recent_entries.append(entry)
        pd.entries.extend(self.recent_entries)

    # Notifications (NotifyXmView) ##########################################

    def notify(self, kind, obj, obj_type):
        if self.app is not None or kind == api.N_DESTROYVIEW:
            for widget, mask, dep_obj, proc, user in list(self.dependents):
                if not mask & kind:
                    continue
                if kind & NMASK_HASOBJECT and dep_obj is not None \
                        and dep_obj != obj:
                    continue
                proc(widget, kind, obj, user)
        if kind != api.N_EXAMINE and obj is not None:
            if obj_type == T_VAR:
                self.changes |= CHF_VARS
                if self.dll.PyVarFromVarSetDef(obj):
                    self.changes |= CHF_VARDEFS
            elif obj_type in _CHANGE_OF_TYPE:
                self.changes |= _CHANGE_OF_TYPE[obj_type]
            else:
                self.dll.PyFatalError(b"NotifyXmView: object type")
        if kind == api.N_NEWAPP:
            self.changes |= ~0
        elif kind == api.N_ALT:
            if self.changes & CHF_APP:
                self.update_title()
                self.update_vars_menu()
            if self.changes & CHF_VARSMENU:
                self.update_vars_menu()
            self.changes = 0
        elif kind == api.N_ADDED:
            if obj_type == T_APP:
                self.update_title()
                self.update_show_flags()
        elif kind == api.N_CHANGED:
            if obj_type == T_VIEW:
                self.update_show_flags()
                self.update_title()
            elif obj_type == T_APP:
                self.changes |= CHF_APP
            elif obj_type == T_VAR and self.dll.PyVarIsLayerIndex(obj):
                self.changes |= CHF_VARSMENU
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

    def update_show_flags(self):
        """UpdateXViewShowFlags: the toggles from the view flags."""
        f = self.lib.get(self.view, "View.showFlags")
        for attr, flag in commands.SHOW_TOGGLES:
            getattr(self, attr).setChecked(bool(f & flag))

    def update_title(self):
        """UpdateXViewTitle."""
        argv0 = self.application.argv[0].encode("latin-1")
        s = self.lib.string_at(self.dll.GetShortFName(argv0))
        s1 = s
        app = self.app
        if app:
            fname = self.lib.get(app, "App.fName")
            if fname:
                short = self.lib.string_at(self.dll.GetShortFName(
                    ctypes.string_at(fname)))
                s = s + " " + short
                s1 = short
        self.setWindowTitle(s)
        self.setWindowIconText(s1)

    def update_vars_menu(self):
        """UpdateXViewVarsMenu: the entries of the Variables menu, its Add
        and Remove submenus."""
        for e, pd in self.vars_entries:
            pd.qmenu.removeAction(e.action)
            if e in pd.entries:
                pd.entries.remove(e)
        self.vars_entries = []
        targets = {0: self.mn_add_var_set, 1: self.mn_vars,
                   2: self.mn_del_var_set}
        names = {0: "addVarSet", 1: "editVarSet", 2: "delVarSet"}
        callbacks = {0: self.commands.cb_add_var_set,
                     1: self.commands.cb_edit_var_set,
                     2: self.commands.cb_del_var_set}
        sub = {}

        def item(menu, kind, obj, label):
            pd = targets[menu]
            text = (label or b"").decode("latin-1").replace("&", "&&")
            if kind == 1:
                qm = QtWidgets.QMenu(text, pd.qmenu)
                qm.setObjectName("vsSubMenu")
                qm.setTearOffEnabled(True)
                pd.qmenu.addMenu(qm)
                act = qm.menuAction()
                act.setObjectName("vsSubMenuButton")
                e = menus.Entry("C", "vsSubMenuButton", act, pd.names,
                                pd.classes)
                sub[menu] = menus.Pulldown("vsSubMenu", qm, pd.level + 1,
                                           pd.names, pd.classes)
                e.pulldown = sub[menu]
                pd.entries.append(e)
                self.vars_entries.append((e, pd))
                return
            if kind == 3:
                sub.pop(menu, None)
                return
            parent = sub[menu] if kind == 2 else pd
            act = QtGui.QAction(text, parent.qmenu)
            act.setObjectName(names[menu])
            parent.qmenu.addAction(act)
            e = menus.Entry("B", names[menu], act, parent.names,
                            parent.classes)
            e.user = obj
            act.triggered.connect(lambda checked=False, en=e,
                                  cb=callbacks[menu]: cb(en))
            parent.entries.append(e)
            if parent is pd:
                self.vars_entries.append((e, pd))

        proc = api.VARSMENUPROC(item)
        r = self.dll.PyVarsMenu(self.view, proc)
        if r < 0:
            return
        self.cm_add_var_set.setEnabled(bool(r & 1))
        self.cm_del_var_set.setEnabled(bool(r & 2))

    # Help line (CbDisplayHelpLine, CbDisplayDataLine, CbClearHelpLine) #####

    def activate(self, handler, entry):
        """A button or toggle of the window used: its arm callback (the
        help line), its callback, its disarm callback (the help line
        cleared), as the callbacks AddCallbackToTree adds in Motif."""
        self.display_help_line(entry.names, entry.classes)
        handler(entry)
        if self.view is not None:
            self.clear_help_line()

    def bind(self, action, handler, entry):
        """The callback of an entry: used with arm and disarm (activate)
        when the user triggers it; kept on the action as entry.callback."""
        entry.callback = lambda: handler(entry)
        self.entry_of[action] = entry
        action.triggered.connect(
            lambda checked=False: self.activate(handler, entry))

    def display_help_line(self, names, classes):
        text = self.application.db.get(names + ["helpLine"],
                                       classes + ["HelpLine"])
        self.msg.setText("No help" if text is None else text)
        self.msg_type = "H"

    def display_data_line(self, text):
        self.msg.setText(text)
        self.msg_type = "H"

    def clear_help_line(self):
        if self.msg_type != "H":
            return
        self.msg.setText("")

    def popup(self):
        """XtPopup and XMapWindow of the shell of the view: shown, out of
        the icon, raised."""
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized)
        self.show()
        self.raise_()

    # Context help (CbHelp) ##################################################

    def help_on(self, dialog):
        """The Help button of a dialog."""
        contexthelp.show_dialog_topic(self, dialog)

    # Tools (CbChangeTool, XtActUseTool) ####################################

    def cb_change_tool(self, slot, tool_name):
        self.tools[slot] = self.lib.tools[tool_name]
        self.notify_view(api.N_NEWTOOL)

    def use_tool(self, what, slot, x, y, shift=False):
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

    # Closing (CloseXmView, the unsaved questions of x_fileio.c) ############

    def closeEvent(self, event):
        """The close button of the window manager: Window > Close."""
        event.ignore()
        if self.view is not None:
            self.commands.cb_window_close()

    def close_view(self, ask):
        a = self.app
        if ask != -1:
            self.discard_flags = 0
        if ask and self.dll.GetPyGroupCount(self.lib.get(a, "App.views")) \
                == 1:
            if self.dll.PyMeshUnsaved(a) and \
                    not self.discard_flags & DISCARD_MESH:
                files.open_mesh_unsaved_dlg(self)
                return
            if self.dll.IsAppUnsaved(a) and \
                    not self.discard_flags & DISCARD_DOC:
                files.open_app_unsaved_dlg(self)
                return
        view = self.view
        self.dll.SetViewApp(view, None)
        self.pump()
        self.dll.FreeView(view)
        self.pump()
        if not self.dll.GetPyGroupCount(self.lib.get(a, "App.views")):
            self.dll.FreeApp(a)
            self.application.pump.process()

    # Autosave (AutosaveProc: a timer instead of the thread) ################

    def start_autosave(self):
        self.autosave = QtCore.QTimer(self)
        self.autosave.setSingleShot(True)
        self.autosave.timeout.connect(self._autosave)
        self._arm_autosave()

    def _arm_autosave(self):
        minutes = prefs.get_int(self.lib, prefs.PSTR_AUTOSAVE_INTERVAL)
        self.autosave.start(max(0, 60 * minutes) * 1000)

    def _autosave(self):
        if self.view is None:
            return
        if self.dll.PyAutosave(self.view):
            self.pump()
            return
        self.pump()
        self._arm_autosave()
