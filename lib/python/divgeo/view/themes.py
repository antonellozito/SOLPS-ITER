"""Themes of the Python interface (Window > Theme; the Motif DivGeo has
none):
- "light" and "dark": the light and dark theme of b2viewer on every
  window; the drawing area and the distribution graph on a white or dark
  background, the colours of the resources turned into the plotting
  colours of Python (the matplotlib tab colours, lightened in the dark
  theme; greys keep their contrast with the background);
- "classic": the widgets in the light theme of b2viewer, the menu
  bar, the command row and the status line in the background colour of
  the resources, every drawing in the colours of the resources, as the
  Motif DivGeo draws.
In every theme the menus show no underlined mnemonics (they still work).
In light and dark the texts of the drawing area are drawn in the font of
the matplotlib plots (DejaVu Sans) instead of the font of the X server.
A start uses the resource DivGeo.theme, "light" by default."""

import colorsys
import os
import weakref

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ...b2viewer import theme as b2theme
from ..core import resources
from . import modes

NAMES = ("light", "dark", "classic")
LABELS = {"light": "Light mode", "dark": "Dark mode",
          "classic": "DivGeo classic"}

# the tab colour of a resource colour: the one of the nearest hue (degrees)
TAB = ((0, 0xd62728), (30, 0xff7f0e), (60, 0xbcbd22), (120, 0x2ca02c),
       (180, 0x17becf), (240, 0x1f77b4), (270, 0x9467bd), (300, 0xe377c2))
BACKGROUND = {name: int(b2theme.COLORS[key]["control"][1:], 16)
              for name, key in (("light", "Light"), ("dark", "Dark"))}
# the closed parts of the elements (all closed polygons but the outermost):
# the fill of the closed parts of the structure in b2viewer, its
# light colour and the dark display colour of it
STRUCTURE_FILL = 0xe0e0e0

# the menu button of the tool slots: its arrow right of the text
OPTION_BUTTON = """
QToolButton#OptionButton { padding-right: 18px; }
QToolButton#OptionButton::menu-indicator { subcontrol-origin: padding;
    subcontrol-position: center right; right: 4px; }
"""

# the distribution graphs shown, to follow a change of theme
GRAPHS = weakref.WeakSet()

# the theme in use (set by the application)
current = "light"

# texts of the drawing area in light and dark: size (pixels of the view)
TEXT_SIZE = 12
_TEXT_FONT = []
_TEXT_CACHE = {}


class Style(b2theme._Indicators):
    """The style of b2viewer, without underlined mnemonics."""

    def styleHint(self, hint, option=None, widget=None, data=None):
        if hint == QtWidgets.QStyle.SH_UnderlineShortcut:
            return 0
        return super().styleHint(hint, option, widget, data)


def install_style(app):
    """Style on the style of the platform (once), in place of the
    indicators of b2viewer."""
    style = app.style()
    if style is not None and not isinstance(style, Style):
        app.setStyle(Style(style.name()))


def _font(size):
    """DejaVu Sans of matplotlib (its file loaded once into Qt)."""
    if not _TEXT_FONT:
        import matplotlib
        path = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data",
                            "fonts", "ttf", "DejaVuSans.ttf")
        families = QtGui.QFontDatabase.applicationFontFamilies(
            QtGui.QFontDatabase.addApplicationFont(path))
        _TEXT_FONT.append(families[0] if families else "")
    font = QtGui.QFont(_TEXT_FONT[0]) if _TEXT_FONT[0] else QtGui.QFont()
    font.setPixelSize(size)
    return font


def text_pixels(x, y, s, f=1):
    """Pixels of a text drawn with its base line at y, in DejaVu Sans of
    TEXT_SIZE pixels of the view, at f pixels per pixel of the view (x, y
    in those pixels): always the same pixels for the same text, so that
    erasing and XOR work as with the font of the X server."""
    key = (s, f)
    if key not in _TEXT_CACHE:
        font = _font(TEXT_SIZE * f)
        fm = QtGui.QFontMetrics(font)
        pad = 2 * f
        w = max(1, fm.horizontalAdvance(s)) + 2 * pad
        h = fm.ascent() + fm.descent() + 2 * pad
        img = QtGui.QImage(w, h, QtGui.QImage.Format_Grayscale8)
        img.fill(0)
        p = QtGui.QPainter(img)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        p.setFont(font)
        p.setPen(QtGui.QColor(255, 255, 255))
        p.drawText(QtCore.QPointF(pad, pad + fm.ascent()), s)
        p.end()
        a = np.frombuffer(img.constBits(), np.uint8).reshape(
            h, img.bytesPerLine())[:, :w]
        rows, cols = np.nonzero(a >= 128)
        _TEXT_CACHE[key] = (cols - pad, rows - pad - fm.ascent())
    dx, dy = _TEXT_CACHE[key]
    return dx + x, dy + y


def _rgb(pixel):
    return tuple(((pixel >> s) & 255) / 255.0 for s in (16, 8, 0))


def _pixel(rgb):
    r, g, b = (min(255, max(0, int(round(v * 255)))) for v in rgb)
    return (r << 16) | (g << 8) | b


def colour(pixel, name, dark_ground=True):
    """A colour of the resources (0xRRGGBB) in a theme. dark_ground: the
    colour is meant for a dark background (the drawing area) rather than
    a light one (the distribution graph, the panels)."""
    if name == "classic":
        return pixel
    dark = name == "dark"
    r, g, b = _rgb(pixel)
    hi, lo = max(r, g, b), min(r, g, b)
    if hi == 0 or (hi - lo) / hi < 0.25:
        # a grey: as far from the background as in the resources
        level = (r + g + b) / 3.0
        contrast = level if dark_ground else 1.0 - level
        v = 0.12 + 0.8 * contrast if dark else 0.92 - 0.8 * contrast
        return _pixel((v, v, v))
    hue = colorsys.rgb_to_hsv(r, g, b)[0] * 360.0
    tab = min(TAB, key=lambda t: min(abs(hue - t[0]),
                                     360.0 - abs(hue - t[0])))[1]
    if not dark:
        return tab
    return _pixel([0.75 * v + 0.25 for v in _rgb(tab)])


def background(name, pixel):
    """The background of a drawing (classic: pixel, from the resources)."""
    return pixel if name == "classic" else BACKGROUND[name]


def draw_res(res, name):
    """The resources of a drawing area with the colours of a theme."""
    if name == "classic":
        return res
    out = dict(res)
    for field, *_ in modes.COLORS:
        out[field] = (BACKGROUND[name] if field == "pxBackground"
                      else colour(res[field], name))
    out["modernText"] = True
    fill = _rgb(STRUCTURE_FILL)
    out["pxFill"] = _pixel(b2theme._dim(np.array(fill)) if name == "dark"
                           else fill)
    return out


def stylesheet(name, db, shell="DivGeo", cls="DivGeo"):
    """The stylesheet of every window in a theme (db: the resources, for
    the background colour of the classic bars; shell, cls: name and class
    of the program)."""
    b2theme.set_dark(name == "dark")
    sheet = b2theme.stylesheet() + OPTION_BUTTON
    if name == "classic":
        value = db.get([shell, "background"], [cls, "Background"])
        pixel = resources.to_pixel(value) if value else None
        if pixel is not None:
            sheet += ("QMenuBar#menu, QWidget#command, QWidget#msgForm "
                      "{ background-color: #%06x; }\n"
                      "QWidget#command > QWidget "
                      "{ background-color: transparent; }\n" % pixel)
    return sheet
