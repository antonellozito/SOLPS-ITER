"""Dialog contents built as the Motif front end builds them
(CreateWidgetSystem, vacreate.c): a flat list of descriptions such as
"x#?:name" (type, flags, name) followed by the arguments of the flags, so
that the dialogs keep the code of their Motif callbacks. Widgets carry
the Motif names, classes and resource paths; forms are laid out as tables
(the # positions) or rows. Also the readers of text fields (strtod and
sscanf as the C library) and the option menus."""

import re
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import resources

MAXDOUBLE = sys.float_info.max
MAXINT = 2147483647
_INT_MIN = -2147483648

# strtod of the C library: decimal, hexadecimal, inf and nan, after spaces
_SPACES = " \t\n\v\f\r"
_NUMBER = re.compile(
    r"[+-]?(?:0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)"
    r"(?:[pP][+-]?[0-9]+)?|(?:[0-9]+\.?[0-9]*|\.[0-9]+)"
    r"(?:[eE][+-]?[0-9]+)?|[iI][nN][fF](?:[iI][nN][iI][tT][yY])?"
    r"|[nN][aA][nN](?:\([0-9A-Za-z_]*\))?)")


def strtod(s):
    """(value, rest) as strtod; rest is s when nothing is converted."""
    t = s.lstrip(_SPACES)
    m = _NUMBER.match(t)
    if m is None:
        return 0.0, s
    text = m.group(0)
    body = text.lstrip("+-")
    sign = -1.0 if text.startswith("-") else 1.0
    if body[:2] in ("0x", "0X"):
        b = body
        if "p" not in b.lower():
            b += "p0"
        if b[2:3] == ".":
            b = b[:2] + "0" + b[2:]
        value = sign * float.fromhex(b)
    elif body[:1] in "nN":
        value = float("nan")
    else:
        value = sign * float(body.split("(")[0])
    return value, t[m.end():]


def scan_double(s):
    """sscanf(s, "%lf%s", ...): the number of fields converted (0, 1 or
    2: something after the number) and the number."""
    value, rest = strtod(s)
    if rest is s:
        return 0, 0.0
    return (2 if rest.strip(_SPACES) else 1), value


def _trunc(s):
    return s.strip(_SPACES)


def is_text_empty(w):
    """IsXmTextEmpty."""
    return not _trunc(text_of(w))


def get_text_double(w):
    """GetXmTextDouble: MAXDOUBLE when the text is not a number."""
    s1 = _trunc(text_of(w))
    value, rest = strtod(s1)
    if not s1 or rest:
        return MAXDOUBLE
    return value


def get_text_int(w):
    """GetXmTextInt: (int)strtod, MAXINT when the text is not a number."""
    s1 = _trunc(text_of(w))
    value, rest = strtod(s1)
    if not s1 or rest:
        return MAXINT
    if value != value:
        return 0
    # the conversion of the machine: saturated
    return int(max(_INT_MIN, min(MAXINT, int(value) if abs(value) <
                                 1e300 else (MAXINT if value > 0
                                             else _INT_MIN))))


def text_of(w):
    if isinstance(w, QtWidgets.QLineEdit):
        return w.text()
    return w.toPlainText()


def set_text(w, s):
    """XmTextSetString."""
    if isinstance(w, QtWidgets.QLineEdit):
        w.setText(s)
    else:
        w.setPlainText(s)


# Resources ###############################################################

def path_of(widget):
    """The resource path (names, classes) of a widget of a dialog."""
    from .base import XmDialog
    if isinstance(widget, XmDialog):
        return widget.path()
    return list(widget.xm_names), list(widget.xm_classes)


def _db(widget):
    from .base import XmDialog
    w = widget
    while not isinstance(w, XmDialog):
        w = w.xm_dialog
    return w.window_.application.db


def resource(widget, name, cls=None):
    """A resource of a widget, None if not set."""
    names, classes = path_of(widget)
    return _db(widget).get(names + [name], classes + [cls or name])


def resource_string(widget, name, cls=None, default=None):
    """GetResourceString: class and default are the name when not
    given."""
    value = resource(widget, name, cls)
    if value is None:
        return name if default is None else default
    return value


def resource_int(widget, name, cls=None, default=0):
    """GetResourceInt (the Xt conversion of a string to an int)."""
    value = resource(widget, name, cls)
    v = resources.to_int(value) if value is not None else None
    return default if v is None else v


def resource_bool(widget, name, cls=None, default=False):
    value = resource(widget, name, cls)
    v = resources.to_bool(value) if value is not None else None
    return default if v is None else v


def mnemonic_free(text):
    """A label for a Qt button: & shown as it is."""
    return text.replace("&", "&&")


# Widgets #################################################################

def _setup(widget, parent, name, cls):
    names, classes = path_of(parent)
    widget.setObjectName(name)
    widget.xm_class = cls
    widget.xm_names = names + [name]
    widget.xm_classes = classes + [cls]
    widget.xm_dialog = parent if not hasattr(parent, "xm_dialog") else \
        parent.xm_dialog
    widget.xm_user = None
    return widget


def label_string(widget):
    return resource_string(widget, "labelString", "LabelString",
                           widget.objectName())


class Label(QtWidgets.QLabel):
    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmLabel")
        self.setTextFormat(QtCore.Qt.PlainText)
        self.setText(label_string(self))

    def set_label(self, text):
        self.setText(text)


class PushButton(QtWidgets.QPushButton):
    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmPushButton")
        self.setText(mnemonic_free(label_string(self)))
        self.setAutoDefault(False)

    def set_label(self, text):
        self.setText(mnemonic_free(text))


class ToggleButton(QtWidgets.QCheckBox):
    """XmToggleButton: valueChanged callbacks on every change of state
    (XmToggleButtonSetState with notify)."""

    def __init__(self, parent, name, radio=False):
        super().__init__(parent)
        _setup(self, parent, name, "XmToggleButton")
        self.setText(mnemonic_free(label_string(self)))
        self.setChecked(resource_bool(self, "set", "Set"))

    def set_state(self, state, notify):
        """XmToggleButtonSetState."""
        if self.isChecked() == bool(state):
            return
        if notify:
            self.setChecked(bool(state))
        else:
            self.blockSignals(True)
            self.setChecked(bool(state))
            self.blockSignals(False)
            self.update()


class RadioToggle(QtWidgets.QRadioButton):
    """A toggle of a radio box: setting it unsets the others of the box,
    each with its callbacks."""

    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmToggleButton")
        self.setText(mnemonic_free(label_string(self)))
        self.setChecked(resource_bool(self, "set", "Set"))

    set_state = ToggleButton.set_state


class Text(QtWidgets.QLineEdit):
    """XmText (one line): valueChanged callbacks on every change."""

    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmText")
        self.setText(resource_string(self, "value", "Value", ""))
        columns = resource_int(self, "columns", "Columns", 0)
        if columns:
            self.setMinimumWidth(self.fontMetrics().averageCharWidth() *
                                 (columns + 2))


class ScrolledText(QtWidgets.QPlainTextEdit):
    """XmCreateScrolledText: an XmText in NAMESW (multi-line)."""

    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmText")
        names, classes = path_of(parent)
        self.xm_names = names + [name + "SW", name]
        self.xm_classes = classes + ["XmScrolledWindow", "XmText"]
        self.setPlainText(resource_string(self, "value", "Value", ""))
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        fm = self.fontMetrics()
        columns = resource_int(self, "columns", "Columns", 0)
        rows = resource_int(self, "rows", "Rows", 0)
        if columns:
            self.setMinimumWidth(fm.averageCharWidth() * (columns + 4))
        if rows:
            self.setMinimumHeight(fm.lineSpacing() * (rows + 1))


class Separator(QtWidgets.QFrame):
    def __init__(self, parent, name, vertical=False):
        super().__init__(parent)
        _setup(self, parent, name, "XmSeparator")
        self.setFrameShape(QtWidgets.QFrame.VLine if vertical
                           else QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class Form(QtWidgets.QWidget):
    """XmForm: children in a table (# positions, or userData x*256+y with
    Form2Table) or one below the other; a child attached with 4 has the
    next one at its right."""

    def __init__(self, parent, name, cls="XmForm"):
        super().__init__(parent)
        _setup(self, parent, name, cls)
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.items = []

    def xm_place(self, w, x=None, y=None, attach=None):
        self.items.append([w, x, y, attach])
        self.relayout()

    def set_table(self, w, x, y):
        for item in self.items:
            if item[0] is w:
                item[1], item[2] = x, y
        self.relayout()

    def relayout(self):
        for w, *_ in self.items:
            self.grid.removeWidget(w)
        table = [it for it in self.items if it[1] is not None]
        last_row = max([it[2] for it in table] + [0])
        row, col = last_row + 1, 1
        for w, x, y, attach in self.items:
            if x is not None:
                self.grid.addWidget(w, y or 1, x or 1, -1 if y == 0 else 1,
                                    -1 if x == 0 else 1)
                continue
            self.grid.addWidget(w, row, col)
            if attach == "4":
                col += 1
            else:
                row, col = row + 1, 1


class Frame(QtWidgets.QFrame):
    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmFrame")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        lay = QtWidgets.QVBoxLayout(self)
        margin = resource_int(self, "marginWidth", "MarginWidth", 3)
        lay.setContentsMargins(margin, margin, margin, margin)

    def xm_place(self, w, x=None, y=None, attach=None):
        self.layout().addWidget(w)


class RowColumn(QtWidgets.QWidget):
    """XmRowColumn in one row (horizontal) or column; a radio box keeps
    one of its toggles set."""

    def __init__(self, parent, name, horizontal=True, radio=False):
        super().__init__(parent)
        _setup(self, parent, name, "XmRowColumn")
        self.radio = radio or resource_bool(self, "radioBehavior",
                                            "RadioBehavior")
        lay = QtWidgets.QHBoxLayout(self) if horizontal else \
            QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        if self.radio:
            self.group = QtWidgets.QButtonGroup(self)
            self.group.setExclusive(True)

    def xm_place(self, w, x=None, y=None, attach=None):
        self.layout().addWidget(w)
        if self.radio and isinstance(w, QtWidgets.QAbstractButton):
            self.group.addButton(w)


def radio_box(parent, name, orientation="horizontal"):
    """XmCreateRadioBox."""
    return RowColumn(parent, name, orientation == "horizontal", radio=True)


def row_column(parent, name, orientation="horizontal"):
    """XmCreateRowColumn."""
    return RowColumn(parent, name, orientation == "horizontal")


class ScrolledList(QtWidgets.QListWidget):
    """XmCreateScrolledList: an XmList in NAMESW; browse selection and
    default action as callbacks."""

    def __init__(self, parent, name, browse=True):
        super().__init__(parent)
        _setup(self, parent, name, "XmList")
        names, classes = path_of(parent)
        self.xm_names = names + [name + "SW", name]
        self.xm_classes = classes + ["XmScrolledWindow", "XmList"]
        if browse:
            self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.browse_callbacks = []
        self.default_callbacks = []
        self.itemSelectionChanged.connect(self._browse)
        self.itemActivated.connect(lambda item: self._default())
        rows = resource_int(self, "visibleItemCount", "VisibleItemCount", 0)
        if rows:
            self.setMinimumHeight(self.sizeHintForRow(0) * rows
                                  if self.count() else 18 * rows)

    def _browse(self):
        if self.selectedItems():
            for cb in list(self.browse_callbacks):
                cb()

    def _default(self):
        for cb in list(self.default_callbacks):
            cb()

    def set_items(self, items):
        """XmListDeleteAllItems, XmListAddItem for each item."""
        self.blockSignals(True)
        self.clear()
        self.addItems(items)
        self.blockSignals(False)

    def set_items_keep_selection(self, items):
        """SetXmListItems: the selected items selected again, without the
        callbacks."""
        selected = [i.text() for i in self.selectedItems()]
        self.blockSignals(True)
        self.clear()
        self.addItems(items)
        for text in selected:
            for k in range(self.count()):
                if self.item(k).text() == text:
                    self.item(k).setSelected(True)
                    break
        self.blockSignals(False)

    def select_pos(self, pos, notify):
        """XmListSelectPos (pos from 1)."""
        if pos < 1 or pos > self.count():
            return
        self.blockSignals(True)
        self.clearSelection()
        self.setCurrentRow(pos - 1)
        self.item(pos - 1).setSelected(True)
        self.blockSignals(False)
        if notify:
            self._browse()

    def selected_positions(self):
        """XmListGetSelectedPos: the positions from 1."""
        return [k + 1 for k in range(self.count())
                if self.item(k).isSelected()]

    def sel_pos(self):
        """GetXmListSelPos: the selected position from 0, -1 if none or
        more."""
        pos = self.selected_positions()
        return pos[0] - 1 if len(pos) == 1 else -1


def scrolled_list(parent, name, browse=True):
    return ScrolledList(parent, name, browse)


class ScrolledWindow(QtWidgets.QScrollArea):
    """XmCreateScrolledWindow (automatic scrolling): its work window is in
    ClipWindow."""

    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmScrolledWindow")
        self.setWidgetResizable(True)

    def set_work_window(self, w):
        """XmNworkWindow."""
        w.xm_names = self.xm_names + ["ClipWindow", w.objectName()]
        w.xm_classes = self.xm_classes + ["XmClipWindow", w.xm_class]
        self.setWidget(w)

    def xm_place(self, w, x=None, y=None, attach=None):
        pass


def scrolled_window(parent, name):
    return ScrolledWindow(parent, name)


class ArrowButton(QtWidgets.QToolButton):
    """XmArrowButton."""

    def __init__(self, parent, name, direction="up"):
        super().__init__(parent)
        _setup(self, parent, name, "XmArrowButton")
        self.set_direction(direction)

    def set_direction(self, direction):
        self.direction = direction
        self.setArrowType({"up": QtCore.Qt.UpArrow,
                           "down": QtCore.Qt.DownArrow,
                           "left": QtCore.Qt.LeftArrow,
                           "right": QtCore.Qt.RightArrow}[direction])


class DrawingArea(QtWidgets.QWidget):
    """XmDrawingArea: the size from its resources; its window is an image
    its user draws into; resize and input as callbacks."""

    def __init__(self, parent, name):
        super().__init__(parent)
        _setup(self, parent, name, "XmDrawingArea")
        self.image = None
        self.resize_callbacks = []
        self.input_handler = None
        self.setMinimumSize(resource_int(self, "width", "Width", 0) or 1,
                            resource_int(self, "height", "Height", 0) or 1)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        if self.image is not None:
            p = QtGui.QPainter(self)
            p.drawImage(0, 0, self.image)
            p.end()

    def resizeEvent(self, event):
        for cb in self.resize_callbacks:
            cb(self)

    def _input(self, kind, event):
        if self.input_handler is not None:
            self.input_handler(kind, event)

    def mousePressEvent(self, event):
        self._input("press", event)

    def mouseMoveEvent(self, event):
        self._input("motion", event)

    def mouseReleaseEvent(self, event):
        self._input("release", event)

    def enterEvent(self, event):
        self._input("enter", event)

    def leaveEvent(self, event):
        self._input("leave", event)


def drawing_area(parent, name):
    return DrawingArea(parent, name)


class Pulldown(QtCore.QObject):
    """XmCreatePulldownMenu: the shell popup_NAME and the menu NAME, its
    push buttons as actions (shown by the option menu)."""

    def __init__(self, parent, name):
        super().__init__(parent)
        names, classes = path_of(parent)
        self.setObjectName(name)
        self.xm_pulldown = True
        self.xm_names = names + ["popup_" + name, name]
        self.xm_classes = classes + ["XmMenuShell", "XmRowColumn"]
        self.xm_dialog = parent if not hasattr(parent, "xm_dialog") else \
            parent.xm_dialog
        self.items = []

    def add_item(self, name):
        act = QtGui.QAction(self)
        act.setObjectName(name)
        act.xm_names = self.xm_names + [name]
        act.xm_classes = self.xm_classes + ["XmPushButton"]
        act.xm_dialog = self.xm_dialog
        act.xm_user = None
        act.setText(mnemonic_free(label_string(act)))
        self.items.append(act)
        return act


class _Choice:
    """An item of an option menu for the user: chosen, then its activate
    callbacks."""

    def __init__(self, menu, action):
        self.name = action.objectName()
        self.action = action
        self.menu = menu

    def callback(self):
        self.action.trigger()


class OptionMenu(QtWidgets.QWidget):
    """XmCreateOptionMenu: OptionLabel and OptionButton (gadgets); the
    chosen item is the menu history."""

    def __init__(self, parent, name, pulldown):
        super().__init__(parent)
        from .base import gadget
        _setup(self, parent, name, "XmRowColumn")
        self.xm_option = True
        self.pulldown = pulldown
        self._history = None
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = gadget(QtWidgets.QLabel(self), "XmLabelGadget")
        self.label.setObjectName("OptionLabel")
        self.label.setText(resource_string(self, "labelString",
                                           "LabelString", ""))
        self.button = gadget(QtWidgets.QPushButton(self),
                             "XmCascadeButtonGadget")
        self.button.setObjectName("OptionButton")
        self.button.setAutoDefault(False)
        self.button.clicked.connect(self._post)
        lay.addWidget(self.label)
        lay.addWidget(self.button, 1)
        for act in pulldown.items:
            self._watch(act)
        visible = [a for a in pulldown.items if a.isVisible()]
        self.set_history(visible[0] if visible else None)

    def _watch(self, act):
        act.triggered.connect(lambda checked=False, a=act:
                              self.set_history(a))
        act.changed.connect(lambda a=act: self._changed(a))

    def _changed(self, act):
        if act is self._history:
            self.button.setText(act.text())

    def _post(self):
        menu = QtWidgets.QMenu(self)
        for act in self.pulldown.items:
            if act.isVisible():
                menu.addAction(act)
        menu.exec(self.button.mapToGlobal(QtCore.QPoint(0, 0)),
                  self._history)
        menu.deleteLater()

    @property
    def history(self):
        return self._history.objectName() if self._history else None

    @history.setter
    def history(self, name):
        for act in self.pulldown.items:
            if act.objectName() == name:
                self.set_history(act)
                return

    def set_history(self, act):
        """XmNmenuHistory."""
        self._history = act
        self.button.setText(act.text() if act is not None else "")

    @property
    def entries(self):
        return [_Choice(self, a) for a in self.pulldown.items
                if a.isVisible()]


def get_option_menu_value(om):
    """GetOptionMenuValue: the userData of the chosen item."""
    return om._history.xm_user


def set_option_menu_value(om, value):
    """SetOptionMenuValue: False when no item has the value."""
    for act in om.pulldown.items:
        if act.xm_user == value:
            om.set_history(act)
            return True
    return False


def set_option_menu_items(om, items):
    """SetOptionMenuItems: labels and values of the first items (push
    buttons item added as needed), the others unmanaged, the first one
    chosen."""
    pd = om.pulldown
    while len(pd.items) < len(items):
        om._watch(pd.add_item("item"))
    for act, (label, value) in zip(pd.items, items):
        act.setText(mnemonic_free(label))
        act.xm_user = value
        act.setVisible(True)
    for act in pd.items[len(items):]:
        act.setVisible(False)
    om.set_history(pd.items[0] if pd.items else None)


def add_callback_to_tree(pulldown, callback, data):
    """AddCallbackToTree on the push buttons of a pulldown (activate)."""
    for act in pulldown.items:
        act.triggered.connect(lambda checked=False, a=act:
                              callback(a, data))


# CreateWidgetSystem ######################################################

_PLAIN = {"x": Text, "t": ToggleButton, "b": PushButton, "l": Label}


def create_widget_system(parent, *args, refs=None):
    """CreateWidgetSystem: refs receives the widgets of ? (by key)."""
    _create(parent, 0, iter(args), refs if refs is not None else {})


def _make(kind, parent, name):
    if isinstance(parent, Pulldown):
        if kind != "b":
            raise ValueError("CreateWidgetSystem: %s in a pulldown" % kind)
        return parent.add_item(name)
    if kind == "t" and getattr(parent, "radio", False):
        return RadioToggle(parent, name)
    return _PLAIN[kind](parent, name)


def _place(parent, w, x, y, attach):
    if isinstance(w, (QtGui.QAction, Pulldown)):
        return
    parent.xm_place(w, x, y, attach)


def _create(parent, nest, it, refs):
    w = None
    while True:
        s = next(it, None)
        if s is None:
            return True
        j = s.find(":")
        if j < 0:
            raise ValueError("CreateWidgetSystem: missing ':' in %r" % s)
        name = s[j + 1:]
        kind = s[0]
        i = 0
        go_child = False
        if kind in "xtbl":
            w = _make(kind, parent, name)
        elif kind == "s":
            vertical = s[1:2] == "|"
            if s[1:2] in ("-", "|"):
                i += 1
            w = Separator(parent, name, vertical)
        elif kind == "$":
            creator = next(it)
            options = next(it)
            w = creator(parent, name, **(options or {}))
            if s[1:2] == "+":
                i += 1
                go_child = True
        elif kind == "f":
            w = Frame(parent, name)
            go_child = True
        elif kind == "#":
            w = Form(parent, name)
            go_child = True
        elif kind == "-":
            if nest <= 0:
                raise ValueError("CreateMenuSystem()-!parent: fatal error 2")
            return False
        elif kind == "*":
            w = Pulldown(parent, name)
            go_child = True
        elif kind == "o":
            w = OptionMenu(parent, name, w)
        else:
            raise ValueError("CreateVaWidgetSystem - Bad type:%s" % s)
        x = y = attach = None
        hidden = False
        for c in s[i + 1:j]:
            if c in "24685":
                attach = c
            elif c == "#":
                x, y = next(it), next(it)
            elif c == "A":
                cb, data = next(it), next(it)
                _activate_signal(w).connect(
                    lambda checked=False, f=cb, ww=w, d=data: f(ww, d))
            elif c == "T":
                cb, data = next(it), next(it)
                _value_signal(w).connect(
                    lambda *a, f=cb, ww=w, d=data: f(ww, d))
            elif c == "@":
                w.xm_user = next(it)
            elif c == "?":
                refs[next(it)] = w
            elif c == "=":
                value = next(it)
                if isinstance(w, QtWidgets.QAbstractButton):
                    w.set_state(value, True)
                else:
                    set_text(w, value)
            elif c == "_":
                hidden = True
            elif c in " \n\b":
                pass
            else:
                raise ValueError("CreateMenuSystem()-syntax %s" % s)
        if hidden:
            w.hide()
        _place(parent, w, x, y, attach)
        if go_child and _create(w, nest + 1, it, refs):
            return True


def _activate_signal(w):
    return w.triggered if isinstance(w, QtGui.QAction) else w.clicked


def _value_signal(w):
    if isinstance(w, QtWidgets.QAbstractButton):
        return w.toggled
    return w.textChanged


def form2table(form):
    """Form2Table: the table positions from the userData (x*256+y)."""
    for item in form.items:
        u = item[0].xm_user or 0
        item[1], item[2] = u // 256, u % 256
    form.relayout()


def manage(w, state):
    """XtManageChild, XtUnmanageChild."""
    w.setVisible(bool(state))
