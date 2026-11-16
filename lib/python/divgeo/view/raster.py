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

import numpy as np

from . import fixedfont, modes

# Octants with an error bias for zero-width lines (none: the X server of the
# references draws plain Bresenham lines; flags: 4 x decreasing, 2 y
# decreasing, 1 y major)
_BIAS_OCTANTS = ()

# Perturbation of a pixel centre for the border rule: right, then down
_EPS_X = 1e-6
_EPS_Y = 1e-9

OPAQUE = np.uint32(0xFF000000)


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


class Raster:
    """The picture of one view and the graphics context of its drawing
    area."""

    def __init__(self, res, width, height, use_squares):
        self.res = res
        self.use_squares = use_squares
        self.function = modes.COPY
        self.fg = 0
        self.width = 0
        self.resize(width, height)

    def resize(self, width, height):
        self.w = max(1, width)
        self.h = max(1, height)
        self.img = np.empty((self.h, self.w), np.uint32)
        self.clear()

    def clear(self):
        self.img.fill(OPAQUE | np.uint32(self.res["pxBackground"]))

    def draw(self, recs, text, view, hl_flag, hidden_flag, clipped_flag):
        """Draws the records of this view (structured array of the library
        records, in order) with the graphics context the records set."""
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
            known = {}
            state = (self.function, self.fg, self.width)
            gcs = []
            for m in mode_idx:
                key = (int(recs["i"][m]), bool(recs["flags"][m] & hl_flag))
                if key not in known:
                    known[key] = modes.gc(self.res, key[0], key[1])
                if known[key] is not None:
                    state = known[key]
                gcs.append(state)
            after = last >= 0
            pos = np.searchsorted(mode_idx, last[after])
            func[after] = np.array([g[0] for g in gcs], np.int64)[pos]
            fg[after] = np.array([g[1] for g in gcs], np.uint32)[pos]
            width[after] = np.array([g[2] for g in gcs], np.int64)[pos]
            self.function, self.fg, self.width = gcs[-1]

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
        for a, b in zip(starts, ends):
            idx = prim[a:b]
            if is_clear[idx[0]]:
                self.clear()
            else:
                self._run(idx, recs, text, is_line, func[idx[0]], fg, width)

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
        key = np.concatenate(keys)
        order = np.argsort(key, kind="stable")
        px = np.concatenate(xs)[order]
        py = np.concatenate(ys)[order]
        col = np.concatenate(colors).astype(np.uint32)[order]
        ok = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
        flat = py[ok] * self.w + px[ok]
        img = self.img.reshape(-1)
        if function == modes.XOR:
            np.bitwise_xor.at(img, flat, col[ok])
        else:
            # the last write of a pixel wins
            rev = flat[::-1]
            _, first = np.unique(rev, return_index=True)
            img[rev[first]] = OPAQUE | col[ok][::-1][first]
