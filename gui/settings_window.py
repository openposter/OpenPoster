from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QComboBox, QLineEdit, QFileDialog, QTabWidget, QWidget, QKeySequenceEdit, QApplication, QListWidgetItem
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
import webbrowser
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
import os
import sys
import xml.etree.ElementTree as ET

from gui._meta import __version__
from ui.ui_settings_dialog import Ui_SettingsDialog

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.parent_window = parent 

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

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
        self.ui.languageListWidget.itemClicked.connect(self.on_language_selected_from_list)

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

    def set_discord_icon_dark(self, is_dark):
        discord_icon_path = ":/icons/discord-white.svg" if is_dark else ":/icons/discord.svg"
        if hasattr(self.ui, 'discordButton'):
            self.ui.discordButton.setIcon(QIcon(discord_icon_path))

    def on_theme_changed(self, is_dark_mode):
        discord_icon_path = ":/icons/discord-white.svg" if is_dark_mode else ":/icons/discord.svg"
        if hasattr(self.ui, 'discordButton'):
            self.ui.discordButton.setIcon(QIcon(discord_icon_path))

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
        self.ui.languageListWidget.clear()
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

        if english_us_item_data:
            display_name, lang_code = english_us_item_data
            percentage = self._get_ts_completion_percentage(lang_code)
            item_text = f"{display_name} ({lang_code}) - {percentage}%" 
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, lang_code)
            self.ui.languageListWidget.addItem(list_item)
            if lang_code == current_lang_code:
                self.ui.languageListWidget.setCurrentItem(list_item)

        for display_name, lang_code in processed_languages:
            if lang_code in ai_translated_langs:
                item_text = f"{display_name} ({lang_code})"
            else:
                percentage = self._get_ts_completion_percentage(lang_code)
                item_text = f"{display_name} ({lang_code}) - {percentage}%"
            
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, lang_code)
            self.ui.languageListWidget.addItem(list_item)
            if lang_code == current_lang_code:
                self.ui.languageListWidget.setCurrentItem(list_item)
    
    def on_language_selected_from_list(self, item: QListWidgetItem):
        lang_code = item.data(Qt.UserRole)
        if not lang_code:
            return

        app = QApplication.instance()
        
        if hasattr(app, 'translator') and app.translator is not None:
            app.removeTranslator(app.translator)

        if not hasattr(self.parent(), 'translator') or self.parent().translator is None:
            print("Error: Parent window does not have a 'translator' attribute or it is None.")
            return

        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        
        qm_dir_path = os.path.join(base_path, "languages")

        translator_to_use = self.parent().translator 

        if translator_to_use.load(f"app_{lang_code}", qm_dir_path):
            app.installTranslator(translator_to_use)
        else:
            if translator_to_use.load("app_en", qm_dir_path):
                app.installTranslator(translator_to_use)
            else:
                print(f"Failed to load translation for {lang_code} from {qm_dir_path} and also failed to load fallback 'en'.")
        
        self.config_manager.set_language(lang_code)
        
        if hasattr(self.parent(), 'retranslateUi'):
            self.parent().retranslateUi() 