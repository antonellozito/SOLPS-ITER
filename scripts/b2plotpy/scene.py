"""Scene model: rebuild NCAR frames, panels and primitives from messages.

The Scene is a small GKS-like state machine fed with the decoded messages
of b2pl_gui.exe (protocol.py). Completed frames are kept in Scene.frames;
the frame being drawn is Scene.current.
"""

from dataclasses import dataclass, field

import numpy as np

from . import protocol


@dataclass(frozen=True)
class LineStyle:
    """Attributes of a polyline: colour index, width, GKS type, dash."""
    ci: int = 1
    width: float = 1.0
    ltype: int = 1
    dash: str = "$"
    jcrt: int = 1


@dataclass
class Polyline:
    x: np.ndarray
    y: np.ndarray
    style: LineStyle


@dataclass
class Fill:
    x: np.ndarray
    y: np.ndarray
    ci: int
    tagkind: int = 0
    tagindex: int = 0
    tagvalue: float = 0.0
    pattern: int = 0            # Softfill TY: 0 solid, else line pattern


@dataclass
class Markers:
    x: np.ndarray
    y: np.ndarray
    ci: int
    mtype: int                  # GKS marker type, 0 a line-width dot
    scale: float                # marker scale, line width for type 0


@dataclass
class Text:
    x: float
    y: float
    size: float
    angd: float
    cntr: float
    text: str
    ci: int
    fc: str
    bold: bool


@dataclass
class Image:
    msg: protocol.Message
    ci: int


@dataclass
class ColorBar:
    msg: protocol.Message
    ci: int
    pattern: int = 0            # Softfill TY when the bar was drawn


@dataclass
class Contour:
    """Contour fill, lines or information label with its mesh or grid."""
    kind: str                      # "fill", "lines" or "info"
    msg: protocol.Message
    data: protocol.Message = None  # CT_MESH or CP_RECT message
    edges: list = field(default_factory=list)  # AREA_EDGE messages


@dataclass
class Panel:
    """Primitives drawn under one SET (viewport, window, log flag)."""
    viewport: tuple
    window: tuple
    lf: int
    items: list = field(default_factory=list)
    axes: dict = None
    meta: dict = None


@dataclass
class Frame:
    panels: list = field(default_factory=list)
    colorbars: list = field(default_factory=list)
    meta: list = field(default_factory=list)
    colors: dict = field(default_factory=dict)
    complete: bool = False

    @property
    def xwidth(self):
        return self.meta[-1]["xwidth"] if self.meta else 1.0

    @property
    def yheight(self):
        return self.meta[-1]["yheight"] if self.meta else 1.0

    def is_empty(self):
        return not self.colorbars and not any(p.items or p.axes
                                              for p in self.panels)


DEFAULT_COLORS = {0: (1.0, 1.0, 1.0), 1: (0.0, 0.0, 0.0)}

# Opcodes that may continue a merged polyline
_LINE_OPS = {protocol.OPCODES["LINE"]}


class Scene:
    """Accumulates frames from a message stream."""

    def __init__(self):
        self.frames = []
        self.current = Frame()
        self.colors = dict(DEFAULT_COLORS)
        self.panel = None
        self.plci = 1
        self.lwsc = 1.0
        self.ln = 1
        self.dash = ("$", 1)
        self.faci = 1
        self.pmci = 1
        self.mk = 3
        self.mksc = 1.0
        self.font = 1
        self.fc = ":"
        self.pc_font = 0
        self.gaset = {}
        self.sfset = {}
        self.edges = []
        self.mesh = None
        self.rect = None
        self.segments = {}
        self.recording = None
        self.run = None
        self.catalog = None
        self.last_sync = None
        self._open = None

    # ------------------------------------------------------------- input
    def feed(self, op, payload):
        """Feed one raw message (opcode and payload bytes)."""
        if self.recording is not None and op not in (61,):
            self.segments[self.recording].append((op, payload))
            return
        self.feed_message(protocol.decode(op, payload))

    def feed_message(self, m):
        if m.op not in _LINE_OPS:
            self._close_line()
        handler = getattr(self, "_on_" + m.name.lower(), None)
        if handler is not None:
            handler(m)

    # ------------------------------------------------------------ helpers
    def _style(self):
        return LineStyle(self.plci, self.lwsc, self.ln, self.dash[0],
                         self.dash[1])

    def _add(self, item):
        if self.panel is None:
            self._set_panel((0.0, 1.0, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0), 1)
        self.panel.items.append(item)

    def _set_panel(self, viewport, window, lf):
        for p in self.current.panels:
            if p.viewport == viewport and p.window == window and p.lf == lf:
                self.panel = p
                return
        self.panel = Panel(viewport, window, lf)
        self.current.panels.append(self.panel)

    def _close_line(self):
        if self._open is None:
            return
        style, panel, xs, ys = self._open
        self._open = None
        panel.items.append(Polyline(np.asarray(xs, np.float32),
                                    np.asarray(ys, np.float32), style))

    # ----------------------------------------------------------- handlers
    def _on_runinfo(self, m):
        self.run = m.fields

    def _on_catalog(self, m):
        self.catalog = m.categories

    def _on_sync(self, m):
        self.last_sync = m.fields

    def _on_frame(self, m):
        self.current.colors = dict(self.colors)
        self.current.complete = True
        if not self.current.is_empty():
            self.frames.append(self.current)
        self.current = Frame()
        self.panel = None

    def _on_page_meta(self, m):
        self.current.meta.append(m.fields)
        if self.panel is not None:
            self.panel.meta = m.fields

    def _on_set(self, m):
        self._set_panel((m.vl, m.vr, m.vb, m.vt), (m.wl, m.wr, m.wb, m.wt),
                        m.lf)

    def _on_color_rep(self, m):
        self.colors[m.ci] = (m.r, m.g, m.b)

    def _on_plci(self, m):
        self.plci = m.ci

    def _on_lwsc(self, m):
        self.lwsc = m.w

    def _on_ln(self, m):
        self.ln = m.ltype

    def _on_dash(self, m):
        self.dash = (m.ipat, m.jcrt)

    def _on_faci(self, m):
        self.faci = m.ci

    def _on_pmci(self, m):
        self.pmci = m.ci

    def _on_mk(self, m):
        self.mk = m.mtype

    def _on_mksc(self, m):
        self.mksc = m.scale

    def _on_txfp(self, m):
        self.font = m.font

    def _on_pcset(self, m):
        key = m.pname[:2].upper()
        if key == "FC" and m.kind == 3:
            self.fc = m.cval[:1] or ":"
        elif key == "FN" and m.kind == 1:
            self.pc_font = m.ival

    def _on_gaset(self, m):
        self.gaset[m.pname[:3].upper()] = m.ival if m.kind == 1 else m.rval

    def _on_sfset(self, m):
        self.sfset[m.pname[:2].upper()] = m.ival

    def _on_line(self, m):
        style = self._style()
        if m.xa == m.xb and m.ya == m.yb:     # a round-capped dot in NCAR
            self._add(Markers(np.array([m.xa], np.float32),
                              np.array([m.ya], np.float32), self.plci, 0,
                              self.lwsc))
            return
        if self.panel is None:
            self._set_panel((0.0, 1.0, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0), 1)
        if (self._open is not None and self._open[0] == style
                and self._open[1] is self.panel
                and self._open[2][-1] == m.xa and self._open[3][-1] == m.ya):
            self._open[2].append(m.xb)
            self._open[3].append(m.yb)
        else:
            self._close_line()
            self._open = (style, self.panel, [m.xa, m.xb], [m.ya, m.yb])

    def _on_polyline(self, m):
        if m.n > 0:
            self._add(Polyline(m.x, m.y, self._style()))

    def _on_fill(self, m):
        ci = self.faci if m.ci < 0 else m.ci
        self._add(Fill(m.x, m.y, ci, m.tagkind, m.tagindex, m.tagvalue,
                       self.sfset.get("TY", 0)))

    def _on_markers(self, m):
        self._add(Markers(m.x, m.y, self.pmci, self.mk, self.mksc))

    def _on_text(self, m):
        self._add(Text(m.x, m.y, m.size, m.angd, m.cntr, m.chrs, self.plci,
                       self.fc, self.font == -30 or self.pc_font == 30))

    def _on_gkstext(self, m):
        self._add(Text(m.x, m.y, 0.01, 0.0, -1.0, m.chrs, self.plci, "",
                       self.font == -30))

    def _on_axes(self, m):
        if self.panel is None:
            return
        self.panel.axes = dict(m.fields, gaset=dict(self.gaset),
                               ci=self.plci)

    def _on_colorbar(self, m):
        self.current.colorbars.append(ColorBar(m, self.plci,
                                               self.sfset.get("TY", 0)))

    def _on_cellarray(self, m):
        self._add(Image(m, self.plci))

    def _on_area_init(self, m):
        self.edges = []

    def _on_area_edge(self, m):
        self.edges.append(m)

    def _on_ct_mesh(self, m):
        self.mesh = m

    def _on_cp_rect(self, m):
        self.rect = m

    def _contour(self, kind, m):
        data = self.mesh if m.source == 1 else self.rect
        self._add(Contour(kind, m, data, list(self.edges)))

    def _on_contour_fill(self, m):
        self._contour("fill", m)

    def _on_contour_lines(self, m):
        self._contour("lines", m)

    def _on_contour_info(self, m):
        self._contour("info", m)

    def _on_seg_open(self, m):
        self.segments[m.ib] = []
        self.recording = m.ib

    def _on_seg_close(self, m):
        self.recording = None

    def _on_seg_insert(self, m):
        for op, payload in self.segments.get(m.ib, []):
            self.feed(op, payload)
