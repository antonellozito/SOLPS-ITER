"""The menu callbacks of a view (x_menu.c, x_view.c): one method per Motif
callback, with the same core calls in the same order. The core part of the
callbacks without widgets is in the library (src/py/py_cmds.c); dialogs
come from the dialogs package."""

import ctypes

from ..core import api, lib as corelib, prefs
from ..dialogs import (boxes, creobj, files, helpwin, importexport, info,
                       printdlg, rotmov, settings, setup, toolbox, topology,
                       variables as varsdlg)

# Show flags of the toggles of the Display and Mode menus
# (ProcessXViewShowFlags): attribute of the window, flag
SHOW_TOGGLES = (
    ("sh_axes", 0x00000001), ("sh_grid", 0x00000002),
    ("sh_elems", 0x00000004), ("sh_normals", 0x00000008),
    ("sh_numbers", 0x00000010), ("sh_nodes", 0x00000020),
    ("sh_irrnodes", 0x00000040), ("sh_template", 0x00000080),
    ("sh_equil", 0x00000100), ("sh_surfaces", 0x00000200),
    ("sh_gridpoints", 0x00000400), ("sh_sonnet", 0x00001000),
    ("sh_separators", 0x00002000), ("sh_sources", 0x00004000),
    ("sh_chords", 0x00008000), ("sh_meshdetails", 0x00080000),
    ("sh_irregcells", 0x00800000), ("sh_stretch", 0x00100000),
    ("sh_topview", 0x00200000), ("sh_3dchords", 0x00400000))


class Commands:
    def __init__(self, window):
        self.w = window

    # helpers

    def _core(self, name, *args):
        """A command of the library, then the records it made."""
        result = getattr(self.w.dll, name)(self.w.view, *args)
        self.w.pump()
        return result

    # File menu

    def cb_file_new(self, entry):
        """CbFileNew."""
        w = self.w
        dll = w.dll
        dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        a = dll.AddApp(w.application.xap)
        w.pump()
        if not a:
            w.error_box(w.str_(api.ERR_NOCONFIG))
            return
        app = w.app
        if not w.lib.get(app, "App.fName") and not dll.IsAppUnsaved(app):
            dll.SetViewApp(w.view, a)
            w.pump()
            if not dll.GetPyGroupCount(w.lib.get(app, "App.views")):
                dll.FreeApp(app)
                w.pump()
        else:
            w.application.create_view(a)
        dll.FreeUndoInfo(a)
        w.pump()
        w.lib.set(a, "App.alt", 0)

    def cb_file_open(self, entry):
        """CbFileOpen."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        files.open_file_open_dlg(w)

    def cb_file_save(self, entry):
        """CbFileSave."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        files.open_file_save_dlg(w, False)

    def cb_file_output(self, entry):
        """CbFileOutput, with the two messages of the main window."""
        w = self.w
        res = [w.application.db.get(["DivGeo", "main", n],
                                    ["DivGeo", "XmMainWindow", n]) or n
               for n in ("msgOutputModeCarre", "msgOutputModeSonnet")]
        self._core("PyCbFileOutput", *(corelib.cstr(r) for r in res))

    def cb_file_print(self, entry):
        printdlg.open_file_print_dlg(self.w)

    def cb_equil(self, entry):
        importexport.cb_equil(self.w)

    def cb_template(self, entry):
        importexport.cb_template(self.w)

    def cb_sonnet(self, entry):
        importexport.cb_sonnet(self.w)

    def cm_import_topology(self, entry):
        importexport.open_import_topology_dlg(self.w)

    def cm_export_mesh(self, entry):
        """CmExportMesh."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        importexport.open_export_mesh_dlg(w, False)

    def cm_export_elems_as_template(self, entry):
        """CmExportElemsAsTemplate."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        importexport.open_export_elems_as_template_dlg(w)

    def cb_quit(self, entry):
        """CbQuit: every view closed in turn, with the questions."""
        for window in list(self.w.application.views_in_order()):
            if window.view is not None:
                window.close_view(True)

    # Edit menu

    def cb_undo(self, entry):
        self._core("PyCbUndo")

    def cb_redo(self, entry):
        self._core("PyCbRedo")

    def cb_redo_all(self, entry):
        self._core("PyCbRedoAll")

    def cb_mark_all(self, entry):
        self._core("PyCbMarkAll")

    def cb_mark_all_chords(self, entry):
        self._core("PyCbMarkAllChords")

    def cb_unmark_all(self, entry):
        self._core("PyCbUnmarkAll")

    def cb_cm_create_at(self, entry):
        creobj.cb_cm_create_at(self.w, entry.user)

    def _open(self, opener, undo_mark=False):
        """A dialog of the model: SetActiveView, the dialog, UndoMark when
        the Motif callback marks."""
        w = self.w
        if not w.app:
            return None
        w.dll.SetActiveView(w.view)
        w.pump()
        dlg = opener(w)
        if undo_mark:
            w.dll.UndoMark(w.app)
            w.pump()
        return dlg

    def cb_cm_rot_move(self, entry):
        """CbCmRotMove."""
        self._open(rotmov.open_rot_move_dlg)

    def cb_cm_del_objects(self, entry):
        self._core("PyCbCmDelObjects", entry.user)

    def cb_cm_remove_separators(self, entry):
        self._core("PyCbCmRemoveSeparators")

    def cb_cm_ext_chords(self, entry):
        self._core("PyCbCmExtChords")

    # View menu

    def cb_view_refresh(self, entry=None):
        self._core("PyCbViewRefresh")

    def cb_zoom_in(self, entry):
        self._core("PyCbZoomIn")

    def cb_zoom_out(self, entry):
        self._core("PyCbZoomOut")

    def cb_show_picture(self, entry):
        self._core("PyCbShowPicture")

    def cb_show_selection(self, entry):
        self._core("PyCbShowSelection")

    def cb_inc_angle(self, entry):
        self._core("PyCbIncAngle")

    def cb_dec_angle(self, entry):
        self._core("PyCbDecAngle")

    def cb_reset_angle(self, entry):
        self._core("PyCbResetAngle")

    def cb_stretch_x(self, entry):
        self._core("PyCbStretchX")

    def cb_stretch_y(self, entry):
        self._core("PyCbStretchY")

    def cb_shrink_x(self, entry):
        self._core("PyCbShrinkX")

    def cb_shrink_y(self, entry):
        self._core("PyCbShrinkY")

    def cb_reset_aspect_ratio(self, entry):
        self._core("PyCbResetAspectRatio")

    def cb_cm_set_angle(self, entry):
        """CbCmSetAngle."""
        self._open(rotmov.open_set_angle_dlg, True)

    def cb_cm_stretch(self, entry):
        """CbCmStretch."""
        self._open(rotmov.open_stretch_dlg, True)

    def cm_view_mesh_header(self, entry):
        """CmViewMeshHeader."""
        w = self.w
        if not w.app:
            return
        w.dll.SetActiveView(w.view)
        w.pump()
        mesh = w.lib.get(w.app, "App.mesh")
        if not mesh:
            w.error_box(w.str_(api.ERR_NOSONNET))
            return
        info.open_edit_mesh_header_dlg(w, mesh)

    def cm_prev_zoom(self, entry):
        self._core("PyCmPrevZoom")

    def cm_remove_labels(self, entry):
        self._core("PyCmRemoveLabels")

    def cb_change_flags(self, entry):
        """CbChangeFlags: the flags of the view with those of the toggles
        (ProcessXViewShowFlags)."""
        w = self.w
        f = w.lib.get(w.view, "View.showFlags")
        for attr, flag in SHOW_TOGGLES:
            if getattr(w, attr).isChecked():
                f |= flag
            else:
                f &= ~flag
        self._core("PyCbChangeFlags", f & 0xFFFFFFFFFFFFFFFF)

    # Commands menu

    def cb_cm_append_template(self, entry):
        self._core("PyCbCmAppendTemplate")

    def cm_convert_elems_to_chords(self, entry):
        self._core("PyCmConvertElemsToChords")

    def cm_convert_chords_to_elems(self, entry):
        self._core("PyCmConvertChordsToElems")

    def cb_cm_renumber(self, entry):
        self._core("PyCbCmRenumber")

    def cb_cm_show_invalid_vars(self, entry):
        """CbCmShowInvalidVars."""
        if self._core("PyCbCmShowInvalidVars"):
            varsdlg.open_invalid_vars_dlg(self.w)

    def cm_rebuild_carre_info(self, entry):
        self._core("PyCmRebuildCarreInfo")

    def cb_glue_points(self, entry):
        rotmov.open_glue_points_dlg(self.w)

    def cb_reduce_elements(self, entry):
        rotmov.open_glue_elems_dlg(self.w)

    def cb_group_normals(self, entry):
        """CbGroupNormals (x_rotmov.c): the normals of all elements, or of
        the marked ones, lined up."""
        w = self.w
        dll = w.dll
        app = w.app
        group = w.lib.get(app, "App.mark") if entry.user else None
        count = ctypes.c_int()
        i = dll.GlueNormals(app, group, ctypes.byref(count))
        w.pump()
        if i:
            dll.Cancel(app)
            w.pump()
            boxes.message_box(w, w.str_(i))
            return
        dll.UndoMark(app)
        w.pump()
        dll.PyViewMsg(w.view, corelib.cstr(files.resource_string_ex(
            w.application.db, ["DivGeo", "main"], ["DivGeo", "XmMainWindow"],
            "msgNormalsGrouped", None, "$(COUNT)%d", count.value)))
        w.pump()

    def cm_edit_topology(self, entry):
        topology.open_topology_dlg(self.w)

    # Variables menu

    def cb_add_var_set(self, entry):
        """CbAddVarSet: the new set, then its Variables dialog."""
        vs = self._core("PyCbAddVarSet", entry.user)
        if vs:
            varsdlg.open_vars_edit_dlg(self.w, vs)

    def cb_del_var_set(self, entry):
        self._core("PyCbDelVarSet", entry.user)

    def cb_edit_var_set(self, entry):
        """CbEditVarSet."""
        w = self.w
        w.dll.ValidatePtr(w.view, b"CbDelVarSet.view")
        if not w.app:
            return
        w.dll.SetActiveView(w.view)
        w.pump()
        varsdlg.open_vars_edit_dlg(w, entry.user)

    # Options menu

    def cm_set_output_mode_x(self, entry):
        """CmSetOutputModeX."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        settings.open_output_mode_dlg(w)

    def cm_set_mesh_options(self, entry):
        """CmSetMeshOptions."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        settings.open_mesh_options_dlg(w)

    def cb_edit_var_set_defs(self, entry):
        setup.cb_edit_var_set_defs(self.w)

    def cb_save_config(self, entry):
        setup.cb_save_config(self.w)

    def cb_set_autosave_interval(self, entry):
        """CbSetAutosaveInterval."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        settings.open_autosave_dlg(w)

    def cb_sw_menu(self, entry=None):
        """CbSwMenu: the menu bar, or the Menu button in the drawing
        area."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        bar = w.menuBar()
        if w.sw_menu.isChecked():
            if bar.isVisible() or not w.isVisible() and not bar.isHidden():
                return
            w.menu_on.hide()
            bar.show()
        else:
            if bar.isHidden():
                return
            bar.hide()
            w.menu_on_created = True
            w.menu_on.show()
            w.menu_on.raise_()

    def options_menu_toggle(self):
        """CbOptionsMenuToggle: the toggle flipped, with its callback."""
        w = self.w
        w.sw_menu.setChecked(not w.sw_menu.isChecked())
        self.cb_sw_menu()

    def cb_sw_toolbar(self, entry=None):
        """CbSwToolbar: the command row shown or hidden."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if w.sw_toolbar.isChecked():
            if not w.command.isHidden():
                return
            w.command.show()
        else:
            if w.command.isHidden():
                return
            w.command.hide()

    def cb_sw_manual_refresh(self, entry=None):
        """CbSwManualRefresh: the Refresh entry shown in manual mode, a
        refresh when it ends."""
        w = self.w
        state = w.sw_manual_refresh.isChecked()
        w.canvas.manual_refresh = state
        if state:
            w.cm_refresh.setVisible(True)
            w.sep_refresh.setVisible(True)
        else:
            w.cm_refresh.setVisible(False)
            w.sep_refresh.setVisible(False)
            self.cb_view_refresh()

    # Window menu

    def cb_window_tool_bar(self, entry=None):
        """CbWindowToolBar: the toolbox, the command row hidden."""
        w = self.w
        if w.tool_box is None:
            w.tool_box = toolbox.ToolBox(w)
            w.tool_box.manage()
            w.notify_view(api.N_NEWTOOL)
        else:
            w.tool_box.popup()
        if w.sw_toolbar.isChecked():
            w.sw_toolbar.setChecked(False)
            self.cb_sw_toolbar()

    def cb_window_open(self, entry):
        """CbWindowOpen: a new view of the model."""
        w = self.w
        if not w.app:
            return
        w.dll.SetActiveView(w.view)
        w.pump()
        app = w.app
        w.application.create_view(app)
        w.dll.UndoMark(app)
        w.pump()

    def cb_window_close(self, entry=None):
        """CbWindowClose, also the close button of the window."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        w.close_view(True)

    def cb_about(self, entry):
        """CbAbout: the About box, modal."""
        dlg = self._open(info.open_about_dlg)
        if dlg is not None:
            dlg.run_modal()

    def cb_window_info(self, entry):
        """CbWindowInfo."""
        self._open(info.open_info_dlg)

    # Help menu

    def cb_help_menu(self, entry):
        """CbHelpMenu: the topic of the resource helpToDisplay."""
        w = self.w
        topic = w.application.db.get(entry.names + ["helpToDisplay"],
                                     entry.classes + ["HelpToDisplay"])
        if topic is None:
            return
        helpwin.display_help_topic(w, topic)

    # Autosave interval of the preferences (CreateAutosaveInfo)

    def create_autosave_info(self):
        w = self.w
        lib = w.lib
        if not prefs.get_int(lib, prefs.PSTR_AUTOSAVE_INTERVAL):
            prefs.set_int(lib, prefs.PSTR_AUTOSAVE_INTERVAL, 5)
        if w.lib.get(w.app, "App.fName"):
            w.start_autosave()
