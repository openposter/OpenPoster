from PySide6 import QtWidgets, QtGui
import sys
from gui.mainwindow import MainWindow
# when the imposter is sus
# from configparser import ConfigParser
from gui.config_manager import ConfigManager
from PySide6.QtCore import QTranslator
import os
from PySide6.QtGui import QFileOpenEvent

class OpenPosterApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_to_open = None
        self.main_window = None

    def event(self, event):
        if isinstance(event, QFileOpenEvent):
            file_path = event.file()
            if self.main_window and hasattr(self.main_window, 'open_project'):
                self.main_window.open_project(file_path)
            else:
                self.file_to_open = file_path
            return True
        return super().event(event)

if __name__ == "__main__":
    app = OpenPosterApplication([])

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
    app.main_window = widget
    widget.resize(1600, 900)
    widget.show()
    widget.config_manager = config;
    widget.translator = translator
    # ───────────────────────────────────────────────────

    # ─── Handle .ca file argument ─────────────────────
    ca_file = None
    for arg in sys.argv[1:]:
        if arg.endswith('.ca') and os.path.exists(arg):
            ca_file = arg
            break
    if ca_file:
        widget.open_project(ca_file)
    elif app.file_to_open:
        widget.open_project(app.file_to_open)
    # ───────────────────────────────────────────────────

    sys.exit(app.exec())