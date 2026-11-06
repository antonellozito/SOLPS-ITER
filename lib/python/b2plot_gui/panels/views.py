"""View bar of the 2D tab: view presets of the run, saved views and the
R, Z box of the view."""

import json

from ...qt import QtGui, QtWidgets, Signal


class ViewBar(QtWidgets.QWidget):
    """Presets, Save view and the box editor of a Plot2D."""

    moved = Signal()            # the view changed (zoom, pan, preset)

    def __init__(self, plot, toolbar, settings, parent=None):
        super().__init__(parent)
        self.plot, self.toolbar, self.settings = plot, toolbar, settings
        self.combo = QtWidgets.QComboBox()
        self.combo.setToolTip("View presets and saved views")
        self.combo.activated.connect(self._chosen)
        save = QtWidgets.QToolButton()
        save.setText("Save view")
        save.clicked.connect(lambda *_: self._save())
        self.box = []
        for tip in ("R min (m)", "R max (m)", "Z min (m)", "Z max (m)"):
            e = QtWidgets.QLineEdit()
            e.setValidator(QtGui.QDoubleValidator())
            e.setToolTip(tip + "; the box is widened to the equal aspect")
            e.setMaximumWidth(64)
            e.editingFinished.connect(self._edited)
            self.box.append(e)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QtWidgets.QLabel("View"))
        row.addWidget(self.combo)
        row.addWidget(save)
        row.addSpacing(12)
        row.addWidget(QtWidgets.QLabel("R"))
        row.addWidget(self.box[0])
        row.addWidget(self.box[1])
        row.addWidget(QtWidgets.QLabel("Z"))
        row.addWidget(self.box[2])
        row.addWidget(self.box[3])
        row.addStretch(1)

    def set_run(self):
        """Presets of the run plotted, then the saved views."""
        for signal in ("xlim_changed", "ylim_changed"):
            self.plot.ax.callbacks.connect(signal, self._moved)
        self._moved()
        self._fill()

    def _fill(self):
        self.combo.clear()
        for name, box in self.plot.views().items():
            self.combo.addItem(name, box)
        saved = self._saved()
        if saved:
            self.combo.insertSeparator(self.combo.count())
            for name, box in saved.items():
                self.combo.addItem(name, tuple(box))

    def _saved(self):
        try:
            return json.loads(self.settings.value("views2d", "") or "{}")
        except ValueError:
            return {}

    def _show(self, box):
        self.plot.set_view(box)
        self.toolbar.push_current()
        self.plot.fig.canvas.draw_idle()

    def _chosen(self, index):
        box = self.combo.itemData(index)
        if box:
            self._show(box)

    def _save(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save view",
                                                  "Name of this view")
        if ok and name.strip():
            saved = self._saved()
            saved[name.strip()] = list(self.plot.get_view())
            self.settings.setValue("views2d", json.dumps(saved))
            self._fill()

    def _moved(self, *_):
        for e, v in zip(self.box, self.plot.get_view()):
            e.setText("%.4g" % v)
        self.moved.emit()

    def _edited(self):
        try:
            box = [float(e.text()) for e in self.box]
        except ValueError:
            return
        if box[1] > box[0] and box[3] > box[2]:
            self._show(box)
