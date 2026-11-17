"""The drawing area of a view (Motif: the widget draw of x_view.c): shows
the picture, passes mouse events to the tools as the translations of the
Motif drawing area, and repaints on the update timer and after exposures as
the Motif view.

Mouse (translations of the resources): a press calls the tool of its slot
(left, middle, right), with Shift as a double click; motion and release go
to the active tool, a release outside the area cancels it; enter and leave
are passed on. On macOS, Option + click is the middle button and Command +
click the right one, as under XQuartz."""

import sys

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import api
from . import raster, scaled

# Renderers (resource DivGeo*draw.renderer): "x" the pixels of the X
# server, one pixel per pixel of the window; "hidpi" the same drawing at
# the resolution of the device; "smooth" also with smoothed edges; "auto"
# (default) hidpi on high-resolution screens (HIDPI_RATIO device pixels per
# pixel of the window or more), smooth on the others, chosen again when
# the window moves to another screen
RENDERERS = ("auto", "x", "hidpi", "smooth")
HIDPI_RATIO = 1.5


class Canvas(QtWidgets.QWidget):
    xm_class = "XmDrawingArea"

    def __init__(self, window, res, renderer="auto"):
        super().__init__(window)
        self.setObjectName("draw")
        self.window_ = window
        self.res = res
        self.renderer = renderer
        self.raster = self._new_raster(1, 1)
        self.image = None
        self.mouse_inside = False
        self.pressed = 0
        self.manual_refresh = False
        self._expose_posted = False
        self.expose_timer = QtCore.QTimer(self)
        self.expose_timer.setSingleShot(True)
        self.expose_timer.timeout.connect(self._expose_timeout)
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.update_tick)
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMinimumSize(1, 1)

    # Picture

    def _choice(self):
        """(renderer, device pixel ratio, supersampling) for the screen of
        the window."""
        dpr = self.devicePixelRatioF()
        kind = self.renderer
        if kind == "auto":
            kind = "hidpi" if dpr >= HIDPI_RATIO else "smooth"
        if kind == "x":
            return ("x", 1, 1)
        return (kind, max(1, int(round(dpr))), 2 if kind == "smooth" else 1)

    def _new_raster(self, width, height):
        self.chosen = self._choice()
        kind, dpr, ss = self.chosen
        squares = bool(self.res["bUseSquares"])
        if kind == "x":
            return raster.Raster(self.res, width, height, squares)
        return scaled.Scaled(self.res, width, height, squares, dpr, ss)

    def event(self, event):
        """Another screen or another resolution: the renderer of the new
        screen, the picture made again after an exposure (the graphics
        context is kept, as that of the X window)."""
        if event.type() in (QtCore.QEvent.DevicePixelRatioChange,
                            QtCore.QEvent.ScreenChangeInternal) \
                and self._choice() != self.chosen:
            old = self.raster
            self.raster = self._new_raster(self.width(), self.height())
            self.raster.function = old.function
            self.raster.fg = old.fg
            self.raster.width = old.width
            self.update()
            self.post_expose()
        return super().event(event)

    def _image(self):
        if isinstance(self.raster, scaled.Scaled):
            self.image = self.raster.image()
            return self.image
        img = self.raster.img
        self.image = QtGui.QImage(img.data, img.shape[1], img.shape[0],
                                  img.strides[0], QtGui.QImage.Format_RGB32)
        return self.image

    def draw_records(self, recs, text, view_id):
        self.raster.draw(recs, text, view_id, PYF_HLMODE, PYF_HIDDEN,
                         PYF_CLIPPED)
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.drawImage(0, 0, self._image())
        p.end()

    def snapshot(self):
        """The picture as 0xRRGGBB values (numpy array)."""
        return self.raster.img & np.uint32(0xFFFFFF)

    # Size and exposure (CbResizeView, CbExposeView, CbViewExposeTimer)

    def resizeEvent(self, event):
        """CbResizeView; the pixels kept at the top left, as the X window
        of the drawing area; an exposure only when it grows."""
        size = event.size()
        old = event.oldSize()
        self.raster.resize(size.width(), size.height(), keep=True)
        self.window_.resized(size.width(), size.height())
        if size.width() > old.width() or size.height() > old.height():
            self.post_expose()

    def showEvent(self, event):
        self.post_expose()

    def moveEvent(self, event):
        """The drawing area moved in the window (menu bar or command row
        shown): exposed, as the X window of the drawing area."""
        if self.window_.view is not None:
            self.post_expose()

    def post_expose(self):
        """An exposure arrives as an event, after the current work (as the
        Expose events of the X server)."""
        if not self._expose_posted:
            self._expose_posted = True
            QtCore.QTimer.singleShot(0, self._posted_expose)

    def _posted_expose(self):
        self._expose_posted = False
        self.expose()

    def expose(self):
        if self.manual_refresh:
            return
        w = self.window_
        if w.view is None:
            return
        if self.res["exposeDelay"]:
            w.set_update_flag(api.UPDATE_MAX)
            self.expose_timer.start(self.res["exposeDelay"])
        else:
            w.repaint_view()

    def _expose_timeout(self):
        w = self.window_
        if w.view is not None and w.update_flag():
            w.repaint_view()

    def expose_pending(self):
        return self._expose_posted or self.expose_timer.isActive()

    # Update timer (CbUpdateViewTimer)

    def start_update_timer(self):
        self.update_tick()
        self.update_timer.start(self.res["updateDelay"] // 10 + 1)

    def update_tick(self):
        w = self.window_
        if w.view is None:
            return
        flag = w.update_flag()
        if flag:
            flag -= api.UPDATE_INCR
            w.set_update_flag(flag)
            if flag <= 0 and not self.manual_refresh:
                w.repaint_view()

    # Mouse (XtActUseTool)

    def _slot(self, event):
        button = event.button()
        mods = event.modifiers()
        if sys.platform == "darwin" and button == QtCore.Qt.LeftButton:
            if mods & QtCore.Qt.AltModifier:
                return 1
            if mods & QtCore.Qt.ControlModifier:
                return 2
        return {QtCore.Qt.LeftButton: 0, QtCore.Qt.MiddleButton: 1,
                QtCore.Qt.RightButton: 2}.get(button)

    def mousePressEvent(self, event):
        slot = self._slot(event)
        if slot is None:
            return
        self.pressed += 1
        p = event.position()
        shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)
        self.window_.use_tool("press", slot, int(p.x()), int(p.y()), shift)

    def mouseReleaseEvent(self, event):
        self.pressed = max(0, self.pressed - 1)
        p = event.position()
        self.window_.use_tool("release", None, int(p.x()), int(p.y()))

    def mouseMoveEvent(self, event):
        p = event.position()
        x, y = int(p.x()), int(p.y())
        if self.pressed:
            # the X server reports leaving and entering during a drag
            inside = self.rect().contains(x, y)
            if inside != self.mouse_inside:
                self.window_.use_tool("enter" if inside else "leave", None,
                                      x, y)
        self.window_.use_tool("motion", None, x, y)

    def enterEvent(self, event):
        if not self.mouse_inside:
            p = event.position()
            self.window_.use_tool("enter", None, int(p.x()), int(p.y()))

    def leaveEvent(self, event):
        if self.mouse_inside:
            pos = self.mapFromGlobal(QtGui.QCursor.pos())
            self.window_.use_tool("leave", None, pos.x(), pos.y())


PYF_HIDDEN, PYF_CLIPPED, PYF_HLMODE = 1, 2, 4
