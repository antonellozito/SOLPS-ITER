"""The only module importing PySide6 and the matplotlib Qt canvas."""

import os

os.environ.setdefault("QT_API", "pyside6")

import matplotlib  # noqa: E402

matplotlib.use("QtAgg")

import PySide6  # noqa: E402
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402,F401
from PySide6.QtCore import Qt, Signal, Slot  # noqa: E402,F401
from matplotlib.backends.backend_qtagg import (  # noqa: E402,F401
    FigureCanvasQTAgg, NavigationToolbar2QT)

PYSIDE6_VERSION = PySide6.__version__
