"""The menu callbacks of a view (ammenu.c, amview.c): the core part in
the library (src/py/py_cmds.c), the dialogs here."""

from ..dialogs import boxes, files, text


class Commands:
    def __init__(self, window):
        self.w = window
        self.dll = window.dll
        self.lib = window.lib

    def _positions(self):
        return self.lib.positions(self.w.list.positions())

    # File

    def cb_file_new(self, entry=None):
        self.w.application.new_view()

    def cb_file_open(self, entry=None):
        files.open_file_open_dlg(self.w)

    def cb_file_save(self, entry=None):
        files.open_file_save_dlg(self.w, False)

    def cb_file_output(self, entry=None):
        files.open_file_output_dlg(self.w)

    def cb_file_quit(self, entry=None):
        self.dll.PyCbFileQuit(self.w.view)

    def cb_new_view(self, entry=None):
        """CbNewView: a subset of all reactions."""
        w0 = self.w
        ss = self.dll.PyNewSubsetDoc(w0.view)
        main = w0.main_view or w0.view
        w = w0.application.create_view(ss, main)
        self.dll.FreeUndoInfo(w.subset)

    def cb_clone_view(self, entry=None):
        """CbCloneView: a subset of the reactions of this view."""
        w0 = self.w
        ss = self.dll.PyCloneSubsetDoc(w0.view)
        main = w0.main_view or w0.view
        w = w0.application.create_view(ss, main)
        self.dll.UndoMark(w.subset)
        self.dll.FreeUndoInfo(w.subset)

    def cb_close_view(self, entry=None):
        w = self.w
        self.dll.PyCloseView(w.view, int(not w.main_view))

    # Restrict

    def cb_restrict_input(self, entry):
        if entry.user:
            self.dll.PyCbRestrictInput(self.w.view, entry.user,
                                       int(entry.name == "__all__"))

    def cb_restrict_output(self, entry):
        if entry.user:
            self.dll.PyCbRestrictOutput(self.w.view, entry.user,
                                        int(entry.name == "__all__"))

    def cb_forbid_particle(self, entry):
        if entry.user:
            self.dll.PyCbForbidParticle(self.w.view, entry.user,
                                        int(entry.name == "__all__"))

    def cb_restrict_type(self, entry):
        self.dll.PyCbRestrictType(self.w.view, entry.user)

    # Edit

    def cb_edit_undo(self, entry=None):
        self.dll.PyUndo(self.w.subset)

    def cb_edit_redo(self, entry=None):
        self.dll.PyRedo(self.w.subset)

    def cb_edit_redo_all(self, entry=None):
        self.dll.PyCbEditRedoAll(self.w.view)

    def cb_activate(self, entry=None):
        self.dll.PyCbActivate(self.w.view, *self._positions())

    def cb_deactivate(self, entry=None):
        self.dll.PyCbDeactivate(self.w.view, *self._positions())

    def cb_cut(self, entry=None):
        self.dll.PyCbCut(self.w.view, *self._positions())

    def cb_copy(self, entry=None):
        self.dll.PyCbCopy(self.w.view, *self._positions())

    def cb_crop(self, entry=None):
        self.dll.PyCbCrop(self.w.view, *self._positions())

    def cb_paste_or(self, entry=None):
        self.dll.PyCbPasteOr(self.w.view)

    def cb_goto(self, entry):
        """CbGoto: the reaction shown at the top of the list."""
        i = self.dll.PyGotoIndex(self.w.view, entry.user)
        if i < 0:
            return
        self.w.list.set_pos(i + 1)

    # Tools

    def cb_show_reaction_text(self, entry=None):
        """CbShowReactionText: the text when one reaction is selected."""
        g = self.w.selected_reactions()
        members = self.lib.group(g)
        if len(members) == 1:
            text.display_reaction_text(self.w, members[0])
        self.dll.PyFreeGroup(g)

    def cb_show_reaction_graph(self, entry=None):
        from ..dialogs import graph
        graph.open_graph_dlg(self.w)

    def cb_validate(self, entry=None):
        from ..dialogs import validate
        validate.open_validate_dlg(self.w)

    # Options, Help

    def cb_options_setup(self, entry=None):
        from ..dialogs import setup
        setup.open_setup_warning_dlg(self.w)

    def cb_about(self, entry=None):
        boxes.show_about_dlg(self.w)
