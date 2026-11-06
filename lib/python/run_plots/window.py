"""The window of the run plots: one tab per page, each with the matplotlib
toolbar (zoom, pan, save)."""

from ..qt import (FigureCanvasQTAgg, NavigationToolbar2QT, QtWidgets)


def show(title, pages, figures):
    """Open the window and wait until it is closed."""
    app = (QtWidgets.QApplication.instance()
           or QtWidgets.QApplication([title]))
    window = QtWidgets.QMainWindow()
    window.setWindowTitle(title)
    tabs = QtWidgets.QTabWidget()
    for page, fig in zip(pages, figures):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(NavigationToolbar2QT(canvas, panel))
        layout.addWidget(canvas)
        tabs.addTab(panel, page.tab)
    window.setCentralWidget(tabs)
    window.resize(1100, 850)
    window.show()
    return app.exec()
