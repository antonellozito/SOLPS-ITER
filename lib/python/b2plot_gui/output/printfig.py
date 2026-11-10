"""Print figure, as AUGVIEW: output format (png, jpg, eps, pdf, svg),
content type (vector or raster), resolution, colour space (rgb, cmyk,
gray) and export theme (light or dark). Vector output keeps the drawing;
raster output is the figure rendered at the resolution, written as an
image or wrapped in a PDF, EPS or SVG file."""

import base64
import io
import os

import numpy as np
from matplotlib import colors as mcolors
from matplotlib.figure import Figure

from ...qt import QtCore, QtGui, QtWidgets

FORMATS = ("png", "jpg", "eps", "pdf", "svg")
VECTOR = ("eps", "pdf", "svg")
FILTERS = {"png": "PNG image (*.png)", "jpg": "JPEG image (*.jpg)",
           "eps": "EPS file (*.eps)", "pdf": "PDF file (*.pdf)",
           "svg": "SVG file (*.svg)"}


def defaults(fmt="png"):
    fmt = "jpg" if fmt == "jpeg" else fmt if fmt in FORMATS else "png"
    return dict(format=fmt, content="vector" if fmt in VECTOR else "raster",
                dpi=600, color="rgb")


class PrintDialog(QtWidgets.QDialog):
    """The options of Print figure; options() after Export."""

    def __init__(self, dark=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Print figure")
        d = defaults()
        lay = QtWidgets.QGridLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setHorizontalSpacing(10)
        lay.setVerticalSpacing(9)
        self.format = QtWidgets.QComboBox()
        self.format.addItems(FORMATS)
        self.content = QtWidgets.QComboBox()
        self.dpi = QtWidgets.QLineEdit(str(d["dpi"]))
        self.color = QtWidgets.QComboBox()
        self.theme = QtWidgets.QComboBox()
        self.theme.addItems(["light", "dark"])
        self.theme.setCurrentIndex(1 if dark else 0)
        for row, (text, w) in enumerate((
                ("Output format", self.format), ("Content type", self.content),
                ("Resolution", self.dpi), ("Color space", self.color),
                ("Export theme", self.theme))):
            lay.addWidget(QtWidgets.QLabel(text), row, 0)
            lay.addWidget(w, row, 1)
        lay.addWidget(QtWidgets.QLabel("dpi"), 2, 2)
        buttons = QtWidgets.QHBoxLayout()
        ok = QtWidgets.QPushButton("Export")
        close = QtWidgets.QPushButton("Close")
        ok.clicked.connect(self._accept)
        close.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(close)
        lay.addLayout(buttons, 5, 0, 1, 3)
        self.format.currentTextChanged.connect(lambda *_: self._refresh(True))
        self.content.currentTextChanged.connect(lambda *_: self._refresh())
        self._refresh(True)

    def _refresh(self, format_changed=False):
        """Choices allowed by the format (as AUGVIEW)."""
        fmt = self.format.currentText()
        contents = ["vector", "raster"] if fmt in VECTOR else ["raster"]
        colors = ["rgb", "gray"] if fmt == "svg" else ["rgb", "cmyk", "gray"]
        content = contents[0] if format_changed else \
            self.content.currentText()
        color = self.color.currentText() or "rgb"
        for combo, items, value in ((self.content, contents, content),
                                    (self.color, colors, color)):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(items)
            combo.setCurrentText(value if value in items else items[0])
            combo.blockSignals(False)
        vector = self.content.currentText() == "vector"
        if vector:
            self.dpi.setText("vector")
        elif self.dpi.text() == "vector":
            self.dpi.setText(str(defaults()["dpi"]))
        self.dpi.setEnabled(not vector)

    def _accept(self):
        if self.content.currentText() != "vector":
            try:
                float(self.dpi.text())
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self, "Print figure", "Resolution must be a number of "
                    "dpi.")
                return
        self.accept()

    def options(self):
        vector = self.content.currentText() == "vector"
        return dict(format=self.format.currentText(),
                    content=self.content.currentText(),
                    dpi=defaults()["dpi"] if vector else max(
                        72, int(round(float(self.dpi.text())))),
                    color=self.color.currentText(),
                    theme=self.theme.currentText())


def with_suffix(path, fmt):
    stem, ext = os.path.splitext(path)
    return path if ext.lower() == "." + fmt else stem + "." + fmt


def save(figure, path, options):
    """Write figure with the options of the dialog (the theme already
    applied; grey vector output changes the colours of the figure, which
    the caller draws again); returns a note on what could not be
    honoured, or ""."""
    fmt, content = options["format"], options["content"]
    color, dpi = options["color"], int(options["dpi"])
    notes = []
    if content == "vector" and fmt in VECTOR:
        if color == "gray":
            _grayscale(figure)
        if color == "cmyk":
            notes.append("CMYK vector export is not supported; RGB "
                         "colours written.")
        figure.savefig(path, format=fmt, dpi=dpi,
                       facecolor=figure.get_facecolor())
        return " ".join(notes)
    buf = io.BytesIO()
    figure.savefig(buf, format="png", dpi=dpi,
                   facecolor=figure.get_facecolor())
    image = QtGui.QImage.fromData(buf.getvalue())
    if color == "gray":
        image = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
    elif color == "cmyk":
        cmyk = getattr(QtGui.QImage.Format, "Format_CMYK8888", None)
        converted = image.convertToFormat(cmyk) if cmyk is not None and \
            fmt == "eps" else None
        if converted is None or converted.isNull():
            notes.append("CMYK is not supported for this format; RGB "
                         "colours written.")
        else:
            image = converted
    if fmt in ("png", "jpg"):
        if not image.save(path, "JPG" if fmt == "jpg" else "PNG"):
            raise OSError("cannot write %s" % path)
    elif fmt == "svg":
        _svg_with_image(image, path)
    else:
        _wrapped(image, path, fmt, dpi)
    return " ".join(notes)


def _rgba(image):
    image = image.convertToFormat(QtGui.QImage.Format_RGBA8888)
    bits = image.constBits()
    a = np.frombuffer(bits, np.uint8, count=image.sizeInBytes())
    return a.reshape(image.height(), image.bytesPerLine())[
        :, :4 * image.width()].reshape(image.height(), image.width(),
                                       4).copy()


def _svg_with_image(image, path):
    """A self-contained SVG file with the image embedded."""
    data = QtCore.QByteArray()
    buf = QtCore.QBuffer(data)
    buf.open(QtCore.QIODevice.WriteOnly)
    image.save(buf, "PNG")
    buf.close()
    w, h = max(image.width(), 1), max(image.height(), 1)
    with open(path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                'width="%d" height="%d" viewBox="0 0 %d %d">\n'
                '  <image width="%d" height="%d" href="data:image/png;'
                'base64,%s"/>\n</svg>\n' % (
                    w, h, w, h, w, h,
                    base64.b64encode(bytes(data)).decode("ascii")))


def _wrapped(image, path, fmt, dpi):
    """The image as the only content of a PDF or EPS page."""
    rgba = _rgba(image)
    h, w = rgba.shape[:2]
    fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.imshow(rgba)
    ax.set_axis_off()
    fig.savefig(path, format=fmt, dpi=dpi, facecolor=fig.get_facecolor(),
                pad_inches=0.0)


def _gray(value):
    try:
        r, g, b, a = mcolors.to_rgba(value)
    except ValueError:
        return value
    v = 0.299 * r + 0.587 * g + 0.114 * b
    return (v, v, v, a)


def _gray_array(value):
    try:
        a = np.array(mcolors.to_rgba_array(value), float)
    except ValueError:
        return value
    if a.size:
        a[:, :3] = (a[:, :3] @ np.array([0.299, 0.587, 0.114]))[:, None]
    return a


def _grayscale(figure):
    """The colours of a figure as grey levels (as AUGVIEW)."""
    figure.set_facecolor(_gray(figure.get_facecolor()))
    for t in figure.texts:
        t.set_color(_gray(t.get_color()))
    for ax in figure.axes:
        ax.set_facecolor(_gray(ax.get_facecolor()))
        for item in [ax.title, ax.xaxis.label, ax.yaxis.label] + \
                list(ax.texts) + ax.get_xticklabels() + ax.get_yticklabels():
            item.set_color(_gray(item.get_color()))
        for spine in ax.spines.values():
            spine.set_color(_gray(spine.get_edgecolor()))
        for line in ax.lines:
            line.set_color(_gray(line.get_color()))
        for a in list(ax.patches) + list(ax.collections):
            mapped = getattr(a, "get_array", lambda: None)() is not None \
                and getattr(a, "colors", None) is None
            if mapped:              # colours from a colour map
                a.set_cmap("gray")
                continue
            for get, put in (("get_facecolor", "set_facecolor"),
                             ("get_edgecolor", "set_edgecolor")):
                if hasattr(a, get):
                    getattr(a, put)(_gray_array(getattr(a, get)()))
        for image in ax.images:
            image.set_cmap("gray")
