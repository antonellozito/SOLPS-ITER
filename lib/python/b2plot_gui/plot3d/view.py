"""The 3D view in the place of the 2D plot: a PyVista render window (drawn
off screen into an image when Qt has no screen), its scene (plot3d/scene),
the camera in parallel projection, at first facing the cut face at the
start of the sector as the 2D plot shows the poloidal plane (R to the
right, Z up, the same extent), turned around its focal point by the
vertical and horizontal angles, moved with the mouse and the keys
(plot3d/navigate), the rendering options and the tracers moved by a
timer."""

import os
import time

import numpy as np

from ...qt import QtCore, QtGui, QtWidgets, Signal
from .navigate import Navigator
from .scene import Scene3D
from ..tools.tracers import FRAME

FRAME_MS = round(1000 * FRAME)  # tracers: about 30 frames a second
DISTANCE = 3.2                  # camera distance, in sizes of the scene
MARGIN = 1.03                   # room around the scene fitted in the view
TEXT = {False: (0.0, 0.0, 0.0), True: (0.93, 0.93, 0.93)}  # dark theme
HARDWARE = ("Vessel", "Structure")  # made transparent: no SSAA (depth)


class View3D(QtWidgets.QWidget):
    """The render window of the 3D view with its scene; orientation: the
    angles (vertical, horizontal) turned with the mouse."""

    orientation = Signal(float, float)

    def __init__(self, parent=None, image=False):
        super().__init__(parent)
        if image:                       # no OpenGL window here (a remote X
            os.environ.setdefault(      # display): EGL off screen
                "VTK_DEFAULT_OPENGL_WINDOW", "vtkEGLRenderWindow")
        import pyvista as pv
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.batch = QtWidgets.QApplication.platformName() in (
            "offscreen", "minimal")     # no window at all: no animation
        self.headless = self.batch or image
        if self.headless:               # no OpenGL in the window: an image
            self.pl = pv.Plotter(off_screen=True, window_size=(900, 700))
            self.pl.show(auto_close=False)  # renders from now on
            self.image = QtWidgets.QLabel()
            self.image.setAlignment(QtCore.Qt.AlignCenter)
            self.image.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                     QtWidgets.QSizePolicy.Ignored)
            lay.addWidget(self.image)
            if image:                   # the mouse on the image
                self.navigator = Navigator(self, self.image)
        else:
            from pyvistaqt import QtInteractor
            self.pl = QtInteractor(self, auto_update=False)
            lay.addWidget(self.pl.interactor)
            self.pl.disable()           # the camera moved by Navigator
            self.navigator = Navigator(self, self.pl.interactor)
        self.scene = Scene3D(self.pl)
        self._fitted = False            # camera placed once there is a scene
        self._extent = None             # half width, height fitted, aspect
        self.pl.hide_axes()
        self.pl.enable_lightkit()
        self.pl.enable_parallel_projection()
        self.pl.enable_depth_peeling(number_of_peels=4, occlusion_ratio=0.12)
        self.angles = (0.0, 0.0)        # vertical, horizontal (degrees)
        self.aa = None                  # anti-aliasing applied
        self.render_opts = dict(aa="ssaa", smooth=True, edl=False,
                                ssao=False)
        self.set_rendering(**self.render_opts)
        self.dark = None
        self.paused = False
        self._last = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(FRAME_MS)
        self.timer.timeout.connect(self._tick)

    # ------------------------------------------------------------ scene
    def show_snapshot(self, snap, sector=None, dark=False, zcut=None):
        """The scene of snap (a sector (phi0, phi1) in radians: built again
        over it, the camera placed again; zcut: the heights kept, None no
        limit)."""
        if dark != self.dark:           # bars and background of the theme
            self.dark = dark
            self.scene.text = TEXT[dark]
            self.scene.keys = {}
        self.pl.set_background(snap.background)
        moved = sector is not None and sector != self.scene.sector
        self.scene.update(snap, sector, zcut)
        if moved or not self._fitted:
            self.restore()
        self._animate()
        self.render()

    def set_factor(self, group, f):
        self.scene.set_factor(group, f)
        self._anti_aliasing()
        self.render()

    def set_tracers(self, **opts):
        """Tracer options (n, tail, size, speed, log); a new number or
        tail starts them again."""
        old = dict(self.scene.tracer_opts)
        self.scene.tracer_opts.update(opts)
        if any(old[k] != self.scene.tracer_opts[k] for k in
               ("n", "tail", "size", "log", "born", "fade")):
            self.scene.rebuild_tracers()
        self._animate()
        self.render()

    def set_paused(self, on):
        self.paused = bool(on)
        self._animate()

    # -------------------------------------------------------- rendering
    def _anti_aliasing(self):
        """The anti-aliasing asked for, MSAA for SSAA while the vessel or
        the structure is made transparent (SSAA spoils their depth)."""
        mode = self.render_opts["aa"]
        if mode == "ssaa" and any(self.scene.factor[g] < 0.999
                                  for g in HARDWARE):
            mode = "msaa"
        if mode == self.aa:
            return
        pl = self.pl
        try:
            if mode == "none":
                pl.disable_anti_aliasing()
            else:
                if self.aa not in (None, "none", mode):
                    pl.disable_anti_aliasing()
                pl.enable_anti_aliasing(mode)
            self.aa = mode
        except Exception:               # a context without MSAA or SSAA
            try:
                pl.disable_anti_aliasing()
                self.aa = "none"
            except Exception:
                pass

    def set_rendering(self, aa="ssaa", smooth=True, edl=False, ssao=False):
        """Anti-aliasing (none, fxaa, msaa, ssaa), smooth shading,
        eye-dome lighting, ambient occlusion."""
        pl = self.pl
        o = self.render_opts
        o["aa"] = aa
        self._anti_aliasing()
        for on, enable, disable in (
                (edl, pl.enable_eye_dome_lighting,
                 pl.disable_eye_dome_lighting),
                (ssao, pl.enable_ssao, pl.disable_ssao)):
            try:
                enable() if on else disable()
            except (AttributeError, ValueError, RuntimeError):
                pass
        if smooth != o.get("smooth") and self.scene.snap is not None:
            self.scene.smooth = smooth
            for part in ("machine", "flux"):
                self.scene.keys.pop(part, None)
            self.scene.update(self.scene.snap)
        self.scene.smooth = smooth
        o.update(aa=aa, smooth=smooth, edl=edl, ssao=ssao)
        self.render()

    def _size(self):
        """The render window as large as the widget (off screen)."""
        if self.headless:
            w, h = max(self.width(), 64), max(self.height(), 64)
            if tuple(self.pl.window_size) != (w, h):
                self.pl.window_size = [w, h]

    def render(self):
        if not self.headless:
            self.pl.render()
            return
        self._size()
        self._rescale()
        self.pl.render()
        img = np.ascontiguousarray(self.pl.screenshot(return_img=True))
        qi = QtGui.QImage(img.data, img.shape[1], img.shape[0],
                          3 * img.shape[1], QtGui.QImage.Format_RGB888)
        self.image.setPixmap(QtGui.QPixmap.fromImage(qi.copy()))

    def mark(self, point):
        """A small red ball at point (x, y, z) (the first end of a line
        drawn), or none."""
        self.pl.remove_actor("mark", render=False)
        if point is not None:
            import pyvista as pv
            self.pl.add_mesh(pv.PolyData(np.asarray(point, float)[None]),
                             name="mark", color="red", point_size=12.0,
                             render_points_as_spheres=True, pickable=False,
                             render=False)
        self.render()

    def save(self, path, scale=2):
        self.pl.screenshot(path, scale=scale)

    # ----------------------------------------------------------- camera
    def _direction(self):
        """(from the focal point to the camera, view up) of the angles:
        horizontal 0 faces the cut face at the start of the sector from
        outside it; the view up is Z, but for a camera within 3 degrees of
        the vertical the direction away from it."""
        v, h = self.angles
        az = self.scene.sector[0] - 0.5 * np.pi + np.radians(h)
        el = np.radians(v)
        d = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el),
                      np.sin(el)])
        up = (-np.cos(az), -np.sin(az), 0.0) if abs(np.cos(el)) < 0.05 \
            else (0.0, 0.0, 1.0)
        return d, up

    def set_angles(self, vertical, horizontal):
        """The view turned to the angles around the focal point, at the
        same distance (zoom and pan kept)."""
        self.angles = (float(vertical), float(horizontal))
        cam = self.pl.camera
        f = np.asarray(cam.focal_point, float)
        dist = float(np.linalg.norm(np.asarray(cam.position, float) - f))
        if not np.isfinite(dist) or dist <= 1e-9:
            self.restore()
        else:
            d, up = self._direction()
            cam.position = tuple(f + dist * d)
            cam.up = up
            self.pl.reset_camera_clipping_range()
        self.render()

    def restore_view(self):
        self.restore()
        self.render()

    def restore(self):
        """The camera at the angles looking at the centre of the cut face
        at the start of the sector, the 2D extent of the poloidal plane
        fitted in."""
        snap = self.scene.snap
        b = np.asarray(self.pl.bounds, float)
        if snap is None or not np.all(np.isfinite(b)) or b[1] <= b[0]:
            return
        span = float(np.max(b[1::2] - b[0::2]))
        p0 = self.scene.sector[0]
        r0, r1, z0, z1 = snap.box
        c, s = np.cos(p0), np.sin(p0)
        focal = np.array([0.5 * (r0 + r1) * c, 0.5 * (r0 + r1) * s,
                          0.5 * (z0 + z1)])
        d, vup = self._direction()
        cam = self.pl.camera
        cam.focal_point = tuple(focal)
        cam.position = tuple(focal + DISTANCE * span * d)
        cam.up = vup
        corners = np.array([[r * c, r * s, z] for r in (r0, r1)
                            for z in (z0, z1)]) - focal
        right = np.cross(-d, vup)
        right /= max(np.linalg.norm(right), 1e-12)
        up = np.cross(right, -d)
        w, h = np.abs(corners @ right).max(), np.abs(corners @ up).max()
        self._size()
        aspect = self._aspect()
        self._extent = (w, h, aspect)
        cam.parallel_scale = self._fit(aspect)
        self.pl.reset_camera_clipping_range()
        self._fitted = True

    def _aspect(self):
        ws = self.pl.window_size
        return max(ws[0] / max(ws[1], 1), 1e-3)

    def _fit(self, aspect):
        w, h, _ = self._extent
        return max(h, w / aspect) * MARGIN

    def _rescale(self):
        """Another shape of the window: the zoom kept, relative to the
        scene fitted in it."""
        if self._extent is None:
            return
        aspect = self._aspect()
        old = self._extent[2]
        if abs(aspect - old) < 1e-3:
            return
        cam = self.pl.camera
        cam.parallel_scale *= self._fit(aspect) / self._fit(old)
        self._extent = self._extent[:2] + (aspect,)

    # ---------------------------------------------------------- tracers
    def _animate(self):
        """The timer runs while there are tracers, not paused, shown."""
        on = self.scene.tracers is not None and not self.paused and \
            self.isVisible() and not self.batch
        if on and not self.timer.isActive():
            self._last = None
            self.timer.start()
        elif not on:
            self.timer.stop()

    def _tick(self):
        now = time.monotonic()
        dt = 0.0 if self._last is None else min(now - self._last, 0.1)
        self._last = now
        if self.scene.step(dt):
            self.render()
        else:
            self.timer.stop()

    def step(self, dt):
        """The tracers moved by dt seconds (drawn off screen)."""
        if self.scene.step(dt):
            self.render()

    def showEvent(self, event):
        super().showEvent(event)
        self._animate()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene.snap is not None:   # once the window has its size
            QtCore.QTimer.singleShot(0, lambda: (self._rescale(),
                                                 self.render()))

    def close_view(self):
        self.timer.stop()
        try:
            self.pl.close()
        except (AttributeError, RuntimeError):
            pass
