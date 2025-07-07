from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, 
    QComboBox, QLineEdit, QFileDialog, QTabWidget, QWidget, QKeySequenceEdit, 
    QApplication, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QToolButton
)
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QFont, QIcon
from PySide6.QtCore import QSize
import os
import sys
import xml.etree.ElementTree as ET
import webbrowser

from gui._meta import __version__
from ui.ui_settings_dialog import Ui_SettingsDialog

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.parent_window = parent 

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.filename_display_layout = QHBoxLayout()
        self.filename_display_label = QLabel("Filename Display:")
        self.ui.filenameDisplayCombo = QComboBox()
        self.ui.filenameDisplayCombo.addItems(["Toggle", "File Name", "File Path"])
        self.filename_display_layout.addWidget(self.filename_display_label)
        self.filename_display_layout.addWidget(self.ui.filenameDisplayCombo)
        self.ui.uiTab.layout().addLayout(self.filename_display_layout)

        current_filename_display = self.config_manager.get_filename_display_mode()
        self.ui.filenameDisplayCombo.setCurrentText(current_filename_display)
        self.ui.filenameDisplayCombo.currentTextChanged.connect(self.on_filename_display_changed)

        self.ui.openFileShortcutDisplay.setText(QKeySequence(QKeySequence.StandardKey.Open).toString(QKeySequence.NativeText))
        self.ui.settingsShortcutDisplay.setText(QKeySequence(QKeySequence.StandardKey.Preferences).toString(QKeySequence.NativeText))

        header = self.ui.languageTableWidget.horizontalHeader()
        header_font = header.font()
        if header_font.pointSize() < 13:
            header_font.setPointSize(header_font.pointSize() + 2) 
            header.setFont(header_font)

        # Add close shortcut for the dialog itself
        close_shortcut_str = self.config_manager.get_close_window_shortcut()
        if close_shortcut_str:
            self.close_shortcut = QShortcut(QKeySequence(close_shortcut_str), self)
            self.close_shortcut.activated.connect(self.close)

        if hasattr(self.parent_window, 'theme_change_callbacks') and callable(self.on_theme_changed):
            self.parent_window.theme_change_callbacks.append(self.on_theme_changed)
        
        self.ui.rememberWindowCheckbox.setChecked(self.config_manager.get_window_geometry()["remember_size"])
        self.ui.rememberWindowCheckbox.stateChanged.connect(lambda s: self.config_manager.set_remember_window_size(s == Qt.Checked))
        self.ui.resetPanelsButton.clicked.connect(lambda: [
            self.config_manager.save_splitter_sizes("mainSplitter", []),
            self.config_manager.save_splitter_sizes("layersSplitter", []),
            self.parent().apply_default_sizes() if hasattr(self.parent(), 'apply_default_sizes') else None
        ])

        self.populate_language_list()
        self.ui.languageTableWidget.itemClicked.connect(self.on_language_selected_from_list)

        self.ui.nuggetPathLineEdit.setText(self.config_manager.get_nugget_exec_path())
        self.ui.nuggetBrowseButton.clicked.connect(self.browse_nugget_executable)

        self.ui.exportKeySequenceEdit.setKeySequence(self.config_manager.get_export_shortcut())
        self.ui.exportKeySequenceEdit.keySequenceChanged.connect(self.on_export_seq_changed)
        self.ui.exportShortcutResetButton.clicked.connect(self.reset_export_shortcut)
        self.ui.zoomInKeySequenceEdit.setKeySequence(self.config_manager.get_zoom_in_shortcut())
        self.ui.zoomInKeySequenceEdit.keySequenceChanged.connect(self.on_zoom_in_seq_changed)
        self.ui.zoomInShortcutResetButton.clicked.connect(self.reset_zoom_in_shortcut)
        self.ui.zoomOutKeySequenceEdit.setKeySequence(self.config_manager.get_zoom_out_shortcut())
        self.ui.zoomOutKeySequenceEdit.keySequenceChanged.connect(self.on_zoom_out_seq_changed)
        self.ui.zoomOutShortcutResetButton.clicked.connect(self.reset_zoom_out_shortcut)
        self.ui.resetAllShortcutsButton.clicked.connect(self.reset_all_shortcuts)

        self.ui.closeWindowKeySequenceEdit.setKeySequence(self.config_manager.get_close_window_shortcut())
        self.ui.closeWindowKeySequenceEdit.keySequenceChanged.connect(self.on_close_window_seq_changed)
        self.ui.closeWindowShortcutResetButton.clicked.connect(self.reset_close_window_shortcut)

        self.ui.versionLabel.setText(f"Version: v{__version__}")
        self.ui.discordButton.clicked.connect(lambda: webbrowser.open("https://discord.gg/t3abQJjHm6"))
        self.on_theme_changed(getattr(self.parent_window, 'isDarkMode', False))

        # Appearance Tab
        self.appearanceTab = QWidget()
        self.ui.tabWidget.insertTab(1, self.appearanceTab, "Appearance")
        appearanceLayout = QVBoxLayout(self.appearanceTab)
        
        self.themeTableWidget = QTableWidget()
        appearanceLayout.addWidget(self.themeTableWidget)
        
        self.populate_theme_list()
        self.themeTableWidget.itemClicked.connect(self.on_theme_selected)

    def set_discord_icon_dark(self, is_dark):
        discord_icon_path = ":/icons/discord-white.svg" if is_dark else ":/icons/discord.svg"
        if hasattr(self.ui, 'discordButton'):
            self.ui.discordButton.setIcon(QIcon(discord_icon_path))

    def on_theme_changed(self, is_dark_mode):
        discord_icon_path = ":/icons/discord-white.svg" if is_dark_mode else ":/icons/discord.svg"
        if hasattr(self.ui, 'discordButton'):
            self.ui.discordButton.setIcon(QIcon(discord_icon_path))
        
        self.apply_theme_to_dialog(is_dark_mode)

    def done(self, result):
        if hasattr(self.parent_window, 'theme_change_callbacks') and self.on_theme_changed in self.parent_window.theme_change_callbacks:
            try:
                self.parent_window.theme_change_callbacks.remove(self.on_theme_changed)
            except ValueError:
                pass 
        super().done(result)

    def browse_nugget_executable(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Nugget Executable", "", "Applications (*.app);;Executables (*.exe);;All Files (*)")
        if path:
            self.ui.nuggetPathLineEdit.setText(path)
            self.config_manager.set_nugget_exec_path(path)

    def on_export_seq_changed(self, seq):
        self.config_manager.set_export_shortcut(seq.toString())

    def reset_export_shortcut(self):
        default = self.config_manager.default_config["shortcuts"]["export"]
        self.ui.exportKeySequenceEdit.setKeySequence(default)
        self.config_manager.set_export_shortcut(default)

    def on_zoom_in_seq_changed(self, seq):
        self.config_manager.set_zoom_in_shortcut(seq.toString())

    def reset_zoom_in_shortcut(self):
        default = self.config_manager.default_config["shortcuts"]["zoom_in"]
        self.ui.zoomInKeySequenceEdit.setKeySequence(default)
        self.config_manager.set_zoom_in_shortcut(default)

    def on_zoom_out_seq_changed(self, seq):
        self.config_manager.set_zoom_out_shortcut(seq.toString())

    def reset_zoom_out_shortcut(self):
        default = self.config_manager.default_config["shortcuts"]["zoom_out"]
        self.ui.zoomOutKeySequenceEdit.setKeySequence(default)
        self.config_manager.set_zoom_out_shortcut(default)

    def on_close_window_seq_changed(self, seq):
        self.config_manager.set_close_window_shortcut(seq.toString())

    def reset_close_window_shortcut(self):
        default = self.config_manager.default_config["shortcuts"]["close_window"]
        self.ui.closeWindowKeySequenceEdit.setKeySequence(default)
        self.config_manager.set_close_window_shortcut(default)

    def reset_all_shortcuts(self):
        defaults = self.config_manager.default_config["shortcuts"]
        self.ui.exportKeySequenceEdit.setKeySequence(defaults["export"])
        self.config_manager.set_export_shortcut(defaults["export"])
        self.ui.zoomInKeySequenceEdit.setKeySequence(defaults["zoom_in"])
        self.config_manager.set_zoom_in_shortcut(defaults["zoom_in"])
        self.ui.zoomOutKeySequenceEdit.setKeySequence(defaults["zoom_out"])
        self.config_manager.set_zoom_out_shortcut(defaults["zoom_out"])
        self.ui.closeWindowKeySequenceEdit.setKeySequence(defaults["close_window"])
        self.config_manager.set_close_window_shortcut(defaults["close_window"])
    
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.populate_language_list()
            if hasattr(self.ui, 'tabWidget') and hasattr(self.ui, 'languagesTab'):
                 temp_ui = Ui_SettingsDialog()
                 temp_dialog = QDialog()
                 temp_ui.setupUi(temp_dialog)
                 
                 for i in range(self.ui.tabWidget.count()):
                     tab_name = self.ui.tabWidget.widget(i).objectName()
                     if self.ui.tabWidget.widget(i) == self.ui.uiTab:
                         self.ui.tabWidget.setTabText(i, QApplication.translate("SettingsDialog", "UI"))
                     elif self.ui.tabWidget.widget(i) == self.ui.nuggetTab:
                         self.ui.tabWidget.setTabText(i, QApplication.translate("SettingsDialog", "Nugget"))
                     elif self.ui.tabWidget.widget(i) == self.ui.shortcutsTab:
                         self.ui.tabWidget.setTabText(i, QApplication.translate("SettingsDialog", "Shortcuts"))
                     elif self.ui.tabWidget.widget(i) == self.ui.languagesTab:
                         self.ui.tabWidget.setTabText(i, QApplication.translate("SettingsDialog", "Languages"))
                     elif self.ui.tabWidget.widget(i) == self.ui.aboutTab:
                         self.ui.tabWidget.setTabText(i, QApplication.translate("SettingsDialog", "About"))
                 temp_dialog.deleteLater()
        super().changeEvent(event)

    def _get_ts_completion_percentage(self, lang_code: str) -> int:
        """Parses a .ts file and returns the translation completion percentage."""
        if lang_code == "en_US":
            pass
        elif lang_code in ["en_GB", "en_AU"]:
            pass

        ts_file_path = ""
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        
        qm_dir_path = os.path.join(base_path, "languages")
        ts_file_path = os.path.join(qm_dir_path, f"app_{lang_code}.ts")

        if not os.path.exists(ts_file_path):
            return 0

        try:
            tree = ET.parse(ts_file_path)
            root = tree.getroot()
            messages = root.findall(".//message")
            total_messages = len(messages)
            if total_messages == 0:
                return 100

            translated_messages = 0
            for msg in messages:
                translation_node = msg.find("translation")
                if translation_node is not None and translation_node.get("type") != "unfinished" and translation_node.text:
                    translated_messages += 1
                elif translation_node is not None and translation_node.get("type") == "vanished":
                    pass
                elif translation_node is None:
                     pass


            return int((translated_messages / total_messages) * 100) if total_messages > 0 else 100
        except ET.ParseError:
            print(f"Error parsing TS file: {ts_file_path}")
            return 0
        except Exception as e:
            print(f"An unexpected error occurred while parsing {ts_file_path}: {e}")
            return 0


    def populate_language_list(self):
        self.ui.languageTableWidget.clearContents()
        self.ui.languageTableWidget.setRowCount(0)
        language_codes = self.config_manager.get_languages()
        current_lang_code = self.config_manager.get_current_language()

        lang_display_names = {
            "en_US": "English (US)",
            "en_GB": "English (UK)",
            "en_AU": "English (Australia)",
            "vi": "Vietnamese (Tiếng Việt)",
            "zh": "Chinese (简体中文)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "th": "Thai (ภาษาไทย)",
            "fr": "French (Français)",
            "it": "Italian (Italiano)"
        }

        ai_translated_langs = ["zh", "ja", "ko", "th", "fr", "it"]

        processed_languages = []
        english_us_item_data = None

        for lang_code in language_codes:
            display_name = lang_display_names.get(lang_code, lang_code.upper())
            if lang_code == "en_US":
                english_us_item_data = (display_name, lang_code)
            else:
                processed_languages.append((display_name, lang_code))
        
        processed_languages.sort(key=lambda x: x[0])

        self.ui.languageTableWidget.setColumnCount(2)
        self.ui.languageTableWidget.setHorizontalHeaderLabels(["Language", "Translation Progress"])
        
        table_stylesheet = (
            "QTableWidget { border: 1px solid black; gridline-color: transparent; }"
            "QTableWidget::item:first-column { border-right: 1px solid black; }"
        )
        self.ui.languageTableWidget.setStyleSheet(table_stylesheet)

        header = self.ui.languageTableWidget.horizontalHeader()
        
        header_stylesheet = (
            "QHeaderView::section {"
            "    border-top: none;"
            "    border-left: none;"
            "    border-right: none;"
            "    border-bottom: 1px solid black;"
            "    background-color: transparent;"
            "    padding: 4px;"
            "}"
        )
        header.setStyleSheet(header_stylesheet)

        self.ui.languageTableWidget.setColumnWidth(0, 340)
        self.ui.languageTableWidget.setColumnWidth(1, 160)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)

        self.ui.languageTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        row_count = 0

        if english_us_item_data:
            display_name, lang_code = english_us_item_data
            percentage = self._get_ts_completion_percentage(lang_code)
            
            self.ui.languageTableWidget.insertRow(row_count)
            lang_item = QTableWidgetItem(f"{display_name} ({lang_code})")
            lang_item.setData(Qt.UserRole, lang_code)
            self.ui.languageTableWidget.setItem(row_count, 0, lang_item)
            progress_item = QTableWidgetItem(f"{percentage}%")
            self.ui.languageTableWidget.setItem(row_count, 1, progress_item)
            
            if lang_code == current_lang_code:
                self.ui.languageTableWidget.setCurrentItem(lang_item)
            row_count += 1

        for display_name, lang_code in processed_languages:
            self.ui.languageTableWidget.insertRow(row_count)
            lang_item = QTableWidgetItem(f"{display_name} ({lang_code})")
            lang_item.setData(Qt.UserRole, lang_code)
            self.ui.languageTableWidget.setItem(row_count, 0, lang_item)

            if lang_code in ai_translated_langs:
                progress_item = QTableWidgetItem("AI Translated")
                self.ui.languageTableWidget.setItem(row_count, 1, progress_item)
            else:
                percentage = self._get_ts_completion_percentage(lang_code)
                progress_item = QTableWidgetItem(f"{percentage}%")
                self.ui.languageTableWidget.setItem(row_count, 1, progress_item)

            if lang_code == current_lang_code:
                self.ui.languageTableWidget.setCurrentItem(lang_item)
            row_count += 1

    def on_language_selected_from_list(self, item: QTableWidgetItem):
        if item is None: return
        lang_code = item.data(Qt.UserRole)
        if lang_code:
            current_lang = self.config_manager.get_current_language()
            if lang_code != current_lang:
                self.config_manager.set_language(lang_code)
                if hasattr(self.parent_window, 'load_language'):
                    self.parent_window.load_language(lang_code)

    def on_filename_display_changed(self, value):
        self.config_manager.set_filename_display_mode(value)

    def populate_theme_list(self):
        self.themeTableWidget.setColumnCount(1)
        self.themeTableWidget.setHorizontalHeaderLabels(["Theme"])
        self.themeTableWidget.horizontalHeader().setVisible(False)
        self.themeTableWidget.verticalHeader().setVisible(False)
        self.themeTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.themeTableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.themeTableWidget.setShowGrid(False)
        self.themeTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        themes = {"Light": "light", "Dark": "dark"}
        current_theme = self.config_manager.get_config("ui_theme", "dark")

        is_dark = current_theme == "dark"
        self.apply_theme_to_dialog(is_dark)

        for name, theme_id in themes.items():
            row_position = self.themeTableWidget.rowCount()
            self.themeTableWidget.insertRow(row_position)
            item = QTableWidgetItem(name)
            item.setData(Qt.UserRole, theme_id)
            self.themeTableWidget.setItem(row_position, 0, item)
            if theme_id == current_theme:
                self.themeTableWidget.setCurrentItem(item)

    def apply_theme_to_dialog(self, is_dark):
        """Apply the theme QSS to the settings dialog"""
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        
        qss_file = "themes/dark_style.qss" if is_dark else "themes/light_style.qss"
        qss_path = os.path.join(base_path, qss_file)
        
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Error applying {qss_file} to settings dialog: {e}")

    def on_theme_selected(self, item):
        theme_id = item.data(Qt.UserRole)
        self.config_manager.set_config("ui_theme", theme_id)
        
        is_dark = theme_id == "dark"
        if self.parent_window.isDarkMode == is_dark:
            return

        self.parent_window.theme_manager.load_theme()
        for callback in self.parent_window.theme_change_callbacks:
            callback(is_dark)