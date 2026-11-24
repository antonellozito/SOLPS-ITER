"""The mouse and the keys on the 3D view (parallel projection, the camera
of VTK not interactive): a left drag pans in the plane of the screen, the
wheel zooms about the point under the cursor, a drag with a modifier
(shift, control, alt or command) and the left or right button turns the
view around the visible point under the cursor (the vertical and
horizontal angles follow, 180 degrees across the view), the arrow keys or
W, A, S, D pan (0.3 heights of the view a second, twice as fast with
shift, a quarter with control). While points are picked, a left click
(not a drag, which still pans) gives the point under the cursor."""

import numpy as np

from ...qt import Qt, QtCore
from ..tools import revolve

PAN_PER_SECOND = 0.30           # heights of the view a second (keys)
SPRINT, PRECISION = 2.0, 0.25   # with shift, with control
WHEEL = (1.03, 0.90, 1.10)      # zoom a wheel step, at least, at most
ORBIT_MODIFIERS = (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier
                   | Qt.MetaModifier)
CLICK = 4                       # pixels a click may move (else a drag)
KEYS = {Qt.Key_W: "up", Qt.Key_Up: "up", Qt.Key_S: "down",
        Qt.Key_Down: "down", Qt.Key_A: "left", Qt.Key_Left: "left",
        Qt.Key_D: "right", Qt.Key_Right: "right", Qt.Key_Shift: "sprint",
        Qt.Key_Control: "precision"}


def _unit(v, fallback):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else np.asarray(fallback, float)


class Navigator(QtCore.QObject):
    """The gestures on widget (the render window of view), for the
    camera of view."""

    def __init__(self, view, widget):
        super().__init__(view)
        self.view, self.w = view, widget
        self.pan_last = self.orbit_last = None
        self.pick = None                # picking: called with each point
        self.pick_faces = False         # picking on the cut faces only
        self.press = None               # where the left button went down
        #                                 (a click without a drag: a pick)
        self.keys = set()
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._step_keys)
        self.clock = QtCore.QElapsedTimer()
        self.last_ms = 0
        widget.setMouseTracking(True)
        widget.setFocusPolicy(Qt.StrongFocus)
        widget.setCursor(Qt.OpenHandCursor)
        widget.installEventFilter(self)

    @property
    def cam(self):
        return self.view.pl.camera

    def _done(self):
        self.view.pl.reset_camera_clipping_range()
        self.view.render()

    # ----------------------------------------------------------- events
    def eventFilter(self, obj, event):
        t = event.type()
        E = QtCore.QEvent
        if t == E.Wheel:
            delta = event.angleDelta().y()
            if delta:
                base, lo, hi = WHEEL
                self.zoom_at(event.position(), float(np.clip(
                    base ** (delta / 120.0), lo, hi)))
            event.accept()
            return True
        if t == E.MouseButtonPress:
            self.w.setFocus(Qt.MouseFocusReason)
            b = event.button()
            self.press = event.position() if b == Qt.LeftButton else None
            if b in (Qt.LeftButton, Qt.RightButton) and \
                    event.modifiers() & ORBIT_MODIFIERS:
                self.orbit_last = event.position()
                self.pivot_at(self.orbit_last)
                self.w.setCursor(Qt.ClosedHandCursor)
            elif b == Qt.LeftButton:
                self.pan_last = event.position()
                self.w.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return True
        if t == E.MouseMove:
            p = event.position()
            if self.orbit_last is not None:
                d = p - self.orbit_last
                self.orbit_last = p
                self.orbit(d.x(), d.y())
            elif self.pan_last is not None and event.buttons() & \
                    Qt.LeftButton:
                d = p - self.pan_last
                self.pan_last = p
                self.pan(d.x(), d.y())
            event.accept()
            return True
        if t == E.MouseButtonRelease:
            p, self.press = self.press, None
            if self.pick is not None and p is not None and \
                    self.orbit_last is None and \
                    event.button() == Qt.LeftButton and \
                    (event.position() - p).manhattanLength() <= CLICK:
                self.pick((self.face_at if self.pick_faces else
                           self.world_at)(p))
            self.pan_last = self.orbit_last = None
            self.w.setCursor(Qt.CrossCursor if self.pick else
                             Qt.OpenHandCursor)
            event.accept()
            return True
        if t in (E.KeyPress, E.KeyRelease) and event.key() in KEYS:
            if t == E.KeyPress:
                self.keys.add(event.key())
                if self._moving() and not self.timer.isActive():
                    self.clock.start()
                    self.last_ms = 0
                    self.timer.start()
            elif not event.isAutoRepeat():
                self.keys.discard(event.key())
            event.accept()
            return True
        if t == E.FocusOut:
            self.keys.clear()
            self.timer.stop()
        return False

    # ------------------------------------------------------------ moves
    def _frame(self):
        """View direction, right and up of the camera."""
        cam = self.cam
        focal = np.asarray(cam.GetFocalPoint(), float)
        pos = np.asarray(cam.GetPosition(), float)
        d = _unit(focal - pos, (1.0, 0.0, 0.0))
        up = _unit(np.asarray(cam.GetViewUp(), float), (0.0, 0.0, 1.0))
        right = _unit(np.cross(d, up), (0.0, -1.0, 0.0))
        return focal, pos, d, right, _unit(np.cross(right, d), up)

    def _shift(self, shift):
        cam = self.cam
        cam.SetFocalPoint(*(np.asarray(cam.GetFocalPoint(), float) + shift))
        cam.SetPosition(*(np.asarray(cam.GetPosition(), float) + shift))

    def pan(self, dx, dy):
        """The camera moved in the plane of the screen by a drag of dx,
        dy pixels, the scene following the cursor."""
        _, _, _, right, up = self._frame()
        w, h = max(float(self.w.width()), 1.0), max(float(self.w.height()),
                                                     1.0)
        s = 2.0 * float(self.cam.GetParallelScale()) / h
        self._shift(-dx * s * right + dy * s * up)
        self._done()

    def _display(self, p):
        """Display coordinates of VTK (device pixels, from the bottom) of
        a point of the widget."""
        w, h = max(float(self.w.width()), 1.0), max(float(self.w.height()),
                                                     1.0)
        size = self.view.pl.render_window.GetSize()
        sx, sy = max(size[0], 1) / w, max(size[1], 1) / h
        y = float(np.clip((h - p.y()) * sy, 0.0, max(size[1] - 1.0, 0.0)))
        return p.x() * sx, y

    def _world(self, p, depth):
        r = self.view.pl.renderer
        x, y = self._display(p)
        r.SetDisplayPoint(x, y, depth)
        r.DisplayToWorld()
        w = np.asarray(r.GetWorldPoint(), float)
        return w[:3] / w[3] if abs(w[3]) > 1e-12 else None

    def zoom_at(self, p, factor):
        """Zoom by factor, the point under the cursor (at the depth of the
        focal point) staying where it is."""
        r = self.view.pl.renderer
        f = self.cam.GetFocalPoint()
        r.SetWorldPoint(f[0], f[1], f[2], 1.0)
        r.WorldToDisplay()
        depth = r.GetDisplayPoint()[2]
        before = self._world(p, depth)
        self.cam.Zoom(factor)
        after = self._world(p, depth)
        if before is not None and after is not None:
            self._shift(before - after)
        self._done()

    def start_pick(self, done, faces=False):
        """The next left clicks (not drags, which still pan) call done
        with the point under the cursor (world_at; faces: only on a cut
        face, face_at); None: no more."""
        self.pick, self.pick_faces = done, faces
        self.w.setCursor(Qt.CrossCursor if done else Qt.OpenHandCursor)

    def face_at(self, p):
        """The point (x, y, z) under the cursor on a cut face of the
        sector, within the extent (R, Z) of the run, the nearest one the
        view ray meets (whatever is in front of it); None if none."""
        return self.world_at(p, faces=True)

    def world_at(self, p, faces=False):
        """The point (x, y, z) under the cursor: on a cut face of the
        sector, within the extent (R, Z) of the run, if the view ray meets
        it before anything else there; else on the visible surface (the
        plasma quantity, the structure, the wall quantity); None if
        neither."""
        from vtkmodules.vtkRenderingCore import vtkCellPicker
        x, y = self._display(p)
        r = self.view.pl.renderer
        ends = []
        for depth in (0.0, 1.0):
            r.SetDisplayPoint(x, y, depth)
            r.DisplayToWorld()
            w = np.asarray(r.GetWorldPoint(), float)
            ends.append(w[:3] / w[3] if abs(w[3]) > 1e-12 else w[:3])
        a, d = ends[0], ends[1] - ends[0]
        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        hit = None
        if not faces and picker.Pick(x, y, 0.0, r) and \
                picker.GetCellId() >= 0:
            hit = np.asarray(picker.GetPickPosition(), float)
        best, scene = None, self.view.scene
        r0, r1, z0, z1 = scene.snap.box
        p0, p1 = scene.sector
        for phi in (p0,) if revolve.full(p0, p1) else (p0, p1):
            n = np.array([-np.sin(phi), np.cos(phi), 0.0])
            den = float(n @ d)
            if abs(den) < 1e-12:
                continue
            t = float(-(n @ a) / den)
            q = a + t * d
            rq = float(q @ np.array([np.cos(phi), np.sin(phi), 0.0]))
            if r0 <= rq <= r1 and z0 <= q[2] <= z1 and (best is None or
                                                         t < best[0]):
                best = (t, q)
        if best is not None and (hit is None or best[0] <= float(
                (hit - a) @ d / (d @ d)) + 1e-6):
            return best[1]
        return hit

    def pivot_at(self, p):
        """The focal point moved to the visible point under the cursor
        (the camera with it), if there is one: the view turns around it."""
        from vtkmodules.vtkRenderingCore import vtkCellPicker
        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        x, y = self._display(p)
        if not picker.Pick(x, y, 0.0, self.view.pl.renderer) or \
                picker.GetCellId() < 0:
            return
        self._shift(np.asarray(picker.GetPickPosition(), float) -
                    np.asarray(self.cam.GetFocalPoint(), float))
        self._done()

    def orbit(self, dx, dy):
        """The angles turned by a drag of dx, dy pixels (180 degrees
        across the view)."""
        v, h = self.view.angles
        w, ht = max(float(self.w.width()), 1.0), max(float(self.w.height()),
                                                     1.0)
        h2 = float(np.clip(h - dx * 180.0 / w, -180.0, 180.0))
        v2 = float(np.clip(v + dy * 180.0 / ht, -90.0, 90.0))
        if abs(h2 - h) <= 1e-9 and abs(v2 - v) <= 1e-9:
            return
        self.view.set_angles(v2, h2)
        self.view.orientation.emit(v2, h2)

    # ------------------------------------------------------------- keys
    def _roles(self):
        return {KEYS[k] for k in self.keys}

    def _moving(self):
        return bool(self._roles() & {"up", "down", "left", "right"})

    def _step_keys(self):
        roles = self._roles()
        if not self._moving():
            self.timer.stop()
            return
        now = self.clock.elapsed()
        dt = float(np.clip((now - self.last_ms) / 1000.0, 0.001, 0.05))
        self.last_ms = now
        a = np.array([("up" in roles) - ("down" in roles),
                      ("right" in roles) - ("left" in roles)], float)
        n = float(np.linalg.norm(a))
        if n <= 1e-12:
            return
        a /= n
        speed = 2.0 * float(self.cam.GetParallelScale()) * PAN_PER_SECOND
        speed *= (SPRINT if "sprint" in roles else 1.0) * \
            (PRECISION if "precision" in roles else 1.0)
        _, _, _, right, up = self._frame()
        self._shift(speed * dt * (a[0] * up + a[1] * right))
        self._done()
