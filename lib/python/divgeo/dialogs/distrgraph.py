"""The distribution graph of the dialogs that create several surfaces or
grid points (x_creobj.c): the law of the distribution drawn from the
count, alpha (delta) values and law of the dialog, updated after a delay,
and the alphas changed by dragging the curve. Drawn into an image, as on
an X window: erasing draws in the background colour."""

from PySide6 import QtCore, QtGui

from ..core import api, resources
from ..view import themes
from . import boxes, files
from . import vacreate as vc

DGD_GRAPH, DGD_FRAME, DGD_LINES, DGD_DISTR = 0x1, 0x2, 0x4, 0x8
DGI_PRESS, DGI_DRAG, DGI_RELEASE, DGI_CANCEL = 1, 2, 4, 8
NC_CURVE_FIT_ITERATIONS = 10
NC_RESET_DELTA = 1e-5
CC_LOWER, CC_UPPER, CC_UPPERDELTA = 1e-10, 1e10, 0.5
MAX_ITERATIONS = 1000


def gi2x(w, x):
    return x / w


def gi2y(h, y):
    return 1 - y / h


def gx2i(w, x):
    return int(w * x)


def gy2i(h, y):
    return int(h * (1 - y))


def _pixel(widget, name, cls, default):
    value = vc.resource(widget, name, cls)
    p = resources.to_pixel(value) if value is not None else None
    if p is None:
        p = resources.to_pixel(default)
    return p


def _color(p):
    return QtGui.QColor((p >> 16) & 255, (p >> 8) & 255, p & 255)


def _db_strex(widget, name, fmt, *args):
    names, classes = vc.path_of(widget)
    return files.resource_string_ex(vc._db(widget), names, classes, name,
                                    None, fmt, *args)


class DistrGraph:
    """DG_Init: the graph of a dialog, its fields and the callbacks."""

    def __init__(self, view_window, dlg, draw, count, alpha, alpha_label,
                 alpha2, alpha2_label, law, law_label):
        self.w = view_window
        self.dll = view_window.dll
        self.dlg = dlg
        self.draw = draw
        self.w_count = count
        self.w_alpha = [alpha, alpha2]
        self.w_alpha_label = [alpha_label, alpha2_label]
        self.w_law = law
        self.w_law_label = law_label
        self.timer = QtCore.QTimer(draw)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._update_graph)
        self.graph_drawn = True
        self.dragging = 0
        self.flags = DGD_GRAPH | DGD_FRAME | DGD_LINES | DGD_DISTR
        self.prev_flags = self.flags
        self.alpha = [-1.0, -1.0]
        self.count = -1
        self.law = -1
        self.gx = [-1.0, -1.0]
        self.gy = [-1.0, -1.0]
        self.mouse_inside = 0
        self.drag_alpha = 0
        self.old_drag_alpha = 0.0
        draw.xm_user = self
        if count is not None:
            count.textChanged.connect(lambda *a: self.numbers_changed(count))
        for a in self.w_alpha:
            if a is not None:
                a.textChanged.connect(
                    lambda *x, ww=a: self.numbers_changed(ww))
        if law is not None:
            vc.add_callback_to_tree(law.pulldown,
                                    lambda wg, d: self.numbers_changed(wg),
                                    None)
        draw.resize_callbacks.append(lambda *a: self.resize())
        draw.input_handler = self.action
        # the colours of the resources, shown in the theme of the windows
        self.pixels = (_pixel(draw, "background", "Background", "#c4c4c4"),
                       _pixel(draw, "foreground", "Foreground", "Black"),
                       _pixel(draw, "rectColor", "Foreground", "Black"),
                       _pixel(draw, "gridColor", "Foreground", "Black"))
        self._theme_colors(view_window.application.theme)
        themes.GRAPHS.add(self)
        self.margin = vc.resource_int(draw, "margin", "Margin", 5)
        self.extra_left = vc.resource_int(draw, "extraMargin", "Margin", 10)
        self.grid_len = vc.resource_int(draw, "gridLength", "GridLength", 5)
        self.image = None
        self.resize()
        self.numbers_changed(None)

    # Drawing (an X window: lines drawn at once, erased in the background)

    def _painter(self, color):
        p = QtGui.QPainter(self.image)
        p.setPen(QtGui.QPen(color, 0))
        return p

    def _line(self, color, x1, y1, x2, y2):
        if self.image is None:
            return
        p = self._painter(color)
        p.drawLine(x1, y1, x2, y2)
        p.end()
        self.draw.update()

    def _rect(self, color, x, y, w, h):
        if self.image is None:
            return
        p = self._painter(color)
        p.drawRect(x, y, w, h)
        p.end()
        self.draw.update()

    def draw_rect(self):
        """DG_DrawRect."""
        if ~self.flags & DGD_FRAME:
            return
        m = self.margin
        self._rect(self.px_rect, m, m, self.width - 2 * m,
                   self.height - 2 * m)
        self._line(self.px_rect, m + self.extra_left, m,
                   m + self.extra_left, self.height - m)

    def law_at(self, x):
        """DG_Law."""
        return self.dll.DistributeLaw(x, self.law, self.alpha[0],
                                      self.alpha[1], self.count)

    def draw_curve(self, draw_or_erase, k_alpha=None, new_alpha=0.0):
        """DG_DrawCurve: the curve, and the curve with alpha k changed."""
        step = vc.resource_int(self.draw, "graphStep", "graphStep", 1)
        m, el = self.margin, self.extra_left
        gw = self.width - 2 * m - el
        gh = self.height - 2 * m
        if self.flags & DGD_GRAPH and self.alpha[0] > 0:
            ox = -1
            oy = oy1 = 0
            i = 0
            while i < gw + step:
                i = min(i, gw)
                x = m + el + i
                y = m + gy2i(gh, self.law_at(gi2x(gw, i)))
                color = self.fg if draw_or_erase else self.bg
                if ox >= 0:
                    self._line(color, ox, oy, x, y)
                oy = y
                if k_alpha is not None:
                    old = self.alpha[k_alpha]
                    self.alpha[k_alpha] = new_alpha
                    y = m + gy2i(gh, self.law_at(gi2x(gw, i)))
                    self.alpha[k_alpha] = old
                    color = self.fg if not draw_or_erase else self.bg
                    if ox >= 0:
                        self._line(color, ox, oy1, x, y)
                    oy1 = y
                ox = x
                i += step

    def draw_graph(self, draw_or_erase):
        """DG_DrawGraph."""
        if not self.graph_drawn and not draw_or_erase and \
                self.prev_flags == self.flags:
            return
        self.graph_drawn = draw_or_erase
        self.prev_flags = self.flags
        if draw_or_erase:
            self.draw_rect()
        m, el = self.margin, self.extra_left
        gw = self.width - 2 * m - el
        gh = self.height - 2 * m
        color = self.px_grid if draw_or_erase else self.bg
        y = 0
        for i in range(self.count if self.count > 0 else 0):
            t = 1.0 / (self.count + 1) * (i + 1)
            x = m + el + gx2i(gw, t)
            if self.alpha[0] > 0:
                if self.flags & DGD_LINES:
                    y = m + gy2i(gh, self.law_at(t))
                    self._line(color, x, self.height - m - 1, x, y)
                    if self.law == api.DGLAW_FLIPPED:
                        self._line(color, self.width - m, y, x, y)
                    else:
                        self._line(color, m + el, y, x, y)
                if self.flags & DGD_DISTR:
                    self._line(color, m, y, el + m, y)
            elif self.flags & DGD_LINES:
                self._line(color, x, m + 1, x, self.height - m)
        self.draw_curve(draw_or_erase)
        if not draw_or_erase:
            self.draw_rect()

    # Data of the dialog

    def get_data(self, show_errors):
        """DG_GetData: 0, or -1 with an error box when asked."""
        self.count = -1
        self.alpha[0] = -1
        self.law = vc.get_option_menu_value(self.w_law)
        self.count = vc.get_text_int(self.w_count)
        if self.count == vc.MAXINT:
            self.count = -1
        self.alpha[0] = vc.get_text_double(self.w_alpha[0])
        if self.alpha[0] == vc.MAXDOUBLE:
            self.alpha[0] = -1
        self.alpha[1] = vc.get_text_double(self.w_alpha[1])
        if self.alpha[1] == vc.MAXDOUBLE:
            self.alpha[1] = -1
        i = vc.resource_int(self.w_count, "max", "max", 0)
        if self.count < 1 or self.count > i:
            self.count = -1
            if show_errors:
                boxes.error_box(self.dlg, _db_strex(
                    self.w_count, "errBadRange", "$(MIN)%d$(MAX)%d", 1, i))
            return -1
        self.count -= 1
        if self.alpha[0] <= 0:
            self.alpha[0] = -1
            if show_errors:
                boxes.error_box(self.dlg, vc.resource_string(
                    self.w_alpha[0], "errBadRange"))
            return -1
        if self.law in (api.DGLAW_2ALPHA, api.DGLAW_DELTA) and \
                self.alpha[0] <= 0:
            self.alpha[0] = -1
            if show_errors:
                boxes.error_box(self.dlg, vc.resource_string(
                    self.w_alpha[1], "errBadRange"))
            return -1
        if self.law_at(-1) < 0:
            if show_errors:
                boxes.error_box(self.dlg, vc.resource_string(
                    self.w_law, "errBadLaw"))
            return -1
        return 0

    def _update_graph(self):
        """ToDG_UpdateGraph."""
        self.draw_graph(True)

    def numbers_changed(self, wg):
        """CbDG_NumbersChanged."""
        if self.dragging:
            return
        old_law = self.law
        old_count = self.count
        self.draw_graph(False)
        self.get_data(False)
        self.timer.stop()
        self.timer.start(vc.resource_int(self.draw, "updateDelay",
                                         "updateDelay", 1000))
        b = self.law in (api.DGLAW_2ALPHA, api.DGLAW_DELTA)
        for w in (self.w_alpha[1], self.w_alpha_label[1]):
            if w.isEnabled() != b:
                w.setEnabled(b)
        if old_law != self.law:
            res = "labelDelta" if self.law == api.DGLAW_DELTA \
                else "labelAlpha"
            for w in self.w_alpha_label:
                w.set_label(vc.resource_string(w, res))
        if self.law == api.DGLAW_DELTA and old_count != self.count and \
                wg is self.w_count:
            if self.gx[0] < 0:
                new_count = self.count
                self.count = old_count
                self.gx[0] = 1.0 / 3
                self.gy[0] = self.law_at(self.gx[0])
                self.gx[1] = 2.0 / 3
                self.gy[1] = self.law_at(self.gx[1])
                self.count = new_count
            self.alpha[0] = self.alpha[1] = NC_RESET_DELTA
            b = 3
            for _ in range(NC_CURVE_FIT_ITERATIONS):
                t = self.calc_coeff(self.gx[0], self.gy[0], 0)
                if t != vc.MAXDOUBLE:
                    self.alpha[0] = t
                    b &= ~1
                else:
                    b |= 1
                t = self.calc_coeff(self.gx[1], self.gy[1], 1)
                if t != vc.MAXDOUBLE:
                    self.alpha[1] = t
                    b &= ~2
                else:
                    b |= 2
            if not b and self.count > 1:
                self.gx[0] = self.gx[1] = -1
            self.dragging += 1
            vc.set_text(self.w_alpha[0], "%g" % self.alpha[0])
            vc.set_text(self.w_alpha[1], "%g" % self.alpha[1])
            self.dragging -= 1
        else:
            self.gx[0] = self.gx[1] = -1

    def expose(self):
        """CbDG_Expose."""
        self.draw_graph(True)

    def _theme_colors(self, name):
        bg, fg, rect, grid = self.pixels
        self.bg = _color(themes.background(name, bg))
        self.fg = _color(themes.colour(fg, name, False))
        self.px_rect = _color(themes.colour(rect, name, False))
        self.px_grid = _color(themes.colour(grid, name, False))

    def apply_theme(self, name):
        """Window > Theme: the colours of the theme, the graph drawn
        again."""
        self._theme_colors(name)
        self.resize()

    def resize(self):
        """CbDG_Resize: the window cleared, then exposed."""
        self.width = self.draw.width()
        self.height = self.draw.height()
        self.image = QtGui.QImage(max(1, self.width), max(1, self.height),
                                  QtGui.QImage.Format_RGB32)
        self.image.fill(self.bg)
        self.draw.image = self.image
        QtCore.QTimer.singleShot(0, self.expose)

    def reset(self, wg=None, data=None):
        """CbDG_Reset."""
        if self.law in (api.DGLAW_NORMAL, api.DGLAW_FLIPPED,
                        api.DGLAW_2ALPHA, api.DGLAW_SYMMETRIC):
            vc.set_text(self.w_alpha[0], "1")
            vc.set_text(self.w_alpha[1], "1")
        elif self.law == api.DGLAW_DELTA:
            s = "%g" % (1.0 / max(1, self.count + 1))
            vc.set_text(self.w_alpha[0], s)
            vc.set_text(self.w_alpha[1], s)

    def calc_coeff(self, x, y, k):
        """DG_CalcCoeff: the alpha k giving the law the value y at x;
        MAXDOUBLE if impossible."""
        old = self.alpha[k]
        lower = CC_LOWER
        upper = CC_UPPERDELTA if self.law == api.DGLAW_DELTA else CC_UPPER
        self.alpha[k] = lower
        v1 = self.law_at(x)
        self.alpha[k] = upper
        v2 = self.law_at(x)
        self.alpha[k] = old
        if (v1 - y) * (v2 - y) >= 0:
            return vc.MAXDOUBLE
        for _ in range(MAX_ITERATIONS):
            self.alpha[k] = (upper + lower) / 2
            if self.alpha[k] == upper or self.alpha[k] == lower:
                break
            v3 = self.law_at(x)
            if (v3 - y) * (v1 - y) == 0:
                break
            if (v3 - y) * (v2 - y) == 0:
                break
            elif (v3 - y) * (v2 - y) < 0:
                lower = self.alpha[k]
                v1 = v3
            else:
                upper = self.alpha[k]
                v2 = v3
        lower = self.alpha[k]
        self.alpha[k] = old
        return lower

    # Mouse (the translations of the graph, XtActDistrGraph)

    def visual_input(self, evt, ix, iy):
        """DG_VisualInput."""
        if evt == DGI_PRESS:
            if self.dragging:
                return
        elif not self.dragging:
            return
        m, el = self.margin, self.extra_left
        gw = self.width - 2 * m - el
        gh = self.height - 2 * m
        x = gi2x(gw, ix - m - el)
        y = gi2y(gh, iy - m)
        if evt == DGI_PRESS:
            self.dragging = 1
            self.drag_alpha = 1 if (self.law in (api.DGLAW_2ALPHA,
                                                 api.DGLAW_DELTA)
                                    and x >= 0.5) else 0
            self.old_drag_alpha = self.alpha[self.drag_alpha]
            self.draw_graph(False)
            self.flags &= ~(DGD_LINES | DGD_DISTR)
            self.draw_graph(True)
        k = self.drag_alpha
        if evt in (DGI_PRESS, DGI_DRAG, DGI_RELEASE):
            nv = vc.MAXDOUBLE
            if 0 <= x <= 1 and 0 <= y <= 1:
                nv = self.calc_coeff(x, y, k)
            if nv == vc.MAXDOUBLE:
                nv = self.alpha[k]
        else:
            nv = self.old_drag_alpha
        if nv != self.alpha[k]:
            self.draw_curve(False, k, nv)
            self.alpha[k] = nv
            vc.set_text(self.w_alpha[k], "%g" % nv)
        if evt in (DGI_RELEASE, DGI_CANCEL):
            self.dragging = 0
            self.flags |= DGD_LINES | DGD_DISTR
            self.numbers_changed(None)
            self.draw_graph(True)

    def action(self, kind, event):
        """The translations: Btn1Down Press, BtnMotion Drag, BtnUp
        RelCancel, Enter and Leave."""
        if kind == "press":
            if event.button() != QtCore.Qt.LeftButton:
                return
            self.mouse_inside = 1
            p = event.position()
            self.visual_input(DGI_PRESS, int(p.x()), int(p.y()))
        elif kind == "motion":
            if not event.buttons() or not self.mouse_inside:
                return
            p = event.position()
            self.visual_input(DGI_DRAG, int(p.x()), int(p.y()))
        elif kind == "release":
            p = event.position()
            self.visual_input(DGI_RELEASE if self.mouse_inside
                              else DGI_CANCEL, int(p.x()), int(p.y()))
        elif kind == "enter":
            self.mouse_inside = 1
        elif kind == "leave":
            self.mouse_inside = 0
