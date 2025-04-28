from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QCheckBox
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # UI Settings Group
        ui_group = QGroupBox("UI Settings")
        ui_layout = QVBoxLayout()
        ui_group.setLayout(ui_layout)
        
        # Window size settings section
        window_layout = QHBoxLayout()
        remember_window_label = QLabel("Remember window size and position")
        self.remember_window_checkbox = QCheckBox()
        
        window_geometry = self.config_manager.get_window_geometry()
        self.remember_window_checkbox.setChecked(window_geometry["remember_size"])
        self.remember_window_checkbox.stateChanged.connect(self.toggle_remember_window_size)
        
        window_layout.addWidget(remember_window_label)
        window_layout.addStretch()
        window_layout.addWidget(self.remember_window_checkbox)
        
        ui_layout.addLayout(window_layout)
        
        # reset UI section
        reset_layout = QHBoxLayout()
        reset_label = QLabel("Reset all panel sizes to default values")
        reset_button = QPushButton("Reset Panels")
        reset_button.clicked.connect(self.reset_panel_sizes)
        
        reset_layout.addWidget(reset_label)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)
        
        ui_layout.addLayout(reset_layout)
        layout.addWidget(ui_group)
        
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def toggle_remember_window_size(self, state):
        if self.config_manager:
            self.config_manager.set_remember_window_size(state == Qt.Checked)
    
    def reset_panel_sizes(self):
        if self.config_manager:
            self.config_manager.reset_to_defaults()
            self.parent().apply_default_sizes() 