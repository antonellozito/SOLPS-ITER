"""Layers panel: overlay toggles of the 2D tab, each with its own style."""

from dataclasses import replace

from ..plot.styles import LAYERS, LayerStyle
from ...qt import QtGui, QtWidgets, Signal

# Why a layer can be missing in a run
MISSING = {"structure": "No structure.dat or mesh.extra found for this "
                        "run",
           "flux": "No rzpsi.dat found for this run",
           "eirene": "No EIRENE triangles in this run",
           "xpoints": "No X-point in this grid",
           "midplanes": "No rzimp or rzomp in b2.user.parameters, or not "
                        "on the B2.5 grid",
           "targets": "No divertor targets sent by b2plot"}
NO_STYLE = ("xpoints",)         # rows without a line style
FILL_STYLES = ("empty", "full", "pattern")      # of the structure
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


class LayersPanel(QtWidgets.QGroupBox):
    """Two lines per overlay: shown (with its name), then colour, width,
    line style and opacity under the column heads."""

    changed = Signal(str, object)

    def __init__(self, styles=None, parent=None):
        super().__init__("Layers", parent)
        self.rows = {}
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setHorizontalSpacing(6)
        grid.setColumnMinimumWidth(0, 14)
        grid.setColumnStretch(3, 1)
        for col, text in enumerate(("", "Colour", "Width", "Style",
                                    "Opacity")):
            head = QtWidgets.QLabel(text)
            head.setProperty("muted", True)
            grid.addWidget(head, 0, col)
        r = 1
        for key, (name, default) in LAYERS.items():
            st = (styles or {}).get(key, default)
            check = QtWidgets.QCheckBox(name)
            check.setChecked(st.visible)
            color = ColorButton(st.color)
            width = spin(0.05, 20.0, 0.1, st.width, tip={
                "xpoints": "Marker size (pt)"}.get(key, "Line width (pt)"))
            style = style_combo(st.style)
            style.setSizeAdjustPolicy(
                QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
            style.setMinimumContentsLength(5)
            alpha = spin(0.05, 1.0, 0.1, st.alpha, tip="Opacity")
            for w in (width, alpha):
                w.setMinimumWidth(44)
            if key in NO_STYLE:
                style.setEnabled(False)
            row = dict(check=check, color=color, width=width, style=style,
                       alpha=alpha, levels=None, rho=None,
                       fill_style=None, fill=None, base=st)
            grid.addWidget(check, r, 0, 1, 5)
            for c, w in enumerate((color, width, style, alpha), 1):
                grid.addWidget(w, r + 1, c)
            r += 2
            if key == "structure":      # the fill of the closed parts
                fill = ColorButton(st.fill)
                fill.setToolTip("Fill colour of the closed parts")
                fill_style = QtWidgets.QComboBox()
                for text in FILL_STYLES:
                    fill_style.addItem(text, text)
                fill_style.setCurrentIndex(
                    max(fill_style.findData(st.fill_style), 0))
                fill_style.setToolTip("Fill of the closed parts of the "
                                      "structure: none, full or hatched")
                label = QtWidgets.QLabel("fill")
                label.setProperty("muted", True)
                grid.addWidget(label, r, 0)
                grid.addWidget(fill, r, 1)
                grid.addWidget(fill_style, r, 3)
                r += 1
                row.update(fill_style=fill_style, fill=fill)
                fill_style.currentIndexChanged.connect(
                    lambda *_, k=key: self._emit(k))
                fill.changed.connect(lambda *_, k=key: self._emit(k))
            if key == "flux":
                levels = QtWidgets.QLineEdit(st.levels)
                levels.setToolTip("Levels, separated by blanks")
                rho = QtWidgets.QComboBox()
                rho.addItem("psiN", False)
                rho.addItem("rhop", True)
                rho.setCurrentIndex(1 if st.rho else 0)
                grid.addWidget(QtWidgets.QLabel("levels"), r, 1)
                grid.addWidget(levels, r, 2, 1, 2)
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
        if row["fill"] is not None:
            st = replace(st, fill_style=row["fill_style"].currentData(),
                         fill=row["fill"].color())
        return st

    def styles(self):
        return {key: self.style(key) for key in self.rows}

    def set_available(self, available):
        """Disable the layers the run does not have (e.g. no EIRENE)."""
        for key, row in self.rows.items():
            on = key in available
            for w in ("check", "color", "width", "style", "alpha",
                      "fill_style", "fill"):
                if row[w] is not None:
                    row[w].setEnabled(on and not (key in NO_STYLE and
                                                  w == "style"))
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


MASKS = (("volume", "Volume regions"), ("face", "Face regions"),
         ("topological", "Topological regions"),
         ("labels", "Boundary labels"),
         ("strata", "Recycling strata labels"))
CELL_MASKS = ("volume", "topological")      # filled cells, one at a time
MASK_MISSING = {"volume": "No b2fgmtry with the unstructured geometry",
                "face": "No b2fgmtry with the unstructured geometry",
                "topological": "No b2fgmtry with the unstructured geometry",
                "labels": "No boundary labels in b2fgmtry",
                "strata": "No recycling strata (crcstra 'A') in "
                "b2.neutrals.parameters"}


class MasksPanel(QtWidgets.QGroupBox):
    """Regions and labels of the grid over the plot: cells filled by
    volume or topological region (over the field), faces by face region,
    boundary label or recycling strata (over the wall strip); one of each
    kind at a time, a legend inside the plot."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Masks", parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.checks = {}
        for key, text in MASKS:
            check = QtWidgets.QCheckBox(text)
            check.toggled.connect(lambda on, k=key: self._toggled(k, on))
            lay.addWidget(check)
            self.checks[key] = check

    def _toggled(self, key, on):
        if on:                  # the other mask of the same kind goes off
            same = CELL_MASKS if key in CELL_MASKS else [
                k for k, _ in MASKS if k not in CELL_MASKS]
            for k in same:
                if k != key and self.checks[k].isChecked():
                    self.checks[k].blockSignals(True)
                    self.checks[k].setChecked(False)
                    self.checks[k].blockSignals(False)
        self.changed.emit()

    def wanted(self):
        return [k for k, _ in MASKS if self.checks[k].isChecked() and
                self.checks[k].isEnabled()]

    def set_available(self, available):
        for key, check in self.checks.items():
            check.setEnabled(key in available)
            check.setToolTip("" if key in available else MASK_MISSING[key])
