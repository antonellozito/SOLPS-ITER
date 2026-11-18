"""Verify chains (amvald.c): the start-up particles of the document and
the particles missing from the chains of its reactions (ValidateReactions
of the core); Add> and Select> particle menus, Remove, and the arrow that
adds the selected missing particles."""

from PySide6 import QtCore, QtWidgets

from ...divgeo.dialogs import vacreate as vc
from ...divgeo.dialogs.base import FormDialog
from ..app import menus
from ..core import api
from .boxes import find_dialog
from .lists import scrolled_list

DLG_VALIDATE = "dlgValidate"


class ValidateDialog(FormDialog):
    """CreateValidateDlg."""

    def __init__(self, w):
        super().__init__(w, DLG_VALIDATE)
        self.w = w
        self.dll = w.dll
        self.lib = w.lib
        self.missing = self.dll.PyCreateGroup()
        self.wm_close = self.popdown
        rc = vc.RowColumn(self, "rowcol")
        self.lay.addWidget(rc)
        self.menus = []
        for name, cascading, activate in (
                ("add", self.cascade_add, self.cb_add_particle),
                ("select", self.cascade_select, self.cb_select_particle)):
            frame = vc.Frame(rc, "frame")
            rc.xm_place(frame)
            bar = QtWidgets.QMenuBar(frame)
            bar.setNativeMenuBar(False)
            bar.setObjectName("menu")
            frame.xm_place(bar)
            names = frame.xm_names + ["menu"]
            classes = frame.xm_classes + ["XmRowColumn"]
            m = menus.Menus(w, bar, names, classes)
            bar.amds_menus = m
            e = m.add(None, "C", name)
            menus.create_particle_menu(w, m, e, None, cascading, activate, 1)
            self.menus.append(m)
        for name, cb in (("remove", self.cb_remove_particles),
                         ("close", self.popdown)):
            b = vc.PushButton(rc, name)
            b.clicked.connect(cb)
            rc.xm_place(b)
        paned = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        paned.setObjectName("paned")
        paned.xm_class = "XmPanedWindow"
        paned.xm_names = self.path()[0] + ["paned"]
        paned.xm_classes = self.path()[1] + ["XmPanedWindow"]
        paned.xm_dialog = self
        self.lay.addWidget(paned, 1)
        f1 = vc.Form(paned, "form1")
        paned.addWidget(f1)
        f1.xm_place(vc.Label(f1, "startupLabel"))
        self.list = scrolled_list(f1, "startupList")
        f2 = vc.Form(paned, "form2")
        paned.addWidget(f2)
        hdr = vc.RowColumn(f2, "missingHdr")
        f2.xm_place(hdr)
        hdr.xm_place(vc.Label(hdr, "missingLabel"))
        self.arrow = vc.ArrowButton(hdr, "copy")
        self.arrow.clicked.connect(self.cb_add_missing_particles)
        hdr.xm_place(self.arrow)
        self.list2 = scrolled_list(f2, "missingList")
        self.list2.selection_callbacks.append(self.sensitive_if_list_sel)
        self.manage()
        w.add_dependent(self, api.N_NOW | api.N_SEL | api.N_ALT,
                        lambda *a: self.dw_validate())

    def free(self):
        """CbValidateDlgDestroy."""
        if self.missing:
            self.dll.PyFreeGroup(self.missing)
            self.missing = None

    # Lists

    def sensitive_if_list_sel(self):
        """CbSensitiveIfListSel on the arrow."""
        state = bool(self.list2.positions())
        if state != self.arrow.isEnabled():
            self.arrow.setEnabled(state)

    def update_dlg(self):
        """UpdateValidateDlg."""
        dll = self.dll
        lib = self.lib
        ss = self.w.subset
        startup = lib.get(ss, "Doc.startupParticles")
        self.list.set_items_keep(
            [lib.string(p, "Particle.name") for p in lib.group(startup)])
        gr = dll.GetActiveReactions(ss)
        g = dll.ValidateReactions(gr, startup)
        dll.PyFreeGroup(gr)
        self.list2.set_items(
            [lib.string(p, "Particle.name") for p in lib.group(g)])
        self.sensitive_if_list_sel()
        dll.PyFreeGroup(self.missing)
        self.missing = g

    def dw_validate(self):
        """DwValidateDlg."""
        if self.isVisible() and not self.destroyed_:
            self.update_dlg()

    def _selected(self, lst, group):
        """GetSelectedParticles."""
        members = self.lib.group(group)
        return [members[pos - 1] for pos in lst.positions()]

    # Commands

    def _particles(self):
        return self.lib.group(self.lib.get(self.lib.get(self.w.view,
                                                        "View.db"),
                                           "Database.particles"))

    def cb_add_particle(self, entry):
        """CbAddParticle."""
        dll = self.dll
        p0 = entry.user
        if not p0:
            return
        ss = self.w.subset
        if entry.name == menus.PB_MASK:
            for p in self._particles():
                if dll.IsSubclassedParticle(p, p0, 0):
                    dll.SetStartupParticle(ss, p, 1)
        else:
            dll.SetStartupParticle(ss, p0, 1)
        dll.UndoMark(ss)

    def cb_select_particle(self, entry):
        """CbSelectParticle: the start-up particles of the entry selected
        (SelectParticles)."""
        dll = self.dll
        p0 = entry.user
        if not p0:
            return
        ss = self.w.subset
        if entry.name == menus.PB_MASK:
            g = [p for p in self._particles()
                 if dll.IsSubclassedParticle(p, p0, 0) and
                 dll.PyIsStartupParticle(ss, p)]
        else:
            g = [p0] if dll.PyIsStartupParticle(ss, p0) else []
        startup = self.lib.group(self.lib.get(ss, "Doc.startupParticles"))
        for i, p in enumerate(startup):
            if p in g:
                self.list.select_pos(i + 1)
            else:
                self.list.deselect_pos(i + 1)

    def cb_remove_particles(self):
        """CbRemoveParticles."""
        ss = self.w.subset
        for p in self._selected(self.list, self.lib.get(
                ss, "Doc.startupParticles")):
            self.dll.SetStartupParticle(ss, p, 0)
        self.dll.UndoMark(ss)

    def cb_add_missing_particles(self):
        """CbAddMissingParticles."""
        ss = self.w.subset
        for p in self._selected(self.list2, self.missing):
            self.dll.SetStartupParticle(ss, p, 1)
        self.dll.UndoMark(ss)

    def cascade_add(self, cascade):
        """CbCascadeAddParticle."""
        dll = self.dll
        ss = self.w.subset
        for e in cascade.pulldown.entries:
            p0 = e.user
            if not p0:
                continue
            if e.kind == "C" or e.name == menus.PB_MASK:
                e.action.setEnabled(any(
                    dll.IsSubclassedParticle(p, p0, 0) and
                    not dll.PyIsStartupParticle(ss, p)
                    for p in self._particles()))
            else:
                e.action.setEnabled(not dll.PyIsStartupParticle(ss, p0))

    def cascade_select(self, cascade):
        """CbCascadeSelectParticle."""
        dll = self.dll
        ss = self.w.subset
        startup = self.lib.group(self.lib.get(ss, "Doc.startupParticles"))
        for e in cascade.pulldown.entries:
            p0 = e.user
            if not p0:
                continue
            if e.kind == "C" or e.name == menus.PB_MASK:
                e.action.setEnabled(any(
                    dll.IsSubclassedParticle(p, p0, 0) for p in startup))
            else:
                e.action.setEnabled(bool(dll.PyIsStartupParticle(ss, p0)))


def open_validate_dlg(w):
    """OpenValidateDlg."""
    dlg = find_dialog(w, DLG_VALIDATE)
    if dlg is None:
        dlg = ValidateDialog(w)
    else:
        dlg.popup()
    dlg.update_dlg()
    return dlg
