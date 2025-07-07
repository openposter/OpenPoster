from PySide6.QtCore import QEvent
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

class ThemeManager:
    def __init__(self, config_manager, window):
        self.config = config_manager
        self.window = window

    def load_theme(self):
        theme = self.config.get_config("ui_theme", "dark")
        is_dark = (theme == "dark")
        self.window.isDarkMode = is_dark
        if is_dark:
            self.apply_dark_mode_styles()
        else:
            self.apply_light_mode_styles()
        self.window.updateButtonIcons()
        self.update_category_headers()

    def apply_dark_mode_styles(self):
        from .custom_widgets import CheckerboardGraphicsScene
        from PySide6.QtGui import QColor
        window = self.window
        if not hasattr(window, 'ui'): return
        qss_path = window.findAssetPath("themes/dark_style.qss")
        if qss_path:
            try:
                with open(qss_path, 'r') as f:
                    content = f.read()
                    window.ui.centralwidget.setStyleSheet(content)
                    window._current_qss = content
                    for name in ('tableWidget','treeWidget','statesTreeWidget'):
                        widget = getattr(window.ui, name, None)
                        if widget:
                            widget.setObjectName(name)
            except Exception as e:
                print(f"[ThemeManager] Error applying dark QSS: {e}")
        scene = getattr(window, 'scene', None)
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(50,50,50), QColor(40,40,40))
            scene.update()
        common = 'padding:5px; border-radius:3px; border:none; background-color:transparent;'
        btn = getattr(window.ui, 'playButton', None)
        if btn:
            btn.setStyleSheet(
                f"QPushButton {{ color: rgba(255,255,255,150); {common} }}"
                f"QPushButton:hover {{ background-color: rgba(255,255,255,0.1); }}"
                f"QPushButton:pressed {{ background-color: rgba(255,255,255,0.2); }}"
            )
        tw = getattr(window.ui, 'tableWidget', None)
        if tw:
            tw.setStyleSheet("""
QTableWidget#tableWidget { border:none; background-color:transparent; gridline-color:transparent; color:#D0D0D0; }
QTableWidget#tableWidget QHeaderView::section { background-color:#424242; color:#D0D0D0; padding:8px; border:none; border-right:1px solid rgba(180,180,180,60); border-bottom:none; }
""")

    def apply_light_mode_styles(self):
        from .custom_widgets import CheckerboardGraphicsScene
        from PySide6.QtGui import QColor
        window = self.window
        if not hasattr(window, 'ui'): return
        qss_path = window.findAssetPath("themes/light_style.qss")
        if qss_path:
            try:
                with open(qss_path, 'r') as f:
                    content = f.read()
                    window.ui.centralwidget.setStyleSheet(content)
                    window._current_qss = content
                    for name in ('tableWidget','treeWidget','statesTreeWidget'):
                        widget = getattr(window.ui, name, None)
                        if widget:
                            widget.setObjectName(name)
            except Exception as e:
                print(f"[ThemeManager] Error applying light QSS: {e}")
        scene = getattr(window, 'scene', None)
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(240,240,240), QColor(220,220,220))
            scene.update()
        common = 'padding:5px; border-radius:3px; border:none; background-color:transparent;'
        btn = getattr(window.ui, 'playButton', None)
        if btn:
            btn.setStyleSheet(
                f"QPushButton {{ color: rgba(0,0,0,150); {common} }}"
                f"QPushButton:hover {{ background-color: rgba(0,0,0,0.1); }}"
                f"QPushButton:pressed {{ background-color: rgba(0,0,0,0.2); }}"
            )

    def update_category_headers(self):
        from PySide6.QtGui import QColor
        window = self.window
        tw = getattr(window.ui, 'tableWidget', None)
        if not tw: return
        if window.isDarkMode:
            bg, fg = QColor(60,60,60), QColor(230,230,230)
        else:
            bg, fg = QColor(220,220,220), QColor(30,30,30)
        for row in range(tw.rowCount()):
            item = tw.item(row, 0)
            if item and tw.columnSpan(row, 0) > 1:
                item.setBackground(bg)
                item.setForeground(fg) 