"""The menus of a view (amview.c, CreateMenuSystem in CreateView): the
entries with their names and callbacks in the order Motif creates them,
the particle and reaction-type menus (CreateParticleMenu,
CreateReactionTypeMenu) and Go to (CbGotoCascade), each entry made
sensitive when its cascade opens (the cascading callbacks).

Labels, mnemonics and accelerators come from the resources, read with
the widget path Motif gives the entry: the pulldowns of the menu bar share
the menu shell of the first one (popup_fileMenu, popup_subsetMenu), the
deeper ones that of the first pulldown of their level."""

from PySide6 import QtCore, QtGui, QtWidgets

from ...divgeo.app.menus import key_sequences, mnemonic_label
from ..core import api, lib as corelib

PB_MASK = "__all__"

SEP = ("S", "separ")


def B(name, cb=None, undo=None):
    return ("B", name, cb, undo)


def C(name, pulldown=None, items=(), kind="cascade"):
    return ("C", name, pulldown, items, kind)


UNDO = [B("undo", "cb_edit_undo", 0), B("redo", "cb_edit_redo", 1),
        B("redoAll", "cb_edit_redo_all", 1)]
CLIP = [B("cut", "cb_cut"), B("copy", "cb_copy"), B("crop", "cb_crop"),
        B("paste", "cb_paste_or")]
GOTO = C("goto", "gotoMenu", (), "goto")

MAIN = [
    C("file", "fileMenu", [
        B("new", "cb_file_new"), B("open", "cb_file_open"),
        B("saveAs", "cb_file_save"), SEP, B("output", "cb_file_output"),
        SEP, B("newSubset", "cb_new_view"),
        B("cloneSubset", "cb_clone_view"), SEP, B("close", "cb_close_view"),
        SEP, B("quit", "cb_file_quit")]),
    C("edit", "editMenu", UNDO + [SEP] + CLIP + [SEP, GOTO]),
    C("reaction", "reactionMenu", [
        B("displayText", "cb_show_reaction_text"),
        B("displayGraph", "cb_show_reaction_graph"),
        B("validate", "cb_validate")]),
    C("options", "optionsMenu", [B("setup", "cb_options_setup")]),
    C("help", "helpMenu", [B("about", "cb_about")]),
]

SUBSET = [
    C("subset", "subsetMenu", [B("cloneSubset", "cb_clone_view"),
                               B("close", "cb_close_view")]),
    C("edit", "editMenu", UNDO + [SEP, B("enable", "cb_activate"),
                                  B("disable", "cb_deactivate"), SEP]
      + CLIP + [SEP, GOTO]),
    C("restrict", "restrictMenu", [
        C("restrictInput", kind="input"), C("restrictOutput", kind="output"),
        C("restrictType", kind="type"), SEP,
        C("forbidParticle", kind="forbid")]),
    C("reaction", "reactionMenu", [
        B("displayText", "cb_show_reaction_text"),
        B("displayGraph", "cb_show_reaction_graph")]),
]

_CLASS = {"B": "XmPushButton", "C": "XmCascadeButton", "S": "XmSeparator"}


class Entry:
    """An entry: kind (B, C, S), name, QAction, resource path, user data
    (a core object), its pulldown (C), its cascading callback."""

    def __init__(self, kind, name, action, names, classes, user=None):
        self.kind = kind
        self.name = name
        self.action = action
        self.names = names
        self.classes = classes
        self.user = user
        self.pulldown = None
        self.cascading = None
        self.data = None


class Pulldown:
    """A pulldown: name, QMenu, entries, resource path, menu shell."""

    def __init__(self, name, qmenu, names, classes, shell):
        self.name = name
        self.qmenu = qmenu
        self.names = names
        self.classes = classes
        self.shell = shell
        self.entries = []

    def child(self, name):
        """XtNameToWidget on the pulldown."""
        for e in self.entries:
            if e.name == name:
                return e
        return None


class Menus:
    """The menu bar of a window and the builder of its entries."""

    def __init__(self, window, bar, names, classes):
        self.window = window
        self.db = window.application.db
        self.bar = bar
        self.names = names
        self.classes = classes
        self.bar_entries = []
        self.shells = {}
        self.entries = {}
        self.created = []

    def label(self, names, classes, default):
        get = self.db.get
        text = get(names + ["labelString"], classes + ["LabelString"])
        mnemonic = get(names + ["mnemonic"], classes + ["Mnemonic"])
        return mnemonic_label(default if text is None else text, mnemonic)

    def pulldown(self, parent_entry, name, level):
        """XmCreatePulldownMenu attached to a cascade entry."""
        shell = self.shells.setdefault(level, "popup_" + name)
        if level == 1:
            names, classes = self.names + [shell], self.classes + [
                "XmMenuShell"]
        else:
            parent_pd = parent_entry.parent
            names = parent_pd.names + [shell]
            classes = parent_pd.classes + ["XmMenuShell"]
        qmenu = parent_entry.action.menu()
        qmenu.setObjectName(name)
        qmenu.setTearOffEnabled(True)
        pd = Pulldown(name, qmenu, names + [name], classes + ["XmRowColumn"],
                      shell)
        pd.level = level
        parent_entry.pulldown = pd
        self.created.append(pd)
        qmenu.aboutToShow.connect(lambda e=parent_entry: self.cascade(e))
        return pd

    def cascade(self, entry):
        """The cascading callbacks of a cascade entry (as when it opens)."""
        if entry.cascading is not None:
            entry.cascading(entry)

    def add(self, pd, kind, name, callback=None, user=None, label=None):
        """An entry created in a pulldown (pd None: the menu bar)."""
        if pd is None:
            names, classes = self.names + [name], self.classes + [_CLASS[kind]]
        else:
            names, classes = pd.names + [name], pd.classes + [_CLASS[kind]]
        text = self.label(names, classes, name) if label is None else \
            label.replace("&", "&&")
        owner = self.bar if pd is None else pd.qmenu
        if kind == "C":
            qmenu = QtWidgets.QMenu(text, owner)
            action = qmenu.menuAction()
            owner.addMenu(qmenu)
        elif kind == "S":
            action = owner.addSeparator()
        else:
            action = QtGui.QAction(text, owner)
            owner.addAction(action)
            seqs = key_sequences(self.db.get(names + ["accelerator"],
                                             classes + ["Accelerator"]))
            if seqs:
                action.setShortcuts(seqs)
                action.setShortcutContext(QtCore.Qt.WindowShortcut)
                self.window.addAction(action)
        action.setObjectName(name)
        e = Entry(kind, name, action, names, classes, user)
        e.parent = pd
        if pd is None:
            self.bar_entries.append(e)
        else:
            pd.entries.append(e)
        if callback is not None and kind == "B":
            action.triggered.connect(lambda checked=False, ee=e: callback(ee))
        return e

    def find(self, name):
        return self.entries.get(name)


def build(window, subset):
    """The menus of CreateView."""
    names, classes = window.main_path()
    bar = window.menuBar()
    bar.setNativeMenuBar(False)
    bar.setObjectName("menu")
    m = Menus(window, bar, names + ["menu"], classes + ["XmRowColumn"])
    cmd = window.commands
    for c in (SUBSET if subset else MAIN):
        _cascade(m, None, c, 1, cmd)
    return m


def _cascade(m, pd, spec, level, cmd):
    _, name, pdname, items, kind = spec
    e = m.add(pd, "C", name)
    m.entries.setdefault(name, e)
    w = m.window
    if kind == "goto":
        m.pulldown(e, pdname, level)
        e.cascading = lambda ee: goto_cascade(w, ee)
        return e
    if kind in ("input", "output", "forbid"):
        cascading = {"input": lambda ee: cascade_particle_menu(w, ee, True,
                                                               True),
                     "output": lambda ee: cascade_particle_menu(w, ee, True,
                                                                False),
                     "forbid": lambda ee: cascade_forbid_particle(w, ee)}
        activate = {"input": cmd.cb_restrict_input,
                    "output": cmd.cb_restrict_output,
                    "forbid": cmd.cb_forbid_particle}
        create_particle_menu(w, m, e, None, cascading[kind], activate[kind],
                             level)
        return e
    if kind == "type":
        create_reaction_type_menu(w, m, e, level)
        return e
    sub = m.pulldown(e, pdname, level)
    for item in items:
        if item[0] == "S":
            m.add(sub, "S", item[1])
        elif item[0] == "C":
            _cascade(m, sub, item, level + 1, cmd)
        else:
            _, iname, cb, undo = item
            entry = m.add(sub, "B", iname, getattr(cmd, cb))
            m.entries.setdefault(iname, entry)
            if undo is not None:
                w.add_dependent(entry.action, api.N_NOW | api.N_ALT,
                                w.dw_undo_button, undo)
    return e


# Particle and reaction-type menus ######################################

def create_particle_menu(w, m, cascade, p_up, cascading, activate, level):
    """CreateParticleMenu: a pulldown "subClasses" on the cascade; for a
    class, the class with its subclasses (*), a separator, the class
    itself; then each direct subclass, a cascade if it has subclasses."""
    dll = w.dll
    lib = w.lib
    pd = m.pulldown(cascade, "subClasses", level)
    if cascading is not None:
        cascade.cascading = cascading
    if p_up:
        m.add(pd, "B", PB_MASK, activate, p_up)
        m.add(pd, "S", "separ")
        m.add(pd, "B", lib.string(p_up, "Particle.name"), activate, p_up)
    for p in lib.group(lib.get(lib.get(w.view, "View.db"),
                               "Database.particles")):
        if not dll.IsSubclassedParticle(p, p_up, 1):
            continue
        name = lib.string(p, "Particle.name")
        if dll.PyGroupCount(lib.get(p, "Particle.subClasses")):
            e = m.add(pd, "C", name, user=p)
            create_particle_menu(w, m, e, p, cascading, activate, level + 1)
        else:
            m.add(pd, "B", name, activate, p)
    return pd


def _subclass_entry(e):
    return e.name == PB_MASK or e.kind == "C"


def cascade_particle_menu(w, cascade, shown, inp):
    """CascadeParticleMenu."""
    pd = cascade.pulldown
    if pd is None:
        return
    for e in pd.entries:
        if not e.user:
            continue
        e.action.setEnabled(bool(w.dll.PyParticleEntrySensitive(
            w.view, e.user, int(shown), int(inp), int(_subclass_entry(e)))))


def cascade_forbid_particle(w, cascade):
    """CbCascadeForbidParticle."""
    pd = cascade.pulldown
    if pd is None:
        return
    for e in pd.entries:
        if not e.user:
            continue
        e.action.setEnabled(bool(w.dll.PyForbidEntrySensitive(
            w.view, e.user, int(_subclass_entry(e)))))


def create_reaction_type_menu(w, m, cascade, level):
    """CreateReactionTypeMenu."""
    lib = w.lib
    pd = m.pulldown(cascade, "reactionTypesMenu", level)
    cascade.cascading = lambda ee: cascade_restrict_type(w, ee)
    for rt in lib.group(lib.get(lib.get(w.view, "View.db"),
                                "Database.reactionTypes")):
        m.add(pd, "B", lib.string(rt, "ReactionType.name"),
              w.commands.cb_restrict_type, rt)


def cascade_restrict_type(w, cascade):
    """CbCascadeRestrictType."""
    for e in cascade.pulldown.entries:
        if not e.user:
            continue
        e.action.setEnabled(bool(w.dll.PyTypeEntrySensitive(w.view, e.user)))


# Go to ##################################################################

def _strtok(s):
    """The words of s as strtok(s, " ") gives them."""
    return [t for t in s.split(" ") if t]


def goto_cascade(w, cascade):
    """CbGotoCascade: the entries of the level made when it opens first,
    then their sensitivity from the active reactions."""
    dll = w.dll
    lib = w.lib
    m = w.menus
    base = cascade.data or ""
    pd = cascade.pulldown
    if not pd.entries:
        for r in lib.group(lib.get(lib.get(w.view, "View.db"),
                                   "Database.reactions")):
            s = corelib.text(dll.PyAltReactionName(r))
            if s[:len(base)] != base:
                continue
            words = _strtok(s[len(base):])
            s = words[0]
            s1 = words[1] if len(words) > 1 else None
            s2 = s.replace(".", "_")
            if pd.child(s2) is not None:
                continue
            if not s1:
                m.add(pd, "B", s2, w.commands.cb_goto, r, label=s)
            else:
                e = m.add(pd, "C", s2, label=s)
                m.pulldown(e, "gotoSubmenu", pd.level + 1)
                e.cascading = lambda ee: goto_cascade(w, ee)
                e.data = base + s + " "
    for e in pd.entries:
        e.action.setEnabled(False)
    ss = lib.get(w.view, "View.subset")
    for r in lib.group(lib.get(lib.get(w.view, "View.db"),
                               "Database.reactions")):
        if dll.PyReactionActive(ss, r):
            s = corelib.text(dll.PyAltReactionName(r))
            for e in pd.entries:
                if e.kind == "C":
                    if s[:len(e.data)] == e.data and not e.action.isEnabled():
                        e.action.setEnabled(True)
                elif e.user == r and not e.action.isEnabled():
                    e.action.setEnabled(True)
