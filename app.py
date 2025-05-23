from PySide6 import QtWidgets, QtGui
import sys
from gui.mainwindow import MainWindow
# when the imposter is sus
# from configparser import ConfigParser
from gui.config_manager import ConfigManager
from PySide6.QtCore import QTranslator

# class MyApp(QtWidgets.QApplication):
#     translator: QTranslator

if __name__ == "__main__":
    app = QtWidgets.QApplication([])


    # ─── Localization ───────────────────────────────────
    config = ConfigManager()  
    translator = QTranslator()
    lang = config.get_current_language()
    translator.load(f"languages/app_{lang}.qm")
    app.translator = translator # type: ignore
    app.installTranslator(translator)
    # ─────────────────────────────────────────────────────
    
    # ─── Application Properties ────────────────────────
    app.setApplicationName("OpenPoster")
    app_icon = QtGui.QIcon(":/assets/openposter.ico")
    app.setWindowIcon(app_icon)
    # ─────────────────────────────────────────────────────

    # ─── Main Window ───────────────────────────────────
    widget = MainWindow(config, translator)
    widget.resize(1600, 900)
    widget.show()
    widget.config_manager = config;
    widget.translator = translator
    # ───────────────────────────────────────────────────

    sys.exit(app.exec())