"""Picking the volume of a balance on the 2D plot, the same steps for
both kinds (kinds.py): two surfaces clicked one after the other (parallel:
the upstream and the downstream surface across a region; radial: the
inner and the outer flux surface), then the surfaces at the start and at
the end of its flux tubes dragged along them, and its limits across them
(parallel: its sides; radial: its inner and outer flux surface). The
balance tool (picker.py) holds the volume and draws it."""

import numpy as np

from . import parallel, radial, style

NEAR = 14.0                         # pixels: an end face wins over others
REACH = 40.0                        # pixels: farthest face picked
WIDTH = 3.0                         # points: contour of the volume


class ParallelPicking:
    """The upstream surface, then the downstream one (surfaces across the
    region); the limits: the sides of the volume, across the tubes of the
    upstream surface (the span: its end tubes)."""
    geometry = parallel
    picks = ("up", "down")              # modes of the two clicks
    first_name = "upstream"
    ends = {"start": "upstream", "end": "downstream"}

    def __init__(self, tool):
        self.tool = tool
        self.reset(True)

    def reset(self, run=False):
        self.picked = None              # the upstream surface clicked
        self.up = self.down = None      # the surfaces of the volume

    def begin(self):
        self.picked = None

    def limit_name(self, which):
        return "side of the volume"

    def hover(self, event):
        """The surface under the mouse while picking (the downstream one in
        the region of the upstream one)."""
        t = self.tool
        region = None if t.mode == "up" else self.picked.region
        s = t._surface(t._face(event.xdata, event.ydata, region), region)
        if s is not t.candidate:
            t.candidate = s
            self._candidate(s, t.mode)

    def _candidate(self, s, which, span=None):
        """Surface s across the tubes of span (all of them without)."""
        self.tool._draw_candidate(
            [] if s is None else [s.segments[u] for u in
                                  parallel.span_tubes(s, span)],
            style.UP if which == "up" else style.DOWN)

    def choose(self, s):
        self.picked = s

    def chosen_text(self):
        return "Parallel balance: upstream surface in the %s (%d flux " \
            "tubes); click the downstream surface in the same region" % (
                self.tool.grid.names[self.picked.region],
                len(self.picked.tubes))

    def pending(self):
        """Segments of the surface clicked first, or None."""
        return self.picked.polyline() if self.picked is not None else None

    def complete(self, s):
        """The volume to the second surface s; False (and a message) if
        there is none."""
        if s is None:
            self.tool.status("Parallel balance: the downstream surface must "
                             "be in the %s" % self.tool.grid.names[
                                 self.picked.region])
            return False
        return self._set(self.picked, s)

    def draw_end(self, s, which):
        """Surface s dragged to (which: "start" or "end")."""
        self._candidate(s, "up" if which == "start" else "down",
                        self.tool.span)

    def move_end(self, which, s):
        """The surface which moved to s: True if the volume changed, False
        if there is none, None if s changes nothing."""
        if s is None or s is (self.up if which == "start" else self.down):
            return None
        up, down = (s, self.down) if which == "start" else (self.up, s)
        return self._set(up, down, self.tool.span)

    def span(self):
        """The end tubes of the volume, the first one first in the order of
        the upstream surface."""
        order = {t: i for i, t in enumerate(self.up.tubes)}
        a, b = self.tool.vol.tubes[0], self.tool.vol.tubes[-1]
        return (a, b) if order[a] <= order[b] else (b, a)

    def tube_at(self, x, y):
        """Tube of the upstream surface nearest to (x, y)."""
        g = self.tool.grid
        faces = np.array([f for f in g.sep_faces
                          if g.face_pos[f][0] in self.up.pos], int)
        if not len(faces):
            return None
        f = int(faces[np.argmin(g.distance(np.array((x, y)), faces))])
        return g.face_pos[f][0]

    def move_limit(self, t):
        """The side dragged at tube t (never past the other side): its new
        place drawn (a dot where it has no faces)."""
        tool = self.tool
        order = {u: i for i, u in enumerate(self.up.tubes)}
        a, b = self.span()
        if tool.mode == "drag-first":
            span = (t if order[t] <= order[b] else b, b)
        else:
            span = (a, t if order[t] >= order[a] else a)
        if span == tool.candidate:
            return
        vol = parallel.volume(tool.grid, self.up, self.down, span)
        if isinstance(vol, str):
            return
        tool.candidate = span
        first, last, _ = parallel.sides(tool.grid, vol, self.up)
        which = tool.mode[5:]
        faces = first if which == "first" else last
        tool._lines("candidate", tool._segments(faces), style.SOURCE, WIDTH)
        if not faces:
            tool._dot("candidate", parallel.corner(tool.grid, vol, self.up,
                                                   which))
        tool.tab.canvas.draw_idle()

    def set_span(self, span):
        return self._set(self.up, self.down, span)

    def limits(self):
        """Faces of the limits of the volume: its sides."""
        return [f for fs in self.tool.sides for f in fs]

    def _set(self, up, down, span=None):
        """The volume between up and down across span (end tubes; None:
        the whole region); False (and a message) if there is none."""
        tool = self.tool
        vol = parallel.volume(tool.grid, up, down, span)
        if isinstance(vol, str):
            tool.status("Parallel balance: " + vol)
            return False
        self.up, self.down, self.picked = up, down, None
        span = span if span is not None and \
            parallel.span_tubes(up, span) != list(up.tubes) else None
        sides = parallel.sides(tool.grid, vol, up)
        corners = {}
        for which, faces in zip(("first", "last"), sides):
            point = None if faces else parallel.corner(tool.grid, vol, up,
                                                        which)
            if point is not None:
                corners[which] = np.array(point)
        tool.set_volume(vol, span, sides, corners)
        return True

    def describe(self):
        v, g = self.tool.vol, self.tool.grid
        walls = sum(not r for r in v.reached)
        return "%s, %d flux tubes from the upstream to the downstream " \
            "surface%s, %d cells, %d slices of the poloidal balance" % (
                g.names[v.region], len(v.tubes),
                " (%d of them end on a wall before it)" % walls if walls
                else "", len(v.cell), v.slices.shape[0] - 1)


class RadialPicking:
    """The inner flux surface, then the outer one (outside it, in its
    region); the surfaces at the start and the end of the tubes (their
    whole extent at first: a closed region a whole turn from its cut); the
    limits: the inner and the outer flux surface (the span: the inner and
    the outer tube)."""
    geometry = radial
    picks = ("inner", "outer")
    first_name = "inner flux"
    ends = {"start": "start", "end": "end"}

    def __init__(self, tool):
        self.tool = tool
        self.reset(True)

    def reset(self, run=False):
        self.first = None               # the inner surface picked
        self.start = self.end = self.turn = None
        if run:
            self._centres = self._faces = None

    def begin(self):
        self.first = None

    def limit_name(self, which):
        return ("inner" if which == "first" else "outer") + " flux surface"

    def _region_cells(self, region):
        """Cells of the flux tubes of region (their centres computed)."""
        g = self.tool.grid
        if self._centres is None:
            self._centres = np.array([g.vx[g.cell_vx[c]].mean(axis=0)
                                      for c in range(len(g.cell_vx))])
        return np.array([c for t in range(g.nFt) if g.region[t] == region
                         for c in g.tube_cells[t]], int)

    def hover(self, event):
        """The flux surface under the mouse while picking: the inner one
        (blue), then the outer one (red), outside it in its region."""
        tool = self.tool
        g = tool.grid
        if self._faces is None:
            self._region_cells(0)
            self._faces = radial.candidates(g)
        p = np.array((event.xdata, event.ydata))
        d = g.distance(p, self._faces)
        near = self._faces[d <= REACH * tool._pixel()]
        which = tool.mode
        region = None if which == "inner" else self.first.region
        s = radial.pick(g, p, which, near, self._centres, region)
        if s is not None and which == "outer" and \
                radial.path(g, self.first.tube, s.tube) is None:
            s = None
        if s == tool.candidate:
            return
        tool.candidate = s
        tool._draw_candidate(tool._segments(s.faces) if s else [],
                             style.UP if which == "inner" else style.DOWN)

    def choose(self, s):
        self.first = s

    def chosen_text(self):
        return "Radial balance: inner flux surface in the %s; click the " \
            "outer flux surface, outside it in the same region" % \
            self.tool.grid.names[self.first.region]

    def pending(self):
        return self.tool._segments(self.first.faces) if \
            self.first is not None else None

    def complete(self, s):
        tool = self.tool
        if s is None:
            tool.status("Radial balance: the outer flux surface must be "
                        "outside the inner one, in the %s" %
                        tool.grid.names[self.first.region])
            return False
        tubes = radial.path(tool.grid, self.first.tube, s.tube)
        turn = radial.cut(tool.grid, self.first.region) if \
            tool.grid.closed[self.first.tube] else None
        return self._set(tubes, None, None, turn)

    def draw_end(self, s, which):
        """Surface s dragged to: yellow, over the tubes of the volume."""
        keep = set(self.tool.vol.tubes)
        self.tool._draw_candidate([] if s is None else [
            s.segments[t] for t in s.tubes if t in keep], style.SOURCE)

    def move_end(self, which, s):
        if s is None:
            return None
        start, end = (s, self.end) if which == "start" else (self.start, s)
        return self._set(self.tool.vol.tubes, start, end, self.turn)

    def span(self):
        """The inner and the outer tube of the volume."""
        return self.tool.vol.tubes[0], self.tool.vol.tubes[-1]

    def tube_at(self, x, y):
        """Tube of the cell of the region nearest to (x, y)."""
        g = self.tool.grid
        cells = self._region_cells(self.tool.vol.region)
        d = np.hypot(*(self._centres[cells] - (x, y)).T)
        return int(g.cvFt[cells[int(np.argmin(d))]])

    def move_limit(self, t):
        """The inner or outer flux surface dragged to tube t, only to a
        tube with an outward path to the other one: its new place drawn."""
        tool = self.tool
        a, b = self.span()
        span = (t, b) if tool.mode == "drag-first" else (a, t)
        tubes = radial.path(tool.grid, *span)
        if span == tool.candidate or tubes is None:
            return
        vol = radial.volume(tool.grid, tubes, self.start, self.end,
                            self.turn)
        if isinstance(vol, str):
            return
        tool.candidate = span
        first = tool.mode == "drag-first"
        tool._lines("candidate", tool._segments(
            vol.sides[0] if first else vol.sides[1]),
            style.UP if first else style.DOWN, WIDTH)
        tool.tab.canvas.draw_idle()

    def set_span(self, span):
        return self._set(radial.path(self.tool.grid, *span), self.start,
                         self.end, self.turn)

    def limits(self):
        """Faces of the limits of the volume: its start and end faces."""
        v = self.tool.vol
        return [f for fs in v.up + v.down for f in fs]

    def _set(self, tubes, start, end, turn):
        """The radial volume over tubes (inner to outer) between the start
        and end surfaces (None: their whole extent; a closed region: a
        turn from the cut turn); False (and a message) if there is none."""
        tool = self.tool
        if not tubes:
            tool.status("Radial balance: no flux tubes between the surfaces")
            return False
        vol = radial.volume(tool.grid, tubes, start, end, turn)
        if isinstance(vol, str):
            tool.status("Radial balance: " + vol)
            return False
        self.start, self.end, self.turn = start, end, turn
        self.first = None
        tool.set_volume(vol, None, vol.sides, {})
        return True

    def describe(self):
        v, g = self.tool.vol, self.tool.grid
        return "%s, %d flux tubes from the inner to the outer flux " \
            "surface, %d cells, %d slices of the poloidal balance" % (
                g.names[v.region], len(v.tubes), len(v.cell),
                v.slices.shape[0] - 1)


PICKINGS = {"parallel": ParallelPicking, "radial": RadialPicking}
