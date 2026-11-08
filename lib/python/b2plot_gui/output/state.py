"""Plot settings of the 2D tab as a dictionary (JSON files): the
quantity, its species and plot type, every option of the quantity
panel, the layers and the view. Saved settings are templates for any
run; several of them make a set of maps on the page composer."""

import json

from ..panels.layers import ColorButton
from ...qt import QtCore, QtWidgets, Qt

SKIP = {"search", "play", "slider", "tree", "info", "current", "partial",
        "base"}
PANELS = __package__.rsplit(".", 1)[0] + ".panels"
VALUES = (ColorButton, QtWidgets.QComboBox, QtWidgets.QAbstractButton,
          QtWidgets.QAbstractSpinBox, QtWidgets.QLineEdit,
          QtWidgets.QListWidget)


def _widgets(obj, prefix="", seen=None):
    """(path, widget) of the value widgets of obj: its attributes, the
    items of its lists and dicts, the boxes and rows of the panels
    package inside them."""
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return
    seen.add(id(obj))
    items = obj.items() if isinstance(obj, dict) else enumerate(obj) \
        if isinstance(obj, (list, tuple)) else vars(obj).items()
    for key, w in items:
        if isinstance(key, str) and (key.startswith("_") or key in SKIP):
            continue
        path = "%s%s" % (prefix, key)
        if isinstance(w, VALUES):
            yield path, w
        elif isinstance(w, (list, tuple, dict)) or \
                type(w).__module__.startswith(PANELS):
            yield from _widgets(w, path + ".", seen)


def _get(w):
    if isinstance(w, ColorButton):
        return w.color()
    if isinstance(w, QtWidgets.QComboBox):
        return w.currentText()
    if isinstance(w, QtWidgets.QAbstractButton):
        return w.isChecked() if w.isCheckable() else None
    if isinstance(w, QtWidgets.QAbstractSpinBox):
        return w.value()
    if isinstance(w, QtWidgets.QLineEdit):
        return w.text()
    return [i for i in range(w.count())
            if w.item(i).checkState() == Qt.Checked]


def _set(w, v):
    w.blockSignals(True)
    if isinstance(w, ColorButton):
        w.set_color(v)
    elif isinstance(w, QtWidgets.QComboBox):
        i = w.findText(v)
        if i >= 0:
            w.setCurrentIndex(i)
        elif w.isEditable():
            w.setEditText(v)
    elif isinstance(w, QtWidgets.QAbstractButton):
        w.setChecked(bool(v))
    elif isinstance(w, QtWidgets.QAbstractSpinBox):
        w.setValue(v)
    elif isinstance(w, QtWidgets.QLineEdit):
        w.setText(v)
    else:
        for i in range(w.count()):
            w.item(i).setCheckState(Qt.Checked if i in v else Qt.Unchecked)
    w.blockSignals(False)


def _values(obj):
    return {p: v for p, v in ((p, _get(w)) for p, w in _widgets(obj))
            if v is not None}


def capture(tab):
    """The plot settings of a Tab2D."""
    panel = tab.quantity
    return {"quantity": tab.wanted.name if tab.wanted else None,
            "species": panel.species.currentText(), "kind": panel.kind(),
            "seeds": [[float(x), float(y)] for x, y in panel.streams.seeds],
            "view": [float(v) for v in tab.plot.get_view()],
            "panel": _values(panel), "layers": _values(tab.layers.rows),
            "run": tab.run.rundir if tab.run is not None else ""}


def restore(tab, st, view=True):
    """Apply plot settings to a Tab2D (one fetch at the end); False if the
    run has no such quantity."""
    panel = tab.quantity
    for obj, values in ((panel, st.get("panel", {})),
                        (tab.layers.rows, st.get("layers", {}))):
        for path, w in _widgets(obj):
            if path in values:
                _set(w, values[path])
    for key in tab.layers.rows:
        tab.layers._emit(key)
    panel.time_box._layout(emit=False)
    panel.streams.seeds = [tuple(p) for p in st.get("seeds", [])]
    panel.wanted_species = st.get("species")
    tab._set_quantities()
    ok = panel.select(st.get("quantity") or "te")
    for b in panel.kind_buttons.buttons():
        if b.property("kind") == st.get("kind") and b.isEnabled():
            b.setChecked(True)
    panel._kind_changed()
    if view and st.get("view"):
        tab.plot.set_view(st["view"])
    return ok


def save(path, st):
    with open(path, "w") as f:
        json.dump(st, f, indent=1)


def load(path):
    with open(path) as f:
        st = json.load(f)
    if not isinstance(st, dict) or "panel" not in st:
        raise ValueError("%s holds no plot settings" % path)
    return st


class MapsJob:
    """Settings files applied one after the other to a Tab2D, each plot
    added to the page composer once it is drawn."""

    def __init__(self, tab):
        self.tab = tab
        self.job = None

    def start(self, paths):
        todo = []
        for p in paths:
            try:
                todo.append((p, load(p)))
            except (OSError, ValueError) as err:
                self.tab.status.emit("Skipped %s: %s" % (p, err))
        self.job = dict(todo=todo, added=0, missing=[])
        self._next()

    def _next(self):
        tab, job = self.tab, self.job
        while job["todo"]:
            path, st = job["todo"][0]
            if restore(tab, st):
                if tab._shown():
                    QtCore.QTimer.singleShot(0, self.ready)
                return
            job["missing"].append(st.get("quantity"))
            job["todo"].pop(0)
        self.job = None
        tab.status.emit("%d maps added to the page composer%s" % (
            job["added"], "; not in this run: " + ", ".join(
                map(str, job["missing"])) if job["missing"] else ""))

    def ready(self):
        """The plot of the current settings drawn: to the page."""
        tab, job = self.tab, self.job
        if job is None or not job["todo"] or not tab._shown():
            return
        job["todo"].pop(0)
        snap = tab.snapshot()
        if snap is not None:
            tab.add_to_page.emit(snap)
            job["added"] += 1
        self._next()
