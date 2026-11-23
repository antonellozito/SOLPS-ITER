"""The 3D view of the 2D tab: the View menu of the Plot group (2D or 3D;
3D in Final state and Run movies only), the view in the place of the 2D
plot and of the plot commands, its options in the right column (those of
the 2D plot alone hidden, the grid layers greyed out), the scene following
what the tab shows (the 2D plot is still drawn, hidden): one of the
plasma, vector and wall quantities at a time, the last one chosen."""

import importlib.util
import os

import numpy as np

from ...qt import QtCore, QtWidgets, opengl_composition
from .. import theme
from ..panels.layers import left_form
from ..panels.view3d import Options3D
from .data import Data3D
from ..tools import births

NEED = (("pyvista", "0.43"), ("pyvistaqt", "0.11"))
FOLLOW_MS = 120                 # the scene after the 2D plot settles
GRIDS = ("grid", "eirene")      # layers not drawn in 3D
SECTOR_MS = 600                 # a new sector after its spin boxes settle


class Mode3D(QtCore.QObject):
    """The 3D view of tab, shown with View 3D (and enabled)."""

    def __init__(self, tab):
        super().__init__(tab)
        self.tab = tab
        self.menu = QtWidgets.QComboBox()   # View: 2D or 3D
        self.menu.addItems(["2D", "3D"])
        self.menu.setToolTip(
            "3D: the plasma, vector and wall quantities and the layers in "
            "three dimensions, in the place of the 2D plot (Final state, "
            "Run movies)")
        self.menu.currentIndexChanged.connect(lambda *_: self.apply())
        self.box = QtWidgets.QGroupBox("Plot")
        left_form(self.box).addRow("View", self.menu)
        if importlib.util.find_spec("pyvistaqt") is not None and \
                QtWidgets.QApplication.platformName() not in ("offscreen",
                                                              "minimal"):
            opengl_composition(tab)     # no flash when the view comes
        self.options = Options3D()
        self.options.hide()
        self.data = Data3D(self)
        self.data.request.connect(tab.request.emit)
        self.data.status.connect(tab.status.emit)
        self.data.changed.connect(self.follow)
        self.view = None
        self.last = None                # plasma, vector, wall: chosen last
        self.band_run = None            # the run of the band of rho_p
        self._missing = False           # no line for the tracers, said
        self.drawing = False            # the 2D plot shown to draw a line
        self.ends = None                # the ends clicked on the 3D view
        self.fractions = list(tab.columns.fractions)   # of the 2D plot
        self._follow = self._timer(FOLLOW_MS, self._update)
        self._sector = self._timer(SECTOR_MS, self._update)
        o = self.options
        o.view.changed.connect(self._sector.start)
        o.view.angles.connect(lambda v, h: self._call("set_angles", v, h))
        o.view.restore.connect(lambda: self._call("restore_view"))
        o.view.save.connect(self._save)
        o.groups.factor.connect(lambda g, f: self._call("set_factor", g, f))
        o.groups.band.connect(self.follow)
        o.tracers.changed.connect(self._tracers)
        o.tracers.draw.connect(self.draw_line)
        o.tracers.draw2d.connect(self.draw_line_2d)
        tab.tools.bar.changed.connect(self._line_drawn)
        o.tracers.pause.toggled.connect(
            lambda on: self._call("set_paused", on))
        o.render.changed.connect(
            lambda: self._call("set_rendering", **o.render.options()))

    def _timer(self, ms, slot):
        t = QtCore.QTimer(self)
        t.setSingleShot(True)
        t.setInterval(ms)
        t.timeout.connect(slot)
        return t

    def _call(self, name, *args, **kw):
        if self.view is not None:
            getattr(self.view, name)(*args, **kw)

    def on(self):
        return self.menu.currentIndex() == 1 and self.menu.isEnabled()

    # ------------------------------------------------------------- mode
    def set_allowed(self, ok):
        """The View menu enabled (Final state, Run movies) or not; the 2D
        plot shown while it is not."""
        self.menu.setEnabled(bool(ok))
        self.apply()

    def apply(self):
        """The 3D view or the 2D plot in the middle, their options."""
        on = self.on()
        if on and self.view is None and not self._create():
            return
        tab = self.tab
        f = list(self.fractions)
        if on:                          # the plot commands: no use
            f[1], f[2] = f[1] + f[2], 0.0
        tab.columns.set_fractions(f)
        tab.commands.setVisible(not on)
        if not on:
            self.drawing = False
            self.options.tracers.drawing(False, in2d=True)
            self._stop_picking()
        tab.canvas.setVisible(not on or self.drawing)
        if self.view is not None:
            self.view.setVisible(on and not self.drawing)
        tab.masks.setVisible(not on)
        tab.layers.set_blocked(GRIDS if on else (), "Not drawn in the 3D "
                               "view")
        tab.quantity.set_3d(on)
        self.options.setVisible(on)
        tools = tab.tools               # chords typed, not drawn
        if on and tools.bar.mode is not None:
            tools.bar.set_mode(None)
        tools.chords_section.draw.setEnabled(not on)
        tab._measures()                 # no statistics, no overlay
        if on:
            self.keep_one()
            self.follow()

    # ------------------------------------------------- one quantity in 3D
    def _plotted(self):
        t = self.tab
        return [k for k, q in (("plasma", t.wanted), ("vector",
                                                      t.vector_wanted),
                               ("wall", t.wall_wanted)) if q is not None]

    def chosen(self, kind):
        """A quantity of kind chosen: in the 3D view, the others go."""
        self.last = kind
        if self.on():
            self.keep_one()

    def keep_one(self):
        """Of the plasma, vector and wall quantities plotted, only the last
        one chosen (else the first) kept."""
        plotted = self._plotted()
        if len(plotted) < 2:
            return
        keep = self.last if self.last in plotted else plotted[0]
        t = self.tab
        for kind in plotted:
            if kind == keep:
                continue
            if kind == "plasma":
                t.quantity.unselect()
                t._chosen(None)
            else:
                t.quantity.unselect_extra(kind)
                getattr(t, "_%s_chosen" % kind)(None)

    def _create(self):
        """The view, once (PyVista needed)."""
        from ... import requirements
        missing = requirements.problems(False, list(NEED))
        err = None
        if not missing:
            try:
                from .view import View3D
                self.view = View3D()
            except Exception as e:      # no OpenGL, a broken VTK
                err = str(e)
        if self.view is None:
            self.tab.status.emit(
                "3D view: needs %s; run $SOLPSTOP/scripts/install_python"
                % ", ".join(missing) if missing else
                "3D view: cannot open (%s)" % err)
            self.menu.blockSignals(True)
            self.menu.setCurrentIndex(0)
            self.menu.blockSignals(False)
            return False
        self.tab.centre_layout.addWidget(self.view, 1)
        self.view.orientation.connect(self.options.view.show_angles)
        o = self.options
        self.view.angles = o.view.angle_values()
        self.view.set_rendering(**o.render.options())
        self.view.scene.tracer_opts.update(o.tracers.options())
        self.view.paused = o.tracers.pause.isChecked()
        for g, s in o.groups.sliders.items():
            self.view.scene.factor[g] = s.value() / 100.0
        return True

    def reset(self):
        """Another run: nothing of the one before kept."""
        self.data.reset()
        if self.view is not None:
            self.view.scene.keys = {}
            self.view._fitted = False

    # ------------------------------------------------------------ scene
    def rho_band(self):
        """(min, max) rho_p of the plasma quantity, None without rzpsi.dat;
        at first those of the B2.5 grid."""
        run = self.tab.run
        if run is None or run.psimap is None:
            return None
        g = self.options.groups
        if self.band_run is not run:
            self.band_run = run
            rho = np.asarray(run.psimap.rhop(run.geometry.vx[:, 0],
                                             run.geometry.vx[:, 1]), float)
            rho = rho[np.isfinite(rho)]
            if rho.size:
                g.set_band(np.floor(rho.min() * 1e3) / 1e3,
                           np.ceil(rho.max() * 1e3) / 1e3)
        return g.band_values()

    def follow(self):
        """What the tab shows changed: the scene follows (soon)."""
        if self.on():
            self._follow.start()

    def sector(self):
        a, b = self.options.view.sector()
        if b - a >= 360:
            return (0.0, 2.0 * np.pi)
        return (float(np.radians(a)), float(np.radians(b)))

    def _update(self):
        if not self.on() or self.view is None or self.tab.run is None:
            return
        try:
            self.draw()
        except Exception as err:        # a bad case must not end the GUI
            self.tab.status.emit("3D view: cannot draw (%s)" % err)

    def draw(self):
        """The scene of what the tab shows now."""
        tab = self.tab
        self.data.want(tab)
        snap = self.data.snapshot(tab)
        z0, z1 = self._grid_heights()
        self.view.show_snapshot(snap, self.sector(), theme.is_dark(),
                                self.options.view.heights(z0, z1))
        lay = snap.layers
        shown = {"Vessel", "Structure"}
        if lay["separatrices"]["visible"] and snap.separatrices or \
                lay["flux"]["visible"] and snap.flux:
            shown.add("Flux surfaces")
        for g, part in (("Plasma quantity", snap.plasma),
                        ("Wall quantity", snap.wall),
                        ("Tracers", snap.vector),
                        ("Chords", snap.chords or None)):
            if part is not None:
                shown.add(g)
        self.options.groups.show_groups(shown, snap.plasma is not None and
                                        tab.run.psimap is not None)
        self.options.tracers.setVisible(snap.vector is not None)
        self._no_line()

    def _tracers(self):
        self._call("set_tracers", **self.options.tracers.options())
        if self.options.tracers.born.currentData() == "line" and len(
                self.tab.quantity.streams.seeds) < 2 and not self.drawing \
                and self.ends is None:
            self.draw_line(True)        # none yet: draw it now
            return
        self._no_line()

    def draw_line(self, on):
        """The next two left clicks on the 3D view: the ends of the line
        the tracers are born on (the seed line of the 2D plot too), the
        poloidal plane point (R, Z) of each; or stop."""
        nav = getattr(self.view, "navigator", None)
        if not self.on() or nav is None:
            self.options.tracers.drawing(False)
            return
        if not on:
            self._stop_picking()
            return
        self.ends = []
        nav.start_pick(self._picked)
        self.options.tracers.drawing(True)
        self.tab.status.emit("Click the two ends of the line on the 3D "
                             "view")

    def _picked(self, point):
        if point is None:
            self.tab.status.emit("Click on the plasma, the structure or "
                                 "the cut face at the start of the sector")
            return
        self.ends.append((float(np.hypot(point[0], point[1])),
                          float(point[2])))
        self.view.mark(point if len(self.ends) == 1 else None)
        if len(self.ends) == 2:
            ends = self.ends
            self._stop_picking()
            self.tab.quantity.set_seeds(ends)
            self.tab.status.emit("Line set: R, Z from (%.3f, %.3f) to "
                                 "(%.3f, %.3f) m" % (*ends[0], *ends[1]))

    def _stop_picking(self):
        self.ends = None
        nav = getattr(self.view, "navigator", None)
        if nav is not None and nav.pick is not None:
            nav.start_pick(None)
            self.view.mark(None)
        self.options.tracers.drawing(False)

    def draw_line_2d(self, on):
        """The 2D plot in place of the 3D view to click the two ends of
        the line the tracers are born on (the seed line of the 2D plot),
        or back to the 3D view."""
        if not self.on():
            return
        self._stop_picking()
        self.drawing = bool(on)
        self.options.tracers.drawing(self.drawing, in2d=True)
        self.apply()
        self.tab.tools.bar.set_mode("seeds" if on else None)

    def _line_drawn(self):
        """The seed line drawn (or the clicks cancelled): the 3D view
        again, its tracers born on the line."""
        if self.drawing and self.tab.tools.bar.mode != "seeds":
            self.drawing = False
            self.options.tracers.drawing(False, in2d=True)
            self.apply()

    def _no_line(self):
        """Tracers to be born on a line the run (or the 2D plot) does not
        have: said once in the status bar."""
        scene = None if self.view is None else self.view.scene
        born = self.options.tracers.born
        missing = scene is not None and scene.snap is not None and \
            scene.snap.vector is not None and scene.tracers is None and \
            born.currentData() in births.LINES
        if missing and not self._missing:
            self.tab.status.emit(
                "3D view: no tracers, draw the seed line in 2D first "
                "(Streamlines options)" if born.currentData() == "line" else
                "3D view: no tracers, the run has no %s" %
                born.currentText().replace("on the ", ""))
        self._missing = missing

    def _grid_heights(self):
        """The lowest and highest points of the grids of the run (B2.5,
        EIRENE): the vertical range."""
        run = self.tab.run
        z = list(run.geometry.bbox[2:])
        if run.trimesh is not None:
            y = np.asarray(run.trimesh.y, float)
            z += [float(y.min()), float(y.max())]
        return min(z), max(z)

    def _save(self):
        if self.view is None:
            return
        path = self.tab._file("Save the 3D view", "view3d.png",
                              "PNG image (*.png)")
        if path is None:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        try:
            self.view.save(path)
        except (OSError, ValueError, RuntimeError) as err:
            self.tab.status.emit("Cannot save the 3D view: %s" % err)
            return
        self.tab.status.emit("3D view saved to %s" % os.path.abspath(path))
