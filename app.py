from PySide6 import QtWidgets, QtGui
import sys
from gui.mainwindow import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    app.setApplicationName("OpenPoster")
    app_icon = QtGui.QIcon("assets/openposter.ico")
    app.setWindowIcon(app_icon)

    widget = MainWindow()
    widget.resize(1600, 900)
    widget.show()

    # force focus
    widget.raise_()
    widget.activateWindow()
    widget.setFocus()

    sys.exit(app.exec())
