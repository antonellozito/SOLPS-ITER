"""The run line over the tabs: run directory (without the runs folder of
the session), coupled or standalone, the grid, the plasma species by
element (D(0,+1), N(0,...,+7)) and, for a coupled run, the EIRENE atom,
molecule and test ion species. The run directory is shortened in the
middle when the line does not fit; the whole line is its tool tip."""

import re

from ..b2plot import labels
from ..qt import QtCore, QtWidgets, Qt

SEP = " - "
EIRENE = (("atom", "a"), ("molecule", "m"), ("test ion", "i"))


def _elements(names):
    """{element: [charge texts]} of the plasma species, in their order."""
    groups = {}
    for name in names:
        m = re.match(r"^([A-Za-z]+)(.*)$", labels.species_text(name) or "")
        if m:
            groups.setdefault(m.group(1), []).append(m.group(2) or "0")
    return groups


def compact(names):
    """Plasma species by element: D(0,+1), N(0,...,+7) (charge states in
    a row of more than three shortened)."""
    groups = _elements(names)
    out = []
    for element, charges in groups.items():
        try:
            z = [int(c) for c in charges]
        except ValueError:
            z = None
        if z and len(z) > 3 and z == list(range(z[0], z[0] + len(z))):
            charges = [charges[0], "...", charges[-1]]
        out.append("%s(%s)" % (element, ",".join(charges)))
    return ", ".join(out)


def details(run, eirene):
    """The line of a run after its directory, from the run information
    of b2plot; eirene maps a, m, i to the species names b2plot sent
    (massa, massm, massi)."""
    info, g = run.info or {}, run.geometry
    coupled = bool(info.get("with_eirene"))
    grid = "%d cells, %d faces, %s grid" % (
        info.get("nCv", len(g.cells)), info.get("nFc", 0),
        "classical" if g.classical else "unstructured")
    if coupled:
        grid += ", %d triangles" % info.get("ntrii", 0)
    plasma = info.get("species", [])
    species = ["Plasma species: " + compact(plasma)]
    if coupled:
        spell = {e.upper(): e for e in _elements(plasma)}  # HE as He
        species += ["%s species: %s" % (word, ", ".join(
            spell.get(n.upper(), n) if k == "a" else n for n in eirene[k]))
            for word, k in EIRENE if eirene.get(k)]
    return "".join(SEP + p for p in ("coupled" if coupled else "standalone",
                                     grid, ", ".join(species)))


class RunLine(QtWidgets.QLabel):
    """The line: set(head, tail) shows tail whole and head (the run
    directory) shortened in the middle if needed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parts = ("", "")
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Preferred)

    def set(self, head, tail=""):
        self.parts = (head, tail)
        self.setToolTip(head + tail)
        self._fit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.FontChange,
                            QtCore.QEvent.StyleChange):
            self._fit()

    def _fit(self):
        head, tail = self.parts
        fm = self.fontMetrics()
        room = self.contentsRect().width() - fm.horizontalAdvance(tail) - 6
        room = max(room, fm.horizontalAdvance("/abc\u2026xyz"))
        self.setText(fm.elidedText(head, Qt.ElideMiddle, room) + tail)
