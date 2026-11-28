"""The choices of a quantity of the plasma tree that has them
(presets.ENTRIES: Radiation, Light, Atomic rates, Neutral collisions): a
menu each, those depending on the choice above filled again when it
changes (the choice kept where it is offered), the plot following each
choice."""

from ...qt import QtWidgets, Signal
from .layers import left_form


class ChoicesBox(QtWidgets.QGroupBox):
    """The menus of the choices of one entry (presets.Entry) for the
    species of the run (presets.Species)."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Choices", parent)
        self.form = left_form(self)
        self.note = QtWidgets.QLabel()      # a choice with nothing to offer
        self.note.setWordWrap(True)
        self.note.setProperty("muted", True)
        self.entry, self.species = None, None
        self.combos, self.offered = [], []

    def set_entry(self, entry, species, labels=()):
        """The menus of entry, filled with the choices of species (the
        labels given chosen where offered)."""
        self.entry, self.species = entry, species
        while self.form.rowCount():
            if self.form.itemAt(0, QtWidgets.QFormLayout.SpanningRole) \
                    is not None:
                self.form.takeRow(0)    # the note: kept
            else:
                self.form.removeRow(0)
        self.setTitle(entry.title)
        self.combos, self.offered = [], []
        for k, (label, _) in enumerate(entry.params):
            combo = QtWidgets.QComboBox()
            combo.setToolTip("%s of %s" % (label, entry.title))
            combo.currentIndexChanged.connect(lambda _, k=k: self._chosen(k))
            self.form.addRow(label, combo)
            self.combos.append(combo)
            self.offered.append([])
        self.form.addRow(self.note)
        self._fill(0, list(labels))

    def _fill(self, start, labels=()):
        """Menus from start on filled from the choices before them, each
        keeping its choice (or the label given) where offered."""
        for k in range(start, len(self.combos)):
            combo, kind = self.combos[k], self.entry.params[k][1]
            keep = labels[k] if k < len(labels) else combo.currentText()
            before = self.items(k)
            items = self.species.choices(kind, before) if \
                self.species is not None and before is not None else []
            self.offered[k] = list(items)
            combo.blockSignals(True)
            combo.clear()
            combo.addItems([self.species.label(kind, x) for x in items])
            combo.setCurrentIndex(max(combo.findText(keep), 0) if items
                                  else -1)
            combo.blockSignals(False)
        empty = [label for (label, _), offered in zip(self.entry.params,
                                                       self.offered)
                 if not offered]
        self.note.setText("Nothing to choose for this run: %s" % ", ".join(
            empty).lower() if empty else "")
        self.note.setVisible(bool(empty))

    def _chosen(self, k):
        self._fill(k + 1)
        self.changed.emit()

    def items(self, upto=None):
        """The items chosen in the menus (before menu upto), None while a
        menu has nothing to offer."""
        out = []
        for combo, offered in zip(self.combos[:upto], self.offered):
            i = combo.currentIndex()
            if i < 0 or i >= len(offered):
                return None
            out.append(offered[i])
        return out

    def labels(self):
        return [c.currentText() for c in self.combos]
