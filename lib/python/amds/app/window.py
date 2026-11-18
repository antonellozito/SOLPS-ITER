"""The window of a view (amview.c, CreateView): main window (File menu,
its own document) or subset window (on the main window, Subset and
Restrict menus), with the reaction list and the dependent widgets that
follow the notifications of the core.

Resource paths as Motif names the widgets: AMDS / primaryShell / main for
a main window, .../secondaryShell_popup / secondaryShell / main for a
subset window."""

from PySide6 import QtCore, QtGui, QtWidgets

from ...divgeo.dialogs import files as dgfiles
from ...divgeo.view import themes
from ..core import api, lib as corelib
from . import commands, menus


THEME_LABELS = {"light": "Light mode", "dark": "Dark mode",
                "classic": "AMDS classic"}


class DependentWidget:
    def __init__(self, widget, mask, proc, user):
        self.widget = widget
        self.mask = mask
        self.proc = proc
        self.user = user


class ReactionList(QtWidgets.QListWidget):
    """The scrolled list "list": extended selection, every change of the
    selection by the user one N_SEL; double click shows the text."""

    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("list")
        self.window_ = window
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFont(QtGui.QFontDatabase.systemFont(
            QtGui.QFontDatabase.FixedFont))
        self.itemSelectionChanged.connect(window.cb_list_selection)
        self.itemDoubleClicked.connect(
            lambda item: window.cb_display_text(self.row(item) + 1))

    def set_items(self, items):
        """SetXmListItems: the selected items selected again by text, each
        with XmListSelectItem without callbacks, which in this extended
        list replaces the selection: the last one still in the list stays
        selected."""
        selected = [self.item(k).text() for k in range(self.count())
                    if self.item(k).isSelected()]
        self.blockSignals(True)
        self.clear()
        self.top_pos = 1
        self.addItems(items)
        for text in selected:
            for k in range(self.count()):
                if self.item(k).text() == text:
                    self.clearSelection()
                    self.item(k).setSelected(True)
                    break
        self.blockSignals(False)
        self.viewport().update()

    def select(self, pos, add):
        """A click on position pos (from 1), or a Ctrl+click (add): one
        selection callback."""
        if pos < 1 or pos > self.count():
            return
        self.blockSignals(True)
        if not add:
            self.clearSelection()
        self.item(pos - 1).setSelected(True)
        self.setCurrentRow(pos - 1, QtCore.QItemSelectionModel.NoUpdate)
        self.blockSignals(False)
        self.window_.cb_list_selection()

    def positions(self):
        """XmListGetSelectedPos: the selected positions from 1."""
        return [k + 1 for k in range(self.count())
                if self.item(k).isSelected()]

    def set_pos(self, pos):
        """XmListSetPos, XmListSetKbdItemPos: position pos at the top."""
        item = self.item(pos - 1)
        if item is not None:
            self.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtTop)
            self.setCurrentRow(pos - 1, QtCore.QItemSelectionModel.NoUpdate)
        self.top_pos = pos


class ViewWindow(QtWidgets.QMainWindow):
    def __init__(self, application, doc, main_view):
        main_win = application.window_of(main_view) if main_view else None
        super().__init__(main_win)
        if main_win is not None:
            self.setWindowFlags(QtCore.Qt.Dialog)
        self.application = application
        self.lib = application.lib
        self.dll = application.dll
        self.main_window = main_win
        self.dependents = []
        self.freed = False
        app = application
        if main_view:
            self.shell_names = [app.name, "primaryShell",
                                "secondaryShell_popup", "secondaryShell"]
            self.shell_classes = ["AMDS", "ApplicationShell", "XmDialogShell",
                                  "XmForm"]
        else:
            self.shell_names = [app.name, "primaryShell"]
            self.shell_classes = ["AMDS", "ApplicationShell"]
        names, classes = self.main_path()
        res = lambda n, c: app.db.get(names + [n], classes + [c])  # noqa
        width = lambda n, c, d: d if res(n, c) is None else int(  # noqa
            res(n, c))
        self.view = app.dll.PyCreateView(
            app.xap, doc, main_view, width("databaseWidth", "Width", 0),
            width("sectionWidth", "Width", 0),
            width("numberWidth", "Width", 0), width("inputWidth", "Width", 0),
            width("groupParticles", "Group", 1))
        app.register(self)
        self.commands = commands.Commands(self)
        self.setObjectName("main")
        self.menus = menus.build(self, main_view is not None)
        self.theme_actions = {}
        if not main_view:
            self._theme_menu()
        self.list = ReactionList(self)
        self.list.top_pos = 1
        self.setCentralWidget(self.list)
        title = self.shell_resource("title", "Title")
        if main_view:
            title = app.db.get(self.shell_names + ["dialogTitle"],
                               self.shell_classes + ["DialogTitle"]) or title
        self.setWindowTitle(title or self.shell_names[-1])
        self.add_dependent(self.list, api.N_NOW | api.N_ENABLE | api.N_ALT,
                           self.dw_list_update)
        self.add_dependent(self, api.N_NOW | api.N_ALT, self.dw_view_update)
        geometry = self.shell_resource("geometry", "Geometry") or "700x500"
        try:
            w, h = (int(v) for v in geometry.split("+")[0].split("x"))
            self.resize(w, h)
        except ValueError:
            pass
        if main_view:
            self.resize(500, 400)
        self.show()

    # Resources

    def main_path(self):
        """Names and classes of the main window widget "main"."""
        return (self.shell_names + ["main"],
                self.shell_classes + ["XmMainWindow"])

    def shell_resource(self, name, cls):
        return self.application.db.get(self.shell_names + [name],
                                       self.shell_classes + [cls])

    def main_resource_ex(self, name, cls, fmt=None, *args):
        """GetResourceStringEx on w->wMain."""
        names, classes = self.main_path()
        return dgfiles.resource_string_ex(self.application.db, names,
                                          classes, name, cls, fmt, *args)

    # The document of the view

    @property
    def subset(self):
        return self.lib.get(self.view, "View.subset")

    @property
    def main_view(self):
        return self.lib.get(self.view, "View.mainView")

    # Dependent widgets (AddDependentWidget, NotifyView)

    def add_dependent(self, widget, mask, proc, user=None):
        self.dependents.append(DependentWidget(widget, mask, proc, user))
        if mask & api.N_NOW:
            proc(widget, api.N_NOW, None, user)

    def del_dependent(self, widget):
        self.dependents = [d for d in self.dependents
                           if d.widget is not widget]

    def notify(self, msg, obj):
        """NotifyView: the dependent widgets in order; one deleted by its
        handler is skipped, one added is reached."""
        k = 0
        while k < len(self.dependents):
            d = self.dependents[k]
            if d.mask & msg:
                d.proc(d.widget, msg, obj, d.user)
            if k < len(self.dependents) and self.dependents[k] is d:
                k += 1

    def dw_list_update(self, widget, evt, obj, user):
        """DwListUpdate."""
        lib = self.lib
        if evt == api.N_ALT and not lib.get(self.view, "View.dirty"):
            return
        if evt in (api.N_ALT, api.N_NOW):
            lib.set(self.view, "View.dirty", 0)
            self.update_list()
        elif evt == api.N_ENABLE:
            lib.set(self.view, "View.dirty",
                    lib.get(self.view, "View.dirty") + 1)
        else:
            raise AssertionError(evt)

    def update_list(self):
        """UpdateViewList."""
        items = []
        proc = api.ITEMPROC(lambda s: items.append(corelib.text(s)))
        self.dll.PyViewListItems(self.view, proc)
        self.list.set_items(items)

    def dw_view_update(self, widget, evt, obj, user):
        """DwViewUpdate: the title of a main window."""
        if self.main_view:
            return
        name = self.lib.string(self.subset, "Doc.fileName")
        if not name:
            names, classes = self.main_path()
            value = self.application.db.get(names + ["dialogTitle"],
                                            classes + ["DialogTitle"])
            s = "" if value is None else value
        else:
            short = corelib.text(self.dll.GetShortFName(corelib.cstr(name)))
            s = self.main_resource_ex("dialogTitleEx", "DialogTitle",
                                      "$(FILENAME)%s", short)
        self.setWindowTitle(s)
        self.setWindowIconText(s)

    def dw_undo_button(self, action, evt, obj, redo):
        """DwUndoButton."""
        stack = "Doc.redoStack" if redo else "Doc.undoStack"
        action.setEnabled(bool(self.dll.PyGroupCount(
            self.lib.get(self.subset, stack))))

    # The list

    def cb_list_selection(self):
        """CbListSelection."""
        self.notify(api.N_SEL, None)

    def selected_reactions(self):
        """GetSelectedReactions (a Group to free)."""
        arr, n = self.lib.positions(self.list.positions())
        return self.dll.PyGetSelectedReactions(self.view, arr, n)

    def cb_display_text(self, pos):
        """CbDisplayText: the text of the reaction at position pos."""
        from ..dialogs import text
        lib = self.lib
        ss = self.subset
        j = 0
        for i in range(lib.get(ss, "Doc.reactionCount")):
            r = self.dll.PyDocReaction(ss, i)
            if self.dll.PyReactionActive(ss, r):
                j += 1
                if j == pos:
                    text.display_reaction_text(self, r)
                    return

    # Theme (Options > Theme, the Python interface only)

    def _theme_menu(self):
        """The submenu Theme at the end of the Options menu."""
        om = self.menus.find("options").pulldown.qmenu
        om.addSeparator().setObjectName("themeSepar")
        tm = om.addMenu("Theme")
        tm.setObjectName("themeMenu")
        tm.menuAction().setObjectName("theme")
        group = QtGui.QActionGroup(tm)
        for name in themes.NAMES:
            act = tm.addAction(THEME_LABELS[name])
            act.setObjectName(name)
            act.setCheckable(True)
            group.addAction(act)
            act.triggered.connect(
                lambda checked, n=name: self.application.set_theme(n))
            self.theme_actions[name] = act
        self.check_theme(self.application.theme)

    def check_theme(self, name):
        if name in self.theme_actions:
            self.theme_actions[name].setChecked(True)

    # Closing

    def closeEvent(self, event):
        """The window manager close: CbCloseView (deleteResponse
        XmDO_NOTHING)."""
        event.ignore()
        if not self.freed:
            self.commands.cb_close_view()

    def free(self):
        """FreeView, the part of the window: dependent widgets removed,
        the window destroyed."""
        self.freed = True
        self.dependents = []
        for child in self.findChildren(QtWidgets.QWidget):
            if hasattr(child, "destroyed_"):
                child.destroyed_ = True
        self.hide()
        self.deleteLater()
