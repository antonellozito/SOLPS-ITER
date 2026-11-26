"""Overlay of the 2D plasma plot: the section of the quantity column with
the tree of the quantity drawn as contour lines over the plasma plot
(opened with Overlay), and its options in the right column: the colour
scale and the volume regions (Overlay plot options), the levels and the
lines (Overlay contours)."""

from ...qt import QtWidgets
from .options import LevelsBox, RegionsMenu
from .plotopts import ColourBox, LinesBox


class OverlaySection(QtWidgets.QGroupBox):
    """"Overlay on the plot": the tree of the quantities, as the plasma
    one, for the quantity drawn over the plasma plot."""

    def __init__(self, tree, parent=None):
        super().__init__("Overlay on the plot", parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(tree)


class OverlayOptions:
    """The options of the overlay, always contour lines: colour scale and
    volume regions (as the plasma plot options without the plot type),
    levels and lines (as the Contours section)."""

    def __init__(self):
        self.colour = ColourBox("Overlay plot options", "cool")
        self.regions = RegionsMenu("overlay")
        self.colour.layout().addWidget(self.regions)
        self.levels = LevelsBox()
        self.levels.number.setValue(10)
        self.lines = LinesBox()
        self.lines.fill_lines.hide()        # no fill under them
        self.contours = QtWidgets.QGroupBox("Overlay contours")
        lay = QtWidgets.QVBoxLayout(self.contours)
        lay.addWidget(self.levels)
        lay.addWidget(self.lines)

    def boxes(self):
        """The two groups of the right column."""
        return (self.colour, self.contours)

    def parts(self):
        """The parts giving the style (each with changed)."""
        return (self.colour, self.regions, self.levels, self.lines)
