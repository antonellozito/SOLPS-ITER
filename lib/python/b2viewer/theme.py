"""Light and dark theme of the GUI: the Qt stylesheet, the figure and
axes backgrounds, and the dark display colour of every plot colour (lines,
fills, texts, colour maps). The theme is one switch for the whole program
(set_dark)."""

import numpy as np
from matplotlib import colors as mcolors

from ..qt import QtCore, QtGui, QtWidgets, Qt

COLORS = {
    "Light": dict(panel="#f0f0f0", control="#ffffff", control_alt="#eeeeee",
                  disabled="#e5e5e5", text="#000000", muted="#606060",
                  disabled_text="#8c8c8c", border="#8a8a8a",
                  soft_border="#b8b8b8", selection="#d9e8f8", tab="#e8e8e8",
                  hover="#f7f7f7", checked="#cfe8ff"),
    "Dark": dict(panel="#262626", control="#1f1f1f", control_alt="#3a3a3a",
                 disabled="#303030", text="#ebebeb", muted="#b8b8b8",
                 disabled_text="#777777", border="#666666",
                 soft_border="#555555", selection="#526d86", tab="#303030",
                 hover="#4a4a4a", checked="#526d86")}
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
    """Dark display colours of RGB triples ((3,) or (n, 3)): white
    stays, black becomes dark grey, colours are desaturated and dimmed."""
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
    """Qt stylesheet of the current theme: one panel
    colour everywhere, controls with a thin frame; font, e.g. "12.5pt",
    the size of every text (a stylesheet stops the font of the window from
    reaching the widgets). Titles (of the groups, the column heads, the
    tabs, widgets with the property bold) in bold, in the size of the
    texts."""
    base = QtWidgets.QApplication.font().pointSizeF()
    size = float(font[:-2]) if font.endswith("pt") else base if base > 0 \
        else 13.0
    k = size / (base if base > 0 else 13.0)     # sizes follow the font
    c = dict(COLORS[name()], accent=ACCENT,
             font="font-size: %s;" % font if font else "",
             title="font-size: %s;" % (font or "%.2fpt" % (
                 base if base > 0 else 13.0)),
             gap=round(0.9 * size),     # under a group title
             **{"px%d" % n: max(round(n * k), 1) for n in (2, 3, 4, 6, 7, 12,
                                                           14, 16, 24)})
    return """
QMainWindow, QWidget {{ background-color: {panel}; color: {text}; {font} }}
QLabel, QCheckBox {{ background-color: transparent; color: {text}; }}
QLabel[muted="true"] {{ color: {muted}; }}
*[bold="true"] {{ font-weight: bold; }}
QGroupBox {{ background-color: {panel}; border: 1px solid {border};
    margin-top: {px7}px; padding-top: {gap}px; font-weight: bold; {title} }}
QGroupBox::title {{ subcontrol-origin: margin; left: {px7}px;
    padding: 0px {px2}px;
    background-color: {panel}; color: {text}; }}
QTabBar::tab {{ background-color: {tab}; color: {text};
    border: 1px solid {border}; border-bottom: 0px; padding: {px3}px {px14}px;
    margin-right: {px2}px; border-top-left-radius: 4px;
    border-top-right-radius: 4px; font-weight: bold; {title} }}
QTabBar::tab:selected {{ background-color: {control}; }}
QTabBar::tab:disabled {{ color: {disabled_text}; }}
QLineEdit, QPlainTextEdit, QTableView, QTableWidget, QTreeView,
QListView, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {control}; color: {text}; border: 1px solid {border};
    border-radius: 3px; padding: 1px {px4}px;
    selection-background-color: {selection}; selection-color: {text}; }}
QTableView, QTableWidget, QTreeView, QListView {{
    gridline-color: {soft_border}; alternate-background-color: {hover};
    border-radius: 0px; padding: 0px; }}
QComboBox {{ padding-right: {px16}px; }}
QComboBox::drop-down {{ width: {px16}px; border-left: 1px solid {soft_border};
    border-top-right-radius: 3px; border-bottom-right-radius: 3px;
    background-color: {control_alt}; }}
QComboBox QAbstractItemView {{ background-color: {control}; color: {text};
    border: 1px solid {border}; padding: {px3}px;
    selection-background-color: {selection}; selection-color: {text};
    outline: 0; }}
QPushButton, QToolButton {{ background-color: {control_alt}; color: {text};
    border: 1px solid {border}; border-radius: 4px; padding: 1px {px6}px;
    min-height: {px16}px; }}
QPushButton:hover, QToolButton:hover {{ background-color: {hover}; }}
QPushButton:checked, QToolButton:checked {{ background-color: {checked};
    font-weight: 600; }}
QPushButton:disabled, QToolButton:disabled, QLineEdit:disabled,
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {disabled}; color: {disabled_text};
    border-color: {soft_border}; }}
QCheckBox:disabled, QRadioButton:disabled, QLabel:disabled {{
    color: {disabled_text}; }}
QScrollBar:vertical {{ background-color: {panel}; width: {px12}px;
    margin: 0px; border: 0px; }}
QScrollBar:horizontal {{ background-color: {panel}; height: {px12}px;
    margin: 0px; border: 0px; }}
QSlider::groove:horizontal {{ height: {px4}px; background: {soft_border};
    border-radius: {px2}px; }}
QSlider::sub-page:horizontal {{ background: {accent};
    border-radius: {px2}px; }}
QSlider::handle:horizontal {{ background: {control};
    border: 1px solid {border}; width: {px14}px; margin: -{px6}px 0px;
    border-radius: {px7}px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {control_alt}; border: 1px solid {soft_border};
    border-radius: 4px; min-height: {px24}px; min-width: {px24}px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QHeaderView::section {{ background-color: {tab}; color: {text};
    border: 1px solid {border}; padding: {px2}px {px3}px; font-weight: bold;
    {title} }}
QScrollArea {{ background-color: {panel}; border: 0px; }}
QMenuBar, QMenu, QStatusBar {{ background-color: {panel}; color: {text}; }}
QMenu::item:selected {{ background-color: {selection}; }}
QToolTip {{ background-color: {control}; color: {text};
    border: 1px solid {border}; padding: {px4}px; }}
""".format(**c)


ACCENT = "#2f7ae5"                # check boxes and radio buttons on


class _Indicators(QtWidgets.QProxyStyle):
    """Check boxes and radio buttons drawn the same way on every platform
    and theme (a stylesheet leaves the native ones without a visible frame
    when off): a framed box or circle, blue with a white mark when on; the
    arrows of the open and closed branches of a tree in the text colour."""

    SCALED = (QtWidgets.QStyle.PM_IndicatorWidth,
              QtWidgets.QStyle.PM_IndicatorHeight,
              QtWidgets.QStyle.PM_ExclusiveIndicatorWidth,
              QtWidgets.QStyle.PM_ExclusiveIndicatorHeight,
              QtWidgets.QStyle.PM_CheckBoxLabelSpacing,
              QtWidgets.QStyle.PM_RadioButtonLabelSpacing,
              QtWidgets.QStyle.PM_LayoutLeftMargin,
              QtWidgets.QStyle.PM_LayoutTopMargin,
              QtWidgets.QStyle.PM_LayoutRightMargin,
              QtWidgets.QStyle.PM_LayoutBottomMargin,
              QtWidgets.QStyle.PM_LayoutHorizontalSpacing,
              QtWidgets.QStyle.PM_LayoutVerticalSpacing)

    def pixelMetric(self, metric, option=None, widget=None):
        """The sizes of indicators and the spacing of layouts follow the
        font of the widget (a window scaled with its size)."""
        v = super().pixelMetric(metric, option, widget)
        if metric in self.SCALED and widget is not None and v > 0:
            base = QtWidgets.QApplication.font().pointSizeF()
            size = widget.font().pointSizeF()
            if base > 0 and size > 0:
                return max(round(v * size / base), 1)
        return v

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QtWidgets.QStyle.PE_IndicatorBranch:
            self._branch(option, painter)
            return
        box = element == QtWidgets.QStyle.PE_IndicatorCheckBox
        if not box and element != QtWidgets.QStyle.PE_IndicatorRadioButton:
            super().drawPrimitive(element, option, painter, widget)
            return
        c = COLORS[name()]
        state = option.state
        enabled = bool(state & QtWidgets.QStyle.State_Enabled)
        on = bool(state & (QtWidgets.QStyle.State_On |
                           QtWidgets.QStyle.State_NoChange))
        side = min(option.rect.width(), option.rect.height()) - 2
        r = QtCore.QRectF(0, 0, side, side)
        r.moveCenter(QtCore.QRectF(option.rect).center())
        fill = ACCENT if on and enabled else c["disabled"] if not enabled \
            else c["control"]
        edge = ACCENT if on and enabled else c[
            "border" if enabled else "soft_border"]
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(edge), 1.0))
        painter.setBrush(QtGui.QColor(fill))
        if box:
            painter.drawRoundedRect(r, 3.0, 3.0)
        else:
            painter.drawEllipse(r)
        if on:
            mark = QtGui.QColor("#ffffff" if enabled else c["disabled_text"])
            if box:
                pen = QtGui.QPen(mark, max(side / 7.0, 1.5))
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                x, y, w = r.x(), r.y(), r.width()
                painter.drawPolyline([QtCore.QPointF(x + u * w, y + v * w)
                                      for u, v in ((0.24, 0.52), (0.43, 0.70),
                                                   (0.76, 0.31))])
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(mark)
                painter.drawEllipse(r.center(), 0.2 * side, 0.2 * side)
        painter.restore()


    @staticmethod
    def _branch(option, painter):
        """A filled triangle, down when open, right when closed (nothing
        for an item without children)."""
        if not option.state & QtWidgets.QStyle.State_Children:
            return
        r = QtCore.QRectF(option.rect)
        c = r.center()
        h = max(min(r.width(), r.height()) * 0.18, 3.0)
        pts = ((-h, -0.6 * h), (h, -0.6 * h), (0.0, 0.8 * h)) if \
            option.state & QtWidgets.QStyle.State_Open else \
            ((-0.6 * h, -h), (0.8 * h, 0.0), (-0.6 * h, h))
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(COLORS[name()]["text"]))
        painter.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(c.x() + x,
                                                            c.y() + y)
                                             for x, y in pts]))
        painter.restore()


def install_indicators(app):
    """The check boxes and radio buttons of _Indicators on the style of the
    platform (once)."""
    style = app.style() if app is not None else None
    if style is not None and not isinstance(style, _Indicators):
        app.setStyle(_Indicators(style.name()))
