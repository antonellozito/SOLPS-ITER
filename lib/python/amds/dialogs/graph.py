"""The graph dialog of a view (amgraph.c): rate coefficients of the
selected reactions against the temperature for up to ten densities,
computed by an external program (AMDSGRAPHCMD, in AMDSGRAPHDIR) and drawn
in log-log scale; Y-Fit, Print.

The graph view and the PostScript are the C code of the library
(src/py/py_graph.c); here the fields, the calculation process, the timers
and the drawing of the calls of the view."""

import itertools
import os
import subprocess
import tempfile

import ctypes
from PySide6 import QtCore, QtGui, QtWidgets

from ...divgeo.core import resources
from ...divgeo.dialogs import vacreate as vc
from ...divgeo.dialogs.base import FormDialog, MessageDialog
from ...divgeo.dialogs.files import resource_string_ex
from ...divgeo.view import themes
from ..app.application import out
from ..core import api, lib as corelib
from . import boxes
from .boxes import find_dialog

DLG_GRAPH = "dlgGraph"
DLG_PRINT = "dlgGraphPrint"
GD_DENSITIES = 10
ENV_DIR = "AMDSGRAPHDIR"
ENV_CMD = "AMDSGRAPHCMD"
V_NONE = vc.MAXDOUBLE
CMT_CMD, CMT_FILE = 1, 2
# text extents of the label font of the Motif dialog (the X font fixed)
FONT_W, FONT_H = 6, 13
DT_ABOVE, DT_CENTERX, DT_CENTERY, DT_LEFT = 0x0001, 0x0004, 0x0008, 0x0010

# The modes of the view: resource, class, default (graphDlgRes)
_BG = ("background", "Background", "RGBi: 1/1/1")
MODES = {0: _BG, 104: _BG, 106: _BG,
         1: ("graphColor1", "GraphColor", "RGBi: 0/0/0"),
         2: ("graphColor2", "GraphColor", "RGBi: 0/0/0"),
         3: ("graphColor3", "GraphColor", "RGBi: 0/0/0"),
         4: ("graphColor4", "GraphColor", "RGBi: 0/0/0"),
         100: ("gridColor", "GridColor", "RGBi: 0/0/0"),
         101: ("gridTextColor", "GridColor", "RGBi: 0/0/0"),
         102: ("legendTextColor", "LegendTextColor", "RGBi: 0/0/0"),
         103: ("symbolColor", "SymbolColor", "RGBi: 0/0/0"),
         105: ("gridBorderColor", "GridBorderColor", "RGBi: 0/0/0")}

GRAPHS = {}         # dialogs by number (the calls of the library)
_NUMBERS = itertools.count(1)


def _graph_proc(gid, op, i, a, b, c, d, text):
    g = GRAPHS.get(gid)
    if g is not None:
        g.view_call(chr(op), i, a, b, c, d, corelib.text(text))


def _text_proc(gid, text, px, py):
    s = corelib.text(text)
    px[0] = float(FONT_W * len(s))
    py[0] = float(FONT_H)


_PROCS = (api.GRAPHPROC(_graph_proc), api.GRAPHTEXTPROC(_text_proc))
_DECLARED = []


def set_value(field, text):
    """XmTextSetString: the text, then the valueChanged callbacks (also
    when the text does not change)."""
    field.blockSignals(True)
    field.setText(text)
    field.blockSignals(False)
    for cb in list(getattr(field, "value_callbacks", [])):
        cb()


def _text(parent, name, user, callback=None):
    t = vc.Text(parent, name)
    t.xm_user = user
    t.value_callbacks = []
    if callback is not None:
        t.value_callbacks.append(callback)
        t.textEdited.connect(lambda s, f=t: [cb() for cb in
                                             list(f.value_callbacks)])
    parent.xm_place(t)
    return t


def _label(parent, name, user):
    w = vc.Label(parent, name)
    w.xm_user = user
    parent.xm_place(w)
    return w


def _button(parent, name, callback, user=None):
    b = vc.PushButton(parent, name)
    b.xm_user = user
    b.clicked.connect(callback)
    parent.xm_place(b)
    return b


class GraphCanvas(vc.DrawingArea):
    """The drawing area: an image the calls of the view are drawn into."""

    def resizeEvent(self, event):
        self.dialog.resized()


class GraphDialog(FormDialog):
    """CreateGraphDlg."""

    def __init__(self, w):
        super().__init__(w, DLG_GRAPH)
        if not _DECLARED:
            w.dll.SetPyGraphProcs(*_PROCS)
            _DECLARED.append(True)
        self.w = w
        self.dll = w.dll
        self.lib = w.lib
        self.gid = next(_NUMBERS)
        GRAPHS[self.gid] = self
        self.mode = 0
        self.realized = False
        self.exposes = 0
        self.calc_proc = None
        self.calc_file = None
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.to_repaint)
        self.calc_timer = QtCore.QTimer(self)
        self.calc_timer.setSingleShot(True)
        self.calc_timer.timeout.connect(self.to_calc)
        self.g = self.dll.PyCreateGraph(w.view, self.gid)
        self.wm_close = self.popdown
        self._build()
        self.adjustSize()
        self.manage()
        self.realize_view()
        self.opened()
        w.add_dependent(self, api.N_NOW | api.N_SEL | api.N_ALT,
                        lambda *a: self.input())

    def _build(self):
        rc = vc.RowColumn(self, "rowcol0")
        sep0 = vc.Separator(self, "sep")
        _button(rc, "print", lambda: open_print_dlg(self))
        _button(rc, "fit", self.cb_fit)
        _button(rc, "close", self.popdown)
        f1 = vc.Form(self, "form1")
        self.density = []
        names, classes = self.path()
        for i in range(1, GD_DENSITIES + 1):
            lab = _label(f1, "densityLabel", 0x100 + i)
            lab.set_label(resource_string_ex(
                self.window_.application.db, names, classes, "densityLabel",
                "DensityLabel", "$(NUMBER)%d", i))
            t = _text(f1, "density", 0x200 + i, self.input)
            self.density.append(t)
            _button(f1, "densityClear", lambda c=False, f=t: set_value(f, ""),
                    0x300 + i)
        vc.form2table(f1)
        sep1 = vc.Separator(self, "sep", vertical=True)
        f2 = vc.Form(self, "form2")
        _label(f2, "t1Label", 0x0101)
        self.t1 = _text(f2, "t1", 0x0201, self.input)
        _label(f2, "t2Label", 0x0301)
        self.t2 = _text(f2, "t2", 0x0401, self.input)
        _label(f2, "y1Label", 0x0102)
        self.y1 = _text(f2, "y1", 0x0202, self.input)
        _label(f2, "y2Label", 0x0302)
        self.y2 = _text(f2, "y2", 0x0402, self.input)
        vc.form2table(f2)
        sep2 = vc.Separator(self, "rowcol")
        frame = vc.Frame(self, "drawFrame")
        self.canvas = GraphCanvas(frame, "draw")
        self.canvas.dialog = self
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Expanding)
        frame.xm_place(self.canvas)
        self._resources()
        # the Motif form: the buttons on top, the densities at the right,
        # the drawing area above the T and Y fields
        left = QtWidgets.QVBoxLayout()
        left.addWidget(frame, 1)
        left.addWidget(sep2)
        left.addWidget(f2)
        row = QtWidgets.QHBoxLayout()
        row.addLayout(left, 1)
        row.addWidget(sep1)
        row.addWidget(f1, 0, QtCore.Qt.AlignTop)
        self.lay.addWidget(rc)
        self.lay.addWidget(sep0)
        self.lay.addLayout(row, 1)

    def _resources(self):
        """graphDlgRes of the drawing area."""
        db = self.window_.application.db
        names, classes = self.canvas.xm_names, self.canvas.xm_classes

        def res(name, cls, default):
            v = db.get(names + [name], classes + [cls])
            return default if v is None else v
        self.pixels = {}
        for mode, (name, cls, default) in MODES.items():
            pixel = resources.to_pixel(res(name, cls, default))
            self.pixels[mode] = 0 if pixel is None else pixel
        self.tm_kill = resources.to_int(res("killInterval", "KillInterval",
                                            "100"))
        self.tm_repaint = resources.to_int(res("repaintInterval",
                                               "RepaintInterval", "500"))

    def opened(self):
        """The dialog is made and shown (a hook of the identity tests)."""

    # The view (the calls of py_graph.c)

    def realize_view(self):
        """The drawing area gets its window: the map callback."""
        self.dll.PyGraphRealize(self.g)
        self.realized = True
        self.resized()

    def resized(self):
        """CbGraphDlgResize: resize of the drawing area and map of the dialog
        (when it is managed, at its creation; not when a popup shows it
        again)."""
        if not getattr(self, "realized", False):
            return
        size = self.canvas.size()
        self._new_image(size.width(), size.height())
        self.dll.PyGraphResize(self.g, size.width(), size.height())

    def _new_image(self, width, height):
        dpr = self.canvas.devicePixelRatioF()
        img = QtGui.QImage(max(1, int(width * dpr)), max(1, int(height * dpr)),
                           QtGui.QImage.Format_RGB32)
        img.setDevicePixelRatio(dpr)
        img.fill(self._colour(0))
        self.canvas.image = img

    def _colour(self, mode):
        """The colour of a mode in the theme in use: the resource colours
        (classic and light), the plotting colours of the dark theme."""
        pixel = self.pixels.get(mode, 0)
        if themes.current == "dark":
            if MODES[mode] is _BG:
                pixel = themes.BACKGROUND["dark"]
            else:
                pixel = themes.colour(pixel, "dark")
        return QtGui.QColor((pixel >> 16) & 255, (pixel >> 8) & 255,
                            pixel & 255)

    def view_call(self, op, i, a, b, c, d, text):
        if op == "U":
            if i:
                self.update_timer.start(self.tm_repaint)
            else:
                self.update_timer.stop()
            return
        if op == "M":
            self.mode = i
            return
        if not self.realized or self.canvas.image is None or op == "E":
            return
        if op == "C":
            self.canvas.image.fill(self._colour(0))
            self.canvas.update()
            if i:
                # each clear with exposure, one Expose and one repaint
                self._queue_expose()
            return
        p = QtGui.QPainter(self.canvas.image)
        p.setPen(QtGui.QPen(self._colour(self.mode), 0))
        if op == "L":
            p.drawLine(int(a), int(b), int(c), int(d))
        elif op == "T":
            dx, dy = FONT_W * len(text), FONT_H
            if i & DT_CENTERX:
                dx //= 2
            elif not i & DT_LEFT:
                dx = 0
            if i & DT_CENTERY:
                dy //= 2
            elif not i & DT_ABOVE:
                dy = 0
            font = QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.FixedFont)
            font.setPixelSize(FONT_H - 2)
            p.setFont(font)
            p.drawText(QtCore.QRectF(int(a) - dx, int(b) - dy, 1000, FONT_H),
                       QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, text)
        p.end()
        self.canvas.update()

    def popup(self):
        """XtPopup: the drawing area of a dialog shown again gets an
        Expose when its window is mapped."""
        shown = self.isVisible()
        super().popup()
        if not shown and self.realized:
            self._queue_expose()

    def _queue_expose(self):
        self.exposes += 1
        QtCore.QTimer.singleShot(0, self.expose)

    def expose(self):
        """CbGraphDlgExpose."""
        self.exposes -= 1
        if not self.destroyed_ and self.g is not None:
            self.dll.PyGraphExpose(self.g)

    def to_repaint(self):
        """ToRepaintGraphDlg."""
        if self.calc_proc is None:
            self.dll.PyGraphRepaint(self.g)
        else:
            self.update_timer.start(self.tm_repaint)

    # Updates (UpdateGraphDlg)

    def is_mapped(self):
        return self.isVisible() and not self.destroyed_

    def input(self):
        """CbGraphDlgInput, DwGraphDlg."""
        if self.is_mapped():
            self.update()

    def update(self):
        dll = self.dll
        if self.calc_proc is not None:
            return
        if self.calc_file is not None:
            dll.PyGraphCalcDone(self.g, corelib.cstr(self.calc_file))
            try:
                os.unlink(self.calc_file)
            except OSError:
                pass
            self.calc_file = None
        t1, t2, y1, y2 = (vc.get_text_double(f)
                          for f in (self.t1, self.t2, self.y1, self.y2))
        dens = (ctypes.c_double * GD_DENSITIES)(
            *[vc.get_text_double(f) for f in self.density])
        g = self.w.selected_reactions()
        r = dll.PyGraphUpdate(self.g, t1, t2, y1, y2, dens, g)
        dll.PyFreeGroup(g)
        if r:
            self.calculate(r, t1, t2, [d for d in dens if d != V_NONE])

    def calculate(self, r, t1, t2, dens):
        """The calculation of reaction r as the child process of the Motif
        program: the reaction variables as standard input, the output in a
        temporary file read when it ends."""
        dll = self.dll
        lib = self.lib
        app = self.w.application
        fd, self.calc_file = tempfile.mkstemp(prefix="amds_")
        os.close(fd)
        dir_str = os.environ.get(ENV_DIR)
        if dir_str is None:
            dir_str = app.app_string("graphDir", "GraphDir", ".")
        cmd_str = os.environ.get(ENV_CMD)
        if cmd_str is None:
            cmd_str = app.app_string("graphCmd", "GraphCmd",
                                     "./calc_atomic_data")
        ss = self.w.subset
        names = []
        lines = []
        for vd in lib.group(lib.get(ss, "Doc.varDefs")):
            name = corelib.text(dll.PyVarDefName(vd))
            names.append(name + "\n")
            if lib.get(vd, "VarDef.flags") & api.VDF_REACTIONS:
                lines.append("%s\n%s\n" % (name, corelib.text(
                    dll.GetParticleVar(ss, r, None, vd))))
        out(1, "".join(names))
        try:
            inp = tempfile.TemporaryFile(prefix="amds_", dir="/tmp")
        except OSError:
            out(2, "amds: Error writing /tmp/amds_graph_input.dat. Cannot "
                   "calculate reaction data\n")
            self.calc_proc = None
            return
        inp.write("".join(lines).encode("latin-1"))
        inp.seek(0)
        types = lib.group(lib.get(r, "Reaction.types"))
        args = ["./calc_atomic_data",
                corelib.text(dll.GetReactionDatabase(r)),
                corelib.text(dll.GetReactionSection(r)),
                corelib.text(dll.GetReactionNumber(r)),
                lib.string(types[0], "ReactionType.name") if types else "??",
                "%e" % t1, "%e" % t2] + ["%e" % d for d in dens]
        with open(self.calc_file, "wb") as output:
            if not os.path.isdir(dir_str) or not os.access(dir_str, os.X_OK):
                out(2, "amds: Cannot chdir to %s\n" % dir_str)
                self.calc_proc = _Ended()
            else:
                try:
                    self.calc_proc = subprocess.Popen(
                        args, executable=cmd_str, stdin=inp, stdout=output,
                        cwd=dir_str)
                except OSError:
                    out(2, "amds: Cannot execute %s\n" % cmd_str)
                    self.calc_proc = _Ended()
        inp.close()
        self.to_calc()

    def to_calc(self):
        """ToGraphDlgCalc: the program ended, or a look again later."""
        if self.calc_proc is None:
            return
        if self.calc_proc.poll() is not None:
            self.calc_proc = None
            self.update()
            return
        self.calc_timer.start(self.tm_kill)

    def busy(self):
        """A calculation, a repaint or an exposure to come (the tests)."""
        return (self.calc_proc is not None or self.update_timer.isActive()
                or self.exposes > 0)

    # Buttons

    def cb_fit(self):
        """CbFit."""
        s1 = ctypes.create_string_buffer(64)
        s2 = ctypes.create_string_buffer(64)
        self.dll.PyGraphFit(self.g, s1, s2)
        set_value(self.y1, corelib.text(s1.value))
        set_value(self.y2, corelib.text(s2.value))

    def free(self):
        """CbGraphDlgDestroy: the view freed with its window."""
        if self.g is None:
            return
        self.update_timer.stop()
        self.calc_timer.stop()
        self.dll.PyGraphFree(self.g)
        self.g = None
        GRAPHS.pop(self.gid, None)
        if self.calc_file is not None:
            try:
                os.unlink(self.calc_file)
            except OSError:
                pass


class _Ended:
    """A child that ended at once (chdir or exec failed: exit 1)."""

    @staticmethod
    def poll():
        return 1


def open_graph_dlg(w):
    """OpenGraphDlg."""
    dlg = find_dialog(w, DLG_GRAPH)
    if dlg is None:
        dlg = GraphDialog(w)
    else:
        dlg.popup()
    dlg.update()
    return dlg


# Print (OpenPrintDlg, CbPrintOk) ########################################

class PrintDialog(MessageDialog):
    def __init__(self, gdlg):
        super().__init__(gdlg.window_, DLG_PRINT, auto_unmanage=False,
                         parent=gdlg)
        self.gdlg = gdlg
        self.help.hide()
        self.callbacks["ok"].append(self.cb_print_ok)
        self.callbacks["cancel"].append(self.popdown)
        self.wm_close = self.popdown
        form = vc.Form(self, "form")
        self.xm_place(form)
        pd = vc.Pulldown(form, "cmdTypeMenu")
        out(2, "Warning - CreateWidgetSystem() - 'O:' is obsolete\n")
        self.cmd_type = vc.OptionMenu(form, "cmdType", pd)
        self.cmd_type.xm_user = 0x0101
        form.xm_place(self.cmd_type)
        for name, value in (("file", CMT_FILE), ("cmd", CMT_CMD)):
            act = pd.add_item(name)
            act.xm_user = value
            self.cmd_type._watch(act)
        self.cmd_type.set_history(pd.items[0])
        self.command = _text(form, "command", 0x0201)
        sep = vc.Separator(form, "separator")
        sep.xm_user = 0x0002
        form.xm_place(sep)
        _label(form, "widthLabel", 0x0103)
        self.width_ = _text(form, "width", 0x0203)
        _label(form, "heightLabel", 0x0104)
        self.height_ = _text(form, "height", 0x0204)
        _label(form, "marginLabel", 0x0105)
        self.margin = _text(form, "margin", 0x0205)
        self.color = vc.ToggleButton(form, "color")
        self.color.xm_user = 0x0006
        form.xm_place(self.color)
        self.manage()
        vc.form2table(form)

    def cb_print_ok(self):
        """CbPrintOk."""
        dll = self.gdlg.dll
        values = []
        for field, error in ((self.width_, "Bad width"),
                             (self.height_, "Bad height"),
                             (self.margin, "Bad margin")):
            v = vc.get_text_double(field)
            if v == V_NONE:
                boxes.error_box(self, error)
                return
            values.append(v)
        bw = int(not self.color.isChecked())
        ps = dll.PyGraphPsCreate(self.gdlg.g, values[0], values[1],
                                 values[2], bw)
        if not ps:
            boxes.error_box(self, "Invalid size")
            return
        s = self.command.text()
        kind = vc.get_option_menu_value(self.cmd_type)
        r = 0
        if kind == CMT_FILE:
            r = dll.PyGraphPsOutput(ps, corelib.cstr(s), -1)
        elif kind == CMT_CMD:
            # the command reads the PostScript, then the rest of its input
            # (system() in a child that empties the pipe); not waited for
            try:
                proc = subprocess.Popen(
                    ["/bin/sh", "-c", '/bin/sh -c "$0"; cat > /dev/null', s],
                    stdin=subprocess.PIPE)
                fd = os.dup(proc.stdin.fileno())
                proc.stdin.close()
                r = dll.PyGraphPsOutput(ps, None, fd)
                if r:
                    os.close(fd)
            except OSError:
                r = -1
        if r:
            boxes.error_box(self, "Output error")
        else:
            self.popdown()
        dll.PyGraphPsFree(ps)


def open_print_dlg(gdlg):
    """OpenPrintDlg."""
    dlg = find_dialog(gdlg, DLG_PRINT)
    if dlg is None:
        dlg = PrintDialog(gdlg)
    else:
        dlg.popup()
    return dlg
