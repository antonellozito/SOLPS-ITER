"""Camera section of the quantity column (opened with Camera, at the right
of Field line): the pinhole camera (position and the point it looks at,
R, Z and toroidal angle, both picked on the plot with Pick, then typed;
roll, field of view, pixels), how its line integral is taken (per
steradian, the step along the rays, the rays per pixel) and Render; the
image of the quantity shown, each Render in a window of its own (colour
scale as the plots have it, the wall edges seen, the value under the
mouse; Save image, Export CSV or netCDF, Export matrix, Export
frames)."""

from dataclasses import replace

import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .. import theme
from ..panels.layers import ColorButton, left_form
from ..panels.plotarea import ScaledCanvas
from ..panels.plotopts import ColourBox
from ..plot.styles import LabelStyle, PlotStyle, cmap3d, norm_for
from ..plot.texts import TextMixin
from ..scaling import Scaled, squeezable
from ...b2plot import labels
from ...qt import QtCore, QtGui, QtWidgets, Qt
from . import camerareal, measure
from .camera import Camera
from .sections import _button, _text

LOOK = "#00a0e0"                # the camera and its rays on the plot
MAX_SAMPLES = 8                 # rays per pixel at most: 8 x 8
MARGIN = 0.012                  # of the figure around image and colour bar
TOP = 0.075                     # of the figure above the image: its title
RIGHT = 0.075                   # of the figure right of the bar: its ticks
BAR = 0.045                     # width of the bar, of the image width
GAP = 0.08                      # inches between the image and its bar
WIDTH = 6.4                     # inches of the figure at first


def _spin(lo, hi, value, step, decimals, suffix, tip):
    s = QtWidgets.QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(value)
    s.setSuffix(suffix)
    s.setToolTip(tip)
    s.setKeyboardTracking(False)
    return s


class CameraSection(QtWidgets.QGroupBox):
    """The widgets of the section (CameraTool drives them)."""

    def __init__(self, owner, parent=None):
        super().__init__("Camera", parent)
        cam = Camera()
        self.pick = _button("Pick", "Click the camera position on the "
                            "plot, then the point it looks at (their "
                            "toroidal angles as typed)", owner.arm, True)
        self.look = _button("3D view", "The camera seen in the 3D view "
                            "(a perspective view through it, its image as "
                            "high as the view): a drag turns it where it "
                            "is, the wheel moves it forwards and backwards, "
                            "the arrow keys or W, A, S, D move it sideways, "
                            "a drag with a modifier turns it around the "
                            "point under the cursor, which it then looks "
                            "at; the position, the point it looks at, the "
                            "roll and the field of view follow it",
                            owner.look3d, True)
        self.render = _button("Render", "The image of the quantity shown: "
                              "its line integral along the ray of each "
                              "pixel up to the first wall", owner.render)
        self.colour = ColorButton(LOOK)
        self.colour.setToolTip("Colour of the camera and its rays on the "
                               "plot")
        top = QtWidgets.QHBoxLayout()
        for w in (self.pick, self.look, self.render):
            top.addWidget(w)
        top.addWidget(self.colour)
        self.pos = [_spin(0, 100, cam.position[0], 0.01, 3, " m",
                          "R of the camera"),
                    _spin(-100, 100, cam.position[1], 0.01, 3, " m",
                          "Z of the camera"),
                    _spin(-360, 360, cam.position[2], 1, 1, "°",
                          "Toroidal angle of the camera")]
        self.target = [_spin(0, 100, cam.target[0], 0.01, 3, " m",
                             "R of the point seen at the centre"),
                       _spin(-100, 100, cam.target[1], 0.01, 3, " m",
                             "Z of the point seen at the centre"),
                       _spin(-360, 360, 30.0, 1, 1, "°",
                             "Toroidal angle of the point seen at the "
                             "centre")]
        self.roll = _spin(-180, 180, cam.roll, 5, 1, "°", "The image turned "
                          "about the line of sight (0: Z up)")
        self.fov = _spin(1, 170, cam.fov, 5, 1, "°", "Horizontal field of "
                         "view")
        self.nx = QtWidgets.QSpinBox()
        self.ny = QtWidgets.QSpinBox()
        for s, v, tip in ((self.nx, cam.nx, "Pixels across"),
                          (self.ny, cam.ny, "Pixels up")):
            s.setRange(4, 2000)
            s.setValue(v)
            s.setToolTip(tip)
            s.setKeyboardTracking(False)
        self.step = _spin(0.1, 50, 2.0, 0.5, 1, " mm", "Step of the samples "
                          "along the rays")
        self.per_sr = QtWidgets.QCheckBox("Per steradian")
        self.per_sr.setChecked(True)
        self.per_sr.setToolTip("Divide by 4π: an emissivity radiated in "
                               "all directions seen as a radiance")
        self.samples = QtWidgets.QComboBox()
        for n in range(1, MAX_SAMPLES + 1):
            self.samples.addItem("1" if n == 1 else "%d × %d" % (n, n), n)
        self.samples.setToolTip("Rays spread evenly over each pixel, their "
                                "line integrals averaged (structures finer "
                                "than a pixel smoothed as a sensor sees "
                                "them; the time grows with their number)")
        form = left_form(None)
        for label, boxes in (("Position", self.pos), ("Looks at",
                                                      self.target)):
            row = QtWidgets.QHBoxLayout()
            for b in boxes:
                row.addWidget(b, 1)
            form.addRow(label, row)
        row = QtWidgets.QHBoxLayout()
        for label, w in (("Roll", self.roll), ("Field of view", self.fov)):
            row.addWidget(QtWidgets.QLabel(label))
            row.addWidget(w, 1)
        form.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Pixels"))
        row.addWidget(self.nx, 1)
        row.addWidget(QtWidgets.QLabel("×"))
        row.addWidget(self.ny, 1)
        row.addWidget(QtWidgets.QLabel("Step"))
        row.addWidget(self.step, 1)
        form.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.per_sr)
        row.addStretch(1)
        row.addWidget(QtWidgets.QLabel("Rays per pixel"))
        row.addWidget(self.samples)
        form.addRow(row)
        self.text = _text()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addLayout(form)
        lay.addWidget(self.text)
        squeezable(self)
        for b in self.pos + self.target + [self.roll, self.fov]:
            b.valueChanged.connect(lambda *_: owner.moved())
        for b in (self.nx, self.ny):
            b.valueChanged.connect(lambda *_: owner.moved())
        self.colour.changed.connect(lambda *_: owner.moved())
        self.step.valueChanged.connect(lambda *_: owner.moved())
        self.per_sr.toggled.connect(lambda *_: owner.moved())
        self.samples.currentIndexChanged.connect(lambda *_: owner.moved())

    def camera(self):
        return Camera(tuple(b.value() for b in self.pos),
                      tuple(b.value() for b in self.target),
                      self.roll.value(), self.fov.value(), self.nx.value(),
                      self.ny.value())

    def set_camera(self, pos, target, roll, fov):
        """Position and target (R, Z, phi), roll and field of view, the
        signals held."""
        for b, v in zip(self.pos + self.target + [self.roll, self.fov],
                        tuple(pos) + tuple(target) + (roll, fov)):
            b.blockSignals(True)
            b.setValue(float(v))
            b.blockSignals(False)

    def set_points(self, pos, target):
        """Position and target (R, Z) picked; their angles kept."""
        for boxes, p in ((self.pos, pos), (self.target, target)):
            for b, v in zip(boxes[:2], p):
                b.blockSignals(True)
                b.setValue(float(v))
                b.blockSignals(False)

    def settings(self):
        cam = self.camera()
        return dict(position=list(cam.position), target=list(cam.target),
                    roll=cam.roll, fov=cam.fov, nx=cam.nx, ny=cam.ny,
                    step=self.step.value(), per_sr=self.per_sr.isChecked(),
                    samples=self.samples.currentData(),
                    colour=self.colour.color())

    def restore(self, d):
        for boxes, key in ((self.pos, "position"), (self.target, "target")):
            for b, v in zip(boxes, d.get(key, ())):
                b.setValue(float(v))
        for b, key in ((self.roll, "roll"), (self.fov, "fov"),
                       (self.step, "step")):
            if key in d:
                b.setValue(float(d[key]))
        for b, key in ((self.nx, "nx"), (self.ny, "ny")):
            if key in d:
                b.setValue(int(d[key]))
        self.per_sr.setChecked(bool(d.get("per_sr", True)))
        k = self.samples.findData(int(d.get("samples", 1)))
        self.samples.setCurrentIndex(max(k, 0))
        if d.get("colour"):
            self.colour.set_color(d["colour"])

    def set_armed(self, on):
        self.pick.blockSignals(True)
        self.pick.setChecked(on)
        self.pick.blockSignals(False)


class _Bar(TextMixin):
    """The colour bar of an image styled as those of the 2D plot: the unit
    inside the bar, compact ticks, the power of ten above it."""

    def __init__(self, figure):
        self.fig, self.label_style = figure, LabelStyle()

    def inches(self):
        return np.asarray(self.fig.get_size_inches(), float)


def _height(aspect, width):
    """Inches of a figure of the width given whose image (aspect: rows
    over columns) fills it."""
    w = ((1.0 - 2.0 * MARGIN - RIGHT) * width - GAP) / (1.0 + BAR)
    return min(aspect * w / (1.0 - MARGIN - TOP), 2.0 * width)


class CameraWindow(Scaled, QtWidgets.QWidget):
    """One image of the camera (each Render a window of its own): the
    colour scale as the plots have it (colour map, reversed, scale,
    range), its colour bar as tall as the image, the wall edges, the
    value under the mouse; Save image, Export, Export matrix, Export
    frames (owner: the CameraTool, last: the image). Colour modes: the
    colour map; transparency (one colour, transparent at the minimum,
    over the vessel structures rendered with the camera); with a light
    quantity true colour and filtered camera (camerareal: their options
    under the colour scale); a click
    on a pixel of a light quantity shows the spectrum along its rays."""

    def __init__(self, owner, last, before=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.owner, self.last = owner, last
        self.setWindowTitle("Camera: %s" % last["name"].replace("$", ""))
        cam = last["camera"]
        self.figure = Figure(figsize=(WIDTH, _height(cam.ny / cam.nx, WIDTH)))
        self.canvas = ScaledCanvas(self.figure)
        self.scale = ColourBox("Colour scale")
        self.scale.add_modes(camerareal.REAL)
        self.scale.show_modes(True)
        self.scale.set_modes(owner.colour_modes(last))
        self.real = camerareal.RealBox()
        self.rng_seed = int(np.random.default_rng().integers(1 << 30))
        self.pixel = None               # the window of a pixel spectrum
        self.pixel_at = None            # its pixel (row, column)
        self.edges = QtWidgets.QCheckBox("Wall edges")
        self.edges.setChecked(True)
        self.edges.setToolTip("The wall elements seen, as toroidal rings "
                              "and poloidal cuts")
        self.where = QtWidgets.QLabel(" ")
        self.where.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.where.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                 QtWidgets.QSizePolicy.Preferred)
        grid = QtWidgets.QGridLayout()  # the buttons
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(12)
        for k, (text, tip, slot) in enumerate((
                ("Save image…", "The image as an image or vector file "
                 "(format, content, resolution, colour space and theme as "
                 "Save plot)", owner.save),
                ("Export…", "The pixels (value, distance to the wall, wall "
                 "element seen) as a CSV or netCDF file with the camera",
                 owner.export),
                ("Export matrix…", "The geometry matrix of the image as a "
                 "netCDF file: the weight of each vertex value in each pixel "
                 "(the image of any frame from its vertex values) and the "
                 "path length of the rays of each pixel in each cell "
                 "(tomography)", owner.export_matrix),
                ("Export frames…", "The image with this camera of every "
                 "position of the movie slider (Run movies: the quantity "
                 "shown there) with its time as a netCDF file",
                 owner.export_frames))):
            grid.addWidget(_button(text, tip, lambda s=slot: s(self)),
                           k // 2, k % 2)
        right = QtWidgets.QVBoxLayout()   # beside the colour scale, under
        right.setContentsMargins(0, QtGui.QFontMetrics(    # its title:
            self.scale.font()).height(), 0, 4)   # Wall edges at the top,
        right.addWidget(self.edges)              # the buttons in the room
        right.addStretch(1)                      # under it
        right.addLayout(grid)
        right.addStretch(1)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.scale, 1)
        row.addLayout(right)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(2)
        lay.addWidget(self.canvas, 1)
        lay.addLayout(row)
        lay.addWidget(self.real)        # the width of the window
        lay.addWidget(self.where)
        if before is not None:          # the colour scale of the last one
            for a, b in ((self.scale.cmap, before.scale.cmap),
                         (self.scale.scale, before.scale.scale)):
                a.setCurrentIndex(b.currentIndex())
            self.scale.reverse.setChecked(before.scale.reverse.isChecked())
            self.scale.auto.setChecked(before.scale.auto.isChecked())
            for a, b in ((self.scale.vmin, before.scale.vmin),
                         (self.scale.vmax, before.scale.vmax)):
                a.setText(b.text())
            self.edges.setChecked(before.edges.isChecked())
            self.scale.mono.set_color(before.scale.mono.color())
            self.real.copy(before.real)
            k = self.scale.mode.findData(before.scale.chosen_mode())
            if self.scale.mode.model().item(k).isEnabled():
                self.scale.mode.setCurrentIndex(k)
        self.ax = None
        self.shown = (last["values"], last["unit"])    # under the mouse
        self._wait = QtCore.QTimer(self)    # the lines of a light quantity
        self._wait.setSingleShot(True)
        self._wait.setInterval(300)
        self._wait.timeout.connect(self.draw)
        self.real.show_mode(self.scale.chosen_mode())
        self.edges.toggled.connect(lambda *_: self.draw())
        self.scale.changed.connect(self.draw)
        self.scale.mode.currentIndexChanged.connect(
            lambda *_: self.real.show_mode(self.scale.chosen_mode()))
        self.real.changed.connect(self.draw)
        self.canvas.mpl_connect("motion_notify_event", self._hover)
        self.canvas.mpl_connect("button_press_event", self._click)
        self.scaled()
        self.draw()

    def _image(self):
        """(values or screen RGB, unit, note) of the colour mode chosen;
        None while the lines of the light quantity are still coming."""
        last, mode = self.last, self.scale.chosen_mode()
        if mode in ("map", "alpha"):
            return last["values"], last["unit"], ""
        light = self.owner.light(last)
        if light is None or "V" not in light:
            return None
        nodes = self.owner.matrix(last)["nodes"]
        return camerareal.compute(mode, last, nodes, light,
                                  self.real.settings(),
                                  np.random.default_rng(self.rng_seed))

    def draw(self):
        last, fig = self.last, self.figure
        got = self._image()
        if got is None:                 # the lines still coming
            light = self.owner.light(last) or {}
            self.where.setText("Loading the lines of %s: %d of %d" % (
                last["name"].replace("$", ""), light.get("got", 0),
                len(light.get("rows", ()))))
            self._wait.start()
            got = (last["values"], last["unit"], "")
        v, unit, note = got
        mode = self.scale.chosen_mode()
        fig.clear()
        fig.set_facecolor(theme.figure_bg())
        ax = fig.add_axes((MARGIN, MARGIN, 1.0 - 2.0 * MARGIN - RIGHT,
                           1.0 - MARGIN - TOP))
        extent = (0, last["camera"].nx, last["camera"].ny, 0)
        im = None
        if v.ndim == 3:                 # true colour
            ax.imshow(v, origin="upper", interpolation="none",
                      extent=extent)
            self.shown = (v.mean(axis=-1), "")
        else:
            st = replace(PlotStyle(), **self.scale.style_fields())
            norm = norm_for(v, st)
            self.scale.set_range(norm.vmin, norm.vmax)
            if mode == "alpha":         # over the vessel seen by the camera
                ax.imshow(self.owner.vessel(last), origin="upper",
                          interpolation="bilinear", extent=extent)
            im = ax.imshow(np.where(v > 0, v, np.nan) if st.scale == "log"
                           else v, cmap=cmap3d(st, norm), norm=norm,
                           origin="upper", interpolation="none",
                           extent=extent)
            self.shown = (v, unit)
        if self.edges.isChecked():
            for x, y in last["edges"]:
                ax.plot(x, y, color="#9ec5ff", linewidth=0.6, alpha=0.8)
        ax.set_xlim(0, v.shape[1])
        ax.set_ylim(v.shape[0], 0)
        ax.set_xticks([])
        ax.set_yticks([])
        color = theme.text()
        for spine in ax.spines.values():
            spine.set_color(color)
        ax.set_title(last["name"], fontsize=11.0, color=color)
        cax = make_axes_locatable(ax).append_axes(
            "right", size="%g%%" % (100.0 * BAR), pad=GAP)
        if im is None:                  # true colour: no bar
            cax.set_axis_off()
        else:
            bar = fig.colorbar(im, cax=cax, extendfrac=0.0)
            try:                        # the bar where it is drawn (its
                cax.set_position(cax.get_axes_locator()(cax, None))
            except (TypeError, ValueError, AttributeError):
                pass
            _Bar(fig)._style_bar(bar, unit)
        if note and not self._wait.isActive():
            self.where.setText(note)
        self.ax = ax
        self.canvas.draw_idle()

    def _hover(self, event):
        if self.ax is None or event.inaxes is not self.ax or \
                event.xdata is None:
            return
        j, i = int(event.xdata), int(event.ydata)
        v, unit = self.shown
        if 0 <= i < v.shape[0] and 0 <= j < v.shape[1]:
            d = self.last["distance"][i, j]
            self.where.setText("pixel (%d, %d): %.5g %s, wall at %s" % (
                j, i, v[i, j], measure.html_unit(labels.any_to_plain(unit)),
                "%.3f m" % d if
                np.isfinite(d) else "none"))

    def _click(self, event):
        """A click on a pixel of a light quantity: the spectrum along its
        rays (all its lines, the filter of the realistic view behind)."""
        if self.ax is None or event.inaxes is not self.ax or \
                event.xdata is None or event.button != 1:
            return
        cam = self.last["camera"]
        j, i = int(event.xdata), int(event.ydata)
        if 0 <= i < cam.ny and 0 <= j < cam.nx:
            self.pixel_at = (i, j)
            self._pixel()

    def _pixel(self):
        """The spectrum of the pixel clicked last (again when the options
        of its window change, with Line shapes while their fields come)."""
        light = self.owner.light(self.last)
        if light is None or "V" not in light or self.pixel_at is None:
            return
        i, j = self.pixel_at
        y = camerareal.pixel_lines(self.owner.matrix(self.last)["nodes"],
                                   light, self.last, i, j)
        if self.pixel is None:
            self.pixel = camerareal.PixelSpectrum(self.owner.tab.settings,
                                                  self._pixel)
        unit = "photons m^-2 s^-1 sr^-1" if light["photons"] else \
            "W m^-2 sr^-1"
        shaped, opts = None, self.pixel.options()
        spectrum = self.owner.tools.spectrum
        if opts is not None and spectrum.want_shapes(light["parts"]):
            shaped = camerareal.pixel_shaped(spectrum, light, self.last, i,
                                             j, y, opts)
        self.pixel.show_pixel("pixel (%d, %d)" % (j, i), light["wl"],
                              light["labels"], y, unit, self.real.filter(),
                              shaped, spectrum.asked)

    def apply_theme(self):
        self.draw()

    def closeEvent(self, event):
        if self.pixel is not None:
            self.pixel.close()
        self.owner.closed(self)
        super().closeEvent(event)
