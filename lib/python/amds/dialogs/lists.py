"""The scrolled lists of the dialogs (XmCreateScrolledList NAME in
NAMESW): browse or extended selection (resource selectionPolicy), the
selection callbacks once per click of the user, and the list functions of
the Motif front end."""

from PySide6 import QtCore, QtWidgets

from ...divgeo.dialogs import vacreate as vc


class XmList(QtWidgets.QListWidget):
    def __init__(self, parent, name, policy=None):
        super().__init__(parent)
        vc._setup(self, parent, name, "XmList")
        names, classes = vc.path_of(parent)
        self.xm_names = names + [name + "SW", name]
        self.xm_classes = classes + ["XmScrolledWindow", "XmList"]
        self.policy = (policy or vc.resource_string(
            self, "selectionPolicy", "SelectionPolicy", "browse_select")
            ).lower().replace("xm", "")
        self.extended = self.policy in ("extended_select", "multiple_select")
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection if self.extended
            else QtWidgets.QAbstractItemView.SingleSelection)
        self.selection_callbacks = []
        self.default_callbacks = []
        self.top_pos = 1
        self.itemSelectionChanged.connect(self._selection)
        self.itemDoubleClicked.connect(
            lambda item: self._default(self.row(item) + 1))

    def _selection(self):
        for cb in list(self.selection_callbacks):
            cb()

    def _default(self, pos):
        for cb in list(self.default_callbacks):
            cb(pos)

    def select(self, pos, add):
        """A click on position pos (from 1), a Ctrl+click (add) in an
        extended list: one selection callback."""
        if pos < 1 or pos > self.count():
            return
        self.blockSignals(True)
        if not add or not self.extended:
            self.clearSelection()
        self.item(pos - 1).setSelected(True)
        self.setCurrentRow(pos - 1, QtCore.QItemSelectionModel.NoUpdate)
        self.blockSignals(False)
        self._selection()

    def select_pos(self, pos):
        """XmListSelectPos without notify: the item selected, the others
        deselected (browse and extended lists)."""
        self.blockSignals(True)
        self.clearSelection()
        self.item(pos - 1).setSelected(True)
        self.blockSignals(False)

    def deselect_pos(self, pos):
        """XmListDeselectPos."""
        self.blockSignals(True)
        self.item(pos - 1).setSelected(False)
        self.blockSignals(False)

    def positions(self):
        """XmListGetSelectedPos: the selected positions from 1."""
        return [k + 1 for k in range(self.count())
                if self.item(k).isSelected()]

    def set_items(self, items):
        """XmListDeleteAllItems and XmListAddItems: no selection."""
        self.blockSignals(True)
        self.clear()
        self.top_pos = 1
        self.addItems(items)
        self.blockSignals(False)

    def set_items_keep(self, items):
        """SetXmListItems: the selected items selected again by text with
        XmListSelectItem, which keeps only the last one."""
        selected = [self.item(k).text() for k in range(self.count())
                    if self.item(k).isSelected()]
        self.set_items(items)
        self.blockSignals(True)
        for text in selected:
            for k in range(self.count()):
                if self.item(k).text() == text:
                    self.clearSelection()
                    self.item(k).setSelected(True)
                    break
        self.blockSignals(False)


def scrolled_list(parent, name, policy=None):
    lst = XmList(parent, name, policy)
    parent.xm_place(lst)
    return lst
