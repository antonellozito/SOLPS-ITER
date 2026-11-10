"""Light and dark theme of the GUI, as the AUGVIEW shell and its
equilibrium tab: the Qt stylesheet, the figure and axes backgrounds, and
the dark display colour of every plot colour (lines, fills, texts, colour
maps). The theme is one switch for the whole program (set_dark)."""

import numpy as np
from matplotlib import colors as mcolors

from ..qt import QtGui, QtWidgets, Qt

COLORS = {
    "Light": dict(panel="#f0f0f0", control="#ffffff", control_alt="#eeeeee",
                  disabled="#e5e5e5", text="#000000", muted="#606060",
                  disabled_text="#8c8c8c", border="#8a8a8a",
                  soft_border="#b8b8b8", selection="#d9e8f8", tab="#e8e8e8",
                  tab_selected="#ffffff", hover="#f7f7f7", checked="#cfe8ff"),
    "Dark": dict(panel="#262626", control="#1f1f1f", control_alt="#3a3a3a",
                 disabled="#303030", text="#ebebeb", muted="#b8b8b8",
                 disabled_text="#777777", border="#666666",
                 soft_border="#555555", selection="#526d86", tab="#303030",
                 tab_selected="#444444", hover="#4a4a4a", checked="#526d86")}
NAMES = tuple(COLORS)

_dark = False


def set_dark(on):
    global _dark
    _dark = bool(on)


def is_dark():
    return _dark


def name():
    return "Dark" if _dark else "Light"


def figure_bg():
    """Figure background: the panel colour of the window."""
    return COLORS[name()]["panel"]


def axes_bg():
    """Axes background of the map (light grey in the dark theme, so that
    the map colours stay readable)."""
    return "#e0e0e0" if _dark else "#ffffff"


def text():
    """Texts, ticks and frames outside the axes."""
    return "#eeeeee" if _dark else "#000000"


def placeholder():
    """(face, frame, text) of an empty colour bar."""
    return ("#3d3d3d", "#777777", "#aaaaaa") if _dark else (
        "#eeeeee", "#808080", "#777777")


def _dim(rgb):
    """Dark display colours of RGB triples ((3,) or (n, 3)), as the
    AUGVIEW equilibrium tab: white stays, black becomes dark grey, colours
    are desaturated and dimmed."""
    a = np.clip(np.asarray(rgb, float), 0.0, 1.0)
    flat = a.reshape(-1, 3)
    lum = flat @ np.array([0.2126, 0.7152, 0.0722])
    out = np.clip(0.82 * (0.58 * flat + 0.42 * lum[:, None]) + 0.08,
                  0.0, 0.86)
    out[lum < 1e-10] = 0.18
    out[np.all(np.abs(flat - 1.0) < 1e-12, axis=1)] = 1.0
    return out.reshape(a.shape)


def rgb(color):
    """A plot colour as drawn in the current theme ("none", "face" and
    unknown values unchanged)."""
    if not _dark or isinstance(color, str) and color in ("none", "face"):
        return color
    try:
        c = mcolors.to_rgba(color)
    except ValueError:
        return color
    return tuple(float(v) for v in _dim(c[:3])) + (c[3],)


def rgb_array(colors):
    """Colours (a list or an (n, 4) array) in the current theme."""
    if not _dark or len(colors) == 0:
        return colors
    a = np.array(mcolors.to_rgba_array(colors), float)
    a[:, :3] = _dim(a[:, :3])
    return a


def label_color(color):
    """A text colour outside the axes: black follows the theme, other
    colours are lightened in the dark theme."""
    c = mcolors.to_hex(color) if mcolors.is_color_like(color) else "#000000"
    if c == "#000000":
        return text()
    if not _dark:
        return c
    return mcolors.to_hex(0.6 * _dim(mcolors.to_rgb(c)) + 0.4)


def cmap(cm):
    """A colour map in the current theme (sampled and dimmed when
    dark)."""
    if not _dark:
        return cm
    rgba = cm(np.linspace(0.0, 1.0, 256))
    rgba[:, :3] = _dim(rgba[:, :3])
    dark = mcolors.ListedColormap(rgba, name=cm.name + "_dark")
    dark.set_under(rgb(cm.get_under()))
    dark.set_over(rgb(cm.get_over()))
    dark.set_bad(rgb(cm.get_bad()))
    return dark


def stylesheet(font=""):
    """Qt stylesheet of the current theme (AUGVIEW shell): one panel
    colour everywhere, controls with a thin frame; font, e.g. "12.5pt",
    the size of every text (a stylesheet stops the font of the window from
    reaching the widgets)."""
    c = dict(COLORS[name()], font="font-size: %s;" % font if font else "")
    return """
QMainWindow, QWidget {{ background-color: {panel}; color: {text}; {font} }}
QLabel, QCheckBox {{ background-color: transparent; color: {text}; }}
QLabel[muted="true"] {{ color: {muted}; }}
QGroupBox {{ background-color: {panel}; border: 1px solid {border};
    margin-top: 7px; padding-top: 5px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 7px; padding: 0px 2px;
    background-color: {panel}; color: {text}; font-weight: 600; }}
QTabWidget::pane {{ background-color: {panel}; border: 1px solid {border};
    top: -1px; }}
QTabWidget::tab-bar {{ alignment: left; }}
QTabBar::tab {{ background-color: {tab}; color: {text};
    border: 1px solid {border}; border-top-left-radius: 4px;
    border-top-right-radius: 4px; padding: 3px 10px; margin-right: 1px;
    min-height: 16px; }}
QTabBar::tab:hover {{ background-color: {hover}; }}
QTabBar::tab:selected {{ background-color: {tab_selected};
    border-bottom-color: {tab_selected}; font-weight: 600; }}
QLineEdit, QPlainTextEdit, QTableView, QTableWidget, QTreeView,
QListView, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {control}; color: {text}; border: 1px solid {border};
    border-radius: 3px; padding: 1px 4px;
    selection-background-color: {selection}; selection-color: {text}; }}
QTableView, QTableWidget, QTreeView, QListView {{
    gridline-color: {soft_border}; alternate-background-color: {hover};
    border-radius: 0px; padding: 0px; }}
QComboBox {{ padding-right: 16px; }}
QComboBox::drop-down {{ width: 16px; border-left: 1px solid {soft_border};
    border-top-right-radius: 3px; border-bottom-right-radius: 3px;
    background-color: {control_alt}; }}
QComboBox QAbstractItemView {{ background-color: {control}; color: {text};
    border: 1px solid {border}; padding: 3px;
    selection-background-color: {selection}; selection-color: {text};
    outline: 0; }}
QPushButton, QToolButton {{ background-color: {control_alt}; color: {text};
    border: 1px solid {border}; border-radius: 4px; padding: 1px 6px;
    min-height: 16px; }}
QPushButton:hover, QToolButton:hover {{ background-color: {hover}; }}
QPushButton:checked, QToolButton:checked {{ background-color: {checked};
    font-weight: 600; }}
QPushButton:disabled, QToolButton:disabled, QLineEdit:disabled,
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {disabled}; color: {disabled_text};
    border-color: {soft_border}; }}
QCheckBox:disabled, QRadioButton:disabled, QLabel:disabled {{
    color: {disabled_text}; }}
QScrollBar:vertical {{ background-color: {panel}; width: 12px; margin: 0px;
    border: 0px; }}
QScrollBar:horizontal {{ background-color: {panel}; height: 12px;
    margin: 0px; border: 0px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {control_alt}; border: 1px solid {soft_border};
    border-radius: 4px; min-height: 24px; min-width: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QHeaderView::section {{ background-color: {tab}; color: {text};
    border: 1px solid {border}; padding: 2px 3px; font-weight: 600; }}
QScrollArea {{ background-color: {panel}; border: 0px; }}
QMenuBar, QMenu, QStatusBar {{ background-color: {panel}; color: {text}; }}
QMenu::item:selected {{ background-color: {selection}; }}
QToolTip {{ background-color: {control}; color: {text};
    border: 1px solid {border}; padding: 4px; }}
QLabel#readout {{ background-color: {control}; border: 1px solid {border};
    padding: 1px 6px; }}
""".format(**c)


class _Frames(QtWidgets.QProxyStyle):
    """Frames of the check boxes, which a stylesheet leaves without one on
    the Fusion style (Linux, no display), as the Linux AUGVIEW."""

    def drawPrimitive(self, element, option, painter, widget=None):
        super().drawPrimitive(element, option, painter, widget)
        if element != QtWidgets.QStyle.PE_IndicatorCheckBox:
            return
        on = bool(option.state & QtWidgets.QStyle.State_Enabled)
        pen = QtGui.QPen(QtGui.QColor(COLORS[name()][
            "border" if on else "soft_border"]), 1.0)
        pen.setCosmetic(True)
        painter.save()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(pen)
        painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
        painter.restore()


def install_frames(app):
    """The check-box frames on every style but the native macOS one, which
    draws its own."""
    style = app.style() if app is not None else None
    if style is None or isinstance(style, _Frames) or \
            style.name().lower() in ("macos", "macintosh"):
        return
    app.setStyle(_Frames(style.name()))
