# Why does init() have its own things? naming it to something like global theme might work'

class DarkMode:
    def __init__(self):
        pass

    playButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(255, 255, 255, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 50);
    border-radius: 20px;
}
"""
    
    editButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(255, 255, 255, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 50);
    border-radius: 20px;
}
QPushButton:checked {
    background-color: rgba(0, 120, 215, 50);
    border-radius: 20px;
}
"""

    tableWidget = """
QTableWidget {
    border: none;
    background-color: transparent;
    gridline-color: transparent;
    color: palette(text);
}
QTableWidget::item { 
    padding: 8px;
    min-height: 30px;
}
QTableWidget::item:first-column {
    border-right: 1px solid rgba(180, 180, 180, 60);
}
QTableWidget::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}
"""

    tableWidgetHorizontalHeader = """
QHeaderView::section {
    background-color: palette(button);
    color: palette(text);
    padding: 8px;
    border: none;
    border-right: 1px solid rgba(180, 180, 180, 60);
    border-bottom: none;
}
"""


class LightMode:
    def __init__(self):
        pass

    playButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(0, 0, 0, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 30);
    border-radius: 20px;
}
"""
    
    editButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(0, 0, 0, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 30);
    border-radius: 20px;
}
QPushButton:checked {
    background-color: rgba(0, 120, 215, 50);
    border-radius: 20px;
}
"""

    tableWidget = """
QTableWidget {
    border: none;
    background-color: transparent;
    gridline-color: transparent;
    color: palette(text);
}
QTableWidget::item { 
    padding: 8px;
    min-height: 30px;
}
QTableWidget::item:first-column {
    border-right: 1px solid rgba(120, 120, 120, 60);
}
QTableWidget::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}
"""

    tableWidgetHorizontalHeader = """
QHeaderView::section {
    background-color: palette(button);
    color: palette(text);
    padding: 8px;
    border: none;
    border-right: 1px solid rgba(120, 120, 120, 60);
    border-bottom: none;
}
"""

class InitUI:
    def __init__(self):
        pass

    previewLabel = "font-size: 14px; padding: 5px;"

    editButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(0, 0, 0, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 30);
    border-radius: 20px;
}
QPushButton:checked {
    background-color: rgba(0, 120, 215, 50);
    border-radius: 20px;
}
"""

    playButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
    color: rgba(255, 255, 255, 150);
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 50);
    border-radius: 20px;
}
"""

    settingsButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 30);
    border-radius: 20px;
}
"""

    discordButton = """
QPushButton { 
    border: none; 
    background-color: transparent;
}
QPushButton:hover { 
    background-color: rgba(128, 128, 128, 30);
    border-radius: 20px;
}
"""

    tableWidget = """
QTableWidget {
    border: none;
    background-color: transparent;
    gridline-color: transparent;
}
QTableWidget::item { 
    padding: 8px;
    min-height: 30px;
}
QTableWidget::item:first-column {
    border-right: 1px solid rgba(120, 120, 120, 60);
}
QTableWidget::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}
"""

    tableWidgetHorizontalHeader = """
QHeaderView::section {
    background-color: palette(button);
    color: palette(text);
    padding: 8px;
    border: none;
    border-right: 1px solid rgba(120, 120, 120, 60);
    border-bottom: none;
}
"""

class OpenFile:
    def __init__(self):
        pass

    validPath = "border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 5px;"

    noFile = "border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 5px; color: #666666; font-style: italic;"