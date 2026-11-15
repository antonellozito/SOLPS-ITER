"""Parallel and radial balance on the 2D plot: the buttons, picking a
volume (picking.py: its two surfaces, the surfaces nearest to the mouse
or the end faces of the flux tubes when the mouse is near them; dragging
its surfaces and its limits), the volume drawn filled with its surfaces,
the glowing segments of a recycling stratum; and the balance window."""

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection

from .. import theme
from ...qt import QtWidgets, Qt
from . import calc, ncfile, strata, style, terms, topology
from .kinds import KINDS
from .picking import NEAR, PICKINGS, REACH, WIDTH
from .windows import BalanceWindow, screen_room

ZORDER = 7.0
FILL = {False: (1.0, 1.0), True: (2.6, 0.45)}   # z-order and opacity of the
#                                               fill without, with a quantity
GRAB = 8.0                          # pixels: a surface taken for dragging
DOT = 10.0                          # pixels: a corner dot taken


class BalanceTool:
    """The parallel and the radial balance of a Tab2D (its canvas, plot,
    status); one volume at a time."""

    def __init__(self, tab):
        self.tab = tab
        self.settings = tab.settings
        self.buttons = {}
        for kind in KINDS.values():
            b = QtWidgets.QPushButton(kind.button)
            b.setCheckable(True)
            b.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                            QtWidgets.QSizePolicy.Fixed)
            b.clicked.connect(lambda on, k=kind.key: self._clicked(k))
            self.buttons[kind.key] = b
        self.kind = "parallel"
        self.pickings = {k: P(self) for k, P in PICKINGS.items()}
        self.run = None
        self.path = None
        self.bf = self.grid = self.strata = None
        self.rc = None                  # b2plot label rc (old strata)
        self.mode = None                # the two clicks of picking (picks
        #                                 of the kind), "drag-" + "start",
        #                                 "end" (surfaces), "first", "last"
        #                                 (limits)
        self.vol = None
        self.span = None                # end tubes of the volume (None: all)
        self.sides = ([], [], [])       # faces to the cells out of it
        self.corners = {}               # side without faces -> its point
        self.candidate = None
        self.window = None
        self.cache = {}                 # face -> Surface
        self._terms = {}
        self.stratum = None
        self.artists = {}
        self._rows = None
        self.xzoom = {}                 # (side, x label) -> x range
        c = tab.canvas
        c.mpl_connect("motion_notify_event", self._motion)
        c.mpl_connect("button_press_event", self._press)
        c.mpl_connect("button_release_event", self._release)
        c.mpl_connect("key_press_event", self._key)
        self.set_run(None)

    @property
    def picking(self):
        """How a volume of the kind is picked (picking.py)."""
        return self.pickings[self.kind]

    # ---------------------------------------------------------------- run
    def set_run(self, run):
        """A new run (or reload): nothing picked; the buttons only with a
        balance.nc of this state of the run."""
        if self.window is not None:
            self.window.close()
        self.window = None
        self._clear()
        self.run, self.mode = run, None
        self.vol = None
        self.span, self.sides, self.corners = None, ([], [], []), {}
        for p in self.pickings.values():
            p.reset(True)
        if self.bf is not None:
            self.bf.close()
        self.bf = self.grid = self.strata = self.rc = None
        self.cache, self._terms, self._rows = {}, {}, None
        if run is None:
            self.path, why = None, "No run"
        else:
            self.path, why = ncfile.status(run.rundir)
        for key, b in self.buttons.items():
            b.setChecked(False)
            b.setEnabled(self.path is not None)
            b.setToolTip(KINDS[key].tip if self.path else why)

    @property
    def name(self):
        return KINDS[self.kind].name

    def _load(self):
        """balance.nc and the topology of its grid, once per run."""
        if self.grid is not None:
            return True
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.bf = ncfile.BalanceFile(self.path)
            self.grid = topology.Grid(self.bf)
            self.strata = strata.Strata(self.run.rundir)
        except (OSError, KeyError, ValueError, IndexError) as err:
            self.tab.status.emit("Cannot read balance.nc: %s" % err)
            self.bf = self.grid = None
            return False
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        if self.strata.needs_rc():
            self.tab.ask_label("rc")
        return True

    def deliver_rc(self, field):
        if field is not None:
            self.rc = np.asarray(field.values[0], float)

    def rundir(self):
        return self.run.rundir if self.run is not None else ""

    def status(self, text):
        self.tab.status.emit(text)

    # -------------------------------------------------------------- modes
    def _picking(self):
        """True while the two surfaces are being clicked."""
        return self.mode in self.picking.picks

    def _clicked(self, kind):
        """A balance button: picking a volume of that kind (the volume of
        the other kind and its window go)."""
        if self._picking() and self.kind == kind:
            self.cancel()
            return
        if not self._load():
            self._buttons()
            return
        if kind != self.kind:
            if self.window is not None:
                self.window.close()
            self.cancel()
            self.closed()
            self.kind = kind
        self.tab.tools.bar.set_mode(None)
        self.tab.commands._mode("zoom", False)
        self.mode = self.picking.picks[0]
        self.picking.begin()
        self._buttons()
        for key in ("in", "out", "fill", "sides", "corners"):
            self._remove(key)           # back if cancelled
        self.tab.canvas.draw_idle()
        self.status("%s: click the %s surface (Escape cancels)" % (
            self.name, self.picking.first_name))

    def _buttons(self):
        """The button of the kind being picked pressed, the other not."""
        picking = self._picking()
        for key, b in self.buttons.items():
            b.setChecked(picking and self.kind == key)

    def cancel(self):
        """Picking stopped; the volume picked before stays."""
        if self._picking():
            self.mode = None
            self._draw_candidate([])
            self._draw_volume()
            self.status("%s: picking cancelled" % self.name)
        self._buttons()

    def busy(self):
        return self.mode is not None

    def grabs(self, event):
        """True if a press on the plot is for the balance (picking, or a
        surface of the volume taken for dragging): no pan then."""
        if self.mode is not None:
            return True
        return self._grab(event) is not None

    # ------------------------------------------------------------ picking
    def _pixel(self):
        """Data units per pixel of the plot."""
        ax = self.tab.plot.ax
        x0, x1 = ax.get_xlim()
        return (x1 - x0) / max(ax.get_window_extent().width, 1.0)

    def _face(self, x, y, region=None):
        """Separating face nearest to (x, y): an end face of a flux tube
        if one is within NEAR pixels, else the nearest face within
        REACH."""
        g = self.grid
        faces = g.sep_faces
        if region is not None:
            faces = faces[g.region[g.cvFt[g.fc[faces, 0]]] == region]
        if not len(faces):
            return None
        d = g.distance(np.array((x, y)), faces)
        px = self._pixel()
        ends = g.guard[faces]
        if ends.any():
            k = np.argmin(np.where(ends, d, np.inf))
            if d[k] <= NEAR * px:
                return int(faces[k])
        k = int(np.argmin(d))
        return int(faces[k]) if d[k] <= REACH * px else None

    def _surface(self, face, region=None):
        if face is None:
            return None
        key = (face, region)
        if key not in self.cache:
            self.cache[key] = topology.surface(self.grid, face, region)
        return self.cache[key]

    def _motion(self, event):
        if self.grid is None or event.inaxes is not self.tab.plot.ax or \
                event.xdata is None:
            return
        if self.mode in ("drag-first", "drag-last"):
            t = self.picking.tube_at(event.xdata, event.ydata)
            if t is not None:
                self.picking.move_limit(t)
        elif self._picking():
            self.picking.hover(event)
        elif self.mode in ("drag-start", "drag-end"):
            region = self.vol.region
            s = self._surface(self._face(event.xdata, event.ydata, region),
                              region)
            if s is not self.candidate:
                self.candidate = s
                self.picking.draw_end(s, self.mode[5:])
        elif self.vol is not None:
            self.tab.canvas.setCursor(Qt.SizeAllCursor if self._grab(
                event) else Qt.ArrowCursor)

    def _press(self, event):
        if self.grid is None or event.button != 1 or \
                event.inaxes is not self.tab.plot.ax or event.dblclick:
            return
        p = self.picking
        if self._picking():
            self._motion(event)         # the surface where it was clicked
            if self.mode == p.picks[0]:
                if self.candidate is None:
                    return
                p.choose(self.candidate)
                self.mode, self.candidate = p.picks[1], None
                self._remove("candidate")
                self._lines("picked", p.pending(), style.UP, WIDTH)
                self.tab.canvas.draw_idle()
                self.status(p.chosen_text())
            elif p.complete(self.candidate):
                self.mode = None
                self._buttons()
                self._open()
        elif self.mode is None and self.vol is not None:
            which = self._grab(event)
            if which in ("first", "last"):
                self.mode, self.candidate = "drag-" + which, None
                self.status("%s: move the %s across the flux tubes and "
                            "release" % (self.name, p.limit_name(which)))
            elif which is not None:
                self.mode, self.candidate = "drag-" + which, None
                self.status("%s: move the %s surface along the flux tubes "
                            "and release" % (self.name, p.ends[which]))

    def _release(self, event):
        if self.mode in ("drag-first", "drag-last"):
            self.mode = None
            span, self.candidate = self.candidate, None
            self._remove("candidate")
            if span is None or span == self.picking.span():
                self._draw_volume()
            elif self.picking.set_span(span):
                self._refresh()
            return
        if self.mode not in ("drag-start", "drag-end"):
            return
        which, self.mode = self.mode[5:], None
        s, self.candidate = self.candidate, None
        self._draw_candidate([])
        ok = self.picking.move_end(which, s)
        if ok is None:
            self._draw_volume()
        elif ok:
            self._refresh()

    def _key(self, event):
        if event.key == "escape":
            if self.mode is not None and self.mode.startswith("drag-"):
                self.mode, self.candidate = None, None
                self._draw_candidate([])
                self._draw_volume()
            else:
                self.cancel()

    def _grab(self, event):
        """"start" or "end" if the mouse is on the surface at the start or
        at the end of the flux tubes of the volume, "first" or "last" on
        that limit."""
        if self.vol is None or event.xdata is None or \
                event.inaxes is not self.tab.plot.ax:
            return None
        g, p = self.grid, np.array((event.xdata, event.ydata))
        px = self._pixel()
        for key, point in self.corners.items():     # a dot wins: it is
            if np.hypot(*(p - point)) <= DOT * px:  # where the surfaces end
                return key
        best, which = np.inf, None
        for key, faces in (("start", [f for fs in self.vol.up for f in fs]),
                           ("end", [f for i, fs in enumerate(self.vol.down)
                                    for f in fs[:len(g.faces_at(
                                        self.vol.tubes[i],
                                        self.vol.down_pos[i]))]
                                    if self.vol.reached[i]]),
                           ("first", self.sides[0]), ("last", self.sides[1])):
            if faces:
                d = g.distance(p, np.array(faces, int)).min()
                if d < best:
                    best, which = d, key
        return which if best <= GRAB * px else None

    def set_volume(self, vol, span, sides, corners):
        """The volume picked (span: its end tubes, None: all; sides: the
        faces to the cells out of it; corners: the points of the limits
        without faces), drawn."""
        self.vol, self.span, self.sides, self.corners = vol, span, sides, \
            corners
        self.xzoom = {}
        self._remove("candidate")
        self._remove("picked")
        self._draw_volume()
        self.status("%s: %s" % (self.name, self.describe()))

    def describe(self):
        return self.picking.describe()

    # ------------------------------------------------------------ results
    def terms(self, quantity, species):
        key = (quantity, tuple(species) if species is not None else None)
        if key not in self._terms:
            if len(self._terms) > 6:
                self._terms.pop(next(iter(self._terms)))
            self._terms[key] = terms.build(self.bf, self.grid, quantity,
                                           species)
        return self._terms[key]

    def compute(self, t, opts, coord):
        g, v = self.grid, self.vol
        psimap = self.run.psimap
        psin = None if psimap is None else (
            lambda r, z: psimap.rhop(r, z) ** 2)
        geometry = self.picking.geometry
        x = geometry.rhop(g, v, psin) if coord == "rhop" and psin else \
            100.0 * geometry.dssep(g, v)
        return calc.compute(g, v, t, opts, x)

    def zoom(self, side, xlim, source):
        """The x range of the plots of one part of the balance in every
        window but source (None: the whole plot)."""
        label = source.panel.xlabel if source.panel is not None else ""
        self.xzoom[(side, label)] = xlim
        w = self.window
        views = [w.radial, w.poloidal] if w is not None else []
        d = w.detail if w is not None else None
        while d is not None and d.isVisible():
            views.append(d.view)
            d = d.child
        for v in views:
            if v is not source and v.side == side and v.panel is not None \
                    and v.panel.xlabel == label:     # the same x axis
                v.set_x(xlim)

    def _open(self):
        """The balance window: at first sized to its content and put at
        the right of the main window, on its screen."""
        main = self.tab.window()
        if self.window is None:
            self.window = BalanceWindow(self, main)
            self.window.set_file(self.bf, self.run.psimap is not None)
            self.window.refresh()
            self.window.prepare()
            top = main.frameGeometry()
            self.window.move(top.x() + top.width() - self.window.width() - 30,
                             top.y() + 60)
            screen_room(self.window, main)
        else:
            self.window.refresh()
        self.window.show()
        self.window.raise_()

    def _refresh(self):
        """The balance window again after the volume changed."""
        if self.window is not None:
            self.window.refresh()

    def closed(self):
        """The balance window was closed: the volume goes."""
        self.window = None
        self.vol = None
        self.span, self.sides, self.corners = None, ([], [], []), {}
        for p in self.pickings.values():
            p.reset()
        self.mode = None
        self._buttons()
        self._clear()

    # ---------------------------------------------------------- drawing
    def _remove(self, key):
        for a in self.artists.pop(key, []):
            try:
                a.remove()
            except ValueError:
                pass

    def _clear(self):
        for key in list(self.artists):
            self._remove(key)
        self.stratum = None
        self.tab.canvas.draw_idle()

    def _lines(self, key, segments, color, width, zorder=ZORDER,
               strong=False):
        self._remove(key)
        if not len(segments):
            return
        lc = LineCollection(segments, colors=[theme.rgb(color)],
                            linewidths=width, zorder=zorder,
                            capstyle="round", joinstyle="round")
        lc.set_path_effects(style.glow(width, color, strong, on_map=True))
        self.tab.plot.ax.add_collection(lc, autolim=False)
        self.artists[key] = [lc]

    def _dot(self, key, point, size=2.4 * WIDTH):
        """A glowing dot of the source colour at point (key: as _lines;
        added to the artists of key), over the surfaces."""
        if point is None:
            return
        line, = self.tab.plot.ax.plot(
            [point[0]], [point[1]], linestyle="none", marker="o",
            markersize=size, color=theme.rgb(style.SOURCE),
            markeredgecolor="white", markeredgewidth=0.8,
            zorder=ZORDER + 0.5)
        line.set_path_effects(style.glow(0.5 * size, style.SOURCE,
                                         on_map=True))
        self.artists.setdefault(key, []).append(line)

    def _segments(self, faces):
        faces = np.asarray(list(faces), int)
        return self.grid.vx[self.grid.fv[faces]] if len(faces) else []

    def _draw_candidate(self, segments, color=style.UP):
        """The surface under the mouse (its segments; none: nothing)."""
        self._lines("candidate", segments, color, 2.4)
        self.tab.canvas.draw_idle()

    def _fill(self):
        """The volume filled with the colour of the sources: opaque over
        the grid alone, see-through over a quantity shown."""
        self._remove("fill")
        if self.vol is None:
            return
        g = self.run.geometry
        if self._rows is None:
            self._rows = np.full(g.cells.max() + 1, -1)
            self._rows[g.cells - 1] = np.arange(len(g.cells))
        rows = self._rows[self.vol.cell]
        z, alpha = FILL[self.tab.plot.data is not None]
        pc = PolyCollection([g.polygons[r] for r in rows if r >= 0],
                            facecolors=[theme.rgb(style.SOURCE)],
                            edgecolors="face", linewidths=0.3, alpha=alpha,
                            zorder=z)
        self.tab.plot.ax.add_collection(pc, autolim=False)
        self.artists["fill"] = [pc]

    def restyle(self):
        """The fill again after the quantity shown changed."""
        if self.vol is not None and self.run is self.tab.run:
            self._fill()

    def _draw_volume(self):
        """The volume: filled, its limits (yellow), the faces where flux
        comes in (blue: parallel upstream, radial inner) and goes out
        (red: downstream and walls, outer), the corner dots; while the
        second surface is clicked, the first one alone."""
        for key in ("picked", "in", "out", "fill", "sides", "corners"):
            self._remove(key)
        v, p = self.vol, self.picking
        pending = p.pending() if self.mode == p.picks[1] else None
        if pending is not None:
            self._lines("picked", pending, style.UP, WIDTH)
        elif v is not None:
            self._fill()
            self._lines("sides", self._segments(p.limits()), style.SOURCE,
                        0.5 * WIDTH)
            self._lines("out", self._segments(v.ends.outflow), style.DOWN,
                        WIDTH)
            self._lines("in", self._segments(v.ends.inflow), style.UP, WIDTH)
            for point in self.corners.values():
                self._dot("corners", point)
        self.tab.canvas.draw_idle()

    def highlight_stratum(self, k):
        """The segments of recycling stratum k glow on the 2D plot (again:
        off; None: off)."""
        if k is None or k == self.stratum:
            self.stratum = None
            self._remove("stratum")
        else:
            faces = self.strata.faces(k, self.grid, self.rc)
            self.stratum = k
            self._lines("stratum", self._segments(faces), style.STRATUM,
                        4.0, ZORDER + 0.5, strong=True)
            if not len(faces):
                self.status("No segments known for stratum %d" % (k + 1))
            else:
                self.status("%s: %d segments" % (self.strata.label(k),
                                                  len(faces)))
        self.tab.canvas.draw_idle()

    def apply_theme(self):
        """Overlays and windows in the colours of the theme."""
        stratum = self.stratum
        self._draw_volume()
        if stratum is not None:
            self.stratum = None
            self.highlight_stratum(stratum)
        if self.window is not None:
            self.window.apply_theme()
            d = self.window.detail
            if d is not None and d.isVisible():
                d.apply_theme()
