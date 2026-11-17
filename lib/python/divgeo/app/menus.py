"""The menus of a view (x_view.c, CreateMenuSystem in CreateXmView): the
entries with their names, callbacks, user data, enable rules (dependent
widgets) and initial states, in the order Motif creates them, and the
builder of the Qt menus.

Entry kinds: B push button, T toggle, C cascade with its pulldown, S
separator. Enable rules: ("undo", n) DwNotifyUndoButton, ("exists", type)
DwNotifyIfExists, ("showflags", n) DwNotifyShowFlags, ("rebuildCarre",)
DwRebuildCarreInfo (on N_ALT and N_NEWAPP only). Labels, mnemonics and
accelerators come from the resources, read with the widget path Motif
gives the entry: pulldowns of the menu bar share the menu shell of the
first one (popup_fileMenu), those of the second level that of the first
second-level pulldown (popup_recentMenu), and so on."""

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import api

# Object types of the user data and enable rules (view.h)
T_ELEM, T_NODE, T_EQUIL, T_TEMPLATE = 1, 2, 3, 7
T_SONNET, T_SEPARATOR, T_SOURCE, T_CHORD, T_MESH = 18, 19, 21, 22, 26
T_GRIDPOINTEX, T_SURFACEEX = 32, 34
T_EMPTYNODE, T_MARKING, T_DEL_VSURFACE = 10001, 10004, 10005

DW_MASK = api.N_NOW | api.N_ALT | api.N_NEWAPP


class E:
    """One entry of the menu table."""

    def __init__(self, kind, name, cb=None, user=None, dw=None, store=None,
                 unmanaged=False, init=None, init_notify=False, menu=None,
                 items=(), menu_store=None):
        self.menu_store = menu_store
        self.kind = kind
        self.name = name
        self.cb = cb
        self.user = user
        self.dw = dw
        self.store = store
        self.unmanaged = unmanaged
        self.init = init
        self.init_notify = init_notify
        self.menu = menu
        self.items = items


def B(name, cb=None, **kw):
    return E("B", name, cb, **kw)


def T(name, cb=None, **kw):
    return E("T", name, cb, **kw)


def S(name="separ", **kw):
    return E("S", name, **kw)


def C(name, menu, items, **kw):
    return E("C", name, menu=menu, items=items, **kw)


def _exists(t):
    return ("exists", t)


def _display(name, store):
    return T(name, "cb_change_flags", store=store)


MENUS = (
    C("file", "fileMenu", (
        B("new", "cb_file_new"),
        B("open", "cb_file_open"),
        C("recent", "recentMenu", (), store="mn_recent"),
        B("save", "cb_file_save"),
        S(),
        C("import", "importMenu", (
            B("importTemplate", "cb_template"),
            B("importEquil", "cb_equil"),
            B("importMesh", "cb_sonnet"),
            B("importTopology", "cm_import_topology",
              dw=_exists(T_EQUIL)))),
        C("export", "exportMenu", (
            B("exportMesh", "cm_export_mesh", dw=_exists(T_MESH)),
            B("exportElemsAsTemplate", "cm_export_elems_as_template",
              dw=_exists(T_ELEM)))),
        S(),
        B("output", "cb_file_output"),
        S(),
        B("print", "cb_file_print"),
        S(),
        B("quit", "cb_quit"))),
    C("edit", "editMenu", (
        B("undo", "cb_undo", dw=("undo", 0)),
        B("redo", "cb_redo", dw=("undo", 1)),
        B("redoAll", "cb_redo_all", dw=("undo", 1)),
        S(),
        B("selAll", "cb_mark_all"),
        B("selAllCh", "cb_mark_all_chords"),
        B("unSelAll", "cb_unmark_all"),
        S(),
        C("create", "createMenu", (
            B("node", "cb_cm_create_at", user=T_NODE),
            B("source", "cb_cm_create_at", user=T_SOURCE),
            B("chord", "cb_cm_create_at", user=T_CHORD),
            B("surface", "cb_cm_create_at", user=T_SURFACEEX,
              dw=_exists(T_EQUIL)),
            B("gridPoint", "cb_cm_create_at", user=T_GRIDPOINTEX))),
        C("delete", "deleteMenu", (
            B("markedObjects", "cb_cm_del_objects", user=T_MARKING,
              dw=_exists(T_MARKING)),
            S("separator"),
            B("emptyNodes", "cb_cm_del_objects", user=T_NODE,
              dw=_exists(T_EMPTYNODE)),
            B("vSurfaces", "cb_cm_del_objects", user=T_DEL_VSURFACE,
              dw=_exists(T_DEL_VSURFACE)),
            S("separator"),
            B("elements", "cb_cm_del_objects", user=T_ELEM,
              dw=_exists(T_ELEM)),
            B("sources", "cb_cm_del_objects", user=T_SOURCE,
              dw=_exists(T_SOURCE)),
            B("chords", "cb_cm_del_objects", user=T_CHORD,
              dw=_exists(T_CHORD)),
            B("surfaces", "cb_cm_del_objects", user=T_SURFACEEX,
              dw=_exists(T_SURFACEEX)),
            B("gridPoints", "cb_cm_del_objects", user=T_GRIDPOINTEX,
              dw=_exists(T_GRIDPOINTEX)),
            B("separators", "cb_cm_remove_separators",
              dw=_exists(T_SEPARATOR)),
            S(),
            B("equil", "cb_cm_del_objects", user=T_EQUIL,
              dw=_exists(T_EQUIL)),
            B("template", "cb_cm_del_objects", user=T_TEMPLATE,
              dw=_exists(T_TEMPLATE)),
            B("sonnet", "cb_cm_del_objects", user=T_MESH,
              dw=_exists(T_MESH)))),
        S(),
        B("extChords", "cb_cm_ext_chords"),
        S(),
        B("rotMove", "cb_cm_rot_move"))),
    C("view", "viewMenu", (
        B("refresh", "cb_view_refresh", store="cm_refresh", unmanaged=True),
        S(store="sep_refresh", unmanaged=True),
        B("zoomIn", "cb_zoom_in"),
        B("zoomOut", "cb_zoom_out"),
        B("showPicture", "cb_show_picture"),
        B("showSelection", "cb_show_selection"),
        S(),
        C("rotate", "rotateMenu", (
            B("incAngle", "cb_inc_angle"),
            B("decAngle", "cb_dec_angle"),
            B("setAngle", "cb_cm_set_angle"),
            B("rectify", "cb_reset_angle"))),
        C("stretch", "stretchMenu", (
            B("stretchX", "cb_stretch_x", dw=("showflags", 0)),
            B("stretchY", "cb_stretch_y", dw=("showflags", 0)),
            B("shrinkX", "cb_shrink_x", dw=("showflags", 0)),
            B("shrinkY", "cb_shrink_y", dw=("showflags", 0)),
            B("stretch", "cb_cm_stretch", dw=("showflags", 0)),
            B("justify", "cb_reset_aspect_ratio", dw=("showflags", 0))),
          dw=("showflags", 0)),
        S(),
        B("prevView", "cm_prev_zoom", dw=("undo", 2)),
        S(),
        B("removeLabels", "cm_remove_labels"),
        S(),
        C("viewopt", "viewoptMenu", (
            _display("stretch", "sh_stretch"),
            _display("topview", "sh_topview"))),
        C("display", "displayMenu", (
            _display("nodes", "sh_nodes"),
            _display("irrNodes", "sh_irrnodes"),
            _display("elements", "sh_elems"),
            _display("sources", "sh_sources"),
            _display("chords", "sh_chords"),
            _display("3dchords", "sh_3dchords"),
            _display("separators", "sh_separators"),
            S("separator"),
            _display("normals", "sh_normals"),
            _display("numbers", "sh_numbers"),
            S("separator"),
            _display("surfaces", "sh_surfaces"),
            _display("gridPoints", "sh_gridpoints"),
            _display("sonnet", "sh_sonnet"),
            _display("meshDetails", "sh_meshdetails"),
            _display("irregCells", "sh_irregcells"),
            S("separator"),
            _display("equil", "sh_equil"),
            _display("template", "sh_template"),
            S("separator"),
            _display("axes", "sh_axes"),
            _display("grid", "sh_grid"))),
        S("separator"),
        B("meshHeader", "cm_view_mesh_header", dw=_exists(T_MESH)))),
    C("commands", "commandsMenu", (
        C("convert", "convertMenu", (
            B("appendTempl", "cb_cm_append_template",
              dw=_exists(T_TEMPLATE)),
            B("elemsToChords", "cm_convert_elems_to_chords",
              dw=_exists(T_ELEM)),
            B("chordsToElems", "cm_convert_chords_to_elems",
              dw=_exists(T_CHORD)))),
        C("simplify", "simplifyMenu", (
            B("gluePoints", "cb_glue_points", dw=_exists(T_ELEM)),
            C("glueNormals", "glueNormalsMenu", (
                B("glueAllNormals", "cb_group_normals", user=0),
                B("glueMarkedNormals", "cb_group_normals", user=1)),
              dw=_exists(T_ELEM)),
            B("glueElements", "cb_reduce_elements", dw=_exists(T_ELEM)))),
        B("renumber", "cb_cm_renumber"),
        B("invalidVars", "cb_cm_show_invalid_vars"),
        B("rebuildCarre", "cm_rebuild_carre_info", dw=("rebuildCarre",)),
        S(),
        B("editTopology", "cm_edit_topology", dw=_exists(T_EQUIL)))),
    C("vars", "varsMenu", (
        C("add", "addMenu", (), store="cm_add_var_set",
          menu_store="mn_add_var_set"),
        C("delete", "deleteMenu", (), store="cm_del_var_set",
          menu_store="mn_del_var_set"),
        S()), menu_store="mn_vars"),
    C("options", "optionsMenu", (
        B("outputModeX", "cm_set_output_mode_x"),
        B("meshOptions", "cm_set_mesh_options"),
        S(),
        T("menu", "cb_sw_menu", store="sw_menu", init=True,
          init_notify=True),
        T("toolbar", "cb_sw_toolbar", store="sw_toolbar", init=True),
        T("manualRefresh", "cb_sw_manual_refresh",
          store="sw_manual_refresh", init=False, init_notify=True),
        S(),
        B("saveInterval", "cb_set_autosave_interval"),
        S(),
        C("setup", "setupMenu", (
            B("varSetDefs", "cb_edit_var_set_defs"),
            B("saveConfig", "cb_save_config"))))),
    C("window", "windowMenu", (
        B("open", "cb_window_open"),
        B("close", "cb_window_close"),
        S(),
        B("info", "cb_window_info"),
        B("toolBar", "cb_window_tool_bar"))),
    C("help", "helpMenu", (
        B("whatsNew", "cb_help_menu"),
        S(),
        B("usingHelp", "cb_help_menu"),
        B("mainWindow", "cb_help_menu"),
        S(),
        B("about", "cb_about")), store="bn_help"),
)


class Entry:
    """A created entry: kind, name, its QAction, its resource path, the
    pulldown of a cascade."""

    def __init__(self, kind, name, action, names, classes, pulldown=None):
        self.kind = kind
        self.name = name
        self.action = action
        self.names = names
        self.classes = classes
        self.pulldown = pulldown
        self.user = None
        self.callback = None


class Pulldown:
    """A created pulldown: its QMenu, level, resource path, entries."""

    def __init__(self, name, qmenu, level, names, classes):
        self.name = name
        self.qmenu = qmenu
        self.level = level
        self.names = names
        self.classes = classes
        self.entries = []


_CLASS = {"B": "XmPushButton", "T": "XmToggleButton",
          "C": "XmCascadeButton", "S": "XmSeparator"}


def mnemonic_label(label, mnemonic):
    """The label with & before the first occurrence of the mnemonic (as
    Motif underlines it) and & doubled elsewhere."""
    text = label.replace("&", "&&")
    if mnemonic:
        k = text.find(mnemonic[0])
        if k >= 0:
            text = text[:k] + "&" + text[k:]
    return text


def key_sequences(spec):
    """Shortcuts of an X accelerator ("Ctrl Shift<Key>Z", "<Key>F5"): on
    macOS with the Command key and the Control key."""
    if not spec or "<Key>" not in spec:
        return []
    mods, _, key = spec.partition("<Key>")
    key = key.strip()
    if not key:
        return []
    parts = []
    words = mods.replace("~", " ").split()
    if "Shift" in words:
        parts.append("Shift")
    if "Alt" in words or "Mod1" in words or "Meta" in words:
        parts.append("Alt")
    ctrl = "Ctrl" in words
    name = {"Escape": "Esc"}.get(key, key.upper() if len(key) == 1
                                  else key)
    seqs = ["+".join((["Ctrl"] if ctrl else []) + parts + [name])]
    if ctrl and sys.platform == "darwin":
        seqs.append("+".join(["Meta"] + parts + [name]))
    return [QtGui.QKeySequence(s) for s in seqs]


class Builder:
    """Builds the menu bar of a window from MENUS (CreateMenuSystem)."""

    def __init__(self, window, bar):
        self.window = window
        self.bar = bar
        self.db = window.application.db
        self.pulldowns = []
        self.entries = {}
        self.shells = {}
        self.bar_entries = []

    def label(self, names, classes, default):
        get = self.db.get
        text = get(names + ["labelString"], classes + ["LabelString"])
        mnemonic = get(names + ["mnemonic"], classes + ["Mnemonic"])
        return mnemonic_label(default if text is None else text, mnemonic)

    def shell_of(self, level, name):
        """The shared menu shell of a pulldown level (named after the
        first pulldown created at that level)."""
        if level not in self.shells:
            self.shells[level] = "popup_" + name
        return self.shells[level]

    def pulldown_path(self, level, name):
        names = ["DivGeo", "main", "menu"]
        classes = ["DivGeo", "XmMainWindow", "XmRowColumn"]
        for k in range(1, level + 1):
            names.append(self.shells[k])
            classes.append("XmMenuShell")
        return names + [name], classes + ["XmRowColumn"]

    def build(self):
        for e in MENUS:
            self.cascade(e, None, 0)
        return self

    def cascade(self, e, parent, level):
        """A cascade entry and its pulldown (level of the pulldown:
        level + 1)."""
        w = self.window
        if parent is None:
            names = ["DivGeo", "main", "menu", e.name]
            classes = ["DivGeo", "XmMainWindow", "XmRowColumn",
                       "XmCascadeButton"]
        else:
            names = parent.names + [e.name]
            classes = parent.classes + ["XmCascadeButton"]
        qmenu = QtWidgets.QMenu(self.label(names, classes, e.name),
                                parent.qmenu if parent else self.bar)
        qmenu.setObjectName(e.menu)
        qmenu.setTearOffEnabled(True)
        if parent is None:
            self.bar.addMenu(qmenu)
        else:
            parent.qmenu.addMenu(qmenu)
        action = qmenu.menuAction()
        action.setObjectName(e.name)
        self.shell_of(level + 1, e.menu)
        pnames, pclasses = self.pulldown_path(level + 1, e.menu)
        pd = Pulldown(e.menu, qmenu, level + 1, pnames, pclasses)
        entry = Entry("C", e.name, action, names, classes, pd)
        w.entry_of[action] = entry
        if parent is None:
            self.bar_entries.append(entry)
        else:
            parent.entries.append(entry)
        if e.store:
            setattr(w, e.store, action)
        if e.menu_store:
            setattr(w, e.menu_store, pd)
        qmenu.aboutToHide.connect(w.clear_help_line)
        self.pulldowns.append(pd)
        if e.dw:
            w.add_dependent_rule(action, e.dw)
        for item in e.items:
            self.item(item, pd)
        return entry

    def item(self, e, pd):
        w = self.window
        if e.kind == "C":
            self.cascade(e, pd, pd.level)
            return
        names = pd.names + [e.name]
        classes = pd.classes + [_CLASS[e.kind]]
        if e.kind == "S":
            action = pd.qmenu.addSeparator()
        else:
            action = QtGui.QAction(self.label(names, classes, e.name),
                                   pd.qmenu)
            pd.qmenu.addAction(action)
            seqs = key_sequences(self.db.get(names + ["accelerator"],
                                             classes + ["Accelerator"]))
            if seqs:
                action.setShortcuts(seqs)
                action.setShortcutContext(QtCore.Qt.WindowShortcut)
                w.addAction(action)
            action.hovered.connect(
                lambda n=names, c=classes: w.display_help_line(n, c))
        action.setObjectName(e.name)
        entry = Entry(e.kind, e.name, action, names, classes)
        entry.user = e.user
        pd.entries.append(entry)
        self.entries.setdefault(e.name, entry)
        if e.store:
            setattr(w, e.store, action)
        if e.kind == "T":
            action.setCheckable(True)
        if e.cb:
            handler = getattr(w.commands, e.cb)
            w.bind(action, handler, entry)
        if e.init is not None:
            changed = action.isChecked() != e.init
            action.setChecked(e.init)
            if e.init_notify and changed and e.cb:
                getattr(w.commands, e.cb)(entry)
        if e.dw:
            w.add_dependent_rule(action, e.dw)
        if e.unmanaged:
            action.setVisible(False)

