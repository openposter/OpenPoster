from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QToolButton, QLabel
from PySide6.QtGui import QIcon, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QSize
from ui.ui_export_options_dialog import Ui_ExportOptionsDialog

class ExportOptionsDialog(QDialog):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.choice = None
        self.config_manager = config_manager

        self.ui = Ui_ExportOptionsDialog()
        self.ui.setupUi(self)

        # Add close shortcut for the dialog itself
        if self.config_manager:
            close_shortcut_str = self.config_manager.get_close_window_shortcut()
            if close_shortcut_str:
                self.close_shortcut = QShortcut(QKeySequence(close_shortcut_str), self)
                self.close_shortcut.activated.connect(self.close)

        # Dynamic properties and signal connections
        # Base styling for titleLabel, buttons is in .ui

        self.ui.copyButton.clicked.connect(lambda: self.set_choice("copy"))
        self.ui.tendiesButton.clicked.connect(lambda: self.set_choice("tendies"))
        self.ui.nuggetButton.clicked.connect(lambda: self.set_choice("nugget"))

        # Dynamic icon based on parent's theme state (if available)
        is_dark = False
        if parent and hasattr(parent, 'isDarkMode'):
            is_dark = parent.isDarkMode
        
        nugget_icon_path = ":/icons/nugget-export-white.png" if is_dark else ":/icons/nugget-export.png"
        self.ui.nuggetButton.setIcon(QIcon(nugget_icon_path))

    def set_choice(self, choice):
        self.choice = choice
        self.accept() 