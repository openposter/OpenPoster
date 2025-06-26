from PySide6 import QtWidgets, QtGui
import sys
from gui.mainwindow import MainWindow
# when the imposter is sus
# from configparser import ConfigParser
from gui.config_manager import ConfigManager
from PySide6.QtCore import QTranslator
from PySide6.QtGui import QFileOpenEvent
from gui.welcome import WelcomeWindow
from gui.newfile import NewFileDialog
import os

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
    # ────────────────────────────────────────────────────
    
    # ─── Application Properties ─────────────────────────
    app.setApplicationName("OpenPoster")
    app_icon = QtGui.QIcon(":/assets/openposter.ico")
    app.setWindowIcon(app_icon)
    # ─────────────────────────────────────────────────────

    # ─── Global QSS theme ───────────────────────────────
    palette = app.palette()
    text_color = palette.color(QtGui.QPalette.Active, QtGui.QPalette.WindowText)
    system_is_dark = text_color.lightness() > 128
    
    theme = config.get_config("ui_theme", None)
    if theme is None:
        theme = "dark" if system_is_dark else "light"
        config.set_config("ui_theme", theme)
    
    is_dark = theme == "dark"
    qss_file = "themes/dark_style.qss" if is_dark else "themes/light_style.qss"
    qss_path = os.path.join(os.path.dirname(__file__), qss_file)
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Could not load global QSS '{qss_path}': {e}")
    else:
        print(f"Global QSS file not found: {qss_path}")
    # ────────────────────────────────────────────────────

    # ─── Welcome / New File Flow ─────────────────────────
    action_type = None
    action_data = None
    while True:
        welcome = WelcomeWindow()
        welcome.exec()
        action = getattr(welcome, 'result', None)
        if action is None:
            sys.exit()
        if action[0] == "open":
            action_type = "open"
            break
        if action[0] == "new":
            newdlg = NewFileDialog()
            newdlg.exec()
            newact = getattr(newdlg, 'result', None)
            if not newact or newact[0] == "back":
                continue
            if newact[0] == "create":
                action_type = "new"
                action_data = newact[1]
                break
    # ────────────────────────────────────────────────────

    # ─── Main Window ────────────────────────────────────
    widget = MainWindow(config, translator)
    app.main_window = widget
    widget.resize(1600, 900)
    widget.show()
    widget.config_manager = config
    widget.translator = translator
    # Apply selected action
    project_root = os.path.dirname(__file__)
    if action_type == "open":
        widget.openFile()
    elif action_type == "new":
        # Load template
        template_path = os.path.join(project_root, "assets", "openposter.ca")
        widget.open_ca_file(template_path)
        # Apply configured name and dimensions
        name = action_data.get("name") if action_data else None
        width = action_data.get("width") if action_data else None
        height = action_data.get("height") if action_data else None
        if hasattr(widget, 'cafile') and widget.cafile and width and height:
            # Set new bounds on root layer
            widget.cafile.rootlayer.bounds = [str(0), str(0), str(width), str(height)]
            # Re-render preview
            widget.scene.clear()
            widget.renderPreview(widget.cafile.rootlayer)
            widget.fitPreviewToView()
        # Store new file name for save defaults
        if name:
            widget.newfile_name = name
    # ────────────────────────────────────────────────────

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