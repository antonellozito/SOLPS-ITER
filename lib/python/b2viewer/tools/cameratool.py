"""What the Camera section does: the camera picked on the plot (its
position, then the point it looks at), drawn there while the section is
open (a dot at the camera, the poloidal projection of the rays of the
corners and of the centre of the image up to the wall they meet), and
Render: the image of the quantity shown (as the chords: the plasma
quantity, else the magnitude of the vector one), each in a window of its
own. The geometry matrix of an image (the weights of the vertex values,
the path lengths in the cells) for export, and for the images of every
position of the movie slider (Export frames)."""

import json
import os
import re

import numpy as np

from ...b2plot import labels
from ...qt import QtCore, QtWidgets, Qt
from .. import catalog, theme
from ..balances.fort44 import Fort44
from ..model import split_unit
from ..output import printfig
from . import camera, cellfiles, measure
from .camerasection import CameraSection, CameraWindow

SURFACES = catalog.Quantity("ewsurf", "Eirene surface of the element",
                            "Geometry", "wall")
RINGS = 720                     # points of a toroidal ring of the wall


class CameraTool:
    """The Camera section of Tools (tools.tab its Tab2D)."""

    def __init__(self, tools):
        self.tools, self.tab = tools, tools.tab
        self.section = CameraSection(self)
        try:
            self.section.restore(json.loads(
                self.tab.settings.value("camera", "") or "{}"))
        except (ValueError, TypeError):
            pass
        self.section.hide()
        self.windows = []               # the images open (CameraWindow)
        self.window = None              # the last one
        self.open = False
        self.artists = []
        self.walls = None               # (segments, stop, kind, transp)
        self.asked = False
        self.last = None                # the image rendered last
        self.frames = None              # Export frames: the window, file

    # ------------------------------------------------------------ state
    def reset(self):
        """A new run: its walls asked for again, no image."""
        self.walls, self.asked, self.last = None, False, None
        self.artists = []
        if self.open:
            self._ask()
            self.draw()

    def set_open(self, on):
        self.open = on
        self.section.setVisible(on)
        if on:
            self._ask()
        else:
            self.arm(False)
            self.section.look.setChecked(False)
        self.draw()

    def look3d(self, on):
        """The camera seen in the 3D view (a perspective camera there,
        moved with the mouse and the keys, the section following it), or
        the 3D view as before."""
        mode = self.tab.mode3d
        if on and not mode.on():
            if not mode.menu.isEnabled():
                self.tab.status.emit("Camera: the 3D view is offered in "
                                     "Final state and Run movies")
                self.section.look.setChecked(False)
                return
            mode.menu.setCurrentIndex(1)
        view = mode.view
        if view is None:
            if on:
                self.section.look.setChecked(False)
            return
        if not getattr(self, "_linked", False):
            view.looked.connect(self._looked)
            mode.menu.currentIndexChanged.connect(
                lambda *_: mode.on() or self.section.look.setChecked(False))
            self._linked = True
        if on:
            self._look()
        else:
            view.stop_looking()

    def _look(self):
        """The 3D view through the camera of the section."""
        cam = self.section.camera()
        try:
            o, _, _, up = camera.frame(cam)
        except ValueError:
            return
        va = np.degrees(2.0 * np.arctan(np.tan(np.radians(cam.fov) / 2.0) *
                                        cam.ny / cam.nx))
        self.tab.mode3d.view.look_through(o, camera.xyz(*cam.target), up,
                                          va)

    def _looked(self):
        """The camera moved in the 3D view: the section follows it (the
        point it looks at the focal point, the roll from the view up, the
        field of view from the view angle and the pixels)."""
        view = self.tab.mode3d.view
        if view is None or not view.looking:
            return
        p, f, u, va = view.pose()
        cam = self.section.camera()

        def rzphi(x):
            return (float(np.hypot(x[0], x[1])), float(x[2]),
                    float(np.degrees(np.arctan2(x[1], x[0]))))
        d = f - p
        d = d / max(np.linalg.norm(d), 1e-300)
        ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.999 else \
            np.array([1.0, 0.0, 0.0])
        right = np.cross(d, ref)
        right /= np.linalg.norm(right)
        up0 = np.cross(right, d)
        roll = float(np.degrees(np.arctan2(-np.dot(u, right),
                                           np.dot(u, up0))))
        fov = float(np.degrees(2.0 * np.arctan(np.tan(np.radians(va) / 2.0)
                                               * cam.nx / cam.ny)))
        self.section.set_camera(rzphi(p), rzphi(f), roll, fov)
        self._syncing = True
        try:
            self.moved()
        finally:
            self._syncing = False

    def arm(self, on):
        """Pick the position and the target with the next two clicks."""
        bar = self.tools.bar
        if on and self.tab.mode3d.on():
            self.tab.status.emit("Camera: pick on the 2D plot (View 2D)")
            on = False
        if on:
            bar.set_mode("camera")
        elif bar.mode == "camera":
            bar.set_mode(None)
        self.section.set_armed(on)

    def modes(self):
        self.section.set_armed(self.tools.bar.mode == "camera")

    def picked(self, pts):
        self.tools.bar._draw([])
        if len(pts) < 2:
            return
        self.section.set_points(pts[0], pts[1])
        self.arm(False)
        self.moved()
        self.tab.status.emit("Camera at R = %.3f m, Z = %.3f m, looking at "
                             "R = %.3f m, Z = %.3f m" % (tuple(pts[0]) +
                                                         tuple(pts[1])))

    def moved(self):
        """The camera changed: kept in the settings, drawn again (and the
        3D view through it moved, when it is seen there)."""
        self.tab.settings.setValue("camera", json.dumps(
            self.section.settings()))
        self.draw()
        if self.section.look.isChecked() and \
                not getattr(self, "_syncing", False) and \
                self.tab.mode3d.view is not None:
            self._look()

    # ------------------------------------------------------------ walls
    def _ask(self):
        """The EIRENE surface of each wall element from b2plot (ewsurf),
        once per run."""
        if self.walls is not None or self.asked or self.tab.run is None:
            return
        self.asked = True
        self.tab.request.emit(("camera", SURFACES, (), None))

    def deliver(self, data):
        """ewsurf arrived: the stopping mask of the elements with the
        types of the surfaces (fort.44 isrftype)."""
        run = self.tab.run
        seg = np.asarray(run.layers.get("wall", np.zeros((0, 4))), float)
        if data is None or len(data.values[0]) != len(seg):
            self.walls = (seg, np.ones(len(seg), bool), np.ones(len(seg),
                                                                int),
                          np.zeros((len(seg), 2)))
            self.tab.status.emit("Camera: no EIRENE surfaces of the wall "
                                 "elements: every element stops the rays")
        else:
            path = cellfiles.find(run.rundir, "fort.44")
            f = Fort44(path) if path else None
            types = f.block("isrftype").astype(int) if f is not None and \
                f.has("isrftype") else np.ones(0, int)
            srf = np.asarray(data.values[0]).astype(int)
            stop, kind = camera.classify(srf, types, seg)
            nlim = f.nlim if f is not None else 0
            table = transmissions(run.rundir, nlim, len(types))
            trans = np.where(((srf > 0) & (srf <= len(table)))[:, None],
                             table[np.clip(srf - 1, 0, max(len(table) - 1,
                                                           0))], 0.0) \
                if len(table) else np.zeros((len(seg), 2))
            trans[kind < 1] = 0.0       # EIRENE: only for ILIIN > 0
            self.walls = (seg, stop, kind, trans)
        self.draw()

    # ------------------------------------------------------------ drawing
    def draw(self):
        """The camera and its edge and centre rays on the plot."""
        for a in self.artists:
            if a.axes is not None:
                a.remove()
        self.artists = []
        tab = self.tab
        if self.open and tab.run is not None:
            ax = tab.plot.ax
            sec = self.section
            colour = sec.colour.color()
            cam = sec.camera()
            for r, z in self._rays(cam):
                self.artists += ax.plot(r, z, color=colour, linewidth=1.0,
                                        linestyle="--", zorder=8)
            self.artists += ax.plot([cam.position[0]], [cam.position[1]],
                                    "o", color=colour, markersize=6,
                                    zorder=9)
            self.artists += ax.plot([cam.target[0]], [cam.target[1]], "+",
                                    color=colour, markersize=9, zorder=9)
        tab.canvas.draw_idle()
        tab.mode3d.follow()

    def chords3d(self):
        """The rays of the corners and of the centre for the 3D view, as
        chords: (number, start, end, look), ends (R, Z, phi in radians)."""
        cam = self.section.camera()
        try:
            o = camera.xyz(*cam.position)
            d = camera.directions(cam)
        except ValueError:
            return []
        picks = [d[0, 0], d[0, -1], d[-1, -1], d[-1, 0],
                 d[cam.ny // 2, cam.nx // 2]]
        seg, stop = self.opaque()
        t, _ = camera.hits(o, np.array(picks), seg[stop])
        start = (cam.position[0], cam.position[1],
                 float(np.radians(cam.position[2])))
        look = (self.section.colour.color(), 0.4, "--", False)
        out = []
        for k, (di, ti) in enumerate(zip(picks, t), 1):
            p = o + (ti if np.isfinite(ti) else 6.0) * di
            out.append((k, start, (float(np.hypot(p[0], p[1])),
                                   float(p[2]),
                                   float(np.arctan2(p[1], p[0]))), look))
        return out

    def opaque(self):
        """Segments of the wall elements and the mask of the opaque ones
        (stopping, not semi-transparent)."""
        if not self.walls:
            return np.zeros((0, 4)), np.zeros(0, bool)
        seg, stop, _, trans = self.walls
        return seg, stop & (trans.max(axis=1) == 0)

    def _rays(self, cam):
        """(R, Z) along the rays of the corners and of the centre, up to
        their wall (6 m without one)."""
        try:
            o = camera.xyz(*cam.position)
            d = camera.directions(cam)
        except ValueError:
            return []
        picks = [d[0, 0], d[0, -1], d[-1, -1], d[-1, 0],
                 d[cam.ny // 2, cam.nx // 2]]
        seg, stop = self.opaque()
        t, _ = camera.hits(o, np.array(picks), seg[stop])
        out = []
        for di, ti in zip(picks, t):
            s = np.linspace(0.0, ti if np.isfinite(ti) else 6.0, 300)
            p = o + s[:, None] * di
            out.append((np.hypot(p[:, 0], p[:, 1]), p[:, 2]))
        return out

    # ------------------------------------------------------------ render
    def _target(self):
        """(data, Quantity, column, data as sent) of the quantity shown if
        it can be imaged (of the B2.5 cells, the walls known), else None
        (the reason in the status)."""
        tab = self.tab
        if tab.run is None:
            return None
        m = self.tools._measured()
        if m is None:
            tab.status.emit("Camera: no quantity shown")
            return None
        data, q, col, _, sent = m
        if data.location != "cells":
            tab.status.emit("Camera: a quantity of the B2.5 cells is needed")
            return None
        if self.walls is None:
            self._ask()
            tab.status.emit("Camera: the wall elements are still loading")
            return None
        return data, q, col, sent

    def _box(self, data, col):
        tri, comps = measure._grid(self.tab.plot, data, col)
        return tri, comps, (tri.x.min(), tri.x.max(), tri.y.min(),
                            tri.y.max())

    def render(self):
        """Render: the image of the quantity shown with the camera of the
        section, in a new window (the others stay)."""
        target = self._target()
        if target is None:
            return
        data, q, col, sent = target
        sec, tab = self.section, self.tab
        cam = sec.camera()
        seg, stop, _, trans = self.walls
        tri, comps = measure._grid(tab.plot, data, col)
        box = (tri.x.min(), tri.x.max(), tri.y.min(), tri.y.max())
        st = dict(camera=cam, per_sr=sec.per_sr.isChecked(),
                  step=sec.step.value() * 1e-3,
                  samples=sec.samples.currentData(), tri=tri, box=box,
                  walls=self.walls, run=tab.run)
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            values, dist, elem = camera.image(
                cam, seg, stop, lambda r, z: measure.at_points(
                    tab.plot, data, r, z, col), per_sr=st["per_sr"],
                step=st["step"], box=box, trans=trans, samples=st["samples"])
            edges = self._edges(cam, dist)
        except ValueError as err:
            tab.status.emit("Camera: %s" % err)
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        name = self.tools._name(q, sent)
        bright = self._unit(q, data, st["per_sr"])
        density = _density(q.description)   # photons or W m^-3: realistic
        spectrum = self.tools.spectrum
        rows = spectrum.lines() if density and spectrum.allowed() else []
        self.last = last = dict(st, values=values, distance=dist,
                                element=elem, edges=edges, unit=bright,
                                name=name,
                                light=dict(rows=rows, parts=list(
                                    spectrum.parts), photons=density ==
                                    "photons") if rows else None)
        n, seen = last["samples"], np.isfinite(dist)
        sec.text.setText(
            "%s: %d × %d pixels%s, maximum %.4g %s, %d%% of the rays end on "
            "a wall (%.2f to %.2f m)" % (
                name, cam.nx, cam.ny, "" if n == 1 else
                " of %d × %d rays" % (n, n), np.nanmax(values),
                measure.html_unit(bright), 100 * seen.mean(),
                dist[seen].min() if seen.any() else np.nan,
                dist[seen].max() if seen.any() else np.nan))
        before = self.window if self.window in self.windows else None
        w = CameraWindow(self, last, before)
        self.windows.append(w)
        self.window = w
        w.show()
        if before is not None:          # beside the last one
            w.move(before.pos() + QtCore.QPoint(30, 30))
        w.raise_()

    @staticmethod
    def _unit(q, data, per_sr):
        """Unit of an image: that of the quantity (its description, else
        the label of its field: quantities with choices have none there)
        times m, per steradian."""
        unit = labels.any_to_plain(split_unit(q.description)[1] or
                                   split_unit(data.label)[1])
        return measure.times_m(unit, 1) + (" sr^{-1}" if per_sr else "")

    @staticmethod
    def colour_modes(last):
        """The colour modes of an image: the colour map and transparency;
        true colour and filtered camera with the lines of a light quantity
        (its rate density)."""
        return ["map", "alpha"] + (["colour", "filter"] if last["light"]
                                   else [])

    def light(self, last):
        """The lines of the light quantity of an image: rows (wavelength,
        label, tokens), photons (else W), got (lines here); once all are
        here also wl (A), labels and V (vertex values, a row per line);
        None for another quantity."""
        info = last.get("light")
        if not info or "V" in info:
            return info
        fields = self.tools.spectrum.fields
        info["got"] = sum(t in fields for _, _, t in info["rows"])
        if info["got"] < len(info["rows"]):
            return info
        ok = [(r, fields[r[2]]) for r in info["rows"]
              if fields[r[2]] is not None]
        info["ok"] = [fields[r[2]] is not None for r in info["rows"]]
        info["wl"] = np.array([r[0] for r, _ in ok], float)
        info["labels"] = [r[1] for r, _ in ok]
        info["V"] = np.array([np.asarray(f.vertex[0], float) for _, f in ok])
        return info

    def vessel(self, last):
        """The vessel structures seen by the camera of an image (RGB,
        rendered once), the background of its transparency mode."""
        if "vessel" not in last:
            from ..plot3d import vessel
            from ..plot3d.data import background
            tab = self.tab
            QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                geo = tab.mode3d.data._build_geometry(last["run"], tab.plot)
                seg, stop, _, _ = last["walls"]     # those the rays stop on
                last["vessel"] = vessel.image(last["camera"], geo,
                                              background()[:3], seg[stop])
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
        return last["vessel"]

    def closed(self, window):
        """A camera window closed."""
        if window in self.windows:
            self.windows.remove(window)
        if self.window is window:
            self.window = self.windows[-1] if self.windows else None
        if self.frames is not None and self.frames[0] is window:
            self.frames = None

    # ------------------------------------------------- the geometry matrix
    def matrix(self, last):
        """The geometry matrix of an image (camera.matrix for its camera
        and the cells it was rendered for: the weights of the vertices,
        the path lengths in the cells, numbered as b2plot from 1), built
        once."""
        if "matrix" not in last:
            g, tri = last["run"].geometry, last["tri"]
            seg, stop, _, trans = last["walls"]
            QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                nodes, cells = camera.matrix(
                    last["camera"], seg, stop, tri, g.trifinder(tri),
                    per_sr=last["per_sr"], step=last["step"],
                    box=last["box"], trans=trans, samples=last["samples"],
                    groups=g.cells[g.tri_cell])
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
            last["matrix"] = dict(nodes=nodes, cells=cells)
        return last["matrix"]

    def snapshot(self):
        """While Export frames draws the positions of the movie: the image
        of the frame drawn with the camera of its window (from the matrix
        of the image for a scalar quantity on the same cells, else
        integrated again), else None."""
        if self.frames is None:
            return None
        m = self.tools._measured()
        if m is None or m[0].location != "cells":
            return None
        data, q, col, _, sent = m
        last = self.frames[0].last
        tri, comps = measure._grid(self.tab.plot, data, col)
        cam = last["camera"]
        same = (tri.mask is None and last["tri"].mask is None) or (
            tri.mask is not None and last["tri"].mask is not None and
            np.array_equal(tri.mask, last["tri"].mask))
        if len(comps) == 1 and same:
            values = camera.apply(self.matrix(last)["nodes"], comps[0],
                                  cam.nx * cam.ny).reshape(cam.ny, cam.nx)
        else:
            seg, stop, _, trans = last["walls"]
            values = camera.image(
                cam, seg, stop, lambda r, z: measure.at_points(
                    self.tab.plot, data, r, z, col), per_sr=last["per_sr"],
                step=last["step"], box=(tri.x.min(), tri.x.max(),
                                        tri.y.min(), tri.y.max()),
                trans=trans, samples=last["samples"])[0]
        return dict(values=values, name=self.tools._name(q, sent),
                    unit=self._unit(q, data, last["per_sr"]))

    def _edges(self, cam, dist):
        """Lines in pixel coordinates of the wall seen: toroidal rings of
        its corners (and loose ends) and the wall cut every 30 degrees,
        the points behind the wall seen at their pixel left out (within
        two pixels)."""
        seg, stop = self.walls[:2]
        if not len(seg):
            return []
        o, f, right, up = camera.frame(cam)
        w = np.tan(np.radians(cam.fov) / 2.0)
        h = w * cam.ny / cam.nx
        lines = [camera.xyz(r, z, np.linspace(0.0, 360.0, RINGS + 1))
                 for r, z in corners(seg[stop])]
        for a in np.arange(0.0, 360.0, 30.0):
            for s in seg[stop]:
                lines.append(camera.xyz(np.linspace(s[0], s[2], 8),
                                        np.linspace(s[1], s[3], 8), a))
        tol = 2.0 * np.radians(cam.fov) / cam.nx    # two pixels (rad)
        out = []
        for p in lines:
            q = p - o
            depth = q @ f
            with np.errstate(invalid="ignore", divide="ignore"):
                x = (q @ right) / np.where(depth > 0, depth, np.nan) / w
                y = (q @ up) / np.where(depth > 0, depth, np.nan) / h
            px = (x + 1.0) * cam.nx / 2.0
            py = (1.0 - y) * cam.ny / 2.0
            inside = (depth > 0) & (px >= 0) & (px < cam.nx) & (py >= 0) & \
                (py < cam.ny)
            ok = np.zeros(len(p), bool)
            j = np.clip(np.nan_to_num(px).astype(int), 0, cam.nx - 1)
            i = np.clip(np.nan_to_num(py).astype(int), 0, cam.ny - 1)
            reach = np.linalg.norm(q, axis=1)
            seen = dist[i[inside], j[inside]]
            ok[inside] = reach[inside] <= np.where(np.isfinite(seen), seen,
                                                   np.inf) * (1.0 + tol) + \
                reach[inside] * tol
            if ok.sum() > 1:
                out.append((np.where(ok, px, np.nan), np.where(ok, py,
                                                               np.nan)))
        return out

    # ------------------------------------------------------------ output
    def _file(self, window, title, ext, filters):
        """A file name (in the folder of the last export), or None."""
        settings = self.tab.settings
        folder = settings.value("export_dir", os.getcwd())
        name = re.sub(r"[^A-Za-z0-9_.+-]+", "_", "camera " + window.last[
            "name"]).strip("_") or "camera"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            window, title, os.path.join(folder, name + "." + ext), filters)
        if path:
            settings.setValue("export_dir", os.path.dirname(path))
        return path or None

    def save(self, window, path=None, options=None):
        """Save image: the image of a window as Save plot does (the options
        and the file asked unless given); the path or None."""
        if options is None:
            dlg = printfig.PrintDialog(theme.is_dark(), window, "Save image")
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return None
            options = dlg.options()
        fmt = options["format"]
        if path is None:
            path = self._file(window, "Save image", fmt,
                              printfig.FILTERS[fmt])
            if path is None:
                return None
        path = printfig.with_suffix(path, fmt)
        dark = theme.is_dark()
        try:
            theme.set_dark(options.get("theme", theme.name().lower()) ==
                           "dark")
            window.draw()
            printfig.save(window.figure, path, options)
        except (OSError, ValueError, RuntimeError) as err:
            self.tab.status.emit("Cannot write %s: %s" % (path, err))
            return None
        finally:                # the image in the theme of the GUI again
            theme.set_dark(dark)
            window.draw()
        self.tab.status.emit("Camera image saved to %s" % path)
        return path

    def export(self, window, path=None):
        path = path or self._file(window, "Export camera image", "csv",
                                  "CSV (*.csv);;netCDF (*.nc)")
        if path:
            write(path, window.last)
            self.tab.status.emit("Camera image written to %s" % path)
        return path

    def export_matrix(self, window, path=None):
        """Export matrix: the geometry matrix of the image of a window as
        netCDF (the file asked unless given); the path or None."""
        if path is None:
            path = self._file(window, "Export geometry matrix", "nc",
                              "netCDF (*.nc)")
            if path is None:
                return None
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            mat = self.matrix(window.last)
            write_matrix(path, window.last, mat,
                         window.last["run"].geometry)
        except (OSError, ImportError, RuntimeError) as err:
            self.tab.status.emit("Cannot write %s: %s" % (path, err))
            return None
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.tab.status.emit(
            "Geometry matrix written to %s (%d vertex weights, %d path "
            "lengths in the cells)" % (path, len(mat["nodes"][2]),
                                        len(mat["cells"][2])))
        return path

    def export_frames(self, window, path=None):
        """Export frames: the image with the camera of a window of every
        position of the movie slider (the quantity shown in Run movies),
        as netCDF with the times (the file asked unless given); the path,
        or None."""
        tab, tb = self.tab, self.tab.time_box
        if window.last["run"] is not tab.run:
            tab.status.emit("Export frames: the run of this image is no "
                            "longer shown")
            return None
        if not tb.movie():
            tab.status.emit("Export frames: the frames of the Run movies "
                            "tab (open it first)")
            return None
        if path is None:
            path = self._file(window, "Export frames", "nc",
                              "netCDF (*.nc)")
            if path is None:
                return None
        mv = tab.movie
        mv.images, mv.snaps, mv.key = {}, {}, None  # each drawn again
        self.frames = (window, path)
        ready = mv.prepare(done=self._frames_done)
        if ready is True:
            self._frames_done()
        elif ready is False:
            self.frames = None
            return None
        return path

    def _frames_done(self):
        if self.frames is None:
            return
        (window, path), self.frames = self.frames, None
        tab, tb = self.tab, self.tab.time_box
        ps = tb.positions()
        snaps = [(self.tab.movie.snaps.get(p) or (None,) * 4)[3]
                 for p in ps]
        if any(s is None for s in snaps):
            tab.status.emit("Export frames: the camera image of a position "
                            "is missing")
            return
        try:
            write_frames(path, window.last, snaps,
                         [tb.time_at(p) for p in ps])
        except (OSError, ImportError, RuntimeError) as err:
            tab.status.emit("Cannot write %s: %s" % (path, err))
            return
        tab.status.emit("Camera frames written to %s (%d positions)" % (
            path, len(ps)))

    def apply_theme(self):
        self.draw()
        for w in self.windows:
            w.apply_theme()


def _density(description):
    """"photons" or "W" when the unit of a quantity (its description) is
    a photon or power density (per m^3), else None."""
    unit = re.sub(r"[\s.]+", " ", re.sub(r"[{}]", "", split_unit(
        description)[1] or "")).strip()
    return {"photons m^-3 s^-1": "photons", "W m^-3": "W"}.get(unit)


def transmissions(rundir, nlim, nsurf):
    """(nsurf, 2) TRANSP of the EIRENE surfaces (additional ones 1 to
    nlim, then the non-default standard ones), as EIRENE sets them: from
    the surface model of the surface (REFLECTION_MODELS), else its card;
    from the side of its normal and from the other."""
    out = np.zeros((nsurf, 2))
    path = cellfiles.find(rundir, "eirene.input.json")
    if not path:
        return out
    with open(path) as fh:
        inp = json.load(fh)
    models = {str(m.get("NAME", "")).strip(): m.get("TRANSP", [0, 0])
              for m in inp.get("REFLECTION_MODELS", {}).get("SURFMODS", [])}
    add = inp.get("ADDITIONAL_SURFACES", {})
    surfs = add.get("SURFACES")
    if surfs is None and add.get("INCLUDE"):
        inc = cellfiles.find(rundir, str(add["INCLUDE"]).strip())
        if inc:
            with open(inc) as fh:
                surfs = json.load(fh).get("ADDITIONAL_SURFACES", {}).get(
                    "SURFACES")
    std = inp.get("NONDEF_STD_SURFACES", {}).get("SURFACES", [])
    for k, sf in list(enumerate(surfs or [])) + [
            (nlim + j, sf) for j, sf in enumerate(std)]:
        if k >= nsurf:
            continue
        name = str(sf.get("SURFMOD", "")).strip()
        tr = models.get(name, sf.get("TRANSP", [0, 0])) if name else \
            sf.get("TRANSP", [0, 0])
        out[k] = [float(tr[0]), float(tr[1])] if tr else 0.0
    return out


def corners(seg, angle=15.0):
    """(R, Z) of the wall polylines where they turn by more than angle
    degrees, and their loose ends."""
    seg = np.asarray(seg, float).reshape(-1, 4)
    ends = {}
    for k, s in enumerate(seg):
        for e, a, b in ((0, s[:2], s[2:]), (1, s[2:], s[:2])):
            ends.setdefault(tuple(np.round(a, 6)), []).append(b - a)
    out = []
    for p, dirs in ends.items():
        if len(dirs) != 2:
            out.append(p)
            continue
        u, v = dirs[0], dirs[1]
        c = -np.dot(u, v) / max(np.linalg.norm(u) * np.linalg.norm(v),
                                1e-300)
        if np.degrees(np.arccos(np.clip(c, -1.0, 1.0))) > angle:
            out.append(p)
    return out


def _head(last):
    """Lines describing the camera of an image and how it was taken."""
    cam = last["camera"]
    head = ["camera position R, Z (m), phi (deg): %g %g %g" % cam.position,
            "looks at R, Z (m), phi (deg): %g %g %g" % cam.target,
            "roll %g deg, field of view %g deg, %d x %d pixels" % (
                cam.roll, cam.fov, cam.nx, cam.ny),
            "steps of %g mm along the rays%s" % (
                1e3 * last["step"], "" if last["samples"] == 1 else
                ", %d x %d rays per pixel, averaged" % (last["samples"],
                                                        last["samples"])),
            "quantity: %s" % last["name"], "unit: %s" % last["unit"]]
    return head


def write(path, last):
    """The image (value, distance to the wall, wall element seen, per
    pixel) and the camera as CSV (a header of comments) or netCDF."""
    head = _head(last)
    v, d, e = last["values"], last["distance"], last["element"]
    if os.path.splitext(path)[1].lower() == ".nc":
        import netCDF4
        with netCDF4.Dataset(path, "w") as nc:
            nc.createDimension("row", v.shape[0])
            nc.createDimension("column", v.shape[1])
            for name, a, unit in (("value", v, last["unit"]),
                                  ("distance", d, "m"),
                                  ("element", e, "")):
                var = nc.createVariable(name, "i4" if name == "element"
                                        else "f8", ("row", "column"))
                var[:] = np.where(np.isfinite(a), a, -1) if name == \
                    "distance" else a
                var.units = unit
            nc.description = "; ".join(head)
        return
    i, j = np.indices(v.shape)
    with open(path, "w") as fh:
        for line in head:
            fh.write("# %s\n" % line)
        fh.write("row,column,value,distance_m,wall_element\n")
        for a, b, c, dd, ee in zip(i.ravel(), j.ravel(), v.ravel(),
                                   d.ravel(), e.ravel()):
            fh.write("%d,%d,%.8g,%s,%d\n" % (a, b, c, "%.6g" % dd if
                                             np.isfinite(dd) else "", ee))


def write_matrix(path, last, mat, grid):
    """The geometry matrix of an image as netCDF: per entry the pixel (row,
    column), the vertex (from 1, as b2plot) and its weight, the image the
    sum of weight x vertex value per pixel; per entry the pixel, the B2.5
    cell (from 1) and the path length of the rays of the pixel in it."""
    import netCDF4
    cam = last["camera"]
    unit = "m sr-1" if last["per_sr"] else "m"
    with netCDF4.Dataset(path, "w") as nc:
        nc.createDimension("vertex", len(grid.vx))
        for name, a in (("vertex_r", grid.vx[:, 0]),
                        ("vertex_z", grid.vx[:, 1])):
            var = nc.createVariable(name, "f8", ("vertex",))
            var[:] = a
            var.units = "m"
        for part, (pix, col, val), what, plus in (
                ("weight", mat["nodes"], "vertex", 1),
                ("length", mat["cells"], "cell", 0)):
            dim = part + "_entry"
            nc.createDimension(dim, len(val))
            for name, a, typ, u in (
                    (part + "_row", pix // cam.nx, "i4", ""),
                    (part + "_column", pix % cam.nx, "i4", ""),
                    (part + "_" + what, col + plus, "i4", ""),
                    (part, val, "f8", unit)):
                var = nc.createVariable(name, typ, (dim,))
                var[:] = a
                var.units = u
        nc.rows, nc.columns = cam.ny, cam.nx
        nc.description = "; ".join(_head(last)[:4]) + (
            "; per steradian" if last["per_sr"] else "")
        nc.weight_use = (
            "image[row, column] = sum over the weight entries of the pixel "
            "of weight x the value at weight_vertex (vertex numbers from 1, "
            "their R and Z in vertex_r, vertex_z): the image of b2viewer "
            "from the vertex values b2plot interpolates from the cells")
        nc.length_use = (
            "length: path length of the rays of the pixel in the B2.5 cell "
            "length_cell (cell numbers from 1, as b2plot): the image of a "
            "field constant in each cell is the sum of length x the cell "
            "value")


def write_frames(path, last, images, times):
    """The images of the positions of a movie (images: values, name, unit)
    with the camera of the image last and their times as netCDF."""
    import netCDF4
    cam = last["camera"]
    with netCDF4.Dataset(path, "w") as nc:
        nc.createDimension("frame", len(images))
        nc.createDimension("row", cam.ny)
        nc.createDimension("column", cam.nx)
        t = nc.createVariable("time", "f8", ("frame",))
        t[:] = [np.nan if x is None else x for x in times]
        t.units = "s"
        v = nc.createVariable("value", "f8", ("frame", "row", "column"))
        v[:] = np.stack([x["values"] for x in images])
        v.units = images[0]["unit"]
        d = nc.createVariable("distance", "f8", ("row", "column"))
        d[:] = np.where(np.isfinite(last["distance"]), last["distance"], -1)
        d.units = "m"
        nc.description = "; ".join(_head(dict(last, name=images[0]["name"],
                                              unit=images[0]["unit"])))
