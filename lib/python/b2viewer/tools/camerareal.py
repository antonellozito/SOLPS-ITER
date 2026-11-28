"""The realistic views of a camera window (CameraWindow, colour modes true
colour and filtered camera): their options (the filter, the exposure and
noise of the camera, the brightness of the true colour), the images
computed from the lines of a light quantity (each line's vertex values,
weighted at the vertices and taken through the geometry matrix of the
image once per channel), and the spectrum along the rays of a pixel."""

import numpy as np

from ...qt import QtCore, QtWidgets, Qt, Signal
from ..panels.layers import spin
from ..scaling import Scaled
from . import camera, lineshape, measure, realistic
from .figure import FigureView
from .spectrum import SHAPE_POINTS, fit_x, shape_text

REAL = (("true colour", "colour"),
        ("filtered camera", "filter"))  # colour modes of the camera
KINDS = (("all lines", "all"), ("wavelength range", "range"),
         ("filter", "filter"))
FULL_WELL = 30000.0             # e-, at first


class RealBox(QtWidgets.QGroupBox):
    """Options of the realistic views (those of the mode shown enabled,
    the others greyed out), in three rows."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Realistic view", parent)
        self.kind = QtWidgets.QComboBox()
        for text, key in KINDS:
            self.kind.addItem(text, key)
        self.kind.setToolTip("The lines seen: all, those in a wavelength "
                             "range, or through an interference filter "
                             "(a Gaussian transmission)")
        self.preset = QtWidgets.QComboBox()
        self.preset.addItem("custom")
        for f in realistic.FILTERS:
            self.preset.addItem(f[0], f)
        self.preset.setToolTip("Filters of the usual lines")
        self.a = spin(1.0, 100000.0, 0.1, 656.1, 1, "")
        self.b = spin(0.01, 100000.0, 0.1, 1.0, 2, "")
        self.a_label, self.b_label = QtWidgets.QLabel(), QtWidgets.QLabel()
        self.noise = QtWidgets.QCheckBox("exposure and noise")
        self.noise.setToolTip("The counts of a camera: the light through "
                              "the aperture on each pixel during the "
                              "exposure, times the quantum efficiency, "
                              "with photon noise, at most the full well")
        self.aperture = spin(0.01, 1000.0, 0.1, 5.0, 2, "Diameter of the "
                             "pinhole aperture (mm)")
        self.exposure = spin(0.0001, 100000.0, 0.1, 1.0, 4, "Exposure "
                             "time (ms)")
        self.qe = spin(0.1, 100.0, 1.0, 60.0, 1, "Quantum efficiency (%)")
        self.full = spin(100.0, 1e7, 1000.0, FULL_WELL, 0, "Full well "
                         "(electrons): the pixel saturates there")
        self.bright = spin(0.01, 100.0, 0.1, 1.0, 2, "Brightness of the "
                           "true colour (1: the brightest 0.5 % of the "
                           "pixels saturate)")
        self.labels = {k: QtWidgets.QLabel(t) for k, t in (
            ("lines", "Lines"), ("aperture", "aperture (mm)"),
            ("exposure", "exposure (ms)"), ("qe", "efficiency (%)"),
            ("full", "full well (e⁻)"), ("bright", "brightness"))}
        lab = self.labels
        lay = QtWidgets.QVBoxLayout(self)       # the width of the window:
        lay.setContentsMargins(6, 4, 6, 4)      # three rows
        lay.setSpacing(4)
        for widgets in ((lab["lines"], self.kind, self.preset, self.a_label,
                         self.a, self.b_label, self.b),
                        (self.noise, lab["aperture"], self.aperture,
                         lab["exposure"], self.exposure, lab["qe"], self.qe),
                        (lab["full"], self.full, lab["bright"],
                         self.bright)):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(6)
            for w in widgets:
                row.addWidget(w)
                if isinstance(w, QtWidgets.QAbstractSpinBox) or \
                        w in (self.preset, self.noise):
                    row.addSpacing(10)
            row.addStretch(1)
            lay.addLayout(row)
        self.kind.currentIndexChanged.connect(self._kind)
        self.preset.currentIndexChanged.connect(self._preset)
        for w in (self.a, self.b, self.aperture, self.exposure, self.qe,
                  self.full, self.bright):
            w.valueChanged.connect(lambda *_: self.changed.emit())
        for w in (self.a, self.b):
            w.valueChanged.connect(lambda *_: self._custom())
        self.noise.toggled.connect(lambda *_: self.show_mode(self.mode))
        self.mode = "colour"
        self.kind.setCurrentIndex(0)
        self._kind()

    def _kind(self, *_):
        k = self.kind.currentData()
        self.a_label.setText("from (nm)" if k == "range" else "centre (nm)")
        self.b_label.setText("to (nm)" if k == "range" else "width (nm)")
        self.b.setToolTip("Full width at half maximum of the filter (nm)"
                          if k == "filter" else "End of the range (nm)")
        self._states()
        self.changed.emit()

    def _preset(self, *_):
        f = self.preset.currentData()
        if not f:
            return
        _, kind, a, b = f
        for w, v in ((self.a, a), (self.b, b)):
            w.blockSignals(True)
            w.setValue(v)
            w.blockSignals(False)
        self.kind.setCurrentIndex(self.kind.findData(kind))
        self._kind()

    def _custom(self):
        self.preset.blockSignals(True)
        self.preset.setCurrentIndex(0)
        self.preset.blockSignals(False)

    def show_mode(self, mode):
        """The options of the mode (true colour, filtered camera) enabled; all of them always there (the window keeps its
        size), the others and, in the other modes, the whole box greyed
        out."""
        self.mode = mode
        self._states()
        self.changed.emit()

    def _states(self):
        mode = self.mode
        light = mode in ("colour", "filter")
        counts = light and self.noise.isChecked()
        lines = light and self.kind.currentData() != "all"
        lab = self.labels
        for ws, on in (((lab["lines"], self.kind), light),
                       ((self.preset, self.a_label, self.a, self.b_label,
                         self.b), lines), ((self.noise,), light),
                       ((lab["aperture"], self.aperture, lab["exposure"],
                         self.exposure, lab["qe"], self.qe, lab["full"],
                         self.full), counts),
                       ((lab["bright"], self.bright),
                        mode == "colour" and not counts)):
            for w in ws:
                w.setEnabled(on)
        self.setEnabled(light)

    def filter(self):
        return (self.kind.currentData(), self.a.value(), self.b.value())

    def settings(self):
        return dict(kind=self.kind.currentData(), a=self.a.value(),
                    b=self.b.value(), noise=self.noise.isChecked(),
                    aperture=self.aperture.value(),
                    exposure=self.exposure.value(), qe=self.qe.value(),
                    full=self.full.value(), bright=self.bright.value())

    def copy(self, other):
        """The options of another box (the last window)."""
        for a, b in ((self.kind, other.kind), (self.preset, other.preset)):
            a.setCurrentIndex(b.currentIndex())
        for a, b in ((self.a, other.a), (self.b, other.b),
                     (self.aperture, other.aperture),
                     (self.exposure, other.exposure), (self.qe, other.qe),
                     (self.full, other.full), (self.bright, other.bright)):
            a.setValue(b.value())
        self.noise.setChecked(other.noise.isChecked())


def per_sr(last):
    """Factor of the image values to the brightness per steradian."""
    return 1.0 if last["per_sr"] else 1.0 / (4.0 * np.pi)


def channels(nodes, light, coeffs, cam):
    """Images (k, ny, nx) of the lines combined by coeffs (k, lines),
    weighted at the vertices and taken once through the vertex weights of
    the geometry matrix (as the image itself)."""
    v = np.asarray(coeffs, float) @ light["V"]
    npix = cam.nx * cam.ny
    return np.array([camera.apply(nodes, c, npix).reshape(cam.ny, cam.nx)
                     for c in v])


def compute(mode, last, nodes, light, opts, rng):
    """(image, unit, note) of a realistic mode: true colour (ny, nx, 3
    screen RGB), filtered camera (brightness through the filter, or the
    counts of the camera)."""
    cam = last["camera"]
    k = per_sr(last)
    to_ph, xyz = realistic.line_weights(light["wl"], light["photons"],
                                        opts["kind"], opts["a"], opts["b"])
    what = {"all": "all lines", "range": "%g to %g nm" % (
        opts["a"], opts["b"]), "filter": "filter %g nm, width %g nm" % (
            opts["a"], opts["b"])}[opts["kind"]]
    if mode == "filter":
        ph = channels(nodes, light, to_ph[None], cam)[0] * k
        if not opts["noise"]:
            return ph, "photons m^-2 s^-1 sr^-1", what
        n, _ = realistic.counts(ph, cam, opts["aperture"],
                                opts["exposure"], 0.01 * opts["qe"],
                                opts["full"], rng)
        return n, "e-", "%s; aperture %g mm, %g ms, %g %%" % (
            what, opts["aperture"], opts["exposure"], opts["qe"])
    img = channels(nodes, light, np.vstack((xyz, to_ph[None])), cam) * k
    xyz_img = np.moveaxis(img[:3], 0, -1)
    if not opts["noise"]:
        rgb, _ = realistic.true_colour(xyz_img, opts["bright"])
        return rgb, "", "true colour, " + what
    n, mean = realistic.counts(img[3], cam, opts["aperture"],
                               opts["exposure"], 0.01 * opts["qe"],
                               opts["full"], rng)
    lin = realistic.to_srgb(np.maximum(np.nan_to_num(xyz_img), 0.0))
    top = lin.max(axis=-1, keepdims=True)
    hue = np.where(top > 0, lin / np.where(top > 0, top, 1.0), 0.0)
    rgb = realistic.gamma(hue * (n / opts["full"])[..., None])
    return rgb, "", "true colour, %s; aperture %g mm, %g ms, %g %%" % (
        what, opts["aperture"], opts["exposure"], opts["qe"])


def pixel_lines(nodes, light, last, i, j):
    """The brightness per steradian of each line along the rays of pixel
    (row i, column j)."""
    rows, cols, vals = nodes
    p = i * last["camera"].nx + j
    a, b = np.searchsorted(rows, p), np.searchsorted(rows, p, "right")
    v = light["V"][:, cols[a:b]]
    v = np.where(np.isfinite(v), v, 0.0)
    return v @ vals[a:b] * per_sr(last)


class PixelSpectrum(Scaled, QtWidgets.QWidget):
    """The spectrum along the rays of a pixel of a camera image: a stick
    per line (in its own colour where visible), the filter behind; with
    Line shapes the lines with their shapes and the continua along its
    central ray (lineshape), redo() again when they change or while the
    fields come; in the theme of the GUI."""

    def __init__(self, settings, redo, parent=None):
        super().__init__(parent, Qt.Window)
        self.redo = redo
        self.view = FigureView(settings)
        self.shapes = QtWidgets.QCheckBox("Line shapes")
        self.shapes.setToolTip(
            "The lines with their shapes along the central ray of the "
            "pixel (each keeping its brightness): Doppler broadening at the "
            "temperature of their emitters, shift by the flow along the "
            "ray, Zeeman splitting, Stark broadening of Balmer alpha and "
            "beta, the instrument width")
        self.continua = QtWidgets.QCheckBox("Continua")
        self.continua.setChecked(True)
        self.continua.setToolTip("Bremsstrahlung and recombination "
                                 "continua of all the ions under the lines")
        self.instrument = QtWidgets.QDoubleSpinBox()
        self.instrument.setRange(0.0, 10.0)
        self.instrument.setDecimals(3)
        self.instrument.setSingleStep(0.01)
        self.instrument.setSuffix(" nm")
        self.instrument.setToolTip("Full width at half maximum of the "
                                   "instrument function (Gaussian)")
        self.wait = QtCore.QTimer(self)     # the fields of the shapes
        self.wait.setSingleShot(True)
        self.wait.setInterval(500)
        self.wait.timeout.connect(lambda: self.redo())
        for w in (self.shapes, self.continua):
            w.toggled.connect(lambda *_: self.redo())
        self.instrument.valueChanged.connect(lambda *_: self.redo())
        save = QtWidgets.QPushButton("Save plot")
        save.clicked.connect(lambda *_: self.view.save())
        export = QtWidgets.QPushButton("Export…")
        export.clicked.connect(lambda *_: self.view.export())
        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.text, 1)
        row.addWidget(save)
        row.addWidget(export)
        row2 = QtWidgets.QHBoxLayout()
        for w in (self.shapes, self.continua,
                  QtWidgets.QLabel("instrument width"), self.instrument):
            row2.addWidget(w)
        row2.addStretch(1)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(row)
        lay.addLayout(row2)
        lay.addWidget(self.view, 1)
        self.resize(560, 460)
        self.scaled()

    def refresh_theme(self):
        if self.view.draw is not None:
            self.view.apply_theme()

    def options(self):
        """(instrument width nm, continua) with Line shapes, else None."""
        return (self.instrument.value(), self.continua.isChecked()) if \
            self.shapes.isChecked() else None

    def show_pixel(self, title, wl, labels, y, unit, filt, shaped=None,
                   asked=()):
        """The spectrum of a pixel (shaped: Spectrum.shaped along its
        central ray, None for the sticks; asked: the fields still
        coming)."""
        kind, a, b = filt
        t = realistic.transmission(0.1 * wl, kind, a, b)
        through = float((y * t).sum())
        self.setWindowTitle("Pixel spectrum: %s" % title)
        text = "%s: %d lines, total %.5g %s, through the filter %.5g" % (
            title, len(y), y.sum(), measure.html_unit(unit), through)
        opts = self.options()
        for w in (self.continua, self.instrument):
            w.setEnabled(opts is not None)
        if opts is not None:
            text += "<br>" + shape_text(shaped, opts, unit, asked)
            if shaped is None and asked:
                self.wait.start()
        self.text.setText(text)
        colours = realistic.line_colour(0.1 * wl) if len(wl) else []
        band = None if kind == "all" else (
            10.0 * (a - 3 * b), 10.0 * (a + 3 * b)) if kind == "filter" \
            else (10.0 * min(a, b) - 10.0, 10.0 * max(a, b) + 10.0)

        def draw(ax, options):
            logy = options.logy.isChecked()
            pos = y[y > 0]
            base = pos.min() / 10.0 if logy and len(pos) else 0.0
            if band is not None and len(y):     # the filter, behind
                lam = np.linspace(band[0], band[1], 400)
                ax.fill_between(lam, base, y.max() * realistic.transmission(
                    0.1 * lam, kind, a, b), color="#888888", alpha=0.15,
                    lw=0, label="_filter")
            ax.vlines(wl, base, y, colors=colours, linewidth=1.5)
            ax.plot(wl, y, linestyle="None", marker="None", label="Lines")
            if not logy:
                ax.set_ylim(bottom=0.0)
            fit_x(ax, wl, y, options.logx.isChecked(), band)
            ax.set_xlabel("wavelength (Å)")
            ax.set_ylabel(measure.math_unit(unit))
            ax.set_title(title, fontsize="medium")
        if shaped is not None:
            draw, header, rows = _shaped_figure(shaped, title, unit, wl, y,
                                                filt, band)
        else:
            header = ["wavelength (A)", "line", unit, "filter transmission"]
            rows = [[w, n, v, tt] for w, n, v, tt in zip(wl, labels, y, t)]
        self.view.set_figure(draw, header, rows, kind="spectrum",
                             space=False, name="pixel_spectrum")
        self.show()
        self.raise_()


def _shaped_figure(shaped, title, unit, wl, y, filt, band):
    """(draw, header, rows) of a pixel spectrum with its shapes and
    continua, the filter behind."""
    lam, curve, ff, fb = shaped
    cont = ff + fb
    total = curve + cont
    per = unit + " Å^-1"
    kind, a, b = filt

    def draw(ax, options):
        if band is not None and total.any():
            x = np.linspace(band[0], band[1], 400)
            ax.fill_between(x, 0.0, total.max() * realistic.transmission(
                0.1 * x, kind, a, b), color="#888888", alpha=0.15, lw=0,
                label="_filter")
        ax.plot(lam, total, label="Spectrum", linewidth=1.0)
        if cont.any():
            ax.plot(lam, cont, label="Continua", linewidth=0.8,
                    linestyle="--")
        if not options.logy.isChecked():
            ax.set_ylim(bottom=0.0)
        fit_x(ax, wl, y, options.logx.isChecked(), band)
        ax.set_xlabel("wavelength (Å)")
        ax.set_ylabel(measure.math_unit(per))
        ax.set_title(title, fontsize="medium")
    t = realistic.transmission(0.1 * lam, kind, a, b)
    return draw, ["wavelength (A)", "lines (%s)" % per,
                  "bremsstrahlung (%s)" % per, "recombination (%s)" % per,
                  "total (%s)" % per, "filter transmission"], [
        [x, c, f1, f2, c + f1 + f2, tt] for x, c, f1, f2, tt in
        zip(lam, curve, ff, fb, t)]


def pixel_shaped(spectrum, light, last, i, j, y, opts):
    """Spectrum.shaped along the central ray of pixel (row i, column j)
    up to the wall it sees (y: the brightness per steradian of each line
    of the pixel, kept by its shape), per steradian; None while fields
    are missing."""
    cam = last["camera"]
    o = camera.frame(cam)[0]
    d = camera.directions(cam)[i, j]
    far = last["distance"][i, j]
    if not np.isfinite(far):            # no wall: across the machine
        far = 2.0 * float(np.linalg.norm(o)) + 10.0
    points, _, s = lineshape.segment(o, o + far * d, SHAPE_POINTS)
    it = iter(y)
    sticks = [next(it) if ok else None for ok in light["ok"]]
    photons = light["photons"]
    return spectrum.shaped(light["rows"], light["parts"], points, d, s,
                           sticks, 1.0 / (4.0 * np.pi), 10.0 * opts[0],
                           opts[1], photons)
