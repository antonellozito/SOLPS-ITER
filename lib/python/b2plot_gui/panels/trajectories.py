"""Trajectories of test particles (b2plot traj) drawn on demand as a layer:
number of particles, weighting, species, time steps, time colouring and
the cells where they start."""

from ...qt import QtWidgets, Qt, Signal
from .options import _row


class TrajBox(QtWidgets.QGroupBox):
    """Draw asks the tab for the trajectories, Clear removes them."""

    draw = Signal()
    clear = Signal()

    def __init__(self, parent=None):
        super().__init__("Trajectories", parent)
        form = QtWidgets.QFormLayout(self)
        self.particles = QtWidgets.QSpinBox()
        self.particles.setRange(1, 100000)
        self.particles.setValue(1000)
        self.weight = QtWidgets.QComboBox()
        self.weight.addItem("by volume", "volume")
        self.weight.addItem("by the quantity shown", "quantity")
        form.addRow("Particles", _row(self.particles, self.weight))
        self.species = QtWidgets.QListWidget()
        self.species.setMaximumHeight(90)
        self.species.setToolTip("Species whose velocities move the "
                                "particles; one species gives colours by "
                                "flight time, several colours by species")
        form.addRow("Species", self.species)
        self.steps = QtWidgets.QSpinBox()
        self.steps.setRange(1, 1000)
        self.steps.setValue(10)
        self.steps.setToolTip("Time steps of each track (b2plot t_#p)")
        self.log_time = QtWidgets.QCheckBox("log time colours")
        form.addRow("Time steps", _row(self.steps, self.log_time))
        self.start = QtWidgets.QComboBox()
        self.start.addItem("all cells", "all")
        self.start.addItem("where the Only where mask holds", "mask")
        form.addRow("Start in", self.start)
        draw, clear = (QtWidgets.QPushButton(t) for t in ("Draw", "Clear"))
        draw.clicked.connect(lambda *_: self.draw.emit())
        clear.clicked.connect(lambda *_: self.clear.emit())
        form.addRow(_row(draw, clear))

    def set_species(self, names):
        """Species of the run, the first ion checked."""
        self.species.clear()
        first = next((i for i, n in enumerate(names) if "+" in n), 0)
        for i, n in enumerate(names):
            item = QtWidgets.QListWidgetItem(n)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if i == first else Qt.Unchecked)
            self.species.addItem(item)

    def chosen(self):
        return [i for i in range(self.species.count())
                if self.species.item(i).checkState() == Qt.Checked]

    def words(self, weight, mask):
        """b2plot words of a draw: weight and mask are the tokens of the
        quantity shown and of the Only where mask (or empty); time steps,
        time scale and start cells are set each time (b2plot keeps them)."""
        species = self.chosen()
        n = self.particles.value()
        by = self.weight.currentData() == "quantity" and weight
        cells = mask if self.start.currentData() == "mask" and mask else \
            "1 itom"
        return " ".join(["%d t_#p" % self.steps.value(),
                         "logt" if self.log_time.isChecked() else "lint",
                         cells, "icse", "guitraj"] + ([weight] if by else [])
                        + ["%d 0" % (-n if by else n)]
                        + ["%d" % i for i in species]
                        + ["%d traj" % len(species)])
