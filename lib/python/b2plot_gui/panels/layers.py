"""Layers panel: overlay toggles of the 2D tab, each with its own style."""

from dataclasses import replace

from matplotlib import colors as mcolors

from .. import theme
from ..plot.styles import LAYERS, LayerStyle
from ...qt import QtCore, QtGui, QtWidgets, Signal
from .glyphs import LineStyleChooser, SizeChooser, WidthChooser

# Why a layer can be missing in a run
MISSING = {"structure": "No structure.dat or mesh.extra found for this "
                        "run",
           "flux": "No rzpsi.dat found for this run",
           "eirene": "No EIRENE triangles in this run",
           "xpoints": "No X-point in this grid",
           "opoints": "No rzpsi.dat found for this run (it gives the "
                      "O-point)",
           "midplanes": "No rzimp or rzomp in b2.user.parameters, or not "
                        "on the B2.5 grid",
           "targets": "No divertor targets sent by b2plot"}
NO_STYLE = ("opoints", "xpoints")      # rows without a line style
FILL_STYLES = ("empty", "full", "pattern")      # of the structure
MARKER_SIZES = (4, 5, 6, 8, 10, 12, 14, 16, 20)


class ColorButton(QtWidgets.QToolButton):
    """Colour swatch (as drawn in the theme) that opens a colour
    dialog."""

    changed = Signal(str)

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.setAutoRaise(True)
        self.setToolTip("Colour")
        self.clicked.connect(lambda *_: self._pick())
        self.set_color(color)

    def set_color(self, color):
        self._color = QtGui.QColor(color).name()
        self._swatch()

    def _swatch(self):
        base = QtWidgets.QApplication.font().pointSizeF()
        k = self.font().pointSizeF() / base if base > 0 else 1.0
        self.setIconSize(QtCore.QSize(round(18 * k), round(14 * k)))
        pix = QtGui.QPixmap(self.iconSize())     # follows the font
        c = QtGui.QColor(mcolors.to_hex(theme.rgb(self._color)))
        c.setAlphaF(self.opacity())
        pix.fill(c)
        self.setIcon(QtGui.QIcon(pix))

    def opacity(self):
        return 1.0

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.StyleChange:   # theme switched
            self._swatch()

    def color(self):
        return self._color

    def _pick(self):
        c = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._color), self)
        if c.isValid():
            self.set_color(c.name())
            self.changed.emit(self._color)


class LayerColour(ColorButton):
    """Colour and opacity of a layer: the colour dialog with its opacity
    (alpha), the swatch as opaque as the layer; the opacity kept in a
    spin box that is not shown (alpha)."""

    def __init__(self, color, alpha, parent=None):
        super().__init__(color, parent)
        self.alpha = alpha
        self.setToolTip("Colour and opacity")
        alpha.valueChanged.connect(lambda *_: self._swatch())
        self._swatch()

    def opacity(self):
        alpha = getattr(self, "alpha", None)
        return alpha.value() if alpha is not None else 1.0

    def _pick(self):
        c = QtGui.QColor(self._color)
        c.setAlphaF(self.opacity())
        c = QtWidgets.QColorDialog.getColor(
            c, self, "Colour and opacity",
            QtWidgets.QColorDialog.ShowAlphaChannel)
        if c.isValid():
            self.alpha.blockSignals(True)
            self.alpha.setValue(max(c.alphaF(), self.alpha.minimum()))
            self.alpha.blockSignals(False)
            self.set_color(c.name())
            self.changed.emit(self._color)


def style_combo(value="-"):
    return LineStyleChooser(value)


def left_form(parent):
    """A form whose labels and fields are left aligned, the fields as wide
    as the box (on every platform)."""
    form = QtWidgets.QFormLayout(parent)
    form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
    return form


def spin(lo, hi, step, value, decimals=2, tip=""):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setSingleStep(step)
    box.setDecimals(decimals)
    box.setValue(value)
    box.setToolTip(tip)
    box.setKeyboardTracking(False)
    return box


def _narrow(w):
    """A box that shares the room of its column (squeezed with it)."""
    w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                    QtWidgets.QSizePolicy.Fixed)
    w.setMinimumWidth(18)


class LayersPanel(QtWidgets.QGroupBox):
    """One line per overlay: shown (with its name), colour and opacity,
    width (or marker size) and line style; the fill of the structure and
    the levels of the flux surfaces on one more line each."""

    changed = Signal(str, object)

    def __init__(self, styles=None, parent=None):
        super().__init__("Layers", parent)
        self.rows = {}
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(6, 6, 4, 6)     # aligned with the masks
        grid.setHorizontalSpacing(4)
        grid.setColumnStretch(2, 1)         # width and style share the room
        grid.setColumnStretch(3, 1)
        r = 0
        for key, (name, default) in LAYERS.items():
            st = (styles or {}).get(key, default)
            check = QtWidgets.QCheckBox(name)
            check.setChecked(st.visible)
            alpha = spin(0.05, 1.0, 0.1, st.alpha, tip="Opacity")
            alpha.setParent(self)           # in the colour dialog
            alpha.hide()
            color = LayerColour(st.color, alpha)
            width = SizeChooser(st.width, MARKER_SIZES, "Marker size (pt)",
                                {"xpoints": "x"}.get(key, "o")) \
                if key in NO_STYLE else WidthChooser(st.width)
            style = style_combo(st.style) if key not in NO_STYLE else \
                WidthChooser(st.ring)       # the ring of the 3D view
            if key in NO_STYLE:
                style.setToolTip("Width of the ring around the axis in the "
                                 "3D view")
            for w in (width, style):        # narrow: the glyph is enough
                _narrow(w)
            row = dict(check=check, color=color, width=width, style=style,
                       alpha=alpha, levels=None, rho=None,
                       fill_style=None, fill=None, species=None, base=st)
            for c, w in enumerate((check, color, width, style)):
                grid.addWidget(w, r, c)
            r += 1
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
                _narrow(fill_style)
                label = QtWidgets.QLabel("    fill")
                label.setProperty("muted", True)
                grid.addWidget(label, r, 0)
                grid.addWidget(fill, r, 1)
                grid.addWidget(fill_style, r, 2, 1, 2)
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
                rho.addItem("ρₚ", True)
                rho.setCurrentIndex(1 if st.rho else 0)
                _narrow(rho)
                label = QtWidgets.QLabel("    levels")
                label.setProperty("muted", True)
                grid.addWidget(label, r, 0)
                grid.addWidget(levels, r, 1, 1, 2)
                grid.addWidget(rho, r, 3)
                r += 1
                row.update(levels=levels, rho=rho)
                levels.editingFinished.connect(
                    lambda k=key: self._emit(k))
                rho.currentIndexChanged.connect(
                    lambda *_, k=key: self._emit(k))
            if key == "stagnation":     # the species of ua
                species = QtWidgets.QComboBox()
                species.setToolTip("Species of the parallel velocity ua "
                                   "(an ion at first)")
                _narrow(species)
                label = QtWidgets.QLabel("    species")
                label.setProperty("muted", True)
                grid.addWidget(label, r, 0)
                grid.addWidget(species, r, 1, 1, 3)
                r += 1
                row.update(species=species)
                species.currentIndexChanged.connect(
                    lambda *_, k=key: self._emit(k))
            check.toggled.connect(lambda *_: self._enable())
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
                     alpha=row["alpha"].value())
        if key in NO_STYLE:             # the width of the 3D ring
            st = replace(st, ring=row["style"].value())
        else:
            st = replace(st, style=row["style"].currentData())
        if row["levels"] is not None:
            st = replace(st, levels=row["levels"].text(),
                         rho=bool(row["rho"].currentData()))
        if row["fill"] is not None:
            st = replace(st, fill_style=row["fill_style"].currentData(),
                         fill=row["fill"].color())
        if row["species"] is not None and row["species"].count():
            st = replace(st, species=row["species"].currentIndex())
        return st

    def set_species(self, names, current):
        """The species of the stagnation surface (current chosen; the one
        chosen before kept when the names are the same)."""
        box = self.rows["stagnation"]["species"]
        if [box.itemText(i) for i in range(box.count())] == list(names):
            return
        box.blockSignals(True)
        box.clear()
        box.addItems(list(names))
        box.setCurrentIndex(current)
        box.blockSignals(False)

    def styles(self):
        return {key: self.style(key) for key in self.rows}

    def set_available(self, available):
        """Disable the layers the run does not have (e.g. no EIRENE)."""
        self._available = set(available)
        self._enable()

    def set_3d(self, on):
        """The 3D view shown: the widths of the rings of the X- and
        O-points active."""
        self._in3d = bool(on)
        self._enable()

    def set_blocked(self, keys, why=""):
        """Disable the layers keys too (not drawn: why), until set again
        without them; their settings are kept."""
        self._blocked, self._why = set(keys), why
        self._enable()

    def _enable(self):
        available = getattr(self, "_available", set(self.rows))
        blocked = getattr(self, "_blocked", set())
        in3d = getattr(self, "_in3d", False)
        for key, row in self.rows.items():
            on = key in available and key not in blocked
            row["check"].setEnabled(on)
            shown = on and row["check"].isChecked()     # its options
            for w in ("color", "width", "alpha", "fill_style", "fill",
                      "levels", "rho", "species"):
                if row[w] is not None:
                    row[w].setEnabled(shown)
            row["style"].setEnabled(shown and (key not in NO_STYLE or
                                               in3d))
            row["check"].setToolTip(
                "" if on else self._why if key in blocked else
                MISSING.get(key, "Not available in this run"))

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
         ("strata", "Strata labels"))
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
        self.grid = grid = QtWidgets.QGridLayout(self)
        grid.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        grid.setContentsMargins(6, 9, 6, 13)
        grid.setHorizontalSpacing(6)
        space = self.style().layoutSpacing(       # one for every row
            QtWidgets.QSizePolicy.CheckBox, QtWidgets.QSizePolicy.CheckBox,
            QtCore.Qt.Vertical)
        grid.setVerticalSpacing(space if space >= 0 else 6)
        self.checks = {}
        for key, text in MASKS:
            check = QtWidgets.QCheckBox(text)
            check.toggled.connect(lambda on, k=key: self._toggled(k, on))
            self.checks[key] = check
        self.two = None
        self._arrange(True)

    RIGHT = ("labels", "strata")    # the labels in the second column

    def _arrange(self, two):
        """Regions left and labels right, or all in one column when the
        two do not fit the width of the column."""
        if two == self.two:
            return
        self.two = two
        rows = [0, 0]
        for r in range(len(MASKS) + 1):
            self.grid.setRowStretch(r, 0)
        for key, check in self.checks.items():
            c = int(two and key in self.RIGHT)
            self.grid.addWidget(check, rows[c], c)
            rows[c] += 1
        self.grid.setRowStretch(max(rows), 1)   # the room left under them

    def _width(self, keys):
        m = self.grid.contentsMargins()
        return max(self.checks[k].sizeHint().width() for k in keys) + \
            m.left() + m.right() + 2

    def minimumSizeHint(self):          # one column at least
        return QtCore.QSize(self._width(self.checks),
                            super().minimumSizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        left = [k for k in self.checks if k not in self.RIGHT]
        need = self._width(left) + self.grid.horizontalSpacing() + max(
            self.checks[k].sizeHint().width() for k in self.RIGHT)
        self._arrange(self.width() >= need)

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
