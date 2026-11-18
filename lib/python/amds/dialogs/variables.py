"""Reaction and particle variables (amxvars.c, CreateVarsEditDlg): a row
per variable definition (description, value, Set) for the reactions
selected in the view (and, for particle variables, the particles selected
in the dialog); Set all, Reset, Hold; the message line shows the old and
new values."""

from ...divgeo.dialogs import vacreate as vc
from ...divgeo.dialogs.base import FormDialog
from ...divgeo.dialogs.files import resource_string_ex
from ..core import api, lib as corelib
from .boxes import find_dialog
from .graph import set_value
from .lists import scrolled_list

DLG_RVARSEDIT = "dlgReactionVars"
DLG_PVARSEDIT = "dlgParticleVars"
VV_NOSEL = None
VV_DIFF = -1


class ValueText(vc.Text):
    """A value field: focus and losing focus, Return, every change as
    callbacks."""

    def __init__(self, parent, name, dlg, index):
        super().__init__(parent, name)
        self.dlg = dlg
        self.index = index
        self.value_callbacks = [lambda: dlg.cb_set_hold()]
        self.textEdited.connect(lambda s: dlg.cb_set_hold())
        self.returnPressed.connect(lambda: dlg.cb_set_field(index))

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.dlg.cb_focus(self.index, True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.dlg.cb_focus(self.index, False)


class VarsEditDialog(FormDialog):
    def __init__(self, w, particles):
        super().__init__(w, DLG_PVARSEDIT if particles else DLG_RVARSEDIT)
        self.w = w
        self.dll = w.dll
        self.lib = w.lib
        self.particles_dlg = particles
        self.fields = []
        self.form = None
        self.wm_close = self.popdown
        tb = vc.RowColumn(self, "toolbar")
        self.lay.addWidget(tb)
        for name, cb in (("accept", self.cb_accept), ("reset", self.cb_reset),
                         ("hold", None), ("close", self.popdown)):
            if cb is None:
                self.hold = vc.ToggleButton(tb, name)
                tb.xm_place(self.hold)
            else:
                b = vc.PushButton(tb, name)
                b.clicked.connect(cb)
                tb.xm_place(b)
        self.xm_place(vc.Separator(self, "separ"))
        self.plist = None
        if particles:
            self.plist = scrolled_list(self, "particles")
            self.plist.selection_callbacks.append(self.cb_particle_sel)
            self.xm_place(vc.Separator(self, "separ"))
        self.msg = vc.Label(self, "msg")
        sep = vc.Separator(self, "separ")
        self.scroll = vc.Form(self, "scroll")
        self.lay.addWidget(self.scroll, 1)
        self.lay.addWidget(sep)
        self.lay.addWidget(self.msg)
        self.manage()
        w.add_dependent(self.scroll, api.N_NOW | api.N_VARDEFS,
                        lambda *a: self.dw_vars())
        w.add_dependent(self, api.N_NOW | api.N_SEL,
                        lambda *a: self.dw_sel())

    # Resources and values

    def _res(self, name, cls, default):
        value = self.resource(name, cls)
        return default if value is None else value

    def _res_ex(self, name, cls, fmt, *args):
        names, classes = self.path()
        return resource_string_ex(self.window_.application.db, names,
                                  classes, name, cls, fmt, *args)

    def _set_msg(self, text):
        self.msg.set_label(text)

    def _selection(self):
        """(selected reactions, selected particles or None)."""
        g = self.w.selected_reactions()
        reactions = self.lib.group(g)
        self.dll.PyFreeGroup(g)
        if self.plist is None:
            return reactions, None
        allp = self.all_particles(reactions)
        return reactions, [allp[pos - 1] for pos in self.plist.positions()]

    def all_particles(self, reactions):
        """GetAllParticles (input particles, in order)."""
        out = []
        for r in reactions:
            for p in self.lib.group(self.lib.get(r, "Reaction.inputSet")):
                if p not in out:
                    out.append(p)
        return out

    def get_var_ex(self, vd, reactions, particles, detail):
        """GetVarEx: the common value; VV_NOSEL, VV_DIFF (detail) or ""."""
        dll = self.dll
        ss = self.w.subset
        s = None
        if particles is None:
            pairs = [(r, None) for r in reactions]
        else:
            pairs = [(r, p) for p in particles for r in reactions
                     if dll.InGroup(self.lib.get(r, "Reaction.inputSet"), p)]
        for r, p in pairs:
            s1 = corelib.text(dll.GetParticleVar(ss, r, p, vd))
            if s is None:
                s = s1
            elif s != s1:
                return VV_DIFF if detail else ""
        if s is None:
            return VV_NOSEL if detail else ""
        return s

    def set_var_ex(self, vd, reactions, particles, value):
        """SetVarEx."""
        dll = self.dll
        ss = self.w.subset
        v = corelib.cstr(value)
        if particles is None:
            for r in reactions:
                dll.SetParticleVar(ss, r, None, vd, v)
        else:
            for p in particles:
                for r in reactions:
                    if dll.InGroup(self.lib.get(r, "Reaction.inputSet"), p):
                        dll.SetParticleVar(ss, r, p, vd, v)

    # The rows (DwVarsEditVars)

    def dw_vars(self):
        if self.form is not None:
            # the rows destroyed and made again, as in Motif
            self.scroll.items = [it for it in self.scroll.items
                                 if it[0] is not self.form]
            self.scroll.grid.removeWidget(self.form)
            self.form.setParent(None)
            self.form.deleteLater()
        self.form = vc.Form(self.scroll, "form")
        self.scroll.xm_place(self.form)
        self.fields = []
        flag = api.VDF_PARTICLES if self.particles_dlg else api.VDF_REACTIONS
        for vd in self.lib.group(self.lib.get(self.w.subset, "Doc.varDefs")):
            if not self.lib.get(vd, "VarDef.flags") & flag:
                continue
            i = len(self.fields)
            descr = corelib.text(self.dll.PyVarDefDescr(vd))
            lab = vc.Label(self.form, descr)
            lab.xm_user = i + 1 + 256 * 1
            self.form.xm_place(lab)
            value = ValueText(self.form, "value", self, i)
            value.xm_user = i + 1 + 256 * 2
            self.form.xm_place(value)
            b = vc.PushButton(self.form, "set")
            b.xm_user = i + 1 + 256 * 3
            b.clicked.connect(lambda c=False, k=i: self.cb_set_field(k))
            self.form.xm_place(b)
            self.fields.append((vd, value))
        vc.form2table(self.form)

    # Callbacks

    def cb_focus(self, index, focus):
        """CbVarsEditFocus."""
        if not focus:
            self._set_msg("")
            return
        vd = self.fields[index][0]
        reactions, particles = self._selection()
        s = self.get_var_ex(vd, reactions, particles, True)
        if s is VV_NOSEL:
            s = self._res("strNoSel", "StrNoSel", "<NoSel>")
        elif s == VV_DIFF:
            s = self._res("strDiff", "StrDiff", "<Diff>")
        else:
            s = self._res_ex("strOldVal", "StrOldVal", "$(VAR)%s$(VALUE)%s",
                             corelib.text(self.dll.PyVarDefDescr(vd)), s)
        self._set_msg(s)

    def cb_set_field(self, index):
        """CbVarsEditSetField."""
        vd, value = self.fields[index]
        reactions, particles = self._selection()
        self.set_var_ex(vd, reactions, particles, value.text())
        self.dll.UndoMark(self.w.subset)
        s = self.get_var_ex(vd, reactions, particles, True)
        if s is VV_NOSEL:
            s = "(null)"            # printf of a null string
        self._set_msg(self._res_ex(
            "strNewVal", "StrNewVal", "$(VAR)%s$(VALUE)%s",
            corelib.text(self.dll.PyVarDefDescr(vd)), s))

    def cb_accept(self):
        """CbVarsEditAccept (Set all)."""
        reactions, particles = self._selection()
        for vd, value in self.fields:
            self.set_var_ex(vd, reactions, particles, value.text())
        self.dll.UndoMark(self.w.subset)
        self._set_msg(self._res("strNewVals", "StrNewVals", "<newVals>"))
        self.hold.set_state(False, False)

    def cb_reset(self):
        """CbVarsEditReset."""
        reactions, particles = self._selection()
        for vd, value in self.fields:
            set_value(value, self.get_var_ex(vd, reactions, particles,
                                             False))
        if self.hold.isChecked():
            self.hold.set_state(False, False)

    def cb_particle_sel(self):
        """CbVarsEditParticleSel."""
        if not self.hold.isChecked():
            self.cb_reset()

    def dw_sel(self):
        """DwVarsEditSel: the particles of the selected reactions."""
        if self.particles_dlg:
            g = self.w.selected_reactions()
            reactions = self.lib.group(g)
            self.dll.PyFreeGroup(g)
            self.plist.set_items([self.lib.string(p, "Particle.name")
                                  for p in self.all_particles(reactions)])
        if not self.hold.isChecked():
            self.cb_reset()

    def cb_set_hold(self):
        """CbVarsEditSetHold."""
        if not self.hold.isChecked():
            self.hold.set_state(True, False)


def open_vars_edit_dlg(w, particles):
    """OpenVarsEditDlg."""
    dlg = find_dialog(w, DLG_PVARSEDIT if particles else DLG_RVARSEDIT)
    if dlg is None:
        dlg = VarsEditDialog(w, particles)
    else:
        dlg.popup()
    return dlg
