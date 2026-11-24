"""Field line section of the quantity column (opened with Field line, at
the right of Chords): the start picked with the mouse, how the line is
drawn (width, style; one colour, or a colour map of the parallel length,
the poloidal length or the toroidal turns), its connection lengths, the profile of the
quantity shown along it with its integral and average (x axis: parallel
length, poloidal length or toroidal turns), Save plot and
Export, the horizontal colour bar of the line under them."""

from matplotlib.colorbar import ColorbarBase
from matplotlib.figure import Figure

from .. import theme
from ..panels.glyphs import CmapChooser, LineStyleChooser, WidthChooser
from ..panels.layers import ColorButton, left_form
from ..panels.plotarea import ScaledCanvas
from ..scaling import squeezable
from ...qt import QtWidgets
from .figure import FigureView
from .sections import _button, _text

LOOK = ("#e6007e", 1.5, "-", "plasma")  # colour, width, style, map
COLOURS = (("one colour", None), ("parallel length", "parallel"),
           ("poloidal length", "poloidal"), ("toroidal turns", "turns"))
XAXES = (("parallel length", "parallel"), ("poloidal length", "poloidal"),
         ("toroidal turns", "turns"))
XLABELS = {"parallel": "parallel length (m)",
           "poloidal": "poloidal length (m)", "turns": "toroidal turns"}


class ColourBar(QtWidgets.QWidget):
    """A horizontal colour bar with its label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5.0, 0.9))
        self.canvas = ScaledCanvas(self.figure)
        h = self.fontMetrics().height()
        self.canvas.setFixedHeight(5 * h)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)
        self.shown = None

    def show_scale(self, norm, cmap, label):
        self.shown = (norm, cmap, label)
        self.figure.clear()
        ax = self.figure.add_axes((0.06, 0.55, 0.88, 0.25))
        color = theme.text()
        self.figure.set_facecolor(theme.figure_bg())
        bar = ColorbarBase(ax, cmap=cmap, norm=norm,
                           orientation="horizontal")
        bar.set_label(label, color=color, fontsize="small")
        ax.tick_params(colors=color, labelsize="small")
        bar.outline.set_edgecolor(color)
        self.canvas.draw_idle()

    def apply_theme(self):
        if self.shown is not None:
            self.show_scale(*self.shown)


class FieldLineSection(QtWidgets.QGroupBox):
    """The widgets of the section (FieldLineTool drives them)."""

    def __init__(self, owner, settings, parent=None):
        super().__init__("Field line", parent)
        self.pick = _button("Pick start", "Click a point of the B2.5 grid "
                            "on the plot (in 3D: on a cut face): the field "
                            "line through it", owner.arm, True)
        self.colour = ColorButton(LOOK[0])
        self.colour.setToolTip("Colour of the field line")
        self.cmap = CmapChooser(LOOK[3], diverging=False)
        self.cmap.hide()                # with a colour scale
        self.width = WidthChooser(LOOK[1])
        self.style = LineStyleChooser(LOOK[2])
        for w in (self.width, self.style, self.cmap):
            w.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                            QtWidgets.QSizePolicy.Fixed)
            w.setMinimumWidth(18)
        clear = _button("Clear", "Remove the field line (in both views)",
                        owner.clear)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.pick)
        top.addWidget(clear)
        look = QtWidgets.QHBoxLayout()
        look.addWidget(self.colour)
        for w in (self.cmap, self.width, self.style):   # share the room
            look.addWidget(w, 1)
        self.by = QtWidgets.QComboBox()
        for text, key in COLOURS:
            self.by.addItem(text, key)
        self.by.setToolTip("The field line in one colour, or coloured by "
                           "the parallel or poloidal length or the "
                           "toroidal turns from "
                           "where it starts (anticlockwise in the 2D plot; "
                           "a closed line from the point picked)")
        self.xaxis = QtWidgets.QComboBox()
        for text, key in XAXES:
            self.xaxis.addItem(text, key)
        self.xaxis.setToolTip("The profile against the parallel length, "
                              "the poloidal length or the toroidal turns "
                              "along the field line, anticlockwise in the "
                              "2D plot")
        form = left_form(None)          # fields as wide as the section
        form.addRow("Colour", self.by)
        form.addRow("Line", look)
        self.conn = _text()
        self.text = _text()
        self.view = FigureView(settings)
        self.view.options.xaxes = False     # the menu of the section
        self.profile = QtWidgets.QWidget()  # with a quantity shown
        rows = QtWidgets.QVBoxLayout(self.profile)
        rows.setContentsMargins(0, 0, 0, 0)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.text, 1)
        row.addWidget(_button("Save plot", "The profile along the field "
                              "line as an image or vector file",
                              lambda: self.view.save()))
        row.addWidget(_button("Export…", "The profile along the field "
                              "line as a CSV file",
                              lambda: self.view.export()))
        rows.addLayout(row)
        xrow = left_form(None)
        xrow.addRow("x axis", self.xaxis)
        rows.addLayout(xrow)
        rows.addWidget(self.view)
        self.bar = ColourBar()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addLayout(form)
        lay.addWidget(self.conn)
        lay.addWidget(self.profile)
        lay.addWidget(self.bar)
        self.profile.hide()
        self.bar.hide()
        squeezable(self)
        for w in (self.colour,):
            w.changed.connect(lambda *_: owner.restyled())
        for w in (self.width, self.style, self.by, self.cmap):
            w.currentIndexChanged.connect(lambda *_: owner.restyled())
        self.by.currentIndexChanged.connect(self._scale)
        self.xaxis.currentIndexChanged.connect(lambda *_: owner.show())

    def _scale(self, *_):
        """The colour map chooser in place of the colour with a colour
        scale."""
        scale = self.by.currentData() is not None
        self.colour.setVisible(not scale)
        self.cmap.setVisible(scale)

    def look(self):
        """(colour, width, line style, colour map)."""
        return (self.colour.color(), self.width.value(),
                self.style.currentData(), self.cmap.name())

    def settings(self):
        return dict(look=list(self.look()[:3]) + [self.cmap.currentText()],
                    by=self.by.currentIndex(), x=self.xaxis.currentIndex())

    def restore(self, d):
        look = list(d.get("look") or LOOK) + list(LOOK[len(d.get("look")
                                                         or LOOK):])
        self.colour.set_color(look[0])
        self.cmap.setCurrentIndex(max(self.cmap.findText(look[3]), 0))
        self.width.setValue(look[1])
        self.style.setCurrentIndex(max(self.style.findData(look[2]), 0))
        self.by.setCurrentIndex(int(d.get("by", 0)))
        self.xaxis.setCurrentIndex(int(d.get("x", 0)))
        self._scale()

    def set_armed(self, on):
        self.pick.blockSignals(True)
        self.pick.setChecked(on)
        self.pick.blockSignals(False)
