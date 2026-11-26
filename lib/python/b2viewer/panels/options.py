"""Option groups of the 2D quantity panel: the contour levels (a part of
the Contours section), the menu of the volume regions shown (in the plasma
and the vector plot options) and the labels."""

import numpy as np

from ..plot.styles import LabelStyle
from ..scaling import Number
from ...qt import QtWidgets, Signal
from .layers import ColorButton, left_form, spin

LEVEL_MODES = [("Number of levels", "number"), ("Step", "step"),
               ("List of values", "list"), ("Proportion", "proportion")]


def _row(*widgets, stretch=True):
    box = QtWidgets.QHBoxLayout()
    for w in widgets:
        box.addWidget(w)
    if stretch:
        box.addStretch(1)
    return box


class LevelsBox(QtWidgets.QWidget):
    """How the contour levels are chosen (the top of the Contours
    section)."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = left_form(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.mode = QtWidgets.QComboBox()
        for text, key in LEVEL_MODES:
            self.mode.addItem(text, key)
        self.mode.setToolTip("Proportion: b2plot clvp, equal integral of "
                             "the absolute value between neighbouring "
                             "levels")
        self.number = QtWidgets.QSpinBox()
        self.number.setRange(2, 200)
        self.number.setValue(20)
        self.number.setKeyboardTracking(False)
        self.step = QtWidgets.QLineEdit()
        self.step.setValidator(Number())
        self.step.setPlaceholderText("step from the minimum")
        self.values = QtWidgets.QLineEdit()
        self.values.setPlaceholderText("values separated by blanks")
        self.positive = QtWidgets.QSpinBox()
        self.positive.setRange(1, 200)
        self.positive.setValue(10)
        self.positive.setToolTip("Intervals of the positive values (all "
                                 "values if the negative count is -1)")
        self.negative = QtWidgets.QSpinBox()
        self.negative.setRange(-1, 200)
        self.negative.setValue(-1)
        self.negative.setToolTip("Intervals of the negative values; -1 "
                                 "treats all values together")
        self.form.addRow("Levels", self.mode)
        self.form.addRow("Number", self.number)
        self.form.addRow("Step", self.step)
        self.form.addRow("Values", self.values)
        self.form.addRow("Intervals", _row(self.positive, self.negative))
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.number.valueChanged.connect(lambda *_: self.changed.emit())
        self.positive.valueChanged.connect(lambda *_: self.changed.emit())
        self.negative.valueChanged.connect(lambda *_: self.changed.emit())
        self.step.editingFinished.connect(lambda: self.changed.emit())
        self.values.editingFinished.connect(lambda: self.changed.emit())
        self._mode_changed(emit=False)

    def key(self):
        return self.mode.currentData()

    def _mode_changed(self, *_, emit=True):
        key = self.key()
        for row, on in ((1, key == "number"), (2, key == "step"),
                        (3, key == "list"), (4, key == "proportion")):
            self.form.setRowVisible(row, on)
        if emit:
            self.changed.emit()

    def proportion(self):
        """(positive, negative) intervals of clvp, or None."""
        if self.key() != "proportion":
            return None
        return self.positive.value(), self.negative.value()

    def style_fields(self):
        try:
            step = float(self.step.text())
        except ValueError:
            step = 0.0
        return dict(level_mode=self.key(), levels=self.number.value(),
                    level_step=step, level_list=self.values.text())


class RegionsMenu(QtWidgets.QWidget):
    """The B2.5 cells shown of a plot: "Volume regions shown" and the
    regions checked in a menu (all at first); the button says which."""

    changed = Signal()

    def __init__(self, what, parent=None):
        super().__init__(parent)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.button = QtWidgets.QToolButton()
        self.button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Fixed)
        self.button.setToolTip("The volume regions whose cells the %s "
                               "plot shows" % what)
        self.menu = QtWidgets.QMenu(self.button)
        self.button.setMenu(self.menu)
        row.addWidget(QtWidgets.QLabel("Volume regions shown"))
        row.addWidget(self.button, 1)
        self.checks = []

    def set_geometry(self, g):
        """The volume regions of the run, all shown."""
        self.menu.clear()
        self.checks = []
        for reg, n in zip(*np.unique(g.region[g.visible],
                                     return_counts=True)):
            c = QtWidgets.QCheckBox("Region %d (%d cells)" % (reg, n))
            c.region = int(reg)
            c.setChecked(True)
            c.toggled.connect(self._toggled)
            act = QtWidgets.QWidgetAction(self.menu)  # the menu stays open
            act.setDefaultWidget(c)
            self.menu.addAction(act)
            self.checks.append(c)
        self._label()

    def _toggled(self, *_):
        self._label()
        self.changed.emit()

    def _label(self):
        on = [c.region for c in self.checks if c.isChecked()]
        self.button.setText("all" if len(on) == len(self.checks) else
                            ", ".join(str(r) for r in on) or "none")

    def style_fields(self):
        """regions, None when all are shown."""
        out = dict(ix_range=None, iy_range=None, regions=None)
        if self.checks and not all(c.isChecked() for c in self.checks):
            out["regions"] = tuple(c.region for c in self.checks
                                   if c.isChecked())
        return out


class LabelsBox(QtWidgets.QGroupBox):
    """Texts of the plot (b2plot xlab, ylab, lbsz, bold, noax and xcol);
    ${NAME} and `date` are expanded as in b2plot."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Labels", parent)
        form = left_form(self)
        self.title = QtWidgets.QLineEdit()
        self.xlabel = QtWidgets.QLineEdit()
        self.xlabel.setPlaceholderText("R (m)")
        self.ylabel = QtWidgets.QLineEdit()
        self.ylabel.setPlaceholderText("Z (m)")
        for w in (self.title, self.xlabel, self.ylabel):
            w.setToolTip("${NAME}: environment, RUN, HOST or TIME; `date`; "
                         "^{...} and _{...} for super- and subscripts")
            w.setClearButtonEnabled(True)
            w.editingFinished.connect(lambda: self.changed.emit())
        self.size = spin(0.5, 3.0, 0.1, 1.0, 1, "Label size (b2plot lbsz)")
        self.bold = QtWidgets.QCheckBox("bold")
        self.axes = QtWidgets.QCheckBox("axes")
        self.axes.setChecked(True)
        self.axes.setToolTip("Axes, ticks and axis labels (b2plot noax)")
        self.color = ColorButton("#000000")
        form.addRow("Title", _row(self.title, self.color, stretch=False))
        form.addRow("x label", self.xlabel)
        form.addRow("y label", self.ylabel)
        form.addRow("Size", _row(self.size, self.bold, self.axes))
        self.size.valueChanged.connect(lambda *_: self.changed.emit())
        for w in (self.bold, self.axes):
            w.toggled.connect(lambda *_: self.changed.emit())
        self.color.changed.connect(lambda *_: self.changed.emit())

    def set_title_hint(self, text):
        self.title.setPlaceholderText(text)

    def style(self):
        return LabelStyle(
            title=self.title.text(), xlabel=self.xlabel.text(),
            ylabel=self.ylabel.text(), size=self.size.value(),
            bold=self.bold.isChecked(), axes=self.axes.isChecked(),
            color=self.color.color())
