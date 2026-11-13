"""Parallel balance on the 2D plot: the button, picking the upstream and
the downstream surface (the surface across the region nearest to the
mouse, the end faces of the flux tubes when the mouse is near them), the
balance volume drawn filled, with its upstream surface and its downstream
surface and walls, dragging either surface along the flux tubes, the
glowing segments of a recycling stratum; and the balance window."""

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection

from .. import theme
from ...qt import QtWidgets, Qt
from . import calc, ncfile, strata, style, terms, topology
from .windows import BalanceWindow, screen_room

ZORDER = 7.0
FILL = {False: (1.0, 1.0), True: (2.6, 0.45)}   # z-order and opacity of the
#                                               fill without, with a quantity
NEAR = 14.0                         # pixels: an end face wins over others
REACH = 40.0                        # pixels: farthest face picked
GRAB = 8.0                          # pixels: a surface taken for dragging
DOT = 10.0                          # pixels: a corner dot taken
WIDTH = 3.0                         # points: contour of the volume
TEXT = "Calculate\nparallel\nbalance"


class BalanceTool:
    """The parallel balance of a Tab2D (its canvas, plot, status)."""

    def __init__(self, tab):
        self.tab = tab
        self.settings = tab.settings
        self.button = QtWidgets.QPushButton(TEXT)
        self.button.setCheckable(True)
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                  QtWidgets.QSizePolicy.Fixed)
        self.button.clicked.connect(self._clicked)
        self.run = None
        self.path = None
        self.bf = self.grid = self.strata = None
        self.rc = None                  # b2plot label rc (old strata)
        self.mode = None                # "up", "down", "drag-" + "up",
        #                                 "down", "first", "last" (sides)
        self.up = self.down = self.vol = None
        self.span = None                # end tubes of the volume (None: all)
        self.sides = ([], [], [])       # side faces (topology.sides)
        self.corners = {}               # side without faces -> its point
        self.candidate = None
        self.window = None
        self.cache = {}                 # face -> Surface
        self._terms = {}
        self.stratum = None
        self.artists = {}
        self._rows = None
        self.xzoom = {}                 # "radial", "poloidal" -> x range
        c = tab.canvas
        c.mpl_connect("motion_notify_event", self._motion)
        c.mpl_connect("button_press_event", self._press)
        c.mpl_connect("button_release_event", self._release)
        c.mpl_connect("key_press_event", self._key)
        self.set_run(None)

    # ---------------------------------------------------------------- run
    def set_run(self, run):
        """A new run (or reload): nothing picked; the button only with a
        balance.nc of this state of the run."""
        if self.window is not None:
            self.window.close()
        self.window = None
        self._clear()
        self.run, self.mode = run, None
        self.up = self.down = self.vol = None
        self.span, self.sides, self.corners = None, ([], [], []), {}
        if self.bf is not None:
            self.bf.close()
        self.bf = self.grid = self.strata = self.rc = None
        self.cache, self._terms, self._rows = {}, {}, None
        if run is None:
            self.path, why = None, "No run"
        else:
            self.path, why = ncfile.status(run.rundir)
        self.button.setChecked(False)
        self.button.setEnabled(self.path is not None)
        self.button.setToolTip(
            "Pick the upstream and the downstream surface of a volume on "
            "the plot (both in one region: core, SOL or PFR); the balances "
            "of balance.nc in it open in their own window" if self.path
            else why)

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
    def _clicked(self, on):
        if self.mode in ("up", "down"):
            self.cancel()
            return
        if not self._load():
            self.button.setChecked(False)
            return
        self.tab.tools.bar.set_mode(None)
        self.tab.commands._mode("zoom", False)
        self.mode = "up"
        self.button.setChecked(True)
        for key in ("up", "down", "fill"):     # back if cancelled
            self._remove(key)
        self.tab.canvas.draw_idle()
        self.status("Parallel balance: click the upstream surface "
                    "(Escape cancels)")

    def cancel(self):
        """Picking stopped; the volume picked before stays."""
        if self.mode in ("up", "down"):
            self.mode = None
            self._draw_candidate(None)
            self._draw_volume()
            self.status("Parallel balance: picking cancelled")
        self.button.setChecked(False)

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
            self._move_side(event)
        elif self.mode in ("up", "down", "drag-up", "drag-down"):
            region = None if self.mode == "up" else self.up.region
            s = self._surface(self._face(event.xdata, event.ydata, region),
                              region)
            if s is not self.candidate:
                self.candidate = s
                self._draw_candidate(s, "up" if self.mode in (
                    "up", "drag-up") else "down",
                    self.span if self.mode.startswith("drag-") else None)
        elif self.vol is not None:
            self.tab.canvas.setCursor(Qt.SizeAllCursor if self._grab(
                event) else Qt.ArrowCursor)

    def _press(self, event):
        if self.grid is None or event.button != 1 or \
                event.inaxes is not self.tab.plot.ax or event.dblclick:
            return
        if self.mode in ("up", "down"):
            self._motion(event)         # the surface where it was clicked
        if self.mode == "up":
            if self.candidate is None:
                return
            self.up, self.mode = self.candidate, "down"
            self.candidate = None
            self._draw_candidate(None)
            self._draw_surface("picked", self.up, style.UP)
            self.status("Parallel balance: upstream surface in the %s (%d "
                        "flux tubes); click the downstream surface in the "
                        "same region" % (self.grid.names[self.up.region],
                                         len(self.up.tubes)))
        elif self.mode == "down":
            if self.candidate is None:
                self.status("Parallel balance: the downstream surface must "
                            "be in the %s" % self.grid.names[self.up.region])
                return
            if self._set(self.up, self.candidate):
                self.mode = None
                self.button.setChecked(False)
                self._open()
        elif self.mode is None and self.vol is not None:
            which = self._grab(event)
            if which in ("first", "last"):
                self.mode = "drag-" + which
                self.candidate = None
                self.status("Parallel balance: move the side of the volume "
                            "across the flux tubes and release")
            elif which is not None:
                self.mode = "drag-" + which
                self.candidate = None
                self.status("Parallel balance: move the %s surface along the "
                            "flux tubes and release" % ("upstream" if which ==
                                                        "up" else
                                                        "downstream"))

    def _release(self, event):
        if self.mode in ("drag-first", "drag-last"):
            self.mode = None
            span, self.candidate = self.candidate, None
            self._remove("candidate")
            if span is None or span == self._span():
                self._draw_volume()
                return
            if self._set(self.up, self.down, span) and \
                    self.window is not None:
                self.window.refresh()
            return
        if self.mode not in ("drag-up", "drag-down"):
            return
        which, self.mode = self.mode[5:], None
        s, self.candidate = self.candidate, None
        self._draw_candidate(None)
        if s is None or s is (self.up if which == "up" else self.down):
            self._draw_volume()
            return
        up, down = (s, self.down) if which == "up" else (self.up, s)
        if self._set(up, down, self.span) and self.window is not None:
            self.window.refresh()

    def _key(self, event):
        if event.key == "escape":
            if self.mode is not None and self.mode.startswith("drag-"):
                self.mode, self.candidate = None, None
                self._draw_candidate(None)
                self._draw_volume()
            else:
                self.cancel()

    def _grab(self, event):
        """"up" or "down" if the mouse is on that surface of the volume,
        "first" or "last" on that side."""
        if self.vol is None or event.xdata is None or \
                event.inaxes is not self.tab.plot.ax:
            return None
        g, p = self.grid, np.array((event.xdata, event.ydata))
        px = self._pixel()
        for key, point in self.corners.items():     # a dot wins: it is
            if np.hypot(*(p - point)) <= DOT * px:  # where the surfaces end
                return key
        best, which = np.inf, None
        for key, faces in (("up", [f for fs in self.vol.up for f in fs]),
                           ("down", [f for i, fs in enumerate(self.vol.down)
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

    def _span(self):
        """The end tubes of the volume, the first one first in the order of
        the upstream surface."""
        order = {t: i for i, t in enumerate(self.up.tubes)}
        a, b = self.vol.tubes[0], self.vol.tubes[-1]
        return (a, b) if order[a] <= order[b] else (b, a)

    def _tube_at(self, x, y):
        """Tube of the upstream surface nearest to (x, y)."""
        g = self.grid
        faces = np.array([f for f in g.sep_faces
                          if g.face_pos[f][0] in self.up.pos], int)
        if not len(faces):
            return None
        f = int(faces[np.argmin(g.distance(np.array((x, y)), faces))])
        return g.face_pos[f][0]

    def _move_side(self, event):
        """The side dragged at the tube under the mouse (never past the
        other side): its new place drawn."""
        t = self._tube_at(event.xdata, event.ydata)
        if t is None:
            return
        order = {u: i for i, u in enumerate(self.up.tubes)}
        a, b = self._span()
        if self.mode == "drag-first":
            span = (t if order[t] <= order[b] else b, b)
        else:
            span = (a, t if order[t] >= order[a] else a)
        if span == self.candidate:
            return
        vol = topology.volume(self.grid, self.up, self.down, span)
        if isinstance(vol, str):
            return
        self.candidate = span
        first, last, _ = topology.sides(self.grid, vol, self.up)
        which = self.mode[5:]
        faces = first if which == "first" else last
        self._lines("candidate", self._segments(faces), style.SOURCE, WIDTH)
        if not faces:
            self._dot("candidate", topology.corner(self.grid, vol, self.up,
                                                   which))
        self.tab.canvas.draw_idle()

    def _set(self, up, down, span=None):
        """The volume between up and down across span (end tubes; None:
        the whole region); False (and a message) if there is none."""
        vol = topology.volume(self.grid, up, down, span)
        if isinstance(vol, str):
            self.status("Parallel balance: " + vol)
            return False
        self.up, self.down, self.vol = up, down, vol
        self.span = span if span is not None and \
            topology.span_tubes(up, span) != list(up.tubes) else None
        self.sides = topology.sides(self.grid, vol, up)
        self.corners = {}
        for which, faces in zip(("first", "last"), self.sides):
            point = None if faces else topology.corner(self.grid, vol, up,
                                                        which)
            if point is not None:
                self.corners[which] = np.array(point)
        self.xzoom = {}
        self._draw_candidate(None)
        self._draw_volume()
        self.status("Parallel balance: " + self.describe())
        return True

    def describe(self):
        v, g = self.vol, self.grid
        walls = sum(not r for r in v.reached)
        return "%s, %d flux tubes from the upstream to the downstream " \
            "surface%s, %d cells, %d slices of the poloidal balance" % (
                g.names[v.region], len(v.tubes),
                " (%d of them end on a wall before it)" % walls if walls
                else "", len(v.cell), v.slices.shape[0] - 1)

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
        if coord == "rhop" and self.run.psimap is not None:
            psimap = self.run.psimap
            x = topology.rhop(g, self.up, v,
                              lambda r, z: psimap.rhop(r, z) ** 2)
        else:
            x = 100.0 * topology.dssep(g, self.up, v)
        return calc.compute(g, v, t, opts, x)

    def zoom(self, side, xlim, source):
        """The x range of the radial or poloidal balance in every window
        but source (None: the whole plot)."""
        self.xzoom[side] = xlim
        w = self.window
        views = [w.radial, w.poloidal] if w is not None else []
        d = w.detail if w is not None else None
        while d is not None and d.isVisible():
            views.append(d.view)
            d = d.child
        for v in views:
            if v is not source and v.side == side:
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

    def closed(self):
        """The balance window was closed: the volume goes."""
        self.window = None
        self.up = self.down = self.vol = None
        self.span, self.sides, self.corners = None, ([], [], []), {}
        self.mode = None
        self.button.setChecked(False)
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

    def _draw_surface(self, key, s, color, width=WIDTH):
        self._lines(key, s.polyline() if s is not None else [], color, width)
        self.tab.canvas.draw_idle()

    def _draw_candidate(self, s, which="up", span=None):
        """Surface s under the mouse, across the tubes of span (the
        volume narrowed: dragging one of its surfaces) or all of them."""
        segs = [] if s is None else [s.segments[t] for t in
                                     topology.span_tubes(s, span)]
        self._lines("candidate", segs, style.UP if which == "up" else
                    style.DOWN, 2.4)
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
        """The volume: filled, its upstream surface, its downstream surface
        and walls."""
        for key in ("picked", "up", "down", "fill", "sides", "corners"):
            self._remove(key)
        v = self.vol
        if v is not None:
            self._fill()
            self._lines("sides", self._segments(
                f for fs in self.sides for f in fs), style.SOURCE,
                0.5 * WIDTH)
            self._lines("down", self._segments(f for fs in v.down
                                               for f in fs), style.DOWN,
                        WIDTH)
            self._lines("up", self._segments(f for fs in v.up for f in fs),
                        style.UP, WIDTH)
            for point in self.corners.values():
                self._dot("corners", point)
        elif self.up is not None and self.mode == "down":
            self._draw_surface("picked", self.up, style.UP)
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
