from PySide6 import QtWidgets, QtGui
import sys
import os
from gui.mainwindow import MainWindow

def resource_path(relative_path: str) -> str:
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    app.setApplicationName("OpenPoster")
    app_icon = QtGui.QIcon(resource_path("assets/openposter.ico"))
    app.setWindowIcon(app_icon)

    widget = MainWindow()
    widget.resize(1600, 900)
    widget.show()

    sys.exit(app.exec())
