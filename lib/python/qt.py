"""The only module importing PySide6 and the matplotlib Qt canvas."""

import os

os.environ["QT_API"] = "pyside6"

import matplotlib  # noqa: E402

matplotlib.use("QtAgg")

import PySide6  # noqa: E402
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402,F401
from PySide6.QtCore import Qt, Signal, Slot  # noqa: E402,F401
from matplotlib.backends.backend_qtagg import (  # noqa: E402,F401
    FigureCanvasQTAgg, NavigationToolbar2QT)

PYSIDE6_VERSION = PySide6.__version__


def _gl_format():
    """The OpenGL format of the 3D view: desktop OpenGL 3.2 core, as
    pyvistaqt asks for."""
    F = QtGui.QSurfaceFormat
    fmt = F()
    fmt.setRenderableType(F.RenderableType.OpenGL)
    fmt.setProfile(F.OpenGLContextProfile.CoreProfile)
    fmt.setVersion(3, 2)
    fmt.setSwapBehavior(F.SwapBehavior.DoubleBuffer)
    for size in (fmt.setRedBufferSize, fmt.setGreenBufferSize,
                 fmt.setBlueBufferSize, fmt.setDepthBufferSize,
                 fmt.setAlphaBufferSize):
        size(8)
    fmt.setStencilBufferSize(0)
    fmt.setSamples(0)               # anti-aliasing is done by VTK
    return fmt


_GL = None


def opengl_works():
    """Whether the display gives a context of the format of the 3D view
    (on an offscreen surface, apart from every window; tried once): not
    over a remote X display or a software renderer without OpenGL 3.2."""
    global _GL
    if _GL is None:
        ctx = QtGui.QOpenGLContext()
        ctx.setFormat(_gl_format())
        surface = QtGui.QOffscreenSurface()
        surface.setFormat(_gl_format())
        surface.create()
        ok = ctx.create() and surface.isValid() and ctx.makeCurrent(surface)
        if ok:
            f = ctx.format()
            ok = (f.majorVersion(), f.minorVersion()) >= (3, 2)
            ctx.doneCurrent()
        _GL = bool(ok)
    return _GL


def remote_display():
    """Whether the X display is on another machine (ssh -X or -Y: a host
    before the colon of DISPLAY), whose OpenGL a window here cannot use
    for the 3D view."""
    host = os.environ.get("DISPLAY", "").partition(":")[0]
    return QtWidgets.QApplication.platformName() == "xcb" and \
        host not in ("", "unix")


def opengl_composition(window):
    """Before window is first shown: the OpenGL format of the 3D view
    (desktop OpenGL 3.2 core, as pyvistaqt asks for) made the default and
    a hidden QOpenGLWidget put in window, so that the window is made for
    the 3D view from the start (else Qt creates it again, a flash, when
    the view first appears; and a window made for OpenGL with another
    format composites the view garbled). False if Qt has no OpenGL
    widgets."""
    try:
        from PySide6.QtOpenGLWidgets import QOpenGLWidget
    except ImportError:
        return False
    F = QtGui.QSurfaceFormat
    old = F.defaultFormat()
    if not (old.renderableType() == F.RenderableType.OpenGL and
            old.profile() == F.OpenGLContextProfile.CoreProfile and
            (old.majorVersion(), old.minorVersion()) >= (3, 2)):
        F.setDefaultFormat(_gl_format())
    QOpenGLWidget(window).hide()
    return True
