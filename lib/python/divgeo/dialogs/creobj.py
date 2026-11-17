"""The dialogs of Edit > Create (x_creobj.c): point, source, chord,
surface(s) and grid point(s); several surfaces or grid points are spread
by a law shown in a graph. The core loops of the callbacks are in the
library (src/py/py_dlgs.c)."""

import ctypes

from ..core import api, lib as corelib
from . import boxes
from . import vacreate as vc
from .base import create_ok_cancel_dialog, find_dialog
from .distrgraph import DistrGraph


def _topology_changed(w):
    """A change of the topology since the last N_ALT (w->x->changes)."""
    from ..app.window import CHF_TOPOLOGY
    return w.changes & CHF_TOPOLOGY


def _set_view_flags(w, flags):
    w.dll.SetViewFlags(w.view, w.lib.get(w.view, "View.showFlags") | flags)
    w.pump()


def _undo_mark(w):
    w.dll.UndoMark(w.app)
    w.pump()


def _box(w, parent, text, kind=boxes.error_box):
    w.pump()
    kind(parent, text)


def _string(w, ptr):
    return w.lib.string_at(ptr)


def cb_cm_create_at(window, obj_type):
    """CbCmCreateAt: the dialog of the object type of the menu entry."""
    w = window
    if not w.app:
        return
    w.dll.SetActiveView(w.view)
    w.pump()
    {api.T_NODE: open_create_node_dlg,
     api.T_SOURCE: open_create_source_dlg,
     api.T_CHORD: open_create_chord_dlg,
     api.T_SURFACEEX: open_create_surface_dlg,
     api.T_GRIDPOINTEX: open_create_grid_point_dlg}[obj_type](w)


# Point and source #########################################################

class _XYDlg:
    def __init__(self, window, name, create):
        w = window
        self.w = w
        self.create = create
        self.dlg = dlg = create_ok_cancel_dialog(w, name)
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "l@:xLabel", 0x0101,
            "x?@:x", "x", 0x0201,
            "l@:yLabel", 0x0102,
            "x?@:y", "y", 0x0202,
            refs=self.r)
        vc.form2table(form)
        dlg.manage()

    def ok(self):
        """CbCreateNode, CbCreateSource."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        nx, x = vc.scan_double(vc.text_of(self.r["x"]))
        ny, y = vc.scan_double(vc.text_of(self.r["y"]))
        if nx < 1 or ny < 1:
            _box(w, w, w.str_(api.ERR_INVNUMBERS))
            return
        err = getattr(w.dll, self.create)(w.view, x, y)
        w.pump()
        if err:
            _box(w, w, _string(w, err))


def _open_xy_dlg(window, name, create, flags):
    w = window
    dlg = find_dialog(w, name)
    if dlg is None:
        dlg = _XYDlg(w, name, create).dlg
    else:
        dlg.popup()
    _set_view_flags(w, flags)
    _undo_mark(w)
    return dlg


def open_create_node_dlg(window):
    """OpenCreateNodeDlg."""
    return _open_xy_dlg(window, "dlgCreateNode", "PyCreateNode",
                        api.SHW_IRRNODES)


def open_create_source_dlg(window):
    """OpenCreateSourceDlg."""
    return _open_xy_dlg(window, "dlgCreateSource", "PyCreateSource",
                        api.SHW_SOURCES)


# Chord ####################################################################

def _toggle_managed(frame):
    """CbCToggleManaged, CbToggleManaged: the frame shown with its
    toggle."""
    return lambda wg, d: vc.manage(frame, wg.isChecked())


class CreateChordDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgCreateChord")
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        r = self.r = {}
        vc.create_widget_system(
            form,
            "#:mainForm",
            "$+8:dialogKind", vc.radio_box, {"orientation": "horizontal"},
            "t?:cartesian", "cartesian",
            "t?:cylindrical", "cylindrical",
            "-:",

            "f5?_:tabFrame", "frameCartes",
            "#:distributeForm",
            "#2:table",
            "l#:x1Label", 1, 1,
            "x#?:x1", 2, 1, "x1",
            "l#:yp1Label", 1, 2,
            "x#?:yp1", 2, 2, "yp1",
            "l#:yt1Label", 1, 3,
            "x#?:yt1", 2, 3, "yt1",
            "l#:x2Label", 1, 4,
            "x#?:x2", 2, 4, "x2",
            "l#:yp2Label", 1, 5,
            "x#?:yp2", 2, 5, "yp2",
            "l#:yt2Label", 1, 6,
            "x#?:yt2", 2, 6, "yt2",
            "-#:",
            "-:",
            "-:",

            "f5?_:tabFrame", "frameCylind",
            "#:distributeForm",
            "#2:table",
            "l#:r1Label", 1, 1,
            "x#?:r1", 2, 1, "r1",
            "l#:z1Label", 1, 2,
            "x#?:z1", 2, 2, "z1",
            "l#:ph1Label", 1, 3,
            "x#?:ph1", 2, 3, "ph1",
            "l#:r2Label", 1, 4,
            "x#?:r2", 2, 4, "r2",
            "l#:z2Label", 1, 5,
            "x#?:z2", 2, 5, "z2",
            "l#:ph2Label", 1, 6,
            "x#?:ph2", 2, 6, "ph2",
            "-#:",
            "-:",
            "-:",
            refs=r)
        r["cartesian"].toggled.connect(
            lambda *a: _toggle_managed(r["frameCartes"])(r["cartesian"],
                                                         None))
        r["cylindrical"].toggled.connect(
            lambda *a: _toggle_managed(r["frameCylind"])(r["cylindrical"],
                                                         None))
        r["cartesian"].set_state(True, True)
        dlg.manage()

    def ok(self):
        """CbCreateChord."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        if not w.app:
            return
        r = self.r
        cartes = r["cartesian"].isChecked()
        names = ("x1", "yp1", "x2", "yp2", "yt1", "yt2") if cartes else \
            ("r1", "z1", "r2", "z2", "ph1", "ph2")
        values = []
        for name in names:
            n, v = vc.scan_double(vc.text_of(r[name]))
            if n < 1:
                _box(w, w, w.str_(api.ERR_INVNUMBERS))
                return
            values.append(v)
        x1, y1, x2, y2, z1, z2 = values
        err = w.dll.PyCreateChord(w.view, cartes, x1, y1, z1, x2, y2, z2)
        w.pump()
        if err:
            _box(w, w, _string(w, err))


def open_create_chord_dlg(window):
    """OpenCreateChordDlg."""
    w = window
    dlg = find_dialog(w, "dlgCreateChord")
    if dlg is None:
        dlg = CreateChordDlg(w).dlg
    else:
        dlg.popup()
    _set_view_flags(w, api.SHW_CHORDS)
    _undo_mark(w)
    return dlg


# Surface(s) ###############################################################

def _items(w, func):
    out = []
    proc = api.ITEMPROC(lambda label, value: out.append(
        (label.decode("latin-1"), value)))
    getattr(w.dll, func)(w.view, proc)
    return out


def _sensitive(widget, state):
    """SetSensitiveEx."""
    if widget.isEnabled() != bool(state):
        widget.setEnabled(bool(state))


class CreateSurfaceDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.old_creator_id = ""
        self.old_output_mode = -1
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgCreateSurface")
        dlg.data = self
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        r = self.r = {}
        vc.create_widget_system(
            dlg,
            "#:mainForm",

            "$+8:dialogKind", vc.radio_box, {"orientation": "horizontal"},
            "t?:single", "single",
            "t?:multiple", "multiple",
            "-:",

            "f5?_:tabFrame", "frameSingle",
            "#:singleForm",
            "$+8:byWhat", vc.radio_box, {"orientation": "horizontal"},
            "t?:byLevel", "byLevel",
            "t?:byPoint", "byPoint",
            "-:",
            "f5_?:tabFrame", "frameXY",
            "#:formXY",
            "l#:xLabel", 1, 1,
            "x?#:x", "x", 2, 1,
            "l#:yLabel", 1, 2,
            "x?#:y", "y", 2, 2,
            "-#:",
            "-:",
            "f5?:tabFrame", "frameLevel",
            "#:formLevel",
            "l#:areaLabel", 1, 1,
            "*:areaMenu",
            "b@:area1", 1,
            "b@:area2", 2,
            "b@:area3", 3,
            "-:",
            "o?#:area", "area", 2, 1,
            "l#:levelLabel", 1, 2,
            "x?#:level", "level", 2, 2,
            "-#:",
            "-:",
            "-:",
            "-:",

            "f5?:tabFrame", "frameMulti",
            "#:distributeForm",
            "#2:table",
            "l#:areaLabel", 1, 1,
            "*:areaMenu",
            "b@A:area1", 1, self.select_area, None,
            "b@A:area2", 2, self.select_area, None,
            "b@A:area3", 3, self.select_area, None,
            "-:",
            "o#?:area", 2, 1, "mArea",
            "l#?:level1Label", 1, 2, "mLevel1Label",
            "x#?:level1", 2, 2, "mLevel1",
            "b#A@?:copy1", 3, 2, self.copy_level, None, 1, "mLevel1Pick",
            "l#?:level2Label", 1, 3, "mLevel2Label",
            "x#?:level2", 2, 3, "mLevel2",
            "b#A@?:copy2", 3, 3, self.copy_level, None, 2, "mLevel2Pick",
            "l#:countLabel", 1, 4,
            "x#?:count", 2, 4, "mCount",
            "l#?:alphaLabel", 1, 5, "mAlphaLabel",
            "x#?:alpha", 2, 5, "mAlpha",
            "l#?:alpha2Label", 1, 6, "mAlpha2Label",
            "x#?:alpha2", 2, 6, "mAlpha2",
            "l#?:lawLabel", 1, 7, "lawLabel",
            "*:lawMenu",
            "b@:lawN", api.DGLAW_NORMAL,
            "b@:lawR", api.DGLAW_FLIPPED,
            "b@:lawS", api.DGLAW_SYMMETRIC,
            "b@:law2", api.DGLAW_2ALPHA,
            "b@:lawD", api.DGLAW_DELTA,
            "-:",
            "o#?:law", 2, 7, "mLaw",
            "b#?:boundingElem", 2, 8, "mBoundingElem",
            "b#A:reset", 1, 9, lambda wg, d: self.dg.reset(), None,
            "t#?:removeOld", 2, 9, "swRemoveOld",
            "b#A:copy3", 4, 0, self.pick_settings, None,
            "-#:",
            "f5:frame",
            "$?:distributeGraph", vc.drawing_area, None, "mDraw",
            "-:",
            "-:",
            "-:",
            "-:",
            refs=r)
        r["byLevel"].set_state(True, True)
        r["multiple"].set_state(True, True)
        _sensitive(r["swRemoveOld"], False)
        for sw, frame in (("single", "frameSingle"),
                          ("multiple", "frameMulti"),
                          ("byLevel", "frameLevel"),
                          ("byPoint", "frameXY")):
            r[sw].toggled.connect(
                lambda *a, s=r[sw], f=r[frame]: vc.manage(f, s.isChecked()))
        r["mBoundingElem"].clicked.connect(self.mark_bounding_elem)
        w.add_dependent_rule(dlg.ok, ("exists", api.T_EQUIL))
        dlg.manage()
        self.dg = DistrGraph(w, dlg, r["mDraw"], r["mCount"], r["mAlpha"],
                             r["mAlphaLabel"],
                             r["mAlpha2"], r["mAlpha2Label"], r["mLaw"],
                             r["lawLabel"])
        w.add_dependent(dlg, api.N_NOW | api.N_NEWAPP | api.N_ALT, None,
                        self.dw_csd)

    # Creation

    def create_single(self):
        """CSD_CreateSingle."""
        w = self.w
        r = self.r
        w.dll.SetActiveView(w.view)
        w.pump()
        app = w.app
        if not app or not w.lib.get(app, "App.equil"):
            return
        if w.lib.get(app, "App.outputMode") == api.OUTPUTMODE_CARRE:
            _box(w, self.dlg, w.str_(api.ERR_CARRE_INHIBITS))
            return
        if r["byLevel"].isChecked():
            area = vc.get_option_menu_value(r["area"])
            level = vc.get_text_double(r["level"])
            if level == vc.MAXDOUBLE:
                _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
                return
            err = w.dll.PyCreateSurfaceByLevel(w.view, area, level)
        else:
            x = vc.get_text_double(r["x"])
            y = vc.get_text_double(r["y"])
            if x == vc.MAXDOUBLE or y == vc.MAXDOUBLE:
                _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
                return
            err = w.dll.PyCreateSurfaceByXY(w.view, x, y)
        w.pump()
        if err:
            _box(w, self.dlg, _string(w, err))

    def create_multiple(self):
        """CSD_CreateMultiple."""
        w = self.w
        r = self.r
        dlg = self.dlg
        dg = self.dg
        area = vc.get_option_menu_value(r["mArea"])
        if dg.get_data(True):
            return
        app = w.app
        carre_mode = w.lib.get(app, "App.outputMode") == \
            api.OUTPUTMODE_CARRE
        if not carre_mode:
            level1 = vc.get_text_double(r["mLevel1"])
            level2 = vc.get_text_double(r["mLevel2"])
            if level1 == vc.MAXDOUBLE or level2 == vc.MAXDOUBLE:
                _box(w, dlg, w.str_(api.ERR_INVNUMBERS))
                return
        else:
            if dg.law != api.DGLAW_DELTA:
                _box(w, dlg, vc.resource_string(r["mLaw"],
                                                "errWrongCarreLaw"))
                return
            level1 = 0.0
            level2 = 1.0
        if level1 == level2:
            _box(w, dlg, vc.resource_string(dlg, "errEqualLevels"))
            return
        if carre_mode:
            r["swRemoveOld"].set_state(True, False)
        if r["swRemoveOld"].isChecked():
            if not carre_mode:
                i = w.dll.PyDelSurfacesOfCreator(
                    w.view, corelib.cstr(self.old_creator_id))
                w.pump()
                if not i:
                    w.dll.Cancel(app)
                    _box(w, dlg, vc.resource_string(
                        dlg, "errOldSurfacesNotFound"))
                    return
        elif carre_mode:
            w.dll.Cancel(app)
            _box(w, dlg, vc.resource_string(dlg, "errCarreOldSurfaces"))
            return
        creator = ctypes.c_void_p()
        rc = w.dll.DistributeSurfaces(app, area, dg.count, dg.alpha[0],
                                      dg.alpha[1], dg.law, level1, level2,
                                      carre_mode, ctypes.byref(creator))
        w.pump()
        if rc:
            w.dll.Cancel(app)
            _box(w, dlg, w.str_(rc), boxes.message_box)
            return
        self.old_creator_id = _string(w, creator.value) or ""
        if not carre_mode:
            _sensitive(r["swRemoveOld"], bool(dg.count))
            r["swRemoveOld"].set_state(bool(dg.count), True)
        _set_view_flags(w, api.SHW_SURFACES)
        _undo_mark(w)

    def ok(self):
        """CbCreateSurfaceOk."""
        if self.r["single"].isChecked():
            self.create_single()
        else:
            self.create_multiple()

    # Buttons of the multiple form

    def copy_level(self, wg, data):
        """CbCSD_CopyLevel: area and level of the examined surface."""
        w = self.w
        r = self.r
        if w.lib.get(w.app, "App.outputMode") == api.OUTPUTMODE_CARRE:
            return
        zone, level, cid = ctypes.c_int(), ctypes.c_double(), \
            ctypes.c_void_p()
        if not w.dll.PyExaminedSurfaceEx(w.view, ctypes.byref(zone),
                                         ctypes.byref(level),
                                         ctypes.byref(cid)):
            _box(w, self.dlg, vc.resource_string(
                self.dlg, "errNoRememberedSurface"))
            return
        if zone.value < 0:
            _box(w, self.dlg, w.str_(api.ERR_NOSURFZONE))
            return
        vc.set_option_menu_value(r["mArea"], zone.value)
        s = "%g" % level.value
        vc.set_text(r["mLevel1"] if wg.xm_user == 1 else r["mLevel2"], s)
        r["swRemoveOld"].set_state(False, True)

    def pick_settings(self, wg, data):
        """CbCSD_PickSettings: the settings of the examined surface."""
        w = self.w
        r = self.r
        dg = self.dg
        zone, level, cid = ctypes.c_int(), ctypes.c_double(), \
            ctypes.c_void_p()
        if not w.dll.PyExaminedSurfaceEx(w.view, ctypes.byref(zone),
                                         ctypes.byref(level),
                                         ctypes.byref(cid)):
            _box(w, self.dlg, vc.resource_string(
                self.dlg, "errNoRememberedSurface"))
            return
        area, count, law, carre = (ctypes.c_int() for _ in range(4))
        a1, a2, l1, l2 = (ctypes.c_double() for _ in range(4))
        if w.dll.ParseSurfaceCreatorId(cid, ctypes.byref(area),
                                       ctypes.byref(count), ctypes.byref(a1),
                                       ctypes.byref(a2), ctypes.byref(law),
                                       ctypes.byref(l1), ctypes.byref(l2),
                                       ctypes.byref(carre)):
            _box(w, self.dlg, vc.resource_string(self.dlg,
                                                 "errBadCreatorId"))
            return
        carre_mode = w.lib.get(w.app, "App.outputMode") == \
            api.OUTPUTMODE_CARRE
        if carre_mode and not carre.value:
            _box(w, self.dlg, vc.resource_string(self.dlg,
                                                 "errNonCarreMode"))
            return
        vc.set_option_menu_value(r["mArea"], area.value)
        if not carre.value:
            vc.set_text(r["mLevel1"], "%g" % l1.value)
            vc.set_text(r["mLevel2"], "%g" % l2.value)
        vc.set_text(dg.w_count, "%d" % (count.value + 1))
        vc.set_text(dg.w_alpha[0], "%g" % a1.value)
        vc.set_text(dg.w_alpha[1], "%g" % a2.value)
        vc.set_option_menu_value(dg.w_law, law.value)
        self.old_creator_id = _string(w, cid.value) or ""
        dg.numbers_changed(None)
        if not carre_mode:
            _sensitive(r["swRemoveOld"], True)
            r["swRemoveOld"].set_state(True, True)

    def select_area(self, wg, data):
        """CbCSD_SelectArea."""
        w = self.w
        if w.lib.get(w.app, "App.outputMode") != api.OUTPUTMODE_CARRE:
            _sensitive(self.r["swRemoveOld"], False)
            self.r["swRemoveOld"].set_state(False, True)

    def mark_bounding_elem(self):
        """CbCSD_MarkBoundingElem."""
        w = self.w
        area = vc.get_option_menu_value(self.r["mArea"])
        if not w.app:
            return
        w.dll.PyMarkBoundingElem(w.view, area)
        w.pump()

    def dw_csd(self, widget=None, kind=api.N_NOW, obj=None, user=None):
        """DwCSD: the area menus after a change of the topology, the fields
        after a change of the output mode."""
        w = self.w
        r = self.r
        if kind == api.N_ALT and not self.dlg.isVisible():
            return
        if kind in (api.N_NOW, api.N_NEWAPP) or \
                (kind == api.N_ALT and _topology_changed(w)):
            items = _items(w, "PySurfaceZoneItems")
            vc.set_option_menu_items(r["area"], items)
            vc.set_option_menu_items(r["mArea"], items)
        mode = w.lib.get(w.app, "App.outputMode")
        if self.old_output_mode != mode:
            self.old_output_mode = mode
            b = mode == api.OUTPUTMODE_CARRE
            for name in ("mLevel1", "mLevel1Label", "mLevel1Pick",
                         "mLevel2", "mLevel2Label", "mLevel2Pick",
                         "swRemoveOld"):
                _sensitive(r[name], not b)
            _sensitive(r["mBoundingElem"], b)
            r["swRemoveOld"].set_state(b, True)
            if b:
                vc.set_text(r["mLevel1"], "")
                vc.set_text(r["mLevel2"], "")
                vc.set_option_menu_value(r["mLaw"], api.DGLAW_DELTA)
                _sensitive(r["swRemoveOld"], False)
                self.dg.numbers_changed(None)


def open_create_surface_dlg(window):
    """OpenCreateSurfaceDlg."""
    w = window
    dlg = find_dialog(w, "dlgCreateSurface")
    if dlg is None:
        dlg = CreateSurfaceDlg(w).dlg
    else:
        dlg.data.dw_csd(None, api.N_NOW)
        dlg.popup()
    _set_view_flags(w, api.SHW_SURFACES)
    _undo_mark(w)
    return dlg


# Grid point(s) ############################################################

class CreateGridPointDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.old_output_mode = -1
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgCreateGridPoint")
        dlg.data = self
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        r = self.r = {}
        vc.create_widget_system(
            dlg,
            "#:mainForm",
            "$+8:dialogKind", vc.radio_box, {"orientation": "horizontal"},
            "t?:single", "single",
            "t?:multiple", "multiple",
            "-:",

            "f5?_:tabFrame", "frameSingle",
            "#:singleForm",
            "l#:areaLabel", 1, 1,
            "*:areaMenu",
            "b@:area0", 0,
            "b@?:area1", 1, "area1",
            "b@:area2", 2,
            "-:",
            "o#?:area", 2, 1, "area",
            "l#:valueLabel", 1, 2,
            "x?#:value", "value", 2, 2,
            "-#:",
            "-:",

            "f5?:tabFrame", "frameMultiple",
            "#:distributeForm",
            "#2:table",
            "l#:zoneLabel", 1, 1,
            "*:zoneMenu",
            "b@:area0", 0,
            "b@:area1", 1,
            "b@:area2", 2,
            "-:",
            "o#?:zone", 2, 1, "mZone",
            "l#:countLabel", 1, 2,
            "x#?:count", 2, 2, "mCount",
            "l#?:alphaLabel", 1, 3, "mAlphaLabel",
            "x#?:alpha", 2, 3, "mAlpha",
            "l#?:alpha2Label", 1, 4, "mAlpha2Label",
            "x#?:alpha2", 2, 4, "mAlpha2",
            "l#?:lawLabel", 1, 5, "lawLabel",
            "*:lawMenu",
            "b@:lawN", api.DGLAW_NORMAL,
            "b@:lawR", api.DGLAW_FLIPPED,
            "b@:lawS", api.DGLAW_SYMMETRIC,
            "b@:law2", api.DGLAW_2ALPHA,
            "b@:lawD", api.DGLAW_DELTA,
            "-:",
            "o#?:law", 2, 5, "mLaw",
            "b#A:reset", 1, 6, lambda wg, d: self.dg.reset(), None,
            "b#A:copy3", 4, 0, self.pick_settings, None,
            "-#:",
            "f5:frame",
            "$?:distributeGraph", vc.drawing_area, None, "mDraw",
            "-:",
            "-:",
            "-:",
            refs=r)
        r["multiple"].set_state(True, True)
        for sw, frame in (("single", "frameSingle"),
                          ("multiple", "frameMultiple")):
            r[sw].toggled.connect(
                lambda *a, s=r[sw], f=r[frame]: vc.manage(f, s.isChecked()))
        dlg.manage()
        self.dg = DistrGraph(w, dlg, r["mDraw"], r["mCount"], r["mAlpha"],
                             r["mAlphaLabel"], r["mAlpha2"],
                             r["mAlpha2Label"], r["mLaw"], r["lawLabel"])
        w.add_dependent(dlg, api.N_NOW | api.N_NEWAPP | api.N_ALT, None,
                        self.dw_cgpd)

    def create_single(self):
        """CGPD_CreateSingle."""
        w = self.w
        r = self.r
        w.dll.SetActiveView(w.view)
        w.pump()
        app = w.app
        if not app:
            return
        if w.lib.get(app, "App.outputMode") == api.OUTPUTMODE_CARRE:
            _box(w, self.dlg, w.str_(api.ERR_CARRE_INHIBITS))
            return
        area = vc.get_option_menu_value(r["area"])
        value = vc.get_text_double(r["value"])
        if value == vc.MAXDOUBLE:
            _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        if value < 0 or value > 1:
            _box(w, self.dlg, w.str_(api.ERR_INVAREA))
            return
        err = w.dll.PyCreateGridPoint(w.view, area, value)
        w.pump()
        if err:
            _box(w, self.dlg, _string(w, err))

    def create_multiple(self):
        """CGPD_CreateMultiple."""
        w = self.w
        dg = self.dg
        zone = vc.get_option_menu_value(self.r["mZone"])
        if dg.get_data(True):
            return
        app = w.app
        carre_mode = w.lib.get(app, "App.outputMode") == \
            api.OUTPUTMODE_CARRE
        if carre_mode and dg.law != api.DGLAW_DELTA:
            _box(w, self.dlg, vc.resource_string(self.r["mLaw"],
                                                 "errWrongCarreLaw"))
            return
        w.dll.PyDelGridPointsOfZone(w.view, zone)
        w.pump()
        rc = w.dll.DistributeGridPoints(app, zone, dg.count, dg.alpha[0],
                                        dg.alpha[1], dg.law, carre_mode)
        w.pump()
        if rc:
            w.dll.Cancel(app)
            _box(w, self.dlg, w.str_(rc))
            return
        _set_view_flags(w, api.SHW_GRIDPOINTS)
        _undo_mark(w)

    def ok(self):
        """CbCreateGridPointOk."""
        if self.r["single"].isChecked():
            self.create_single()
        else:
            self.create_multiple()

    def pick_settings(self, wg, data):
        """CbCGPD_PickSettings."""
        w = self.w
        dg = self.dg
        cid = ctypes.c_void_p()
        if not w.dll.PyExaminedGridPointEx(w.view, ctypes.byref(cid)):
            _box(w, self.dlg, vc.resource_string(
                self.dlg, "errNoRememberedGridPoint"))
            return
        area, count, law, carre = (ctypes.c_int() for _ in range(4))
        a1, a2 = ctypes.c_double(), ctypes.c_double()
        if w.dll.ParseGridPointCreatorId(cid, ctypes.byref(area),
                                         ctypes.byref(count),
                                         ctypes.byref(a1), ctypes.byref(a2),
                                         ctypes.byref(law),
                                         ctypes.byref(carre)):
            _box(w, self.dlg, vc.resource_string(self.dlg,
                                                 "errBadCreatorId"))
            return
        if w.lib.get(w.app, "App.outputMode") == api.OUTPUTMODE_CARRE \
                and not carre.value:
            _box(w, self.dlg, vc.resource_string(self.dlg,
                                                 "errNonCarreMode"))
            return
        vc.set_option_menu_value(self.r["mZone"], area.value)
        vc.set_text(dg.w_count, "%d" % (count.value + 1))
        vc.set_text(dg.w_alpha[0], "%g" % a1.value)
        vc.set_text(dg.w_alpha[1], "%g" % a2.value)
        vc.set_option_menu_value(dg.w_law, law.value)
        dg.numbers_changed(None)

    def dw_cgpd(self, widget=None, kind=api.N_NOW, obj=None, user=None):
        """DwCGPD."""
        w = self.w
        r = self.r
        if kind == api.N_ALT and not self.dlg.isVisible():
            return
        if kind in (api.N_NOW, api.N_NEWAPP) or \
                (kind == api.N_ALT and _topology_changed(w)):
            items = _items(w, "PyGridPointSegItems")
            vc.set_option_menu_items(r["area"], items)
            vc.set_option_menu_items(r["mZone"], items)
        mode = w.lib.get(w.app, "App.outputMode")
        if self.old_output_mode != mode:
            self.old_output_mode = mode
            if mode == api.OUTPUTMODE_CARRE:
                vc.set_option_menu_value(r["mLaw"], api.DGLAW_DELTA)
                self.dg.numbers_changed(None)


def open_create_grid_point_dlg(window):
    """OpenCreateGridPointDlg."""
    w = window
    dlg = find_dialog(w, "dlgCreateGridPoint")
    if dlg is None:
        dlg = CreateGridPointDlg(w).dlg
    else:
        dlg.data.dw_cgpd(None, api.N_NOW)
        dlg.popup()
    _set_view_flags(w, api.SHW_GRIDPOINTS)
    _undo_mark(w)
    return dlg
