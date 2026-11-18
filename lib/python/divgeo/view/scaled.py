"""The raster drawing of raster.py at a finer resolution: the same records,
modes, erasing and XOR, with the picture computed at F = dpr * ss pixels
per pixel of the view (dpr: device pixels per pixel of the window, 2 on
high-resolution screens; ss: supersampling, 1 or 2) and shown at the
resolution of the device (the ss x ss blocks averaged, which smooths the
edges).

Screen positions are not rounded to whole pixels of the view: a position s
of the view maps to s * F - 1/2 in fine pixels (centres of fine pixels at
whole numbers), on average the place where the X server puts it. Lines are
one device pixel wide when the resource width is 0 and width device pixels
otherwise; texts are the glyphs of the X font, each pixel a block."""

import numpy as np
from PySide6 import QtGui

from . import raster, themes


def frame(x0, y0, x1, y1, width):
    """Pixels of a rectangle outline of the given width around the corners
    (x0, y0) and (x1, y1) (fine pixel units, centres at whole numbers)."""
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    hw = width / 2.0
    i0, i1 = int(np.floor(x0 - hw)) - 1, int(np.ceil(x1 + hw)) + 1
    j0, j1 = int(np.floor(y0 - hw)) - 1, int(np.ceil(y1 + hw)) + 1
    jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
    cx = ii + raster._EPS_X
    cy = jj + raster._EPS_Y
    outer = (cx > x0 - hw) & (cx < x1 + hw) & (cy > y0 - hw) & (cy < y1 + hw)
    inner = (cx > x0 + hw) & (cx < x1 - hw) & (cy > y0 + hw) & (cy < y1 - hw)
    keep = outer & ~inner
    return ii[keep].astype(np.int64), jj[keep].astype(np.int64)


def ring(cx, cy, a, b, width):
    """Pixels of an ellipse outline (centre, half axes) of the given width."""
    hw = width / 2.0
    i0, i1 = int(np.floor(cx - a - hw)) - 1, int(np.ceil(cx + a + hw)) + 1
    j0, j1 = int(np.floor(cy - b - hw)) - 1, int(np.ceil(cy + b + hw)) + 1
    jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
    dx = (ii - cx) / max(a, 1e-9)
    dy = (jj - cy) / max(b, 1e-9)
    dist = np.abs(np.sqrt(dx * dx + dy * dy) - 1.0) * min(max(a, 1e-9),
                                                         max(b, 1e-9))
    keep = dist < hw
    return ii[keep].astype(np.int64), jj[keep].astype(np.int64)


class Scaled(raster.Raster):
    def __init__(self, res, width, height, use_squares, dpr=1, ss=1):
        self.dpr = max(1, int(round(dpr)))
        self.ss = ss
        self.F = self.dpr * ss
        super().__init__(res, width, height, use_squares)

    def resize(self, width, height, keep=False):
        old = getattr(self, "img", None)
        self.lw = max(1, width)
        self.lh = max(1, height)
        self.w = self.lw * self.F
        self.h = self.lh * self.F
        self.img = np.empty((self.h, self.w), np.uint32)
        self.clear()
        if keep and old is not None:
            h = min(self.h, old.shape[0])
            w = min(self.w, old.shape[1])
            self.img[:h, :w] = old[:h, :w]

    def _pos(self, v):
        return np.asarray(v, np.float64) * self.F - 0.5

    def _fine(self, v):
        return self._pos(v)

    @property
    def C_SCALE(self):
        return (1, self.F, self.dpr, self.ss)

    def _text_pixels(self, k, recs, text):
        s = recs["s"]
        F = self.F
        off, length = int(recs["i"][k]), int(recs["j"][k])
        t = text[off:off + max(length, 0)].decode("latin-1")
        if self.res.get("modernText"):
            return themes.text_pixels(raster._i16(s[k, 0]) * F,
                                      raster._i16(s[k, 1]) * F, t, F)
        gx, gy = raster.text_pixels(raster._i16(s[k, 0]),
                                    raster._i16(s[k, 1]), t)
        bx, by = np.meshgrid(np.arange(F), np.arange(F))
        return ((gx[:, None] * F + bx.ravel()[None, :]).ravel(),
                (gy[:, None] * F + by.ravel()[None, :]).ravel())

    def _run(self, idx, recs, text, is_line, function, fg, width):
        s = recs["s"]
        ops = recs["op"]
        F = self.F
        keys, xs, ys, colors = [], [], [], []
        lines = idx[is_line[idx]]
        if len(lines):
            e = self._pos(s[lines])
            dev = np.where(width[lines] == 0, 1, width[lines] * self.dpr)
            thin = (width[lines] == 0) & (self.ss == 1)
            px, py, line_of = self._lines(e, dev * self.ss, thin)
            keys.append(lines[line_of])
            xs.append(px)
            ys.append(py)
            colors.append(fg[lines][line_of])
        for k in idx[~is_line[idx]]:
            op = chr(ops[k])
            w = (int(width[k]) * self.dpr or 1) * self.ss
            if op == "r":
                x0, y0, x1, y1 = self._pos(s[k])
                px, py = frame(x0, y0, x1, y1, w)
            elif op == "T":
                off, length = int(recs["i"][k]), int(recs["j"][k])
                t = text[off:off + max(length, 0)].decode("latin-1")
                if self.res.get("modernText"):
                    # drawn at the fine resolution (smooth edges)
                    px, py = themes.text_pixels(
                        raster._i16(s[k, 0]) * F, raster._i16(s[k, 1]) * F,
                        t, F)
                else:
                    gx, gy = raster.text_pixels(raster._i16(s[k, 0]),
                                                raster._i16(s[k, 1]), t)
                    bx, by = np.meshgrid(np.arange(F), np.arange(F))
                    px = (gx[:, None] * F + bx.ravel()[None, :]).ravel()
                    py = (gy[:, None] * F + by.ravel()[None, :]).ravel()
            else:
                cx, cy = self._pos(s[k, :2])
                px, py = ring(cx, cy, s[k, 2] * F, s[k, 3] * F, w)
            keys.append(np.full(len(px), k))
            xs.append(px)
            ys.append(py)
            colors.append(np.full(len(px), fg[k], np.uint32))
        if not keys:
            return
        self._put(np.concatenate(keys), np.concatenate(xs),
                  np.concatenate(ys), np.concatenate(colors), function)

    def _lines(self, e, widths, thin):
        """Lines between fine positions: Bresenham lines for the thin ones
        without supersampling, wide lines (with a dot for a zero length)
        otherwise. The pixels and the line of each (position in e), in no
        particular order."""
        parts = []
        if np.any(thin):
            t = np.nonzero(thin)[0]
            c = np.floor(e[t] + 0.5).astype(np.int64)
            px, py = raster.zero_lines(c[:, 0], c[:, 1], c[:, 2], c[:, 3])
            cnt = np.maximum(np.abs(c[:, 2] - c[:, 0]),
                             np.abs(c[:, 3] - c[:, 1])) + 1
            parts.append((t, px, py, cnt))
        wide = np.nonzero(~thin)[0]
        if len(wide):
            ew = e[wide]
            px, py, cnt = raster.wide_lines(ew[:, 0], ew[:, 1], ew[:, 2],
                                            ew[:, 3], widths[wide])
            parts.append((wide, px, py, cnt))
            # a dot where a wide line has no pixel (zero or tiny length)
            dots = wide[cnt == 0]
            if len(dots):
                c = np.floor(e[dots, :2] + 0.5).astype(np.int64)
                parts.append((dots, c[:, 0], c[:, 1],
                              np.ones(len(dots), np.int64)))
        line_of = np.concatenate([np.repeat(p[0], p[3]) for p in parts])
        return (np.concatenate([p[1] for p in parts]),
                np.concatenate([p[2] for p in parts]), line_of)

    def image(self):
        """The picture at the resolution of the device (QImage with its
        device pixel ratio)."""
        img = self.img
        if self.ss > 1 and raster.CLIB is not None:
            h, w = img.shape
            out = np.empty((h // self.ss, w // self.ss), np.uint32)
            raster.CLIB.PyRasterAverage(img.ctypes.data, w, h, self.ss,
                                        out.ctypes.data)
        elif self.ss > 1:
            # the mean of each block and channel in integers, rounded half
            # to even as np.rint (the bytes of 0xFFRRGGBB in little-endian
            # order: B, G, R, A)
            ss = self.ss
            n = ss * ss
            h, w = img.shape
            b = img.astype("<u4", copy=False).view(np.uint8).reshape(
                h, w, 4)[..., :3]
            total = np.zeros((h // ss, w // ss, 3), np.uint16)
            for dy in range(ss):
                for dx in range(ss):
                    total += b[dy::ss, dx::ss]
            q, r = np.divmod(total, n)
            up = (2 * r > n) | ((2 * r == n) & (q % 2 == 1))
            out = np.empty((h // ss, w // ss), "<u4")
            o = out.view(np.uint8).reshape(h // ss, w // ss, 4)
            o[..., :3] = q + up
            o[..., 3] = 255
            out = out.astype(np.uint32, copy=False)
        else:
            out = img
        self._shown = np.ascontiguousarray(out)
        q = QtGui.QImage(self._shown.data, self._shown.shape[1],
                         self._shown.shape[0], self._shown.strides[0],
                         QtGui.QImage.Format_RGB32)
        q.setDevicePixelRatio(self.dpr)
        return q
