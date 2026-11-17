"""Commands > Edit topology (x_topo.c): X points, separatrix sections,
equilibrium zones and the topology name, in four tabs; an object examined
with the mouse is shown in its tab. The core part of the callbacks is in
the library (src/py/py_topo.c)."""

import ctypes

from ..core import api, lib as corelib
from . import boxes
from . import vacreate as vc
from .base import MessageDialog, find_dialog

SZ_NEWPTR = -4


def _str(w, ptr):
    return w.lib.string_at(ptr)


def _sensitive(widget, state):
    """SetSensitiveEx."""
    if widget.isEnabled() != bool(state):
        widget.setEnabled(bool(state))


def _one_word(s):
    words = s.split()
    return words[0] if len(words) == 1 else None


class TopologyDlg:
    def __init__(self, window):
        w = window
        self.w = w
        self.old_output_mode = -1
        self.cur = None
        self.dlg = dlg = MessageDialog(w, "dlgTopology", auto_unmanage=False)
        dlg.data = self
        dlg.callbacks["cancel"].append(self.unmap)
        dlg.wm_close = self.unmap
        for b in (dlg.message, dlg.ok, dlg.cancel, dlg.help):
            b.hide()
        r = self.r = {}
        vc.create_widget_system(
            dlg,
            "#:mainForm",
            "$+8:dialogKind", vc.row_column, {"orientation": "horizontal"},
            "t?:xpoints", "swXPoints",
            "t?:sections", "swSections",
            "t?:zones", "swZones",
            "t?:name", "swName",
            "-:",

            "f5?:tabFrame", "frameXPoints",
            "#:xpointsForm",
            "b#A:detectAllXPoints", 0, 1, lambda wg, d: self.detect(False),
            None,
            "s-#:separator", 0, 5,
            "l#:xptLevelLabel", 1, 6,
            "x#?:levelText", 2, 6, "xptLevel",
            "b#?A:xptLevelBtn", 3, 6, "xptLevelBtn",
            lambda wg, d: self.xpt_level(), None,
            "-#:",
            "-:",

            "f5?_:tabFrame", "frameSections",
            "#:sectionsForm",
            "b#A:detectAll", 0, 1, lambda wg, d: self.detect(True), None,
            "s-#:separator", 0, 5,
            "l#:sectTitle", 0, 6,
            "l#:idLabel", 1, 10,
            "x#?:id", 2, 10, "xSegId",
            "l#:shortLabel", 1, 11,
            "x#?:short", 2, 11, "xSegName",
            "l#:longLabel", 1, 12,
            "x#?:long", 2, 12, "xSegDescr",
            "t#?:gpsTargetCW", 1, 13, "xSegTargetCW",
            "t#?:sectUsed", 2, 13, "xSegUsed",
            "b#?A:sectBtn", 0, 20, "xSegBtn",
            lambda wg, d: self.xseg(), None,
            "b#?A:sectRevertBtn", 0, 21, "xSegRevertBtn",
            lambda wg, d: self.xseg_revert(), None,
            "-#:",
            "-:",

            "f5?_:tabFrame", "frameZones",
            "#:zonesForm",
            "##:listForm", 0, 1,
            "$?5:list", vc.scrolled_list, {"browse": True}, "szList",
            "-:",
            "s-#:separator", 0, 5,
            "l#:zonesTitle", 0, 6,
            "l#:zidLabel", 1, 10,
            "x#?:id", 2, 10, "szId",
            "l#:zshortLabel", 1, 11,
            "x#?:short", 2, 11, "szName",
            "l#:zlongLabel", 1, 12,
            "x#?:long", 2, 12, "szDescr",
            "l#:gps1Label", 1, 13,
            "x#?:gps1", 2, 13, "szGps1",
            "l#:orientLabel", 1, 15,
            "*:orientMenu",
            "b@:left", 1,
            "b@:right", -1,
            "-:",
            "o#?:orient", 2, 15, "szOrient",
            "l#:gps2Label", 1, 14,
            "x#?:gps2", 2, 14, "szGps2",
            "t#?:closed", 2, 16, "szClosed",
            "b#?A:szSetBtn", 0, 20, "szSetBtn",
            lambda wg, d: self.sz_set(), None,
            "b#?A:szDeleteBtn", 0, 22, "szDeleteBtn",
            lambda wg, d: self.sz_delete(), None,
            "-#:",
            "-:",

            "f5?_:tabFrame", "frameName",
            "#:nameForm",
            "l#:topoNameLabel", 1, 6,
            "x#?T:topoName", 2, 6, "tnName",
            lambda wg, d: _sensitive(self.r["tnSetBtn"], True), None,
            "b#?A:topoNameBtn", 3, 6, "tnSetBtn",
            lambda wg, d: self.name_btn(), None,
            "-#:",
            "-:",

            "-:",
            refs=r)
        r["szList"].browse_callbacks.append(self.sz_list_select)
        r["swXPoints"].set_state(True, True)
        for sw, frame in (("swXPoints", "frameXPoints"),
                          ("swSections", "frameSections"),
                          ("swZones", "frameZones"),
                          ("swName", "frameName")):
            r[sw].toggled.connect(
                lambda *a, s=r[sw], f=r[frame]: vc.manage(f, s.isChecked()))
        w.add_dependent(dlg, api.N_NOW | api.N_NEWAPP | api.N_ALT, None,
                        self.dw_topo)
        dlg.manage()

    def _msg(self, res):
        w = self.w
        w.dll.PyViewMsg(w.view, corelib.cstr(vc.resource_string(self.dlg,
                                                                res)))
        w.pump()

    def _error(self, res):
        if res:
            boxes.error_box(self.dlg, vc.resource_string(
                self.dlg, self.w.lib.string_at(res)))
            return True
        return False

    def _cur(self):
        return None if self.cur in (None, SZ_NEWPTR) else self.cur

    # Callbacks

    def unmap(self):
        """CbTopoUnmap."""
        self.w.dll.SetViewEditTopology(self.w.view, 0)
        self.w.pump()
        self.dlg.popdown()

    def detect(self, segments):
        """CbTopoDetectXPoints, CbTopoDetectXSegs."""
        self.w.dll.PyTopoDetect(self.w.view, segments)
        self.w.pump()

    def notify_examine(self, obj):
        """TopoDlg_NotifyExamine."""
        w = self.w
        r = self.r
        _sensitive(r["xptLevelBtn"], False)
        _sensitive(r["xSegRevertBtn"], False)
        if not obj:
            return
        level, zone, flags = ctypes.c_double(), ctypes.c_int(), \
            ctypes.c_long()
        short, long_ = ctypes.c_void_p(), ctypes.c_void_p()
        t = w.dll.PyTopoExamined(w.view, obj, ctypes.byref(level),
                                 ctypes.byref(zone), ctypes.byref(short),
                                 ctypes.byref(long_), ctypes.byref(flags))
        if t == api.T_XPOINTTEST:
            r["swXPoints"].set_state(True, True)
            vc.set_text(r["xptLevel"], "%g" % level.value)
            _sensitive(r["xptLevelBtn"], True)
            self.cur = obj
        elif t == api.T_XPOINTSEG:
            if r["swXPoints"].isChecked():
                r["swSections"].set_state(True, True)
            vc.set_text(r["xSegId"], "%d" % zone.value)
            vc.set_text(r["xSegName"], _str(w, short.value) or "")
            vc.set_text(r["xSegDescr"], _str(w, long_.value) or "")
            _sensitive(r["xSegBtn"], True)
            r["xSegUsed"].set_state(flags.value & api.GPSF_USED, False)
            r["xSegTargetCW"].set_state(flags.value & api.GPSF_TARGET_CW,
                                        False)
            _sensitive(r["xSegRevertBtn"], True)
            self.cur = obj

    def xpt_level(self):
        """CbTopoXptLevelBtn."""
        w = self.w
        level = vc.get_text_double(self.r["xptLevel"])
        err = w.dll.PyTopoXptLevel(w.view, self._cur(), level)
        w.pump()
        if self._error(err):
            return
        _sensitive(self.r["xptLevelBtn"], False)
        self._msg("msgXptLevelAdjusted")

    def xseg(self):
        """CbTopoXSegBtn."""
        w = self.w
        r = self.r
        err = w.dll.PyTopoXSeg(
            w.view, self._cur(), vc.get_text_int(r["xSegId"]),
            corelib.cstr(vc.text_of(r["xSegName"])),
            corelib.cstr(vc.text_of(r["xSegDescr"])),
            r["xSegUsed"].isChecked(), r["xSegTargetCW"].isChecked())
        w.pump()
        if self._error(err):
            return
        _sensitive(r["xSegBtn"], False)
        self._msg("msgXSegChanged")

    def xseg_revert(self):
        """CbTopoXSegRevert."""
        w = self.w
        err = w.dll.PyTopoXSegRevert(w.view, self._cur())
        w.pump()
        if self._error(err):
            return
        self._msg("msgXSegReverted")

    def sz_set(self):
        """CbTopoSZSetBtn."""
        w = self.w
        r = self.r
        gps2 = -1 if vc.is_text_empty(r["szGps2"]) else \
            vc.get_text_int(r["szGps2"])
        err = w.dll.PyTopoSZSet(
            w.view, self._cur(), self.cur == SZ_NEWPTR,
            vc.get_text_int(r["szId"]), vc.get_text_int(r["szGps1"]), gps2,
            vc.get_option_menu_value(r["szOrient"]),
            r["szClosed"].isChecked(),
            corelib.cstr(vc.text_of(r["szName"])),
            corelib.cstr(vc.text_of(r["szDescr"])))
        w.pump()
        if self._error(err):
            return
        self._msg("msgSZChanged")

    def sz_delete(self):
        """CbTopoSZDeleteBtn."""
        w = self.w
        err = w.dll.PyTopoSZDelete(w.view, self._cur())
        w.pump()
        self._error(err)

    def name_btn(self):
        """CbTopoNameBtn."""
        w = self.w
        w.dll.SetActiveView(w.view)
        w.pump()
        name = _one_word(vc.text_of(self.r["tnName"]))
        if name is None:
            boxes.error_box(self.dlg, vc.resource_string(self.dlg,
                                                         "errBadTopoName"))
            return
        w.dll.SetTopologyName(w.app, corelib.cstr(name))
        w.dll.UndoMark(w.app)
        w.pump()
        self._msg("msgTopoNameChanged")

    # The list of zones

    def update_list(self):
        """TopoDlgUpdateList."""
        w = self.w
        items = ["(New)"]
        proc = api.ITEMPROC(lambda label, value: items.append(
            label.decode("latin-1")))
        w.dll.PyTopoZoneItems(w.view, proc)
        self.r["szList"].set_items_keep_selection(items)
        self.cur = None
        self.sz_list_select()

    def sz_list_select(self):
        """CbTopoSZListSelect."""
        w = self.w
        r = self.r
        pos = r["szList"].sel_pos()
        if pos < 0:
            self.cur = None
            self.init_sz(None)
        elif pos == 0:
            self.cur = SZ_NEWPTR
            self.init_sz(None)
        else:
            sz = w.dll.GroupAt(w.lib.get(w.app, "App.surfaceZones"),
                               pos - 1)
            self.cur = sz
            self.init_sz(sz)
        _sensitive(r["szSetBtn"], pos >= 0)
        _sensitive(r["szDeleteBtn"], pos > 0)

    def init_sz(self, sz):
        """InitSZFromZone (the toggle Has O point from bit 1 of the
        flags, as in Motif)."""
        w = self.w
        r = self.r
        if not sz:
            for name in ("szId", "szName", "szDescr", "szGps1", "szGps2"):
                vc.set_text(r[name], "")
            return
        zone, gps1, gps2, orient = (ctypes.c_int() for _ in range(4))
        short, long_ = ctypes.c_void_p(), ctypes.c_void_p()
        flags = ctypes.c_long()
        w.dll.PyTopoZoneInfo(sz, ctypes.byref(zone), ctypes.byref(short),
                             ctypes.byref(long_), ctypes.byref(gps1),
                             ctypes.byref(gps2), ctypes.byref(orient),
                             ctypes.byref(flags))
        vc.set_text(r["szId"], "%d" % zone.value)
        vc.set_text(r["szName"], _str(w, short.value) or "")
        vc.set_text(r["szDescr"], _str(w, long_.value) or "")
        vc.set_text(r["szGps1"], "%d" % gps1.value)
        vc.set_text(r["szGps2"], "" if gps2.value < 0 else
                    "%d" % gps2.value)
        vc.set_option_menu_value(r["szOrient"], orient.value)
        r["szClosed"].set_state(flags.value & 1, False)

    def dw_topo(self, widget=None, kind=api.N_NOW, obj=None, user=None):
        """DwTopoDlg."""
        from ..app.window import CHF_TOPOLOGY
        w = self.w
        if kind != api.N_NOW and not self.dlg.isVisible():
            return
        vc.set_text(self.r["tnName"], _str(w, w.dll.GetTopologyName(w.app))
                    or "")
        _sensitive(self.r["tnSetBtn"], False)
        if kind == api.N_ALT and not w.changes & CHF_TOPOLOGY:
            return
        self.update_list()


def open_topology_dlg(window):
    """CmEditTopology, OpenTopologyDlg."""
    w = window
    w.dll.SetActiveView(w.view)
    w.pump()
    dlg = find_dialog(w, "dlgTopology")
    if dlg is None:
        dlg = TopologyDlg(w).dlg
    else:
        dlg.data.dw_topo(None, api.N_NOW)
        dlg.popup()
    w.dll.SetViewEditTopology(w.view, 1)
    w.pump()
    notify_examine(w, None)
    return dlg


def notify_examine(window, obj):
    """TopoDlg_NotifyExamine: the examined object in the dialog, if
    any."""
    dlg = find_dialog(window, "dlgTopology")
    if dlg is not None:
        dlg.data.notify_examine(obj)
