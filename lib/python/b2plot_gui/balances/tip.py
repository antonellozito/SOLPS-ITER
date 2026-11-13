"""A floating window near the mouse with the equation of a term (its
name, a thin rule, then the equation drawn by matplotlib mathtext; a
group: each of its terms with its name, under thin rules), in the font
size of the window it belongs to."""

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from .. import theme
from ...qt import QtGui, QtWidgets, Qt
from . import style

PAD = 0.6                           # font sizes around the text
SKIP = 0.45                         # font sizes between a name and its text
RULE = 0.7                          # font sizes from a rule to the text
GAP = 18                            # pixels from the mouse


def render(title, parts, points, dpi):
    """QPixmap of the name (bold) over the equations parts [(name or
    None, equation)], text of the theme on a transparent background;
    points: font size, dpi: pixels per inch (logical dpi times the device
    pixel ratio)."""
    _, _, text, grid = style.axes_colors()
    fig = Figure(dpi=dpi)
    fig.patch.set_alpha(0.0)
    canvas = FigureCanvasAgg(fig)
    em = points / 72.0 * dpi                    # pixels of one font size
    blocks = [(fig.text(0, 0, title, fontsize=points, fontweight="bold",
                        color=text, va="top", ha="left"), 0.0, False)]
    for name, eq in parts:
        rule = True                     # a thin line over each part
        if name is not None:
            blocks.append((fig.text(0, 0, name, fontsize=points,
                                    fontweight="bold", color=text,
                                    va="top", ha="left", alpha=0.75),
                           (2 * RULE if rule else SKIP) * em, rule))
        blocks.append((fig.text(0, 0, eq, fontsize=points, color=text,
                                va="top", ha="left"),
                       SKIP * em if name is not None else
                       (2 * RULE if rule else SKIP) * em,
                       rule and name is None))
    renderer = canvas.get_renderer()
    sizes = [t.get_window_extent(renderer) for t, _, _ in blocks]
    w = max(b.width for b in sizes) + 2 * PAD * em
    h = sum(b.height + skip for b, (_, skip, _) in zip(sizes, blocks)) + \
        2 * PAD * em
    fig.set_size_inches(w / dpi, h / dpi)
    y = PAD * em
    for b, (t, skip, rule) in zip(sizes, blocks):
        if rule:
            yr = 1.0 - (y + RULE * em) / h
            fig.add_artist(Line2D([PAD * em / w, 1.0 - PAD * em / w],
                                  [yr, yr], color=grid, linewidth=1.0))
        y += skip
        t.set_position((PAD * em / w, 1.0 - y / h))
        y += b.height
    canvas.draw()
    buf = canvas.buffer_rgba()
    image = QtGui.QImage(bytes(buf), buf.shape[1], buf.shape[0],
                         QtGui.QImage.Format_RGBA8888).copy()
    return QtGui.QPixmap.fromImage(image)


class EquationTip(QtWidgets.QLabel):
    """The floating window: shown at a point (global), hidden when the
    mouse leaves the line."""

    def __init__(self):
        super().__init__(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._key = None

    def show_at(self, title, parts, point, points):
        """The equations parts of the line title near point, in the font
        size points of the window."""
        screen = QtGui.QGuiApplication.screenAt(point) or self.screen()
        dpr = screen.devicePixelRatio()
        dpi = screen.logicalDotsPerInch() * dpr
        key = (title, tuple(parts), round(points, 2), dpi, theme.is_dark())
        if key != self._key:
            fig_bg, _, _, grid = style.axes_colors()
            self.setStyleSheet("QLabel { background: %s; border: 1px solid "
                               "%s; border-radius: 4px; }" % (fig_bg, grid))
            pixmap = render(title, parts, points, dpi)
            pixmap.setDevicePixelRatio(dpr)
            self.setPixmap(pixmap)
            self.adjustSize()
            self._key = key
        room = screen.availableGeometry()
        x, y = point.x() + GAP, point.y() + GAP
        if x + self.width() > room.right():
            x = point.x() - GAP - self.width()
        if y + self.height() > room.bottom():
            y = point.y() - GAP - self.height()
        self.move(max(x, room.left()), max(y, room.top()))
        self.show()
        self.raise_()

    def shown(self):
        """(name, parts, font size) shown, or None."""
        return self._key[:3] if self._key and self.isVisible() else None
