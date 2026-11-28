"""Calculator of derived quantities: an expression (expression.py) with a
name and a unit, the presets (presets.py) and the list of the quantities
saved by the user (kept in the settings by the 2D tab). The quantities of
the species of the run with choices are in the plasma tree."""

from ..expression import FUNCTIONS, ExpressionError
from ..presets import PRESETS
from ..scaling import Scaled
from ...qt import QtWidgets, Qt


class CalculatorDialog(Scaled, QtWidgets.QDialog):
    """specs: list of dicts (expr, name, unit), edited in place."""

    def __init__(self, specs, translate, names, expr="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Derived quantities")
        self.specs, self.translate = specs, translate
        lay = QtWidgets.QVBoxLayout(self)
        self.presets = QtWidgets.QComboBox()
        self.presets.addItem("Presets…")
        for group, name, unit, text in PRESETS:
            self.presets.addItem("%s: %s" % (group, name), (name, unit, text))
        self.presets.activated.connect(self._preset)
        self.expr = QtWidgets.QLineEdit(expr)
        self.expr.setPlaceholderText("e.g. ti/te, pvol(sna), te > 10")
        self.expr.setToolTip("Quantities by their b2plot label; + - * / **, "
                             "comparisons, functions: "
                             + ", ".join(sorted(FUNCTIONS)))
        done = QtWidgets.QCompleter(sorted(set(names) | set(FUNCTIONS)),
                                    self)
        done.setCaseSensitivity(Qt.CaseInsensitive)
        self.expr.setCompleter(done)
        self.expr.textChanged.connect(self._check)
        self.name, self.unit = QtWidgets.QLineEdit(), QtWidgets.QLineEdit()
        self.name.setPlaceholderText("name in the list (default: the "
                                     "expression)")
        self.unit.setPlaceholderText("unit, e.g. m^{-3} s^{-1}")
        self.result = QtWidgets.QLabel(" ")
        self.result.setWordWrap(True)
        self.result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        form = QtWidgets.QFormLayout()
        form.addRow(self.presets)
        form.addRow("Expression", self.expr)
        form.addRow("Name", self.name)
        form.addRow("Unit", self.unit)
        form.addRow(self.result)
        lay.addLayout(form)
        self.saved = QtWidgets.QListWidget()
        lay.addWidget(QtWidgets.QLabel("Saved derived quantities"))
        lay.addWidget(self.saved, 1)
        buttons = QtWidgets.QHBoxLayout()
        for text, slot in (("Add", self._add), ("Remove", self._remove),
                           ("Close", self.accept)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda *_, f=slot: f())
            buttons.addWidget(b)
        lay.addLayout(buttons)
        self._fill()
        self._check()
        self.scaled()

    def _fill(self):
        self.saved.clear()
        for s in self.specs:
            self.saved.addItem("%s   [%s]" % (s.get("name") or s["expr"],
                                              s["expr"]))

    def _preset(self, index):
        data = self.presets.itemData(index)
        if data:
            name, unit, text = data
            self.name.setText(name)
            self.unit.setText(unit)
            self.expr.setText(text)

    def _check(self, *_):
        try:
            tokens, kind = self.translate(self.expr.text())
        except ExpressionError as err:
            self.result.setText("Not valid: %s" % err)
            return None
        self.result.setText("b2plot (%s stack): %s" % (
            "Eirene" if kind == "eirene" else "matrix", tokens))
        return tokens

    def _add(self):
        if self._check() is None:
            return
        spec = dict(expr=self.expr.text().strip(), name=self.name.text()
                    .strip(), unit=self.unit.text().strip())
        self.specs[:] = [s for s in self.specs if s["expr"] != spec["expr"]]
        self.specs.append(spec)
        self._fill()

    def _remove(self):
        row = self.saved.currentRow()
        if 0 <= row < len(self.specs):
            del self.specs[row]
            self._fill()
