"""Raster drawing of the view records with the semantics of the X server
that the Motif view draws on:
- integer screen coordinates, 16-bit in the protocol;
- zero-width lines as Bresenham lines with the end point drawn;
- wide lines and rectangles as the pixels whose centres lie inside the
  shape (a centre on the border counts when the inside is to its right, or
  below it for a horizontal border);
- texts in the default font of the X servers (fixedfont);
- XOR on pixel values (0xRRGGBB), erasing by drawing in the background
  colour;
- full ellipses (circles when the resource useSquares is off) sampled
  along the curve, not with the arc algorithm of the X server.

The picture is a numpy array of uint32 (0xFFRRGGBB), shown as a QImage."""

import ctypes

import numpy as np
from PySide6 import QtCore, QtGui

from . import fixedfont, modes, themes

# Octants with an error bias for zero-width lines (none: the X server of the
# references draws plain Bresenham lines; flags: 4 x decreasing, 2 y
# decreasing, 1 y major)
_BIAS_OCTANTS = ()

# Perturbation of a pixel centre for the border rule: right, then down
_EPS_X = 1e-6
_EPS_Y = 1e-9

OPAQUE = np.uint32(0xFF000000)

# the rasterizer of the library (src/py/py_raster.c), when it has one
CLIB = None


def use_library(dll):
    """The rasterizer of the library for every picture, if it has one (a
    library built before it: the rasterizer of this module)."""
    global CLIB
    try:
        dll.PyRasterDraw
        CLIB = dll
    except AttributeError:
        CLIB = None


def _i16(v):
    """Coordinate as the X protocol carries it (INT16)."""
    return ((int(v) + 32768) & 0xFFFF) - 32768


def _c16(v):
    """Size as the X protocol carries it (CARD16)."""
    return int(v) & 0xFFFF


def zero_lines(x1, y1, x2, y2):
    """Pixels of zero-width lines (arrays of int), in drawing order: per
    line from its first point, end point included."""
    x1 = np.asarray(x1, np.int64)
    y1 = np.asarray(y1, np.int64)
    x2 = np.asarray(x2, np.int64)
    y2 = np.asarray(y2, np.int64)
    dx = x2 - x1
    dy = y2 - y1
    adx = np.abs(dx)
    ady = np.abs(dy)
    sx = np.where(dx < 0, -1, 1)
    sy = np.where(dy < 0, -1, 1)
    ymajor = ady >= adx
    octant = (np.where(dx < 0, 4, 0) + np.where(dy < 0, 2, 0)
              + np.where(ymajor, 1, 0))
    bias = np.isin(octant, _BIAS_OCTANTS).astype(np.int64)
    amaj = np.where(ymajor, ady, adx)
    amin = np.where(ymajor, adx, ady)
    e1 = 2 * amin
    dd = 2 * amaj
    e0 = e1 - amaj - bias
    n = amaj + 1
    total = int(n.sum())
    if total == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    idx = np.repeat(np.arange(len(n)), n)
    start = np.cumsum(n) - n
    k = np.arange(total) - start[idx]
    ddi = dd[idx]
    safe = np.where(ddi == 0, 1, ddi)
    m = np.where(k == 0, 0, (e0[idx] + (k - 1) * e1[idx]) // safe + 1)
    ym = ymajor[idx]
    px = x1[idx] + np.where(ym, m * sx[idx], k * sx[idx])
    py = y1[idx] + np.where(ym, k * sy[idx], m * sy[idx])
    return px, py


def wide_lines(x1, y1, x2, y2, width):
    """Pixels of wide lines with butt caps (arrays), line after line, and
    the count per line: the centres inside the rectangle of the given width
    around the segment, solved per pixel column (rows for steep lines)."""
    x1 = np.asarray(x1, np.float64)
    y1 = np.asarray(y1, np.float64)
    x2 = np.asarray(x2, np.float64)
    y2 = np.asarray(y2, np.float64)
    hw = np.asarray(width, np.float64) / 2.0
    lx = x2 - x1
    ly = y2 - y1
    length = np.hypot(lx, ly)
    keep = length > 0
    order = np.nonzero(keep)[0]
    steep = np.abs(ly[order]) > np.abs(lx[order])
    # in the frame of the major axis: a along it, b across (swapped for
    # steep lines, with the perturbation of each axis)
    a1 = np.where(steep, y1[order], x1[order])
    b1 = np.where(steep, x1[order], y1[order])
    la = np.where(steep, ly[order], lx[order])
    lb = np.where(steep, lx[order], ly[order])
    ea = np.where(steep, _EPS_Y, _EPS_X)
    eb = np.where(steep, _EPS_X, _EPS_Y)
    L = length[order]
    h = hw[order]
    ua = la / L
    ub = lb / L
    # rectangle extent along the major axis
    a2 = a1 + la
    ext = h * np.abs(ub)
    amin = np.floor(np.minimum(a1, a2) - ext) - 1
    amax = np.ceil(np.maximum(a1, a2) + ext) + 1
    n = (amax - amin + 1).astype(np.int64)
    idx = np.repeat(np.arange(len(order)), n)
    start = np.cumsum(n) - n
    i = amin[idx] + (np.arange(int(n.sum())) - start[idx])
    A = i + ea[idx] - a1[idx]
    uai, ubi, hi, Li = ua[idx], ub[idx], h[idx], L[idx]
    # across: -A*ub + t*ua in (-h, h), ua != 0 for the major axis
    t1 = (A * ubi - hi) / uai
    t2 = (A * ubi + hi) / uai
    lo = np.minimum(t1, t2)
    hi_ = np.maximum(t1, t2)
    # along: A*ua + t*ub in (0, L)
    flat = ubi == 0
    safe = np.where(flat, 1.0, ubi)
    s1 = -A * uai / safe
    s2 = (Li - A * uai) / safe
    lo = np.where(flat, lo, np.maximum(lo, np.minimum(s1, s2)))
    hi_ = np.where(flat, hi_, np.minimum(hi_, np.maximum(s1, s2)))
    inside = ~flat | ((A * uai > 0) & (A * uai < Li))
    base = b1[idx] - eb[idx]
    jmin = np.floor(lo + base) + 1
    jmax = np.ceil(hi_ + base) - 1
    cnt = np.where(inside, np.maximum(jmax - jmin + 1, 0), 0).astype(np.int64)
    idx2 = np.repeat(np.arange(len(i)), cnt)
    start2 = np.cumsum(cnt) - cnt
    j = jmin[idx2] + (np.arange(int(cnt.sum())) - start2[idx2])
    a = i[idx2]
    st = steep[idx[idx2]]
    px = np.where(st, j, a).astype(np.int64)
    py = np.where(st, a, j).astype(np.int64)
    counts = np.zeros(len(x1), np.int64)
    np.add.at(counts, order[idx[idx2]], 1)
    return px, py, counts


def rectangle(x, y, w, h, width):
    """Pixels of the outline of a rectangle (XDrawRectangle), each once."""
    if width == 0:
        xs = np.arange(x, x + w + 1)
        ys = np.arange(y + 1, y + h)
        px = np.concatenate([xs, np.full(len(ys), x + w), xs[::-1] if h else
                             xs[:0], np.full(len(ys) if w else 0, x)])
        py = np.concatenate([np.full(len(xs), y), ys,
                             np.full(len(xs) if h else 0, y + h),
                             ys[::-1] if w else ys[:0]])
        return px.astype(np.int64), py.astype(np.int64)
    hw = width / 2.0
    pad = int(np.ceil(hw)) + 1
    jj, ii = np.mgrid[y - pad:y + h + pad + 1, x - pad:x + w + pad + 1]
    cx = ii + _EPS_X
    cy = jj + _EPS_Y
    outer = (cx > x - hw) & (cx < x + w + hw) & (cy > y - hw) & (cy < y + h
                                                                 + hw)
    inner = (cx > x + hw) & (cx < x + w - hw) & (cy > y + hw) & (cy < y + h
                                                                 - hw)
    keep = outer & ~inner
    return ii[keep].astype(np.int64), jj[keep].astype(np.int64)


def text_pixels(x, y, s):
    """Pixels of a text drawn with its base line at y (XDrawString)."""
    pxs, pys = [], []
    for ch in s.encode("latin-1", "replace"):
        g = fixedfont.GLYPHS.get(ch, fixedfont.GLYPHS.get(
            fixedfont.DEFAULT_CHAR))
        if g is None:
            continue
        lsb, ascent, advance, wbits, rows = g
        for r, bits in enumerate(rows):
            for c in range(wbits):
                if bits >> (wbits - 1 - c) & 1:
                    pxs.append(x + lsb + c)
                    pys.append(y - ascent + r)
        x += advance
    return np.array(pxs, np.int64), np.array(pys, np.int64)


def ellipse_pixels(x, y, w, h):
    """Pixels of the full ellipse in the box (x, y, w, h), each once."""
    if w == 0 and h == 0:
        return np.array([x], np.int64), np.array([y], np.int64)
    n = int(4 * (w + h)) + 8
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    px = np.rint(x + w / 2.0 + w / 2.0 * np.cos(t)).astype(np.int64)
    py = np.rint(y + h / 2.0 + h / 2.0 * np.sin(t)).astype(np.int64)
    flat = np.unique(py * 70000 + px)
    return flat % 70000, flat // 70000


def _clip(poly, x0, y0, x1, y1):
    """A polygon clipped to a rectangle (Sutherland-Hodgman), so that a
    view zoomed far in never gives the painter coordinates it cannot
    handle."""
    pts = [tuple(p) for p in poly]
    for axis, bound, keep_low in ((0, x0, False), (0, x1, True),
                                  (1, y0, False), (1, y1, True)):
        if not pts:
            break
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            cin = cur[axis] <= bound if keep_low else cur[axis] >= bound
            pin = prev[axis] <= bound if keep_low else prev[axis] >= bound
            if cin != pin:
                t = (bound - prev[axis]) / (cur[axis] - prev[axis])
                out.append(tuple(prev[a] + t * (cur[a] - prev[a])
                                 for a in (0, 1)))
            if cin:
                out.append(cur)
        pts = out
    return pts


class Raster:
    """The picture of one view and the graphics context of its drawing
    area."""

    # light and dark themes: the elements of the model as screen segments
    # for the fill of their closed parts (set by the canvas when the
    # library gives them; else the element lines of the records), and a
    # repaint of the whole view coming without a clear (an exposure)
    fill_source = None
    fill_next = False

    def __init__(self, res, width, height, use_squares):
        self.res = res
        self.use_squares = use_squares
        self.function = modes.COPY
        self.fg = 0
        self.width = 0
        self.resize(width, height)

    def resize(self, width, height, keep=False):
        old = getattr(self, "img", None)
        self.w = max(1, width)
        self.h = max(1, height)
        self.img = np.empty((self.h, self.w), np.uint32)
        self.clear()
        if keep and old is not None:
            h = min(self.h, old.shape[0])
            w = min(self.w, old.shape[1])
            self.img[:h, :w] = old[:h, :w]

    def clear(self):
        self.img.fill(OPAQUE | np.uint32(self.res["pxBackground"]))

    def draw(self, recs, text, view, hl_flag, hidden_flag, clipped_flag):
        """Draws the records of this view (structured array of the library
        records, in order) with the graphics context the records set."""
        if CLIB is not None:
            self._draw_c(recs, text, view, hl_flag, hidden_flag,
                         clipped_flag)
            return
        recs = recs[(recs["view"] == view) & ((recs["flags"] & hidden_flag)
                                              == 0)]
        if not len(recs):
            return
        ops = recs["op"]
        n = len(recs)
        is_mode = ops == ord("M")
        # graphics context of every record: that of the last mode record
        # before it, or the one carried over from earlier records
        last = np.maximum.accumulate(np.where(is_mode, np.arange(n), -1))
        func = np.full(n, self.function, np.int64)
        fg = np.full(n, self.fg, np.uint32)
        width = np.full(n, self.width, np.int64)
        mode_idx = np.nonzero(is_mode)[0]
        if len(mode_idx):
            # the context of each different mode once; a mode without one
            # keeps the context before it (the last mode with one, else
            # the context carried over)
            code = (recs["i"][mode_idx].astype(np.int64) * 2
                    + ((recs["flags"][mode_idx] & hl_flag) != 0))
            codes, which = np.unique(code, return_inverse=True)
            table = [modes.gc(self.res, int(c) >> 1, bool(c & 1))
                     for c in codes]
            state = (self.function, self.fg, self.width)
            known = np.array([g is not None for g in table])
            src = np.maximum.accumulate(
                np.where(known[which], np.arange(len(mode_idx)), -1))
            ctx = [g if g is not None else state for g in table]
            pick = which[np.maximum(src, 0)]
            gf = np.where(src >= 0, np.array([g[0] for g in ctx],
                                             np.int64)[pick], state[0])
            gcol = np.where(src >= 0, np.array([g[1] for g in ctx],
                                             np.uint32)[pick], state[1])
            gw = np.where(src >= 0, np.array([g[2] for g in ctx],
                                             np.int64)[pick], state[2])
            after = last >= 0
            pos = np.searchsorted(mode_idx, last[after])
            func[after] = gf[pos]
            fg[after] = gcol[pos]
            width[after] = gw[pos]
            if src[-1] >= 0:
                self.function, self.fg, self.width = table[which[src[-1]]]

        clipped = (recs["flags"] & clipped_flag) != 0
        is_line = ((ops == ord("L")) | (ops == ord("l"))) & ~clipped
        is_rect = ops == ord("r")
        is_arc = (ops == ord("C")) & ~clipped & (not self.use_squares)
        is_text = ops == ord("T")
        is_clear = ops == ord("K")
        prim = np.nonzero(is_line | is_rect | is_arc | is_text | is_clear)[0]
        if not len(prim):
            return
        # runs of primitives with the same raster function, cut at clears
        f = func[prim]
        cut = np.ones(len(prim), bool)
        cut[1:] = (f[1:] != f[:-1]) | is_clear[prim][1:] | is_clear[prim][:-1]
        starts = np.nonzero(cut)[0]
        ends = np.append(starts[1:], len(prim))
        fill = self.res.get("pxFill")
        model = fill is not None and self.fill_source is not None
        if model and self.fill_next:
            self._fill_model(fill)
        self.fill_next = False
        if fill is not None and not model:
            # the lines drawing elements (mode VM1_ELEM, not highlighted)
            at = np.maximum(last, 0)
            elem_line = ((ops == ord("L")) | (ops == ord("l"))) & \
                (last >= 0) & (recs["i"][at] == modes.VM1_ELEM) & \
                ((recs["flags"][at] & hl_flag) == 0)
            clears = np.append(np.nonzero(is_clear)[0], n)
            # before the first clear too: a repaint after an exposure
            # comes without a clear (the area was cleared by the exposure)
            sel = np.nonzero(elem_line[:clears[0]])[0]
            if len(sel):
                self._fill_closed(recs["s"][sel], fill)
        for a, b in zip(starts, ends):
            idx = prim[a:b]
            if is_clear[idx[0]]:
                self.clear()
                if model:
                    self._fill_model(fill)
                elif fill is not None:
                    end = clears[np.searchsorted(clears, idx[0], "right")]
                    sel = idx[0] + np.nonzero(elem_line[idx[0]:end])[0]
                    self._fill_closed(recs["s"][sel], fill)
            else:
                self._run(idx, recs, text, is_line, func[idx[0]], fg, width)

    def _gc_table(self, hl_flag):
        """The graphics context of every mode, without and with highlight
        (modes.gc), for the rasterizer of the library: valid, function,
        colour, width, index 2 * mode + highlight."""
        if getattr(self, "_gc_res", None) is not self.res or \
                self._gc_hl != hl_flag:
            n = modes.VMX12_MESHELEMENT + 1
            valid = np.zeros(2 * n, np.int32)
            func = np.zeros(2 * n, np.int32)
            fg = np.zeros(2 * n, np.uint32)
            wd = np.zeros(2 * n, np.int32)
            for m in range(n):
                for hl in (0, 1):
                    g = modes.gc(self.res, m, bool(hl))
                    if g is not None:
                        valid[2 * m + hl] = 1
                        func[2 * m + hl], fg[2 * m + hl], wd[2 * m + hl] = g
            self._gc_tab = (n, valid, func, fg, wd)
            self._gc_res, self._gc_hl = self.res, hl_flag
        return self._gc_tab

    def _draw_c(self, recs, text, view, hl_flag, hidden_flag, clipped_flag):
        """draw by the rasterizer of the library: the records walked in C,
        texts and (light and dark themes) the closed parts of the elements
        here."""
        recs = np.ascontiguousarray(recs)
        n = len(recs)
        if not n:
            return
        nm, valid, func, fg, wd = self._gc_table(hl_flag)
        st_f = ctypes.c_int(int(self.function))
        st_c = ctypes.c_uint(int(self.fg))
        st_w = ctypes.c_int(int(self.width))
        fill = self.res.get("pxFill")
        args = (view, hidden_flag, clipped_flag, hl_flag,
                int(bool(self.use_squares)), int(fill is not None),
                int(self.res["pxBackground"]), valid.ctypes.data,
                func.ctypes.data, fg.ctypes.data, wd.ctypes.data, nm,
                ctypes.byref(st_f), ctypes.byref(st_c),
                ctypes.byref(st_w)) + tuple(self.C_SCALE)
        model = fill is not None and self.fill_source is not None
        if model and self.fill_next:
            self._fill_model(fill)
        elif fill is not None and not model:
            self._fill_from(recs, 0, view, hl_flag, hidden_flag, fill)
        self.fill_next = False
        k = 0
        while True:
            k = CLIB.PyRasterDraw(self.img.ctypes.data, self.w, self.h,
                                  recs.ctypes.data, n, k, *args)
            if k >= n:
                break
            if recs["op"][k] == ord("T"):
                px, py = self._text_pixels(k, recs, text)
                self._put(np.full(len(px), k), px, py,
                          np.full(len(px), st_c.value, np.uint32),
                          st_f.value)
            else:
                self.clear()
                if model:
                    self._fill_model(fill)
                else:
                    self._fill_from(recs, k, view, hl_flag, hidden_flag,
                                    fill)
            k += 1
        self.function, self.fg, self.width = (st_f.value, st_c.value,
                                              st_w.value)

    def _fill_model(self, colour):
        """The closed parts of the elements of the model (fill_source:
        all elements, whatever the view shows of them)."""
        segs = self.fill_source()
        if segs is not None and len(segs):
            self._fill_closed(segs, colour)

    def _fill_from(self, recs, start, view, hl_flag, hidden_flag, colour):
        n = len(recs)
        out = np.empty((max(n, 1), 4), np.float64)
        m = CLIB.PyRasterElemLines(recs.ctypes.data, n, start, view,
                                   hidden_flag, hl_flag, modes.VM1_ELEM,
                                   out.ctypes.data, n)
        if m:
            self._fill_closed(out[:m], colour)

    def _fine(self, v):
        """Screen positions as positions of the picture."""
        return np.asarray(v, np.float64)

    def _fill_closed(self, s, colour):
        """Light and dark themes: the closed polygons of the element lines
        s (screen positions x1, y1, x2, y2) drawn after a clear, all but
        the outermost (largest), filled under everything drawn after."""
        if len(s) < 3:
            return
        ends = np.round(np.asarray(s, np.float64)[:, :4] * 1000).astype(
            np.int64)
        adj = {}
        for e, (x1, y1, x2, y2) in enumerate(ends):
            if (x1, y1) != (x2, y2):
                adj.setdefault((x1, y1), []).append((e, (x2, y2)))
                adj.setdefault((x2, y2), []).append((e, (x1, y1)))
        used, loops = set(), []
        for e0, (x1, y1, x2, y2) in enumerate(ends):
            if e0 in used or (x1, y1) == (x2, y2):
                continue
            used.add(e0)
            start, cur, path = (x1, y1), (x2, y2), [(x1, y1), (x2, y2)]
            while cur != start:
                step = [(e, k) for e, k in adj[cur] if e not in used]
                if not step:
                    break
                used.add(step[0][0])
                cur = step[0][1]
                path.append(cur)
            if cur == start and len(path) > 3:
                loops.append(np.array(path[:-1], np.float64) / 1000.0)
        if len(loops) < 2:
            return
        area = [abs(np.dot(p[:, 0], np.roll(p[:, 1], -1))
                    - np.dot(p[:, 1], np.roll(p[:, 0], -1))) for p in loops]
        outer = int(np.argmax(area))
        mask = QtGui.QImage(self.w, self.h, QtGui.QImage.Format_Grayscale8)
        mask.fill(0)
        p = QtGui.QPainter(mask)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(255, 255, 255))
        for k, loop in enumerate(loops):
            if k != outer:
                f = _clip(self._fine(loop), -4.0, -4.0, self.w + 4.0,
                          self.h + 4.0)
                if len(f) > 2:
                    p.drawPolygon(QtGui.QPolygonF(
                        [QtCore.QPointF(x, y) for x, y in f]))
        p.end()
        m = np.frombuffer(mask.constBits(), np.uint8).reshape(
            self.h, mask.bytesPerLine())[:, :self.w]
        self.img[m != 0] = OPAQUE | np.uint32(colour)

    # the picture for the rasterizer of the library: scaled, f, dpr, ss
    C_SCALE = (0, 1, 1, 1)

    def _text_pixels(self, k, recs, text):
        s = recs["s"]
        off, length = int(recs["i"][k]), int(recs["j"][k])
        t = text[off:off + max(length, 0)].decode("latin-1")
        if self.res.get("modernText"):
            return themes.text_pixels(_i16(s[k, 0]), _i16(s[k, 1]), t)
        return text_pixels(_i16(s[k, 0]), _i16(s[k, 1]), t)

    def _run(self, idx, recs, text, is_line, function, fg, width):
        """The pixels of the primitives of one run, in drawing order."""
        s = recs["s"]
        ops = recs["op"]
        keys, xs, ys, colors = [], [], [], []
        zero = idx[is_line[idx] & (width[idx] == 0)]
        if len(zero):
            c = np.trunc(s[zero]).astype(np.int64)
            c = ((c + 32768) & 0xFFFF) - 32768
            px, py = zero_lines(c[:, 0], c[:, 1], c[:, 2], c[:, 3])
            counts = np.maximum(np.abs(c[:, 2] - c[:, 0]),
                                np.abs(c[:, 3] - c[:, 1])) + 1
            keys.append(np.repeat(zero, counts))
            xs.append(px)
            ys.append(py)
            colors.append(np.repeat(fg[zero], counts))
        wide = idx[is_line[idx] & (width[idx] != 0)]
        if len(wide):
            c = np.trunc(s[wide]).astype(np.int64)
            c = ((c + 32768) & 0xFFFF) - 32768
            px, py, counts = wide_lines(c[:, 0], c[:, 1], c[:, 2], c[:, 3],
                                        width[wide])
            keys.append(np.repeat(wide, counts))
            xs.append(px)
            ys.append(py)
            colors.append(np.repeat(fg[wide], counts))
        for k in idx[~is_line[idx]]:
            op = chr(ops[k])
            if op == "r":
                sx1, sy1, sx2, sy2 = (int(v) for v in s[k])
                if sx1 > sx2:
                    sx1, sx2 = sx2, sx1
                if sy1 > sy2:
                    sy1, sy2 = sy2, sy1
                px, py = rectangle(_i16(sx1), _i16(sy1), _c16(sx2 - sx1),
                                   _c16(sy2 - sy1), int(width[k]))
            elif op == "T":
                off, length = int(recs["i"][k]), int(recs["j"][k])
                t = text[off:off + max(length, 0)].decode("latin-1")
                if self.res.get("modernText"):
                    px, py = themes.text_pixels(_i16(s[k, 0]),
                                                _i16(s[k, 1]), t)
                else:
                    px, py = text_pixels(_i16(s[k, 0]), _i16(s[k, 1]), t)
            else:
                wh, h = int(s[k, 2]), int(s[k, 3])
                px, py = ellipse_pixels(_i16(int(s[k, 0]) - wh),
                                        _i16(int(s[k, 1]) - h),
                                        _c16(wh * 2 - 1), _c16(h * 2 - 1))
            keys.append(np.full(len(px), k))
            xs.append(px)
            ys.append(py)
            colors.append(np.full(len(px), fg[k], np.uint32))
        if not keys:
            return
        self._put(np.concatenate(keys), np.concatenate(xs),
                  np.concatenate(ys), np.concatenate(colors), function)

    def _put(self, key, px, py, col, function):
        """The pixels of a run (key: the record drawing each pixel, the
        records in drawing order). XOR in any order, as XOR commutes;
        otherwise the last write of a pixel wins: the record with the
        highest key, found through an image of keys."""
        ok = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
        flat = py[ok] * self.w + px[ok]
        img = self.img.reshape(-1)
        col = col[ok].astype(np.uint32)
        if function == modes.XOR:
            np.bitwise_xor.at(img, flat, col)
            return
        key = key[ok].astype(np.int32)
        keys = getattr(self, "_keys", None)
        if keys is None or keys.size != img.size:
            keys = self._keys = np.full(img.size, -1, np.int32)
        np.maximum.at(keys, flat, key)
        last = keys[flat] == key
        img[flat[last]] = OPAQUE | col[last]
        keys[flat] = -1
