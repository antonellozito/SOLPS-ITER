"""Layers panel: overlay toggles of the 2D tab, each with its own style."""

from dataclasses import replace

from ..plot2d import LAYERS, LayerStyle
from ..qt import QtGui, QtWidgets, Signal

# Why a layer can be missing in a run
MISSING = {"device": "No structure.dat found for this run",
           "structure": "No mesh.extra found for this run",
           "flux": "No rzpsi.dat found for this run",
           "eirene": "No EIRENE triangles in this run",
           "xpoints": "No X-point in this grid"}
LINESTYLES = [("solid", "-"), ("dashed", "--"), ("dotted", ":"),
              ("dash-dot", "-.")]


class ColorButton(QtWidgets.QToolButton):
    """Colour swatch that opens a colour dialog."""

    changed = Signal(str)

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.setAutoRaise(True)
        self.setToolTip("Colour")
        self.clicked.connect(lambda *_: self._pick())
        self.set_color(color)

    def set_color(self, color):
        self._color = QtGui.QColor(color).name()
        pix = QtGui.QPixmap(18, 14)
        pix.fill(QtGui.QColor(self._color))
        self.setIcon(QtGui.QIcon(pix))

    def color(self):
        return self._color

    def _pick(self):
        c = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._color), self)
        if c.isValid():
            self.set_color(c.name())
            self.changed.emit(self._color)


def style_combo(value="-"):
    combo = QtWidgets.QComboBox()
    for text, ls in LINESTYLES:
        combo.addItem(text, ls)
    combo.setCurrentIndex(max(combo.findData(value), 0))
    return combo


def spin(lo, hi, step, value, decimals=2, tip=""):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setSingleStep(step)
    box.setDecimals(decimals)
    box.setValue(value)
    box.setToolTip(tip)
    box.setKeyboardTracking(False)
    return box


class LayersPanel(QtWidgets.QWidget):
    """One row per overlay: shown, colour, width, line style, opacity."""

    changed = Signal(str, object)

    def __init__(self, styles=None, parent=None):
        super().__init__(parent)
        self.rows = {}
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setHorizontalSpacing(6)
        for col, text in enumerate(("Layer", "", "Width", "Style",
                                    "Opacity")):
            head = QtWidgets.QLabel(text)
            head.setStyleSheet("color: palette(mid);")
            grid.addWidget(head, 0, col)
        r = 1
        for key, (name, default) in LAYERS.items():
            st = (styles or {}).get(key, default)
            check = QtWidgets.QCheckBox(name)
            check.setChecked(st.visible)
            color = ColorButton(st.color)
            width = spin(0.05, 20.0, 0.1, st.width, tip="Line width (pt)"
                         if key != "xpoints" else "Marker size (pt)")
            style = style_combo(st.style)
            alpha = spin(0.05, 1.0, 0.1, st.alpha, tip="Opacity")
            if key == "xpoints":
                style.setEnabled(False)
            row = dict(check=check, color=color, width=width, style=style,
                       alpha=alpha, levels=None, rho=None, base=st)
            for c, w in enumerate((check, color, width, style, alpha)):
                grid.addWidget(w, r, c)
            r += 1
            if key == "flux":
                levels = QtWidgets.QLineEdit(st.levels)
                levels.setToolTip("Levels, separated by blanks")
                rho = QtWidgets.QComboBox()
                rho.addItem("\u03c8N", False)
                rho.addItem("\u03c1pol", True)
                rho.setCurrentIndex(1 if st.rho else 0)
                grid.addWidget(QtWidgets.QLabel("   levels"), r, 0)
                grid.addWidget(levels, r, 1, 1, 3)
                grid.addWidget(rho, r, 4)
                r += 1
                row.update(levels=levels, rho=rho)
                levels.editingFinished.connect(
                    lambda k=key: self._emit(k))
                rho.currentIndexChanged.connect(
                    lambda *_, k=key: self._emit(k))
            check.toggled.connect(lambda *_, k=key: self._emit(k))
            color.changed.connect(lambda *_, k=key: self._emit(k))
            width.valueChanged.connect(lambda *_, k=key: self._emit(k))
            style.currentIndexChanged.connect(lambda *_, k=key: self._emit(k))
            alpha.valueChanged.connect(lambda *_, k=key: self._emit(k))
            self.rows[key] = row
        grid.setRowStretch(r, 1)

    def style(self, key):
        row = self.rows[key]
        st = replace(row["base"], visible=row["check"].isChecked(),
                     color=row["color"].color(),
                     width=row["width"].value(),
                     style=row["style"].currentData(),
                     alpha=row["alpha"].value())
        if row["levels"] is not None:
            st = replace(st, levels=row["levels"].text(),
                         rho=bool(row["rho"].currentData()))
        return st

    def styles(self):
        return {key: self.style(key) for key in self.rows}

    def set_available(self, available):
        """Disable the layers the run does not have (e.g. no EIRENE)."""
        for key, row in self.rows.items():
            on = key in available
            for w in ("check", "color", "width", "style", "alpha"):
                row[w].setEnabled(on and not (key == "xpoints"
                                              and w == "style"))
            row["check"].setToolTip("" if on else MISSING.get(
                key, "Not available in this run"))

    def _emit(self, key):
        self.changed.emit(key, self.style(key))


def as_dict(style):
    return dict(style.__dict__)


def from_dict(d, default):
    try:
        return LayerStyle(**{**default.__dict__, **d})
    except TypeError:
        return default

