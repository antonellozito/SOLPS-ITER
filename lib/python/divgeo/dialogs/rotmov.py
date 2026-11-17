"""Dialogs of geometric changes (x_rotmov.c): Move/Rotate, Fill gaps,
Merge/Split elements, Stretch and Set angle. The core part of Move/Rotate
and Stretch is in the library (src/py/py_dlgs.c)."""

import ctypes
import math

from ..core import api, lib as corelib
from . import boxes, files
from . import vacreate as vc
from .base import create_ok_cancel_dialog, find_dialog


def _box(window, parent, text, kind=boxes.error_box):
    window.pump()
    kind(parent, text)


# Move/Rotate ##############################################################

class RotMoveDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgRotMove")
        dlg.callbacks["ok"].append(self.move)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        rotate = vc.PushButton(dlg, "rotate")
        dlg.xm_place(rotate)
        rotate.clicked.connect(self.rotate)
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        r = self.r = {}
        vc.create_widget_system(
            form,
            "#8?:form1", "form1",
            "l#:xLabel", 1, 1,
            "x#?:x", 2, 1, "x",
            "l#:yLabel", 1, 2,
            "x#?:y", 2, 2, "y",
            "l#:scaleLabel", 1, 3,
            "x#?:scale", 2, 3, "scale",
            "-#:",
            refs=r)
        form.xm_place(vc.Separator(form, "separ"))
        row = vc.row_column(form, "rowCol")
        form.xm_place(row)
        self.sw_elems = vc.ToggleButton(row, "elems")
        row.xm_place(self.sw_elems)
        w.add_dependent_rule(self.sw_elems, ("exists", api.T_ELEM))
        self.sw_template = vc.ToggleButton(row, "template")
        row.xm_place(self.sw_template)
        w.add_dependent_rule(self.sw_template, ("exists", api.T_TEMPLATE))
        dlg.manage()

    def rotate(self):
        """CbRotMoveDlgRotate."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        err = w.dll.PyRotMoveRotate(w.view, self.sw_elems.isChecked(),
                                    self.sw_template.isChecked())
        w.pump()
        if err:
            _box(w, self.dlg, w.lib.string_at(err))

    def move(self):
        """CbRotMoveDlgMove."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        x = vc.get_text_double(self.r["x"])
        y = vc.get_text_double(self.r["y"])
        scale = vc.get_text_double(self.r["scale"])
        if vc.MAXDOUBLE in (x, y, scale):
            _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        if scale <= 0:
            _box(w, self.dlg, vc.resource_string(self.dlg, "errBadScale"))
            return
        err = w.dll.PyRotMoveMove(w.view, x, y, scale,
                                  self.sw_elems.isChecked(),
                                  self.sw_template.isChecked())
        w.pump()
        if err:
            _box(w, self.dlg, w.lib.string_at(err))


def open_rot_move_dlg(window):
    """OpenRotMoveDlg."""
    dlg = find_dialog(window, "dlgRotMove")
    if dlg is None:
        dlg = RotMoveDlg(window).dlg
    else:
        dlg.popup()
    return dlg


# Fill gaps, Merge/Split elements #########################################

def _glue_message(w, dlg, name, count):
    w.dll.PyViewMsg(w.view, corelib.cstr(vc_resource_ex(
        dlg, name, "$(COUNT)%d", count)))
    w.pump()


def vc_resource_ex(widget, name, fmt, *args):
    """GetResourceStringEx of a dialog widget (class: the name)."""
    names, classes = vc.path_of(widget)
    return files.resource_string_ex(vc._db(widget), names, classes, name,
                                    None, fmt, *args)


class GluePointsDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgGluePoints")
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        self.r = {}
        vc.create_widget_system(
            dlg,
            "#:form",
            "l#:maxDistLabel", 1, 1,
            "x#?:maxDist", 2, 1, "maxDist",
            "l#:millimeters", 3, 1,
            "t#?:markedOnly", 2, 2, "markedOnly",
            "-#:",
            refs=self.r)
        dlg.manage()

    def ok(self):
        """CbGluePointsDlgOk."""
        w, dlg = self.w, self.dlg
        max_dist = vc.get_text_double(self.r["maxDist"])
        if max_dist == vc.MAXDOUBLE or max_dist <= 0:
            _box(w, dlg, vc.resource_string(dlg, "errBadMaxDist"))
            return
        marked = self.r["markedOnly"].isChecked()
        count = ctypes.c_int(0)
        app = w.app
        i = w.dll.GlueNodes(app, w.lib.get(app, "App.mark") if marked
                            else None, max_dist, ctypes.byref(count))
        w.pump()
        if i:
            w.dll.Cancel(app)
            _box(w, dlg, w.str_(i), boxes.message_box)
            return
        w.dll.UndoMark(app)
        w.pump()
        dlg.popdown()
        _glue_message(w, dlg, "msgElemsAdded", count.value)


def open_glue_points_dlg(window):
    """CbGluePoints, OpenGluePointsDlg."""
    dlg = find_dialog(window, "dlgGluePoints")
    if dlg is None:
        dlg = GluePointsDlg(window).dlg
    else:
        dlg.popup()
    return dlg


class GlueElemsDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgGlueElems")
        dlg.callbacks["ok"].append(self.ok)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        self.r = {}
        vc.create_widget_system(
            dlg,
            "#:form",
            "l#:thresholdLabel", 1, 1,
            "x#?:threshold", 2, 1, "threshold",
            "l#:millimeters", 3, 1,
            "l#:maxLenLabel", 1, 2,
            "x#?:maxLen", 2, 2, "maxLen",
            "l#:millimeters", 3, 2,
            "t#?:cutLonger", 2, 3, "cutLonger",
            "t#?:markedOnly", 2, 4, "markedOnly",
            "-#:",
            refs=self.r)
        dlg.manage()

    def ok(self):
        """CbGlueElemsDlgOk."""
        w, dlg = self.w, self.dlg
        max_dist = vc.get_text_double(self.r["threshold"])
        if max_dist == vc.MAXDOUBLE or max_dist <= 0:
            _box(w, dlg, vc.resource_string(dlg, "errBadMaxDist"))
            return
        max_len = vc.get_text_double(self.r["maxLen"])
        if max_len == vc.MAXDOUBLE or max_len <= 0:
            _box(w, dlg, vc.resource_string(dlg, "errBadMaxLen"))
            return
        marked = self.r["markedOnly"].isChecked()
        cut = self.r["cutLonger"].isChecked()
        count = ctypes.c_int(0)
        app = w.app
        i = w.dll.GlueElems(app, w.lib.get(app, "App.mark") if marked
                            else None, max_dist, max_len, cut,
                            ctypes.byref(count))
        w.pump()
        if i:
            w.dll.Cancel(app)
            _box(w, dlg, w.str_(i), boxes.message_box)
            return
        w.dll.UndoMark(app)
        w.pump()
        dlg.popdown()
        _glue_message(w, dlg, "msgElemsRemoved", count.value)


def open_glue_elems_dlg(window):
    """CbReduceElements, OpenGlueElemsDlg."""
    dlg = find_dialog(window, "dlgGlueElems")
    if dlg is None:
        dlg = GlueElemsDlg(window).dlg
    else:
        dlg.popup()
    return dlg


# Stretch ##################################################################

class StretchDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgStretch")
        dlg.callbacks["ok"].append(self.set_factors)
        dlg.callbacks["help"].append(lambda: w.help_on(dlg))
        reset = vc.PushButton(dlg, "reset")
        dlg.xm_place(reset)
        reset.clicked.connect(self.reset_fields)
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "#8?:form1", "form1",
            "l#:xLabel", 1, 1,
            "x#?:x", 2, 1, "x",
            "l#:yLabel", 1, 2,
            "x#?:y", 2, 2, "y",
            "-#:",
            refs=self.r)
        self.reset_fields()
        form.xm_place(vc.Separator(form, "separ"))
        dlg.manage()

    def reset_fields(self):
        """StretchDlgResetFields."""
        s = "%f" % 1.0
        vc.set_text(self.r["x"], s)
        vc.set_text(self.r["y"], s)

    def set_factors(self):
        """CbStretchDlgSetFactors."""
        w = self.w
        w.dll.ValidatePtr(w.view, b"CbStretchDlgSetFactors")
        w.dll.SetActiveView(w.view)
        w.pump()
        xs = vc.get_text_double(self.r["x"])
        ys = vc.get_text_double(self.r["y"])
        if xs == 0 or xs == vc.MAXDOUBLE or ys == 0 or ys == vc.MAXDOUBLE:
            _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        w.dll.PyStretchDlgSet(w.view, xs, ys)
        w.pump()


def open_stretch_dlg(window):
    """OpenStretchDlg."""
    dlg = find_dialog(window, "dlgStretch")
    if dlg is None:
        dlg = StretchDlg(window).dlg
    else:
        dlg.popup()
    return dlg


# Set angle ################################################################

class SetAngleDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.dlg = dlg = create_ok_cancel_dialog(w, "dlgSetAngle")
        dlg.callbacks["ok"].append(self.set_angle)
        dlg.help.hide()
        form = vc.Form(dlg, "form")
        dlg.xm_place(form)
        self.r = {}
        vc.create_widget_system(
            form,
            "l@:angleLabel", 0x0101,
            "x?@:angle", "angle", 0x0102,
            refs=self.r)
        vc.form2table(form)
        vc.set_text(self.r["angle"], _angle_text(w))
        dlg.manage()

    def set_angle(self):
        """CbSetAngle."""
        w = self.w
        w.dll.ValidatePtr(w.view, b"CbSetAngle")
        w.dll.SetActiveView(w.view)
        w.pump()
        deg = vc.get_text_double(self.r["angle"])
        if deg == vc.MAXDOUBLE:
            _box(w, self.dlg, w.str_(api.ERR_INVNUMBERS))
            return
        w.dll.SetViewAngle(w.view, math.pi / 180 * deg)
        w.pump()
        self.dlg.popdown()
        w.dll.UndoMark(w.app)
        w.pump()


def _angle_text(w):
    return "%f" % (180 / math.pi * w.lib.get(w.view, "View.xyAngle"))


def open_set_angle_dlg(window):
    """OpenSetAngleDlg."""
    dlg = find_dialog(window, "dlgSetAngle")
    if dlg is None:
        dlg = SetAngleDlg(window).dlg
    else:
        angle = dlg.findChild(vc.Text, "angle")
        vc.set_text(angle, _angle_text(window))
        dlg.popup()
    return dlg
