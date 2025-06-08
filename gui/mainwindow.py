import sys
import os
import math
from lib.ca_elements.core.cafile import CAFile
from PySide6 import QtCore
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QEvent, QVariantAnimation, QKeyCombination, QKeyCombination, QTimer, QSettings, QStandardPaths, QDir, QObject, QProcess, QByteArray, QBuffer, QIODevice, QXmlStreamReader, QPoint, QMimeData, QRegularExpression, QTranslator
from PySide6.QtGui import QPixmap, QImage, QBrush, QPen, QColor, QTransform, QPainter, QLinearGradient, QIcon, QPalette, QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem, QMainWindow, QTableWidgetItem, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem, QApplication, QHeaderView, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QTreeWidget, QWidget, QGraphicsItemAnimation, QMessageBox, QDialog, QColorDialog, QProgressDialog, QSizePolicy, QSplitter, QFrame, QToolButton, QGraphicsView, QGraphicsScene, QStyleFactory, QSpacerItem, QMenu, QLineEdit, QTableWidget, QTableWidgetItem, QSystemTrayIcon, QGraphicsProxyWidget, QGraphicsDropShadowEffect
from ui.ui_mainwindow import Ui_OpenPoster
from .custom_widgets import CustomGraphicsView, CheckerboardGraphicsScene
import PySide6.QtCore as QtCore
import platform
import webbrowser
import re
import subprocess
import tempfile, shutil

import resources_rc
from gui._meta import __version__

# temporary code split for reading
from ._formatter import Format
from ._parse import Parse
from ._applyanimation import ApplyAnimation
from ._assets import Assets

from .config_manager import ConfigManager
from .settings_window import SettingsDialog
from .exportoptions_window import ExportOptionsDialog

class MainWindow(QMainWindow):
    def __init__(self, config_manager, translator):
        super().__init__()
        self.scene: CheckerboardGraphicsScene = None

        # config manager
        self.config_manager = config_manager
        # translator
        self.translator = translator
        # Clear nugget-exports cache on startup
        self._clear_nugget_exports_cache()

        self.animations_playing = False # Initialize animations_playing earlier
        self.animations = [] # Initialize animations list earlier
        self.shortcuts_list = [] # Initialize list to store shortcuts
        self.theme_change_callbacks = [] # For notifying dialogs of theme changes

        # app resources then load
        self.bindOperationFunctions()
        self.loadIconResources()

        self.ui = Ui_OpenPoster()
        self.ui.setupUi(self)
        
        self.isMacOS = platform.system() == "Darwin"
        if self.isMacOS:
            self.setupSystemAppearanceDetection()
        else:
            self.detectDarkMode()
        
        self.initUI()
        
        # Restore window geometry
        self.loadWindowGeometry()
        
        # set up keyboard shortcuts
        self.setupShortcuts()
        self.isDirty = False
        
        # print(f"OpenPoster v{__version__} started") # Commented out startup message

    # app resources
    def bindOperationFunctions(self):
        # TEMPORARY NAMES **not so temp now
        self._format = Format()
        self.formatFloat = self._format.formatFloat
        self.formatPoint = self._format.formatPoint

        self._parse = Parse()
        self.parseTransform = self._parse.parseTransform
        self.parseColor = self._parse.parseColor

        self._applyAnimation = ApplyAnimation(self.scene)
        self.applyAnimationsToPreview = self._applyAnimation.applyAnimationsToPreview
        self.applyKeyframeAnimationToItem = self._applyAnimation.applyKeyframeAnimationToItem
        self.applyTransitionAnimationToPreview = self._applyAnimation.applyTransitionAnimationToPreview
        self.applySpringAnimationToItem = self._applyAnimation.applySpringAnimationToItem

        self._Assets = Assets()
        self.findAssetPath = self._Assets.findAssetPath
        self.loadImage = self._Assets.loadImage

    def loadIconResources(self):
        self.editIcon = QIcon(":/icons/edit.svg")
        self.editIconWhite = QIcon(":/icons/edit-white.svg")
        self.playIcon = QIcon(":/icons/play.svg")
        self.playIconWhite = QIcon(":/icons/play-white.svg")
        self.pauseIcon = QIcon(":/icons/pause.svg")
        self.pauseIconWhite = QIcon(":/icons/pause-white.svg")
        self.settingsIcon = QIcon(":/icons/settings.svg")
        self.settingsIconWhite = QIcon(":/icons/settings-white.svg")
        self.discordIcon = QIcon(":/icons/discord.svg")
        self.discordIconWhite = QIcon(":/icons/discord-white.svg")
        self.exportIcon = QIcon(":/icons/export.svg")
        self.exportIconWhite = QIcon(":/icons/export-white.svg")
        self.isDarkMode = False
    
    def updateButtonIcons(self):
        if not hasattr(self, 'ui'):
            return

        if hasattr(self.ui, 'editButton'):
            self.ui.editButton.setIcon(self.editIconWhite if self.isDarkMode else self.editIcon)
        
        if hasattr(self.ui, 'playButton'):
            if self.animations_playing: # Currently playing, show PAUSE icon (two vertical lines)
                self.ui.playButton.setIcon(self.pauseIconWhite if self.isDarkMode else self.pauseIcon)
                self.ui.playButton.setToolTip("Playing (Click to Pause)")
            else: # Currently not playing, show PLAY icon (triangle)
                self.ui.playButton.setIcon(self.playIconWhite if self.isDarkMode else self.playIcon)
                self.ui.playButton.setToolTip("Paused/Stopped (Click to Play)")

        if hasattr(self.ui, 'settingsButton'):
            self.ui.settingsButton.setIcon(self.settingsIconWhite if self.isDarkMode else self.settingsIcon)
        
        # discordButton is likely in a different part of the UI (e.g. settings dialog)
        # but if it were on the main window UI:
        # if hasattr(self.ui, 'discordButton'):
        #     self.ui.discordButton.setIcon(self.discordIconWhite if self.isDarkMode else self.discordIcon)
            
        if hasattr(self.ui, 'exportButton'):
            self.ui.exportButton.setIcon(self.exportIconWhite if self.isDarkMode else self.exportIcon)

    # themes section
    def detectDarkMode(self):
        previous_dark_mode_state = getattr(self, 'isDarkMode', False)
        new_dark_mode_detected = False
        if platform.system() == 'Windows':
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                val = winreg.QueryValueEx(key, 'AppsUseLightTheme')[0]
                new_dark_mode_detected = (val == 0)
            except:
                new_dark_mode_detected = False
        else:
            try:
                app = QApplication.instance()
                if app:
                    text = app.palette().color(QPalette.Active, QPalette.WindowText)
                    new_dark_mode_detected = (text.lightness() > 128)
            except:
                new_dark_mode_detected = False
        self.isDarkMode = new_dark_mode_detected
        if hasattr(self, 'ui') and previous_dark_mode_state != self.isDarkMode:
            if self.isDarkMode:
                self.applyDarkModeStyles()
            else:
                self.applyLightModeStyles()
            self.updateCategoryHeaders()
    
    def updateCategoryHeaders(self):
        if not hasattr(self, 'ui') or not hasattr(self.ui, 'tableWidget'):
            return
            
        if self.isDarkMode:
            bg_color = QColor(60, 60, 60)
            text_color = QColor(230, 230, 230)
        else:
            bg_color = QColor(220, 220, 220)
            text_color = QColor(30, 30, 30)
            
        for row in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(row, 0)
            if item and self.ui.tableWidget.columnSpan(row, 0) > 1:
                item.setBackground(bg_color)
                item.setForeground(text_color)

    def setupSystemAppearanceDetection(self):
        try:
            from Foundation import NSUserDefaults # type: ignore
            self.macAppearanceObserver = NSUserDefaults.standardUserDefaults()
            self.updateAppearanceForMac()
            
            self.app = QApplication.instance()
            self.app.installEventFilter(self)
        except ImportError:
            print("Foundation module not available - dark mode detection limited")
            self.detectDarkMode()
    
    def changeEvent(self, event: QtCore.QEvent):
        # if event.type() == QEvent.ApplicationPaletteChange:
        #     self.updateAppearanceForMac()
        # if event.type() == QEvent.ApplicationFontChange:
        #     self.updateCategoryHeaders()
        if event.type() == QtCore.QEvent.LanguageChange:
            # self.ui.retranslateUi(self)
            self.retranslateUi()
            self.updateCategoryHeaders()
        super().changeEvent(event)
    
    def retranslateUi(self):
        # super().retranslateUi(self);
        self.ui.retranslateUi(self)
        # :3
        
    def load_language(self, lang_code: str):
        app = QApplication.instance()
        if app is None:
            print("Error: QApplication instance not found.")
            return

        if hasattr(app, 'translator') and app.translator is not None:
            app.removeTranslator(app.translator)

        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        
        qm_dir_path = os.path.join(base_path, "languages")

        new_translator = QTranslator()
        loaded = False
        if new_translator.load(f"app_{lang_code}", qm_dir_path):
            app.installTranslator(new_translator)
            app.translator = new_translator
            loaded = True
            print(f"Successfully loaded and installed translation for: {lang_code}")
        else:
            print(f"Failed to load translation for {lang_code} from {qm_dir_path}. Attempting fallback.")
            if new_translator.load("app_en_US", qm_dir_path): 
                app.installTranslator(new_translator)
                app.translator = new_translator
                loaded = True
                print("Successfully loaded and installed fallback translation: en_US")
            else:
                print(f"Failed to load fallback translation from {qm_dir_path}.")
        
        if loaded:
            QApplication.postEvent(self, QEvent(QEvent.LanguageChange))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ApplicationPaletteChange:
            self.updateAppearanceForMac()
        return super(MainWindow, self).eventFilter(obj, event)
            
    def updateAppearanceForMac(self):
        previous_dark_mode = self.isDarkMode
        # self.isDarkMode = False # Let's not reset it here, detect and then compare
        
        current_system_is_dark = False
        try:
            from Foundation import NSUserDefaults # type: ignore
            appleInterfaceStyle = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            current_system_is_dark = appleInterfaceStyle == "Dark"
            # print(f"[updateAppearanceForMac] AppleInterfaceStyle: {appleInterfaceStyle}, current_system_is_dark: {current_system_is_dark}")
        except Exception as e:
            # print(f"[updateAppearanceForMac] Error getting AppleInterfaceStyle: {e}. Falling back.")
            app = QApplication.instance()
            if app:
                windowText = app.palette().color(QPalette.Active, QPalette.WindowText)
                current_system_is_dark = windowText.lightness() > 128
                # print(f"[updateAppearanceForMac] Fallback detection: lightness > 128 is {current_system_is_dark}")

        print(f"[updateAppearanceForMac] Detected system dark mode: {current_system_is_dark}. Previous MainWindow.isDarkMode: {previous_dark_mode}")

        if self.isDarkMode == current_system_is_dark and previous_dark_mode == current_system_is_dark:
             # print("[updateAppearanceForMac] No change in effective theme or system theme. MainWindow.isDarkMode already aligned.")
             # Still, ensure styles are applied if UI isn't fully constructed yet or needs refresh
             if hasattr(self, 'ui'):
                if self.isDarkMode:
                    self.applyDarkModeStyles()
                else:
                    self.applyLightModeStyles()
             # No need to call callbacks if no effective change from previous state
             return

        self.isDarkMode = current_system_is_dark # Update MainWindow state
        print(f"[updateAppearanceForMac] MainWindow.isDarkMode is NOW: {self.isDarkMode}")
        
        if hasattr(self, 'ui'): 
            if self.isDarkMode:
                # print("[updateAppearanceForMac] Applying Dark Mode Styles")
                self.applyDarkModeStyles()
            else:
                # print("[updateAppearanceForMac] Applying Light Mode Styles")
                self.applyLightModeStyles()
        
        # Only call updateCategoryHeaders and callbacks if the effective theme of the window changed.
        if previous_dark_mode != self.isDarkMode:
            print(f"[updateAppearanceForMac] Effective theme changed from {previous_dark_mode} to {self.isDarkMode}. Updating headers and notifying callbacks.")
            self.updateCategoryHeaders() 
            for callback in self.theme_change_callbacks:
                callback(self.isDarkMode)
        else:
            print(f"[updateAppearanceForMac] System theme might have changed to {current_system_is_dark}, but MainWindow.isDarkMode ({self.isDarkMode}) was already effectively this state. No callback spam.")

    def applyDarkModeStyles(self):
        if not hasattr(self, 'ui'): return

        # Apply main dark stylesheet
        try:
            qss_path = self.findAssetPath("themes/dark_style.qss")
            print(f"[MainWindow.applyDarkModeStyles] QSS path from findAssetPath: {qss_path}")
            with open(qss_path, "r") as f:
                self.ui.centralwidget.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error applying dark_style.qss: {e}")

        scene = self.scene if hasattr(self, 'scene') else None
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(50, 50, 50), QColor(40, 40, 40))
            scene.update()
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'playButton'): # Check self.ui
            self.ui.playButton.setStyleSheet("color: rgba(255, 255, 255, 150);") # Only set color
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'editButton'): # Check self.ui
            self.ui.editButton.setStyleSheet("color: rgba(255, 255, 255, 150);") # Only set color
            
        self.ui.tableWidget.setStyleSheet("""
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
        """)
        
        self.ui.tableWidget.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: palette(button); /* Adapts to QSS */
                color: palette(text); /* Adapts to QSS */
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(180, 180, 180, 60); /* Might need adjustment based on QSS */
                border-bottom: none;
            }
        """)

        # Style for QTreeWidget headers
        tree_header_style = """
            QHeaderView::section {
                background-color: palette(button);
                color: palette(text);
                padding: 4px;
                border: none;
                border-bottom: 1px solid palette(midlight);
                border-right: 1px solid palette(midlight);
            }
            QHeaderView::section:first {
                border-left: none;
            }
        """
        if hasattr(self.ui, 'treeWidget') and self.ui.treeWidget:
            self.ui.treeWidget.header().setStyleSheet(tree_header_style)
        if hasattr(self.ui, 'statesTreeWidget') and self.ui.statesTreeWidget:
            self.ui.statesTreeWidget.header().setStyleSheet(tree_header_style)

        self.updateButtonIcons() 
        self.updateCategoryHeaders() 
        self.ui.retranslateUi(self)

        # Explicitly style problematic UI elements for dark mode
        dark_border_color = "#606060"  # Mid-grey border
        dark_button_bg_color = "#3A3A3A"
        dark_button_hover_bg_color = "#4A4A4A"
        dark_button_pressed_bg_color = "#5A5A5A"
        dark_button_text_color = "#D0D0D0" # Light grey text for buttons
        dark_general_text_color = "#B0B0B0" # Softer light grey for general labels

        button_style_dark = (
            f"QPushButton {{ "
            f"border: 1px solid {dark_border_color}; "
            f"border-radius: 6px; "
            f"padding: 5px 10px; "
            f"background-color: {dark_button_bg_color}; "
            f"color: {dark_button_text_color}; "
            f"}} "
            f"QPushButton:hover {{ background-color: {dark_button_hover_bg_color}; }} "
            f"QPushButton:pressed {{ background-color: {dark_button_pressed_bg_color}; }}"
        )
        if hasattr(self.ui, 'openFile'): self.ui.openFile.setStyleSheet(button_style_dark);
        if hasattr(self.ui, 'exportButton'): self.ui.exportButton.setStyleSheet(button_style_dark);
        
        if hasattr(self.ui, 'filename'):
            font_style_filename = "italic" if self.ui.filename.text() == "No File Open" else "normal"
            filename_style_dark = (
                f"font-style: {font_style_filename}; "
                f"color: {dark_button_text_color}; " # Use button text color for prominence
                f"border: 1.5px solid {dark_border_color}; "
                f"border-radius: 8px; "
                f"padding: 5px 10px;"
            )
            self.ui.filename.setStyleSheet(filename_style_dark)

        if hasattr(self.ui, 'layersLabel'): self.ui.layersLabel.setStyleSheet(f"color: {dark_general_text_color};");
        if hasattr(self.ui, 'statesLabel'): self.ui.statesLabel.setStyleSheet(f"color: {dark_general_text_color};");
        if hasattr(self.ui, 'inspectorLabel'): self.ui.inspectorLabel.setStyleSheet(f"color: {dark_general_text_color};");
        if hasattr(self.ui, 'previewLabel'): self.ui.previewLabel.setStyleSheet(f"color: {dark_general_text_color};");

    def applyLightModeStyles(self):
        if not hasattr(self, 'ui'): return

        try:
            qss_path = self.findAssetPath("themes/light_style.qss")
            with open(qss_path, "r") as f:
                self.ui.centralwidget.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error applying light_style.qss: {e}")

        scene = self.scene if hasattr(self, 'scene') else None
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(240, 240, 240), QColor(220, 220, 220))
            scene.update()
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'playButton'): 
            self.ui.playButton.setStyleSheet("color: rgba(0, 0, 0, 150);") 
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'editButton'): 
            self.ui.editButton.setStyleSheet("color: rgba(0, 0, 0, 150);") 
            
        self.ui.tableWidget.setStyleSheet("""
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
        """)
        
        self.ui.tableWidget.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: palette(button); /* Adapts to QSS */
                color: palette(text); /* Adapts to QSS */
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(120, 120, 120, 60); /* Might need adjustment based on QSS */
                border-bottom: none;
            }
        """)

        # Style for QTreeWidget headers (same as dark for now, relies on palette)
        tree_header_style = """
            QHeaderView::section {
                background-color: palette(button);
                color: palette(text);
                padding: 4px;
                border: none;
                border-bottom: 1px solid palette(midlight);
                border-right: 1px solid palette(midlight);
            }
            QHeaderView::section:first {
                border-left: none;
            }
        """
        if hasattr(self.ui, 'treeWidget') and self.ui.treeWidget:
            self.ui.treeWidget.header().setStyleSheet(tree_header_style)
        if hasattr(self.ui, 'statesTreeWidget') and self.ui.statesTreeWidget:
            self.ui.statesTreeWidget.header().setStyleSheet(tree_header_style)

        self.updateButtonIcons() 
        self.updateCategoryHeaders() 
        self.ui.retranslateUi(self)

        # Explicitly style problematic UI elements for light mode
        light_border_color = "#A0A0A0"  # Mid-light grey border
        light_button_bg_color = "#F0F0F0"
        light_button_hover_bg_color = "#E0E0E0"
        light_button_pressed_bg_color = "#D0D0D0"
        light_button_text_color = "#303030" # Dark grey text for buttons
        light_general_text_color = "#505050" # Softer dark grey for general labels

        button_style_light = (
            f"QPushButton {{ "
            f"border: 1px solid {light_border_color}; "
            f"border-radius: 6px; "
            f"padding: 5px 10px; "
            f"background-color: {light_button_bg_color}; "
            f"color: {light_button_text_color}; "
            f"}} "
            f"QPushButton:hover {{ background-color: {light_button_hover_bg_color}; }} "
            f"QPushButton:pressed {{ background-color: {light_button_pressed_bg_color}; }}"
        )
        if hasattr(self.ui, 'openFile'): self.ui.openFile.setStyleSheet(button_style_light);
        if hasattr(self.ui, 'exportButton'): self.ui.exportButton.setStyleSheet(button_style_light);

        if hasattr(self.ui, 'filename'):
            font_style_filename = "italic" if self.ui.filename.text() == "No File Open" else "normal"
            text_color_filename_light = "#666666" if font_style_filename == "italic" else light_button_text_color # Keep specific color for "No File Open"
            filename_style_light = (
                f"font-style: {font_style_filename}; "
                f"color: {text_color_filename_light}; "
                f"border: 1.5px solid {light_border_color}; "
                f"border-radius: 8px; "
                f"padding: 5px 10px;"
            )
            self.ui.filename.setStyleSheet(filename_style_light)

        if hasattr(self.ui, 'layersLabel'): self.ui.layersLabel.setStyleSheet(f"color: {light_general_text_color};");
        if hasattr(self.ui, 'statesLabel'): self.ui.statesLabel.setStyleSheet(f"color: {light_general_text_color};");
        if hasattr(self.ui, 'inspectorLabel'): self.ui.inspectorLabel.setStyleSheet(f"color: {light_general_text_color};");
        if hasattr(self.ui, 'previewLabel'): self.ui.previewLabel.setStyleSheet(f"color: {light_general_text_color};");

    # gui loader section
    def initUI(self):
        # Connect signals and set dynamic properties.
        self.ui.editButton.setIcon(self.editIconWhite if self.isDarkMode else self.editIcon)
        self.ui.editButton.clicked.connect(self.toggleEditMode)
        
        self.ui.playButton.setIcon(self.playIconWhite if self.isDarkMode else self.playIcon) 
        self.ui.playButton.clicked.connect(self.toggleAnimations)
        
        self.ui.settingsButton.setIcon(self.settingsIconWhite if self.isDarkMode else self.settingsIcon)
        self.ui.settingsButton.clicked.connect(self.showSettingsDialog)
        
        self.ui.exportButton.setIcon(self.exportIconWhite if self.isDarkMode else self.exportIcon)
        self.ui.exportButton.clicked.connect(self.exportFile)
        
        self.ui.openFile.clicked.connect(self.openFile)
        self.ui.treeWidget.currentItemChanged.connect(self.openInInspector)
        self.ui.statesTreeWidget.currentItemChanged.connect(self.openStateInInspector)
        self.ui.tableWidget.itemChanged.connect(self.onInspectorChanged)
        self.ui.filename.mousePressEvent = self.toggleFilenameDisplay
        self.showFullPath = True
        
        self.scene = CheckerboardGraphicsScene()
        orig_make_item = self.scene.makeItemEditable
        def makeItemEditable(item):
            editable = orig_make_item(item)
            if editable:
                editable.itemChanged.connect(lambda it, item=item: self.onItemMoved(item))
                editable.transformChanged.connect(lambda tr, item=item: self.onTransformChanged(item, tr))
            return editable
        self.scene.makeItemEditable = makeItemEditable
        self.ui.graphicsView.setScene(self.scene)
        
        self.ui.graphicsView.minZoom = 0.05
        self.ui.graphicsView.maxZoom = 10.0
        self.ui.graphicsView.contentFittingZoom = 0.05
        
        self.ui.mainSplitter.splitterMoved.connect(self.saveSplitterSizes)
        self.ui.layersSplitter.splitterMoved.connect(self.saveSplitterSizes)
        
        self.loadSplitterSizes()
        
        self.currentSelectedItem = None
        self.cachedImages = {}
        self.currentZoom = 1.0

        # Ensure scene background matches the current theme after scene creation
        if hasattr(self, 'scene') and self.scene:
            if self.isDarkMode:
                self.scene.setBackgroundColor(QColor(50, 50, 50), QColor(40, 40, 40))
            else:
                self.scene.setBackgroundColor(QColor(240, 240, 240), QColor(220, 220, 220))
            self.scene.update()

    # file display section
    def toggleFilenameDisplay(self, event):
        if hasattr(self, 'cafilepath'):
            if self.showFullPath:
                self.ui.filename.setText(os.path.basename(self.cafilepath))
            else:
                self.ui.filename.setText(self.cafilepath)

            self.showFullPath = not self.showFullPath

    def openFile(self):
        self.ui.treeWidget.clear()
        self.ui.statesTreeWidget.clear()
        if sys.platform == "darwin":
            self.cafilepath = QFileDialog.getOpenFileName(
                self, "Select File", "", "Core Animation Files (*.ca)")[0]
        else:
            self.cafilepath = QFileDialog.getExistingDirectory(
                self, "Select Folder", "")
                
        if self.cafilepath:
            self.setWindowTitle(f"OpenPoster - {os.path.basename(self.cafilepath)}")
            self.ui.filename.setText(self.cafilepath)
            # Apply style for opened file (normal font, default text color)
            self.ui.filename.setStyleSheet("font-style: normal; color: palette(text); border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 10px;")
            self.showFullPath = True
            self.cafile = CAFile(self.cafilepath)
            self.cachedImages = {}
            self.missing_assets = set()
            
            rootItem = QTreeWidgetItem([self.cafile.rootlayer.name, "Root", self.cafile.rootlayer.id, ""])
            self.ui.treeWidget.addTopLevelItem(rootItem)

            if len(self.cafile.rootlayer._sublayerorder) > 0:
                self.treeWidgetChildren(rootItem, self.cafile.rootlayer)
            
            self.populateStatesTreeWidget()
            
            # Clear previous animations and reset buffer
            if hasattr(self._applyAnimation, 'animations'):
                self._applyAnimation.animations.clear()
            self.animations = []
            # Render preview and capture default layer animations
            self.scene.clear()
            self.currentZoom = 1.0
            self.ui.graphicsView.resetTransform()
            self.renderPreview(self.cafile.rootlayer)
            if hasattr(self._applyAnimation, 'animations'):
                self.animations = list(self._applyAnimation.animations)
            self.fitPreviewToView()
            self.isDirty = False
        else:
            self.ui.filename.setText("No File Open")
            # Apply style for no file open (italic font, specific grey color)
            self.ui.filename.setStyleSheet("font-style: italic; color: #666666; border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 10px;")

    def fitPreviewToView(self):
        if not hasattr(self, 'cafilepath') or not self.cafilepath:
            return
            
        all_items_rect = self.scene.itemsBoundingRect()
        
        if all_items_rect.isEmpty():
            return
            
        all_items_rect.adjust(-30, -30, 30, 30)
        
        self.ui.graphicsView.updateContentFittingZoom(all_items_rect)
        
        # Use Qt.AspectRatioMode.KeepAspectRatio for correct enum access
        self.ui.graphicsView.fitInView(all_items_rect, Qt.AspectRatioMode.KeepAspectRatio)
        
        transform = self.ui.graphicsView.transform()
        self.currentZoom = transform.m11()

    # only called like once
    def treeWidgetChildren(self, item: QTreeWidgetItem, layer) -> None:
        for id in getattr(layer, '_sublayerorder', []):
            sublayer = getattr(layer, 'sublayers', {}).get(id)
            if sublayer is None:
                continue
            childItem = QTreeWidgetItem([getattr(sublayer, 'name', ''), "Layer", getattr(sublayer, 'id', ''), getattr(layer, 'id', '')])
            
            if hasattr(self, 'missing_assets') and hasattr(sublayer, '_content') and sublayer._content is not None:
                if hasattr(sublayer, "content") and hasattr(sublayer.content, 'src'):
                    if sublayer.content.src in self.missing_assets:
                        childItem.setText(0, "⚠️ " + getattr(sublayer, 'name', ''))
                        childItem.setForeground(0, QColor(255, 0, 0))
            
            item.addChild(childItem)

            if hasattr(sublayer, '_sublayerorder') and len(sublayer._sublayerorder) > 0:
                self.treeWidgetChildren(childItem, sublayer)
            if hasattr(sublayer, '_animations') and sublayer._animations is not None:
                for animation in getattr(sublayer, 'animations', []):
                    animItem = QTreeWidgetItem([getattr(animation, 'keyPath', ''), "Animation", "", getattr(sublayer, 'id', '')])
    def openInInspector(self, current: QTreeWidgetItem, _) -> None:
        # Inspector for tree widget item selection
        if current is None:
            return
        self.ui.tableWidget.blockSignals(True)
        self.currentInspectObject = None

        self.currentSelectedItem = current
        self.ui.tableWidget.setRowCount(0)
        row_index = 0

        element_type = current.text(1)
        if element_type == "Animation":
            parent = self.cafile.rootlayer.findlayer(current.text(3))
            element = parent.findanimation(current.text(0)) if parent is not None else None
            if element:
                self.currentInspectObject = element
                row_index = self.add_category_header("Basic Info", row_index)
                self.add_inspector_row("NAME", current.text(0), row_index)
                row_index += 1
                self.add_inspector_row("TYPE", element.type, row_index)
                row_index += 1

                # Timing properties
                if (
                    (hasattr(element, "duration") and element.duration)
                    or (hasattr(element, "beginTime") and element.beginTime)
                    or (hasattr(element, "fillMode") and element.fillMode)
                    or (hasattr(element, "removedOnCompletion") and element.removedOnCompletion)
                    or (hasattr(element, "repeatCount") and element.repeatCount)
                    or (hasattr(element, "calculationMode") and element.calculationMode)
                ):
                    row_index = self.add_category_header("Timing", row_index)
                
                if hasattr(element, "duration") and element.duration:
                    self.add_inspector_row("DURATION", self.formatFloat(element.duration), row_index)
                    row_index += 1
                
                if hasattr(element, "beginTime") and element.beginTime:
                    self.add_inspector_row("BEGIN TIME", self.formatFloat(element.beginTime), row_index)
                    row_index += 1
                if hasattr(element, "duration") and element.duration:
                    self.add_inspector_row("DURATION", self.formatFloat(element.duration), row_index)
                    row_index += 1

                if hasattr(element, "beginTime") and element.beginTime:
                    self.add_inspector_row("BEGIN TIME", self.formatFloat(element.beginTime), row_index)
                    row_index += 1

                if hasattr(element, "fillMode") and element.fillMode:
                    self.add_inspector_row("FILL MODE", element.fillMode, row_index)
                    row_index += 1

                if hasattr(element, "removedOnCompletion") and element.removedOnCompletion:
                    self.add_inspector_row("REMOVED ON COMPLETION", element.removedOnCompletion, row_index)
                    row_index += 1

                if hasattr(element, "repeatCount") and element.repeatCount:
                    self.add_inspector_row("REPEAT COUNT", self.formatFloat(element.repeatCount), row_index)
                    row_index += 1

                if hasattr(element, "calculationMode") and element.calculationMode:
                    self.add_inspector_row("CALCULATION MODE", element.calculationMode, row_index)
                    row_index += 1

                # Spring Animation properties
                if getattr(element, "type", "") == "CASpringAnimation":
                    row_index = self.add_category_header("Spring Properties", row_index)
                    if hasattr(element, "damping") and element.damping:
                        self.add_inspector_row("DAMPING", self.formatFloat(element.damping), row_index)
                        row_index += 1
                    if hasattr(element, "mass") and element.mass:
                        self.add_inspector_row("MASS", self.formatFloat(element.mass), row_index)
                        row_index += 1
                    if hasattr(element, "stiffness") and element.stiffness:
                        self.add_inspector_row("STIFFNESS", self.formatFloat(element.stiffness), row_index)
                        row_index += 1
                    if hasattr(element, "velocity") and element.velocity:
                        self.add_inspector_row("VELOCITY", self.formatFloat(element.velocity), row_index)
                        row_index += 1
                    if hasattr(element, "mica_autorecalculatesDuration"):
                        self.add_inspector_row("AUTO RECALCULATES DURATION", element.mica_autorecalculatesDuration, row_index)
                        row_index += 1

                # Keyframe Animation properties
                if getattr(element, "type", "") == "CAKeyframeAnimation":
                    row_index = self.add_category_header("Keyframe Data", row_index)
                    if hasattr(element, "values") and element.values:
                        values_str = ", ".join([str(self.formatFloat(value.value)) for value in element.values])
                        self.add_inspector_row("VALUES", values_str, row_index)
                        row_index += 1
                    if hasattr(element, "keyTimes") and element.keyTimes:
                        times_str = ", ".join([str(self.formatFloat(time.value)) for time in element.keyTimes])
                        self.add_inspector_row("KEY TIMES", times_str, row_index)
                        row_index += 1
                    if hasattr(element, "timingFunctions") and element.timingFunctions:
                        self.add_inspector_row("TIMING FUNCTIONS", str(len(element.timingFunctions)), row_index)
                        row_index += 1
                    if hasattr(element, "path") and element.path:
                        self.add_inspector_row("PATH", "Path Animation", row_index)
                        row_index += 1

                # Match Move Animation properties
                if getattr(element, "type", "") == "CAMatchMoveAnimation":
                    row_index = self.add_category_header("Match Move Properties", row_index)
                    if hasattr(element, "additive") and element.additive:
                        self.add_inspector_row("ADDITIVE", element.additive, row_index)
                        row_index += 1
                    if hasattr(element, "appliesX") and element.appliesX:
                        self.add_inspector_row("APPLIES X", element.appliesX, row_index)
                        row_index += 1
                    if hasattr(element, "appliesY") and element.appliesY:
                        self.add_inspector_row("APPLIES Y", element.appliesY, row_index)
                        row_index += 1
                    if hasattr(element, "appliesScale") and element.appliesScale:
                        self.add_inspector_row("APPLIES SCALE", element.appliesScale, row_index)
                        row_index += 1
                    if hasattr(element, "appliesRotation") and element.appliesRotation:
                        self.add_inspector_row("APPLIES ROTATION", element.appliesRotation, row_index)
                        row_index += 1
                
                self.highlightAnimationInPreview(parent, element)
                
        elif element_type == "Layer" or element_type == "Root":
            if element_type == "Layer":
                element = self.cafile.rootlayer.findlayer(current.text(2))
            else:
                element = self.cafile.rootlayer
                
            if element:
                self.currentInspectObject = element
                row_index = self.add_category_header("Basic Info", row_index)
                
                self.add_inspector_row("NAME", current.text(0), row_index)
                row_index += 1
                
                self.add_inspector_row("ID", element.id, row_index)
                row_index += 1
                
                layer_type = "CALayer"
                if hasattr(element, "layer_class") and element.layer_class:
                    layer_type = element.layer_class
                self.add_inspector_row("CLASS", layer_type, row_index)
                row_index += 1
                
                geometry_properties = False
                if (hasattr(element, "position") and element.position) or \
                   (hasattr(element, "bounds") and element.bounds) or \
                   (hasattr(element, "frame") and element.frame) or \
                   (hasattr(element, "transform") and element.transform) or \
                   (hasattr(element, "anchorPoint") and element.anchorPoint) or \
                   (hasattr(element, "zPosition") and element.zPosition) or \
                   (hasattr(element, "geometryFlipped")):
                    row_index = self.add_category_header("Geometry", row_index)
                    geometry_properties = True
                
                if element_type == "Layer" and hasattr(element, "position") and element.position:
                    pos_str = self.formatPoint(" ".join(element.position))
                    self.add_inspector_row("POSITION", pos_str, row_index)
                    row_index += 1
                
                if hasattr(element, "bounds") and element.bounds:
                    bounds_str = self.formatPoint(" ".join(element.bounds))
                    self.add_inspector_row("BOUNDS", bounds_str, row_index)
                    row_index += 1
                
                if hasattr(element, "frame") and element.frame:
                    frame_str = self.formatPoint(" ".join(element.frame))
                    self.add_inspector_row("FRAME", frame_str, row_index)
                    row_index += 1
                
                if hasattr(element, "transform") and element.transform:
                    transform_str = self.formatPoint(element.transform)
                    self.add_inspector_row("TRANSFORM", transform_str, row_index)
                    row_index += 1
                
                if hasattr(element, "anchorPoint") and element.anchorPoint:
                    anchor_str = self.formatPoint(element.anchorPoint)
                    self.add_inspector_row("ANCHOR POINT", anchor_str, row_index)
                    row_index += 1
                
                if hasattr(element, "anchorPointZ") and element.anchorPointZ:
                    self.add_inspector_row("ANCHOR POINT Z", self.formatFloat(element.anchorPointZ), row_index)
                    row_index += 1
                
                if hasattr(element, "zPosition") and element.zPosition:
                    self.add_inspector_row("Z POSITION", self.formatFloat(element.zPosition), row_index)
                    row_index += 1
                
                if hasattr(element, "geometryFlipped"):
                    flipped_value = "Yes" if element.geometryFlipped else "No"
                    self.add_inspector_row("FLIPPED", flipped_value, row_index)
                    row_index += 1
                
                if hasattr(element, "doubleSided"):
                    self.add_inspector_row("DOUBLE SIDED", element.doubleSided, row_index)
                    row_index += 1
                
                if hasattr(element, "sublayerTransform") and element.sublayerTransform:
                    self.add_inspector_row("SUBLAYER TRANSFORM", element.sublayerTransform, row_index)
                    row_index += 1
                
                appearance_properties = False
                if (hasattr(element, "backgroundColor") and element.backgroundColor) or \
                   (hasattr(element, "cornerRadius") and element.cornerRadius) or \
                   (hasattr(element, "borderWidth") and element.borderWidth) or \
                   (hasattr(element, "borderColor") and element.borderColor) or \
                   (hasattr(element, "opacity") and element.opacity is not None) or \
                   (hasattr(element, "mica_animatedAlpha") and element.mica_animatedAlpha is not None) or \
                   (hasattr(element, "hidden")) or \
                   (hasattr(element, "opaque")) or \
                   (hasattr(element, "masksToBounds")) or \
                   (hasattr(element, "shadowPath")) or \
                   (hasattr(element, "shadowColor")) or \
                   (hasattr(element, "shadowOpacity")) or \
                   (hasattr(element, "shadowOffset")) or \
                   (hasattr(element, "shadowRadius")):
                    row_index = self.add_category_header("Appearance", row_index)
                    appearance_properties = True
                
                if hasattr(element, "backgroundColor") and element.backgroundColor:
                    self.add_inspector_row("BACKGROUND COLOR", element.backgroundColor, row_index)
                    row_index += 1
                
                if hasattr(element, "borderWidth") and element.borderWidth:
                    self.add_inspector_row("BORDER WIDTH", self.formatFloat(element.borderWidth), row_index)
                    row_index += 1
                
                if hasattr(element, "borderColor") and element.borderColor:
                    self.add_inspector_row("BORDER COLOR", element.borderColor, row_index)
                    row_index += 1
                
                if hasattr(element, "cornerRadius") and element.cornerRadius:
                    self.add_inspector_row("CORNER RADIUS", self.formatFloat(element.cornerRadius), row_index)
                    row_index += 1
                
                if hasattr(element, "opacity") and element.opacity is not None:
                    self.add_inspector_row("OPACITY", self.formatFloat(element.opacity), row_index)
                    row_index += 1
                
                if hasattr(element, "mica_animatedAlpha") and element.mica_animatedAlpha is not None:
                    self.add_inspector_row("ANIMATED ALPHA", self.formatFloat(element.mica_animatedAlpha), row_index)
                    row_index += 1
                
                if hasattr(element, "hidden"):
                    hidden_value = "Yes" if element.hidden else "No"
                    self.add_inspector_row("HIDDEN", hidden_value, row_index)
                    row_index += 1
                
                if hasattr(element, "opaque"):
                    opaque_value = "Yes" if element.opaque else "No"
                    self.add_inspector_row("OPAQUE", opaque_value, row_index)
                    row_index += 1
                
                if hasattr(element, "masksToBounds"):
                    masks_value = "Yes" if element.masksToBounds else "No"
                    self.add_inspector_row("MASKS TO BOUNDS", masks_value, row_index)
                    row_index += 1
                
                if hasattr(element, "shadowPath"):
                    self.add_inspector_row("SHADOW PATH", element.shadowPath, row_index)
                    row_index += 1
                
                if hasattr(element, "shadowPathIsBounds"):
                    shadow_path_is_bounds = "Yes" if element.shadowPathIsBounds else "No"
                    self.add_inspector_row("SHADOW PATH IS BOUNDS", shadow_path_is_bounds, row_index)
                    row_index += 1
                
                if hasattr(element, "shadowColor") and element.shadowColor:
                    self.add_inspector_row("SHADOW COLOR", element.shadowColor, row_index)
                    row_index += 1
                
                if hasattr(element, "shadowOpacity") and element.shadowOpacity:
                    self.add_inspector_row("SHADOW OPACITY", self.formatFloat(element.shadowOpacity), row_index)
                    row_index += 1
                
                if hasattr(element, "shadowOffset") and element.shadowOffset:
                    offset_str = self.formatPoint(element.shadowOffset)
                    self.add_inspector_row("SHADOW OFFSET", offset_str, row_index)
                    row_index += 1
                
                if hasattr(element, "shadowRadius") and element.shadowRadius:
                    self.add_inspector_row("SHADOW RADIUS", self.formatFloat(element.shadowRadius), row_index)
                    row_index += 1
                
                if hasattr(element, "invertsShadow"):
                    inverts_shadow = "Yes" if element.invertsShadow else "No"
                    self.add_inspector_row("INVERTS SHADOW", inverts_shadow, row_index)
                    row_index += 1
                
                contents_properties = False
                if (hasattr(element, "contents") and element.contents) or \
                   (hasattr(element, "contentsRect") and element.contentsRect) or \
                   (hasattr(element, "contentsCenter") and element.contentsCenter) or \
                   (hasattr(element, "contentsGravity") and element.contentsGravity) or \
                   (hasattr(element, "contentsScale") and element.contentsScale) or \
                   (hasattr(element, "minificationFilter") and element.minificationFilter) or \
                   (hasattr(element, "magnificationFilter") and element.magnificationFilter):
                    row_index = self.add_category_header("Contents", row_index)
                    contents_properties = True
                
                if hasattr(element, "contents") and element.contents:
                    self.add_inspector_row("CONTENTS", "Has Contents", row_index)
                    row_index += 1
                
                if hasattr(element, "contentsRect") and element.contentsRect:
                    rect_str = self.formatPoint(element.contentsRect)
                    self.add_inspector_row("CONTENTS RECT", rect_str, row_index)
                    row_index += 1
                
                if hasattr(element, "contentsCenter") and element.contentsCenter:
                    center_str = self.formatPoint(element.contentsCenter)
                    self.add_inspector_row("CONTENTS CENTER", center_str, row_index)
                    row_index += 1
                
                if hasattr(element, "contentsGravity") and element.contentsGravity:
                    self.add_inspector_row("CONTENTS GRAVITY", element.contentsGravity, row_index)
                    row_index += 1
                
                if hasattr(element, "contentsScale") and element.contentsScale:
                    self.add_inspector_row("CONTENTS SCALE", self.formatFloat(element.contentsScale), row_index)
                    row_index += 1
                
                if hasattr(element, "minificationFilter") and element.minificationFilter:
                    self.add_inspector_row("MINIFICATION FILTER", element.minificationFilter, row_index)
                    row_index += 1
                
                if hasattr(element, "magnificationFilter") and element.magnificationFilter:
                    self.add_inspector_row("MAGNIFICATION FILTER", element.magnificationFilter, row_index)
                    row_index += 1
                
                if hasattr(element, "layer_class") and element.layer_class == "CATextLayer":
                    row_index = self.add_category_header("Text", row_index)
                    
                    if hasattr(element, "string") and element.string:
                        self.add_inspector_row("STRING", element.string, row_index)
                        row_index += 1
                    
                    if hasattr(element, "fontSize") and element.fontSize:
                        self.add_inspector_row("FONT SIZE", self.formatFloat(element.fontSize), row_index)
                        row_index += 1
                    
                    if hasattr(element, "fontFamily") and element.fontFamily:
                        self.add_inspector_row("FONT FAMILY", element.fontFamily, row_index)
                        row_index += 1
                    
                    if hasattr(element, "alignmentMode") and element.alignmentMode:
                        self.add_inspector_row("ALIGNMENT MODE", element.alignmentMode, row_index)
                        row_index += 1
                    
                    if hasattr(element, "color") and element.color:
                        self.add_inspector_row("COLOR", element.color, row_index)
                        row_index += 1
                    
                    if hasattr(element, "wrapped"):
                        wrapped_value = "Yes" if element.wrapped else "No"
                        self.add_inspector_row("WRAPPED", wrapped_value, row_index)
                        row_index += 1
                    
                    if hasattr(element, "tracking") and element.tracking:
                        self.add_inspector_row("TRACKING", self.formatFloat(element.tracking), row_index)
                        row_index += 1
                
                relationships_properties = False
                if (hasattr(element, "states") and element.states) or \
                   (hasattr(element, "animations") and element.animations) or \
                   (hasattr(element, "_sublayerorder") and element._sublayerorder) or \
                   (hasattr(element, "_content") and element._content is not None):
                    row_index = self.add_category_header("Content & Relationships", row_index)
                    relationships_properties = True
                
                if hasattr(element, "states") and element.states:
                    states_str = ", ".join(element.states.keys())
                    self.add_inspector_row("STATES", states_str, row_index)
                    row_index += 1
                
                if hasattr(element, "stateTransitions") and element.stateTransitions:
                    self.add_inspector_row("STATE TRANSITIONS", str(len(element.stateTransitions)), row_index)
                    row_index += 1
                
                if hasattr(element, "animations") and element.animations:
                    self.add_inspector_row("ANIMATION COUNT", str(len(element.animations)), row_index)
                    row_index += 1
                
                if hasattr(element, "_sublayerorder") and element._sublayerorder:
                    self.add_inspector_row("SUBLAYER COUNT", str(len(element._sublayerorder)), row_index)
                    row_index += 1
                
                if hasattr(element, "_content") and element._content is not None:
                    if hasattr(element, "content") and isinstance(element.content, object):
                        if hasattr(element.content, "src"):
                            self.add_inspector_row("CONTENT SRC", element.content.src, row_index)
                            row_index += 1
                
                self.highlightLayerInPreview(element)
        
        self.ui.tableWidget.blockSignals(False)

    def add_category_header(self, category_name, row_index):
        self.ui.tableWidget.insertRow(row_index)
        
        header_item = QTableWidgetItem(category_name)
        header_item.setFlags(QtCore.Qt.ItemIsEnabled)
        
        if self.isDarkMode:
            bg_color = QColor(60, 60, 60)
            text_color = QColor(230, 230, 230) 
        else:
            bg_color = QColor(220, 220, 220) 
            text_color = QColor(30, 30, 30) 
        
        header_item.setBackground(bg_color)
        font = QFont()
        font.setBold(True)
        header_item.setFont(font)
        header_item.setForeground(text_color)
        
        self.ui.tableWidget.setItem(row_index, 0, header_item)
        self.ui.tableWidget.setSpan(row_index, 0, 1, 2)
        
        return row_index + 1
        
    def add_inspector_row(self, key, value, row_index):
        self.ui.tableWidget.insertRow(row_index)
        
        key_item = QTableWidgetItem(key)
        key_item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.ui.tableWidget.setItem(row_index, 0, key_item)
        
        value_str = str(value)
        
        if isinstance(value, bool) or (isinstance(value_str, str) and value_str.lower() in ["yes", "no", "true", "false"]):
            if isinstance(value, bool):
                display_value = "Yes" if value else "No"
            else:
                display_value = value_str.capitalize()
            value_item = QTableWidgetItem(display_value)
            
        elif isinstance(value, (int, float)) or value_str.replace(".", "", 1).replace("-", "", 1).isdigit():
            value_item = QTableWidgetItem(self.formatFloat(value) if isinstance(value, (float)) else str(value))
            
        elif value_str.startswith("#") and (len(value_str) == 7 or len(value_str) == 9):
            try:
                color = QColor(value_str)
                if color.isValid():
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(color)
                    value_item = QTableWidgetItem()
                    value_item.setData(Qt.DecorationRole, pixmap)
                    value_item.setText(value_str)
                else:
                    value_item = QTableWidgetItem(value_str)
            except:
                value_item = QTableWidgetItem(value_str)
                
        elif isinstance(value_str, str) and " " in value_str and all(p.replace(".", "", 1).replace("-", "", 1).isdigit() for p in value_str.split()):
            try:
                parts = value_str.split()
                if len(parts) == 2:
                    value_item = QTableWidgetItem(f"X: {self.formatFloat(float(parts[0]))}, Y: {self.formatFloat(float(parts[1]))}")
                elif len(parts) == 4:
                    value_item = QTableWidgetItem(f"X: {self.formatFloat(float(parts[0]))}, Y: {self.formatFloat(float(parts[1]))}, " +
                                                 f"W: {self.formatFloat(float(parts[2]))}, H: {self.formatFloat(float(parts[3]))}")
                elif len(parts) == 6:
                    value_item = QTableWidgetItem(f"[{self.formatFloat(float(parts[0]))} {self.formatFloat(float(parts[1]))} " +
                                                 f"{self.formatFloat(float(parts[2]))} {self.formatFloat(float(parts[3]))} " +
                                                 f"{self.formatFloat(float(parts[4]))} {self.formatFloat(float(parts[5]))}]")
                else:
                    value_item = QTableWidgetItem(self.formatPoint(value_str))
            except:
                value_item = QTableWidgetItem(value_str)
                
        else:
            value_item = QTableWidgetItem(value_str)
            
        self.ui.tableWidget.setItem(row_index, 1, value_item)
    
    # preview section
    def renderPreview(self, root_layer, target_state=None):
        """Render the preview of the layer hierarchy with optional target state"""
        # Clear previous animation buffers
        if hasattr(self._applyAnimation, 'animations'):
            self._applyAnimation.animations.clear()
        # Also clear MainWindow animations list
        self.animations = []
        # Clear scene for fresh render
        self.scene.clear()
        
        # Treat the root layer's top-left as (0,0)
        default_x, default_y, default_w, default_h = 0, 0, 1000, 1000
        try:
            root_x = float(root_layer.bounds[0]) if hasattr(root_layer, "bounds") and root_layer.bounds else default_x
            root_y = float(root_layer.bounds[1]) if hasattr(root_layer, "bounds") and root_layer.bounds else default_y
            root_w = float(root_layer.bounds[2]) if hasattr(root_layer, "bounds") and root_layer.bounds else default_w
            root_h = float(root_layer.bounds[3]) if hasattr(root_layer, "bounds") and root_layer.bounds else default_h
        except (ValueError, IndexError):
            root_x, root_y, root_w, root_h = default_x, default_y, default_w, default_h
        bounds = QRectF(0, 0, root_w, root_h)
        
        border_rect = QGraphicsRectItem(bounds)
        border_rect.setPen(QPen(QColor(0, 0, 0), 2))
        border_rect.setBrush(QBrush(Qt.transparent))
        self.scene.addItem(border_rect)
        
        base_state = None
        if hasattr(root_layer, "states") and root_layer.states and "Base State" in root_layer.states:
            base_state = root_layer.states["Base State"]
        
        root_pos = QPointF(0, 0)
        
        self.renderLayer(root_layer, root_pos, QTransform(), base_state, target_state)
        
        all_items_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(all_items_rect)
        # Capture all animations applied during this render
        if hasattr(self._applyAnimation, 'animations'):
            self.animations = list(self._applyAnimation.animations)

    def renderLayer(self, layer, parent_pos, parent_transform, base_state=None, target_state=None):
        if hasattr(layer, "hidden") and layer.hidden:
            return
        if layer.id == self.cafile.rootlayer.id:
            for layer_id in layer._sublayerorder:
                sublayer = layer.sublayers.get(layer_id)
                if sublayer:
                    self.renderLayer(sublayer, QPointF(0, 0), parent_transform, base_state, target_state)
            return

        absolute_position = QPointF(parent_pos)
        layer_position = QPointF(0, 0)
        
        if hasattr(layer, "position") and layer.position:
            try:
                layer_position = QPointF(float(layer.position[0]), float(layer.position[1]))
            except (ValueError, IndexError):
                pass
        
        bounds = QRectF(0, 0, 100, 100)
        if hasattr(layer, "bounds") and layer.bounds:
            try:
                x = float(layer.bounds[0])
                y = float(layer.bounds[1])
                w = float(layer.bounds[2])
                h = float(layer.bounds[3])
                bounds = QRectF(x, y, w, h)
            except (ValueError, IndexError):
                pass
        
        transform = QTransform(parent_transform)
        if hasattr(layer, "transform") and layer.transform:
            layer_transform = self.parseTransform(layer.transform)
            transform = transform * layer_transform
        
        anchor_point = QPointF(0.5, 0.5)
        if hasattr(layer, "anchorPoint") and layer.anchorPoint:
            try:
                anchor_parts = layer.anchorPoint.split(" ")
                if len(anchor_parts) >= 2:
                    anchor_point = QPointF(float(anchor_parts[0]), float(anchor_parts[1]))
            except:
                pass
        
        z_position = 0
        if hasattr(layer, "zPosition") and layer.zPosition:
            try:
                z_position = float(layer.zPosition)
            except (ValueError, TypeError):
                pass
        
        opacity = 1.0
        if hasattr(layer, "opacity") and layer.opacity is not None:
            try:
                opacity = float(layer.opacity)
            except (ValueError, TypeError):
                pass
        
        background_color = None
        if hasattr(layer, "backgroundColor") and layer.backgroundColor:
            background_color = self.parseColor(layer.backgroundColor)
        
        corner_radius = 0
        if hasattr(layer, "cornerRadius") and layer.cornerRadius:
            try:
                corner_radius = float(layer.cornerRadius)
            except (ValueError, TypeError):
                pass
        
        if base_state and hasattr(base_state, "elements"):
            for element in base_state.elements:
                if element.__class__.__name__ == "LKStateSetValue" and element.targetId == layer.id:
                    if element.keyPath == "position.x" and element.value:
                        try:
                            layer_position.setX(float(element.value))
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "position.y" and element.value:
                        try:
                            layer_position.setY(float(element.value))
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "transform" and element.value:
                        transform = self.parseTransform(element.value) * parent_transform
                    elif element.keyPath == "opacity" and element.value:
                        try:
                            opacity = float(element.value)
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "zPosition" and element.value:
                        try:
                            z_position = float(element.value)
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "backgroundColor" and element.value:
                        background_color = self.parseColor(element.value)
                    elif element.keyPath == "cornerRadius" and element.value:
                        try:
                            corner_radius = float(element.value)
                        except (ValueError, TypeError):
                            pass
        
        if target_state and hasattr(target_state, "elements"):
            for element in target_state.elements:
                if element.__class__.__name__ == "LKStateSetValue" and element.targetId == layer.id:
                    if element.keyPath == "position.x" and element.value:
                        try:
                            layer_position.setX(float(element.value))
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "position.y" and element.value:
                        try:
                            layer_position.setY(float(element.value))
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "transform" and element.value:
                        transform = self.parseTransform(element.value) * parent_transform
                    elif element.keyPath == "opacity" and element.value:
                        try:
                            opacity = float(element.value)
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "zPosition" and element.value:
                        try:
                            z_position = float(element.value)
                        except (ValueError, TypeError):
                            pass
                    elif element.keyPath == "backgroundColor" and element.value:
                        background_color = self.parseColor(element.value)
                    elif element.keyPath == "cornerRadius" and element.value:
                        try:
                            corner_radius = float(element.value)
                        except (ValueError, TypeError):
                            pass
        
        has_content = False
        missing_asset = False
        
        is_text_layer = hasattr(layer, "layer_class") and layer.layer_class == "CATextLayer"
        
        if is_text_layer:
            text_item = QGraphicsTextItem()
            text = layer.string if hasattr(layer, "string") and layer.string else "Text Layer"
            text_item.setPlainText(text)
            
            if hasattr(layer, "fontSize") and layer.fontSize:
                try:
                    font = text_item.font()
                    font_size = float(layer.fontSize)
                    font.setPointSizeF(font_size)
                    text_item.setFont(font)
                except (ValueError, TypeError):
                    pass
            
            if hasattr(layer, "fontFamily") and layer.fontFamily:
                font = text_item.font()
                font.setFamily(layer.fontFamily)
                text_item.setFont(font)
            
            if hasattr(layer, "color") and layer.color:
                color = self.parseColor(layer.color)
                if color:
                    text_item.setDefaultTextColor(color)
            
            text_item.setTransformOriginPoint(bounds.width() * anchor_point.x(),
                                         bounds.height() * anchor_point.y())
            pos_x = layer_position.x() - bounds.width() * anchor_point.x()
            pos_y = layer_position.y() - bounds.height() * anchor_point.y()
            text_item.setPos(pos_x, pos_y)
            text_item.setTransform(transform)
            text_item.setZValue(z_position)
            text_item.setOpacity(opacity)
            
            text_item.setData(0, layer.id)
            text_item.setData(1, "Layer")
            self.scene.addItem(text_item)
            has_content = True
            
            self.applyDefaultAnimationsToLayer(layer, text_item)
            
        elif hasattr(layer, "_content") and layer._content is not None:
            if hasattr(layer, "content") and hasattr(layer.content, "src"):
                src_path = layer.content.src
                # umm...
                self._Assets.cafilepath = self.cafilepath
                self._Assets.cachedImages = self.cachedImages
                pixmap = self.loadImage(src_path)
                self.cachedImages = self._Assets.cachedImages
                
                if not pixmap and hasattr(self, 'missing_assets') and src_path in self.missing_assets:
                    missing_asset = True
                    
                if pixmap:
                    pixmap_item = QGraphicsPixmapItem()
                    pixmap_item.setPixmap(pixmap)

                    scale_x = bounds.width() / pixmap.width() if pixmap.width() > 0 else 1.0
                    scale_y = bounds.height() / pixmap.height() if pixmap.height() > 0 else 1.0
                    item_transform = QTransform()
                    item_transform.scale(scale_x, scale_y)
                    pixmap_item.setTransform(item_transform * transform)

                    scaled_width = pixmap.width() * scale_x
                    scaled_height = pixmap.height() * scale_y
                    pixmap_item.setTransformOriginPoint(scaled_width * anchor_point.x(),
                                                        scaled_height * anchor_point.y())

                    pos_x = layer_position.x() - scaled_width * anchor_point.x()
                    pos_y = layer_position.y() - scaled_height * anchor_point.y()
                    pixmap_item.setPos(pos_x, pos_y)

                    pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                    pixmap_item.setZValue(z_position)
                    pixmap_item.setOpacity(opacity)
                    pixmap_item.setData(0, layer.id)
                    pixmap_item.setData(1, "Layer")
                    self.scene.addItem(pixmap_item)
                    has_content = True
                    
                    self.applyDefaultAnimationsToLayer(layer, pixmap_item)
        
        if not has_content:
            rect_item = QGraphicsRectItem()
            rect_item.setRect(bounds)
            rect_item.setTransformOriginPoint(bounds.width() * anchor_point.x(),
                                             bounds.height() * anchor_point.y())
            
            pos_x = layer_position.x() - bounds.width() * anchor_point.x()
            pos_y = layer_position.y() - bounds.height() * anchor_point.y()
            
            rect_item.setPos(pos_x, pos_y)
            rect_item.setTransform(transform)
            rect_item.setZValue(z_position)
            rect_item.setOpacity(opacity)
            
            pen = QPen(QColor(200, 200, 200, 180), 1.0)
            brush = QBrush(QColor(180, 180, 180, 30))
            
            if layer.id == self.cafile.rootlayer.id:
                pen = QPen(QColor(0, 0, 0, 200), 1.5)
                brush = QBrush(Qt.transparent)
            
            if missing_asset:
                pen = QPen(QColor(255, 0, 0, 200), 2.0)
                brush = QBrush(QColor(255, 200, 200, 30))
            
            if background_color:
                brush = QBrush(background_color)
            
            if corner_radius > 0:
                pen.setStyle(Qt.PenStyle.DashLine)
            
            rect_item.setPen(pen)
            rect_item.setBrush(brush)
            rect_item.setData(0, layer.id)
            rect_item.setData(1, "Layer")
            self.scene.addItem(rect_item)
            
            self.applyDefaultAnimationsToLayer(layer, rect_item)
            
            if layer.id != self.cafile.rootlayer.id:
                name_item = QGraphicsTextItem(layer.name)
                name_item.setPos(rect_item.pos() + QPointF(5, 5))
                name_item.setDefaultTextColor(QColor(60, 60, 60))
                name_item.setData(0, layer.id + "_name")
                name_item.setTransform(transform)
                name_item.setZValue(z_position + 0.1)
                self.scene.addItem(name_item)
        
        if hasattr(layer, "_sublayerorder") and layer._sublayerorder:
            for layer_id in layer._sublayerorder:
                sublayer = layer.sublayers.get(layer_id)
                if sublayer:
                    self.renderLayer(sublayer, layer_position, transform, base_state, target_state)
    
    def applyDefaultAnimationsToLayer(self, layer, item):
        if not hasattr(layer, "animations") or not layer.animations:
            return
            
        for animation in layer.animations:
            if animation.type == "CAKeyframeAnimation":
                self.applyKeyframeAnimationToItem(item, animation.keyPath, animation)
    
    def highlightLayerInPreview(self, layer):
        self.scene.clearSelection()
        for item in self.scene.items():
            if hasattr(item, "data") and item.data(0) == layer.id and item.data(1) == "Layer":
                if isinstance(item, QGraphicsRectItem):
                    if layer.id == self.cafile.rootlayer.id:
                        item.setPen(QPen(QColor(0, 120, 215, 255), 2))
                    else:
                        item.setPen(QPen(QColor(0, 120, 215, 200), 1.5))
                    item.setSelected(True)
                    self.ui.graphicsView.centerOn(item)
                
        if layer.id is not None:
            for item in self.scene.items():
                if hasattr(item, "data") and item.data(0) == layer.id + "_name":
                    item.setDefaultTextColor(QColor(0, 120, 215))
    
    def highlightAnimationInPreview(self, layer, animation):
        self.highlightLayerInPreview(layer)

    def populateStatesTreeWidget(self):
        if not hasattr(self, 'cafile') or not self.cafile:
            return
            
        self.ui.statesTreeWidget.clear()
        
        self.processStatesInLayer(self.cafile.rootlayer, None)
    
    def processStatesInLayer(self, layer, parentItem):
        if not hasattr(layer, "states") or not layer.states:
            return
            
        layerItem = None
        if len(layer.states) > 0:
            if parentItem is None:
                for state_name, state in layer.states.items():
                    stateItem = QTreeWidgetItem([state_name, "State", layer.id])
                    self.ui.statesTreeWidget.addTopLevelItem(stateItem)
                    
                    if hasattr(state, "elements") and state.elements:
                        self.addStateElements(state, stateItem)
            else:
                layerName = layer.name if hasattr(layer, "name") else "Sublayer"
                layerItem = QTreeWidgetItem([f"{layerName} States", "LayerFolder", ""])
                parentItem.addChild(layerItem)
                
                for state_name, state in layer.states.items():
                    stateItem = QTreeWidgetItem([state_name, "State", layer.id])
                    layerItem.addChild(stateItem)
                    
                    if hasattr(state, "elements") and state.elements:
                        self.addStateElements(state, stateItem)
                     
        if hasattr(layer, "layers") and layer.layers:
            for sublayer in layer.layers:
                self.processStatesInLayer(sublayer, layerItem)
                
    def addStateElements(self, state, stateItem):
        """Helper function to add elements to a state item"""
        for element in state.elements:
            if element.__class__.__name__ == "LKStateSetValue":
                setValue = QTreeWidgetItem([
                    f"{element.keyPath}",
                    "SetValue",
                    f"{element.value} ({element.valueType})"
                ])
                setValue.setData(0, QtCore.Qt.UserRole, element.targetId)
                stateItem.addChild(setValue)
            elif element.__class__.__name__ == "LKStateAddAnimation":
                animItem = QTreeWidgetItem([
                    f"{element.keyPath}",
                    "AddAnimation",
                    element.targetId
                ])
                stateItem.addChild(animItem)
                
                if hasattr(element, "animations") and element.animations:
                    for anim in element.animations:
                        animType = anim.type if hasattr(anim, "type") else "Unknown"
                        animDetails = QTreeWidgetItem([
                            f"{animType}",
                            "Animation",
                            anim.id if hasattr(anim, "id") else ""
                        ])
                        animItem.addChild(animDetails)

    # states inspector, private functions below
    def openStateInInspector(self, current, _):
        if current is None:
            return
        element_type = current.text(1)
        if element_type == "State":
            layer_id = current.text(2)
            layer = self.cafile.rootlayer.findlayer(layer_id) if layer_id else self.cafile.rootlayer
            state_name = current.text(0)
            self.previewState(layer, state_name)
            return
        self.ui.tableWidget.blockSignals(True)
        self.currentInspectObject = None

        self.currentSelectedItem = current
        self.ui.tableWidget.setRowCount(0)
        row_index = 0

        element_type = current.text(1)

        row_index = self.add_category_header("Basic Info", row_index)
        self.add_inspector_row("NAME", current.text(0), row_index)
        row_index += 1
        self.add_inspector_row("TYPE", element_type, row_index)
        row_index += 1

        # Route to the correct handler (my fav way)
        handler = {
            "State": self._handle_state,
            "Transition": self._handle_transition,
            "SetValue": self._handle_set_value,
            "Animation": self._handle_animation,
            "AddAnimation": self._handle_add_animation,
            "TransitionElement": self._handle_transition_element,
        }.get(element_type)

        if handler:
            handler(current, row_index)

        # Reset animations list and preview state for State items
        was_playing = getattr(self, 'animations_playing', False)
        self.animations = []
        if element_type == "State":
            # Determine layer and state name for preview
            layer_id = current.text(2)
            layer = self.cafile.rootlayer.findlayer(layer_id) if layer_id else self.cafile.rootlayer
            state_name = current.text(0)
            self.previewState(layer, state_name)
            if was_playing:
                self.animations_playing = False
                self.toggleAnimations()
        self.ui.tableWidget.blockSignals(False)

    # STATES
    def _handle_state(self, current, row_index):
        layer_id = current.text(2)
        if layer_id:
            self.add_inspector_row("LAYER ID", layer_id, row_index)
            row_index += 1
        
        current.setData(0, QtCore.Qt.UserRole, layer_id)
        
        state_name = current.text(0)
        layer = None
        
        if layer_id:
            layer = self.cafile.rootlayer.findlayer(layer_id)
        else:
            layer = self.cafile.rootlayer
        
        if layer and hasattr(layer, "states") and state_name in layer.states:
            state = layer.states[state_name]
            
            # State timing info
            if hasattr(state, "nextDelay") or hasattr(state, "previousDelay") or hasattr(state, "basedOn"):
                row_index = self.add_category_header("State Properties", row_index)
                
                if hasattr(state, "basedOn") and state.basedOn:
                    self.add_inspector_row("BASED ON", state.basedOn, row_index)
                    row_index += 1
                
                if hasattr(state, "nextDelay") and state.nextDelay:
                    self.add_inspector_row("NEXT DELAY", self.formatFloat(state.nextDelay), row_index)
                    row_index += 1
                
                if hasattr(state, "previousDelay") and state.previousDelay:
                    self.add_inspector_row("PREVIOUS DELAY", self.formatFloat(state.previousDelay), row_index)
                    row_index += 1
            
            # State elements info
            if hasattr(state, "elements"):
                row_index = self.add_category_header("Elements", row_index)
                self.add_inspector_row("ELEMENT COUNT", str(len(state.elements)), row_index)
                row_index += 1
                
                # Count element types
                element_counts = {}
                for element in state.elements:
                    element_type = element.__class__.__name__
                    element_counts[element_type] = element_counts.get(element_type, 0) + 1
                
                for element_type, count in element_counts.items():
                    if element_type == "LKStateSetValue":
                        self.add_inspector_row("SET VALUE ELEMENTS", str(count), row_index)
                        row_index += 1
                    elif element_type == "LKStateAddAnimation":
                        self.add_inspector_row("ADD ANIMATION ELEMENTS", str(count), row_index)
                        row_index += 1
            
            self.animations = []
            
            self.previewState(layer, state_name)
            
            was_playing = hasattr(self, 'animations_playing') and self.animations_playing
            if was_playing:
                self.animations_playing = False
                self.toggleAnimations()

    # TRANSITION
    def _handle_transition(self, current, row_index):
        parent = current.parent()
        if parent and parent.parent():
            state_item = parent.parent()
            layer_id = state_item.text(2)
            
            transition_data = current.data(0, QtCore.Qt.UserRole)
            if transition_data:
                fromState, toState = transition_data
            else:
                direction_parts = current.text(0).split(" ")
                direction = direction_parts[0]
                other_state = " ".join(direction_parts[1:])
                
                if other_state == "any state":
                    other_state = "*"
                    
                state_name = state_item.text(0)
                
                if direction == "from":
                    fromState = state_name
                    toState = other_state
                else:
                    fromState = other_state
                    toState = state_name
            
            # Transition details
            row_index = self.add_category_header("Transition Details", row_index)
            
            self.add_inspector_row("FROM STATE", fromState, row_index)
            row_index += 1
            self.add_inspector_row("TO STATE", toState, row_index)
            row_index += 1
            
            if layer_id:
                self.add_inspector_row("LAYER ID", layer_id, row_index)
                row_index += 1
            
            # Check if there's actual transition data
            if layer_id:
                layer = self.cafile.rootlayer.findlayer(layer_id)
            else:
                layer = self.cafile.rootlayer
            
            if layer and hasattr(layer, "stateTransitions"):
                transition = None
                for t in layer.stateTransitions:
                    if (t.fromState == fromState or t.fromState == "*") and t.toState == toState:
                        transition = t
                        break
                
                if transition:
                    # Show more transition details if available
                    if hasattr(transition, "elements") and transition.elements:
                        self.add_inspector_row("ELEMENT COUNT", str(len(transition.elements)), row_index)
                        row_index += 1
            
            self.animations = []
            
            self.previewTransition(layer_id, fromState, toState)
            
            was_playing = hasattr(self, 'animations_playing') and self.animations_playing
            if was_playing:
                self.animations_playing = False
                self.toggleAnimations()

    # SET VALUE
    def _handle_set_value(self, current, row_index):
        # Target information
        row_index = self.add_category_header("Target Info", row_index)
        
        targetId = current.data(0, QtCore.Qt.UserRole)
        if targetId:
            self.add_inspector_row("TARGET ID", targetId, row_index)
            row_index += 1
            
            # Try to find the target layer to show its name
            target_layer = self.cafile.rootlayer.findlayer(targetId)
            if target_layer and hasattr(target_layer, "name"):
                self.add_inspector_row("TARGET NAME", target_layer.name, row_index)
                row_index += 1
        
        # Value information
        row_index = self.add_category_header("Value", row_index)
            
        keyPath = current.text(0)
        if keyPath:
            self.add_inspector_row("KEY PATH", keyPath, row_index)
            row_index += 1
            
        value = current.text(2)
        if value:
            self.add_inspector_row("VALUE", value, row_index)
            row_index += 1

    # ANIMATION
    def _handle_animation(self, current, row_index):
        # Animation details
        row_index = self.add_category_header("Animation Details", row_index)
        
        details = current.text(2)
        if details:
            for detail in details.split(", "):
                if ":" in detail:
                    key, value = detail.split(":", 1)
                    self.add_inspector_row(key.strip().upper(), value.strip(), row_index)
                    row_index += 1

    # ADD ANIMATION
    def _handle_add_animation(self, current, row_index):
        # Target information
        row_index = self.add_category_header("Target Info", row_index)
        
        targetId = current.text(2)
        if targetId:
            self.add_inspector_row("TARGET ID", targetId, row_index)
            row_index += 1
            
            # Try to find the target layer to show its name
            target_layer = self.cafile.rootlayer.findlayer(targetId)
            if target_layer and hasattr(target_layer, "name"):
                self.add_inspector_row("TARGET NAME", target_layer.name, row_index)
                row_index += 1
            
        keyPath = current.text(0)
        if keyPath:
            self.add_inspector_row("KEY PATH", keyPath, row_index)
            row_index += 1
        
        # Find the animations
        parent = current.parent()
        if parent and parent.text(1) == "State":
            state_name = parent.text(0)
            layer_id = parent.text(2)
            
            if layer_id:
                layer = self.cafile.rootlayer.findlayer(layer_id)
            else:
                layer = self.cafile.rootlayer
                
            if layer and hasattr(layer, "states") and state_name in layer.states:
                state = layer.states[state_name]
                if hasattr(state, "elements"):
                    for element in state.elements:
                        if element.__class__.__name__ == "LKStateAddAnimation" and element.targetId == targetId and element.keyPath == keyPath:
                            if hasattr(element, "animations") and element.animations:
                                row_index = self.add_category_header("Animations", row_index)
                                self.add_inspector_row("ANIMATION COUNT", str(len(element.animations)), row_index)
                                row_index += 1

    # TRANSITION ELEMENT
    def _handle_transition_element(self, current, row_index):
        # Element details
        row_index = self.add_category_header("Element Details", row_index)
        
        key = current.text(0)
        if key:
            self.add_inspector_row("KEY", key, row_index)
            row_index += 1
            
        targetId = current.text(2)
        if targetId:
            self.add_inspector_row("TARGET ID", targetId, row_index)
            row_index += 1
            
            # Try to find the target layer to show its name
            target_layer = self.cafile.rootlayer.findlayer(targetId)
            if target_layer and hasattr(target_layer, "name"):
                self.add_inspector_row("TARGET NAME", target_layer.name, row_index)
                row_index += 1
    
    # previewing
    def previewState(self, layer, state_name):
        if not layer or not state_name:
            return
            
        # Clear previous animations in applyAnimation and mainWindow
        if hasattr(self._applyAnimation, 'animations'):
            self._applyAnimation.animations.clear()
        self.animations = []
        
        self.scene.clear()
        
        base_state = None
        if hasattr(layer, "states") and "Base State" in layer.states:
            base_state = layer.states["Base State"]
        
        target_state = None
        if hasattr(layer, "states") and state_name in layer.states:
            target_state = layer.states[state_name]
        
        self.renderPreview(layer, target_state)
        
        if target_state and hasattr(target_state, "elements"):
            for element in target_state.elements:
                if element.__class__.__name__ == "LKStateAddAnimation":
                    self.applyAnimationsToPreview(element)
        
        # Copy applied animations to MainWindow.animations for toggling
        if hasattr(self._applyAnimation, 'animations'):
            self.animations = list(self._applyAnimation.animations)

    def previewTransition(self, layer_id, fromState, toState):
        layer = None
        if layer_id:
            layer = self.cafile.rootlayer.findlayer(layer_id)
        else:
            layer = self.cafile.rootlayer
            
        if not layer:
            return
            
        self.previewState(layer, fromState if fromState != "*" else "Base State")
        
        transition = None
        if hasattr(layer, "stateTransitions"):
            for t in layer.stateTransitions:
                if (t.fromState == fromState or t.fromState == "*") and t.toState == toState:
                    transition = t
                    break
                    
        if not transition:
            return
            
        if hasattr(transition, "elements"):
            for element in transition.elements:
                if hasattr(element, "animations"):
                    for anim in element.animations:
                        self.applyTransitionAnimationToPreview(element.targetId, element.key, anim)
        
        # Copy applied transition animations to MainWindow.animations for toggling
        if hasattr(self._applyAnimation, 'animations'):
            self.animations = list(self._applyAnimation.animations)

    # pause and play section
    def toggleAnimations(self):
        self.animations_playing = not getattr(self, 'animations_playing', False)
        
        if self.animations_playing: # Just toggled TO playing
            if self.isDarkMode:
                self.ui.playButton.setIcon(self.pauseIconWhite) # Show PAUSE icon
            else:
                self.ui.playButton.setIcon(self.pauseIcon)
            self.ui.playButton.setToolTip("Playing (Click to Pause)")

            for anim, _ in self.animations:
                if isinstance(anim, QVariantAnimation):
                    if anim.state() == QVariantAnimation.State.Stopped:
                        anim.start()
                    else:
                        anim.resume()
                elif isinstance(anim, QtCore.QTimeLine):
                    if anim.state() == QtCore.QTimeLine.State.NotRunning:
                        anim.start()
                    else:
                        anim.resume()
        else: # Just toggled TO NOT playing (paused/stopped)
            if self.isDarkMode:
                self.ui.playButton.setIcon(self.playIconWhite) # Show PLAY icon
            else:
                self.ui.playButton.setIcon(self.playIcon)
            self.ui.playButton.setToolTip("Paused/Stopped (Click to Play)")

            for anim, _ in self.animations:
                if isinstance(anim, QVariantAnimation):
                    anim.pause()
                elif isinstance(anim, QtCore.QTimeLine):
                    anim.setPaused(True)

    def toggleEditMode(self):
        edit_enabled = self.editButton.isChecked()
        self.ui.graphicsView.setEditMode(edit_enabled)
        
        if edit_enabled:
            self.ui.graphicsView.setCursor(Qt.ArrowCursor)
            self.editButton.setToolTip("Disable Edit Mode")
        else:
            self.ui.graphicsView.setCursor(Qt.OpenHandCursor)
            self.editButton.setToolTip("Enable Edit Mode")
        
        if edit_enabled:
            status_message = "Edit mode enabled - Click and drag to select/move items"
        else:
            status_message = "Edit mode disabled - Use two fingers to pan"
            
        self.statusBar().showMessage(status_message, 3000)

    def setupShortcuts(self):
        # Clear existing shortcuts for live updates
        for shortcut_item in self.shortcuts_list:
            shortcut_item.setEnabled(False)
            shortcut_item.activated.disconnect()
        self.shortcuts_list.clear()

        # Standard shortcut for opening preferences/settings
        settings_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Preferences), self)
        settings_shortcut.activated.connect(self.showSettingsDialog)
        self.shortcuts_list.append(settings_shortcut)

        # Standard shortcut for opening a file
        open_file_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Open), self)
        open_file_shortcut.activated.connect(self.openFile)
        self.shortcuts_list.append(open_file_shortcut)

        export_shortcut_str = self.config_manager.get_export_shortcut()
        if export_shortcut_str:
            export_shortcut = QShortcut(QKeySequence(export_shortcut_str), self)
            export_shortcut.activated.connect(self.exportFile)
            self.shortcuts_list.append(export_shortcut)

        zoom_in_shortcut_str = self.config_manager.get_zoom_in_shortcut()
        if zoom_in_shortcut_str:
            zoom_in_shortcut = QShortcut(QKeySequence(zoom_in_shortcut_str), self)
            zoom_in_shortcut.activated.connect(self.zoomIn)
            self.shortcuts_list.append(zoom_in_shortcut)

        zoom_out_shortcut_str = self.config_manager.get_zoom_out_shortcut()
        if zoom_out_shortcut_str:
            zoom_out_shortcut = QShortcut(QKeySequence(zoom_out_shortcut_str), self)
            zoom_out_shortcut.activated.connect(self.zoomOut)
            self.shortcuts_list.append(zoom_out_shortcut)

        close_window_shortcut_str = self.config_manager.get_close_window_shortcut()
        if close_window_shortcut_str:
            close_window_shortcut = QShortcut(QKeySequence(close_window_shortcut_str), self)
            close_window_shortcut.activated.connect(self.close) # Connect to self.close
            self.shortcuts_list.append(close_window_shortcut)

        play_pause_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        play_pause_shortcut.activated.connect(self.toggleAnimations)
        self.shortcuts_list.append(play_pause_shortcut)

    # settings section
    def showSettingsDialog(self):
        dialog = SettingsDialog(self, self.config_manager)
        if dialog.exec() == QDialog.Accepted:
            self.setupShortcuts()
            # Theme update logic based on config
            current_theme_preference = self.config_manager.get_config("ui_theme", "system")
            if current_theme_preference == "dark":
                if not self.isDarkMode:
                    self.isDarkMode = True # Update state before applying
                    self.applyDarkModeStyles()
                    self.updateCategoryHeaders()
                    # Notify callbacks
                    for callback in self.theme_change_callbacks:
                        callback(self.isDarkMode)
            elif current_theme_preference == "light":
                if self.isDarkMode:
                    self.isDarkMode = False # Update state before applying
                    self.applyLightModeStyles()
                    self.updateCategoryHeaders()
                    # Notify callbacks
                    for callback in self.theme_change_callbacks:
                        callback(self.isDarkMode)
            else: # System theme
                # Re-detect system theme. This will trigger updates if different.
                self.detectDarkMode() # This internally calls applyXStyles, updateButtonIcons, updateCategoryHeaders and notifies callbacks if mode changed

    def apply_default_sizes(self):
        if hasattr(self, 'ui') and hasattr(self.ui, 'mainSplitter'):
            total_width = self.ui.mainSplitter.width()
            section_width = total_width // 3
            self.ui.mainSplitter.setSizes([section_width, section_width, section_width])
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'layersSplitter'):
            total_height = self.ui.layersSplitter.height()
            section_height = total_height // 2
            self.ui.layersSplitter.setSizes([section_height, section_height])
    
    def saveSplitterSizes(self):
        if hasattr(self, 'ui') and hasattr(self.ui, 'mainSplitter'):
            sizes = self.ui.mainSplitter.sizes()
            self.config_manager.save_splitter_sizes("mainSplitter", sizes)
            
        if hasattr(self, 'ui') and hasattr(self.ui, 'layersSplitter'):
            sizes = self.ui.layersSplitter.sizes()
            self.config_manager.save_splitter_sizes("layersSplitter", sizes)
    
    def loadSplitterSizes(self):
        if hasattr(self, 'ui') and hasattr(self.ui, 'mainSplitter'):
            sizes = self.config_manager.get_splitter_sizes("mainSplitter")
            if sizes:
                self.ui.mainSplitter.setSizes(sizes)
                
        if hasattr(self, 'ui') and hasattr(self.ui, 'layersSplitter'):
            sizes = self.config_manager.get_splitter_sizes("layersSplitter")
            if sizes:
                self.ui.layersSplitter.setSizes(sizes)

    def loadWindowGeometry(self):
        geometry = self.config_manager.get_window_geometry()
        
        if geometry["remember_size"]:
            self.resize(geometry["size"][0], geometry["size"][1])
            self.move(geometry["position"][0], geometry["position"][1])
            
            if geometry["maximized"]:
                self.showMaximized()
                
    def saveWindowGeometry(self):
        if self.isMaximized():
            size = [self.normalGeometry().width(), self.normalGeometry().height()]
            position = [self.normalGeometry().x(), self.normalGeometry().y()]
            self.config_manager.save_window_geometry(size, position, True)
        else:
            size = [self.width(), self.height()]
            position = [self.x(), self.y()]
            self.config_manager.save_window_geometry(size, position, False)

    def closeEvent(self, event):
        if getattr(self, 'isDirty', False):
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("You have unsaved changes. Are you sure you want to discard them and exit?")
            pix = QPixmap(":/assets/openposter.png")
            msg.setIconPixmap(pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            reply = msg.exec()
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self.saveSplitterSizes()
        self.saveWindowGeometry()
        super().closeEvent(event)

    def saveFile(self):
        if not hasattr(self, 'cafile') or not self.cafile:
            QMessageBox.warning(self, "Save Error", "No file is open to save.")
            return False
        
        if hasattr(self, 'cafilepath') and self.cafilepath:
            try:
                dest, name = os.path.split(self.cafilepath)
                self.cafile.write_file(name, dest)
                self.statusBar().showMessage(f"File saved to {self.cafilepath}", 3000)
                self.isDirty = False
                return True
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save file to {self.cafilepath}:\n{e}")
                return False
        else:
            return self.saveFileAs() # No current path, so use Save As

    def saveFileAs(self):
        if not hasattr(self, 'cafile') or not self.cafile:
            QMessageBox.warning(self, "Save As Error", "No file is open to save.")
            return False

        # Default to current cafilepath if it exists, otherwise user's documents or home directory
        initial_path = self.cafilepath if hasattr(self, 'cafilepath') and self.cafilepath else QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        if not initial_path:
             initial_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)

        path, _ = QFileDialog.getSaveFileName(self, "Save As...", initial_path, "Core Animation Bundle (*.ca)")
        
        if not path:
            return False # User cancelled
            
        # Ensure the path ends with .ca if the filter doesn't enforce it
        if not path.lower().endswith('.ca'):
            path += '.ca'
            
        try:
            dest, name = os.path.split(path)
            self.cafile.write_file(name, dest)
            self.cafilepath = path # Update current file path
            self.ui.filename.setText(path) # Update filename label
            self.setWindowTitle(f"OpenPoster - {name}") # Update window title
            self.statusBar().showMessage(f"File saved as {path}", 3000)
            self.isDirty = False
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save As Error", f"Could not save file to {path}:\n{e}")
            return False

    def openDiscord(self):
        webbrowser.open("https://discord.gg/t3abQJjHm6")
    def exportFile(self):
        if not self.cafile:
            QMessageBox.warning(self, "No File", "Please open a CAFile first.")
            return

        dialog = ExportOptionsDialog(self, self.config_manager) # Pass config_manager
        if dialog.exec():
            choice = dialog.choice
            if choice == "copy":
                path, _ = QFileDialog.getSaveFileName(self, "Save As", self.cafilepath, "Core Animation Bundle (*.ca)")
                if not path:
                    return
                dest, name = os.path.split(path)
                self.cafile.write_file(name, dest)
                self.cafilepath = path
                self.ui.filename.setText(path)
                self.statusBar().showMessage(f"Saved As {path}", 3000)
                self.isDirty = False # Mark clean after successful save
                
            elif choice == 'tendies':
                path, _ = QFileDialog.getSaveFileName(self, "Save as .tendies", self.cafilepath, "Tendies Bundle (*.tendies)")
                if not path:
                    return
                
                # Ensure the path ends with .tendies
                if not path.lower().endswith('.tendies'):
                    path += '.tendies'

                temp_dir = tempfile.mkdtemp()
                try:
                    self._create_tendies_structure(temp_dir, self.cafilepath)

                    shutil.make_archive(path[:-len('.tendies')], 'zip', root_dir=temp_dir)
                    
                    os.rename(path[:-len('.tendies')] + '.zip', path)

                except Exception as e:
                     QMessageBox.critical(self, "Export Error", f"Failed to create .tendies file: {e}")
                finally:
                    shutil.rmtree(temp_dir) # Clean up temp directory

            elif choice == 'nugget':
                temp_dir = tempfile.mkdtemp()
                try:
                    self._create_tendies_structure(temp_dir, self.cafilepath)

                    export_dir = os.path.join(self.config_manager.config_dir, 'nugget-exports')
                    os.makedirs(export_dir, exist_ok=True)
                    base_name = os.path.splitext(os.path.basename(self.cafilepath))[0]
                    archive_base = os.path.join(export_dir, base_name)
                    zip_file = shutil.make_archive(archive_base, 'zip', root_dir=temp_dir)
                    tendies_path = archive_base + '.tendies'
                    os.rename(zip_file, tendies_path)
                    target = tendies_path

                    nugget_exec = self.config_manager.get_nugget_exec_path()
                    if not nugget_exec:
                        QMessageBox.information(self, "Nugget Export", "Nugget executable path is not configured in settings.")
                        return
                    if not os.path.exists(nugget_exec):
                        QMessageBox.warning(self, "Nugget Error", f"Nugget executable not found at: {nugget_exec}")
                        return

                    # Asynchronous nugget execution
                    if nugget_exec.lower().endswith(".py"):
                        program = sys.executable
                        args = [nugget_exec, target]
                    elif nugget_exec.endswith(".app") and self.isMacOS:
                        program = "open"
                        args = [nugget_exec, "--args", target]
                    else:
                        program = nugget_exec
                        args = [target]

                    print("Running Nugget:", program, *args)
                    self._run_nugget_export(program, args)
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Failed during Nugget export preparation: {e}")
                finally:
                    shutil.rmtree(temp_dir)  # Clean up temp directory (incl. content and zip)
            
            # Removed self.isDirty = False from here as it's now handled per-case

    def _create_tendies_structure(self, base_dir, ca_source_path):
        """Creates the necessary directory structure for a .tendies bundle inside base_dir."""
        try:
            # Copy descriptors template
            root = sys._MEIPASS if hasattr(sys, '_MEIPASS') else (os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd())
            descriptors_src = os.path.join(root, "descriptors")
            if not os.path.exists(descriptors_src):
                raise FileNotFoundError("descriptors template directory not found")
                
            descriptors_dest = os.path.join(base_dir, "descriptors")
            shutil.copytree(descriptors_src, descriptors_dest, dirs_exist_ok=True)

            # Find the EID directory (assuming only one)
            eid = next((d for d in os.listdir(descriptors_dest) if os.path.isdir(os.path.join(descriptors_dest, d)) and not d.startswith('.')), None)
            if not eid:
                raise FileNotFoundError("Could not find EID directory within descriptors template")

            # Define the path for the .wallpaper bundle
            contents_dir = os.path.join(descriptors_dest, eid, "versions", "0", "contents")
            wallpaper_dir = os.path.join(contents_dir, "OpenPoster.wallpaper")
            os.makedirs(wallpaper_dir, exist_ok=True)

            # Copy the .ca bundle content into the .wallpaper directory
            if not os.path.exists(ca_source_path):
                 raise FileNotFoundError(f".ca source path does not exist: {ca_source_path}")
            ca_basename = os.path.basename(ca_source_path)
            ca_dest_dir = os.path.join(wallpaper_dir, ca_basename)
            shutil.copytree(ca_source_path, ca_dest_dir)
            
        except Exception as e:
            print(f"Error creating tendies structure in {base_dir}: {e}")
            raise # Re-raise the exception to be caught by the caller

    def markDirty(self):
        self.isDirty = True

    def onItemMoved(self, item):
        layer_id = item.data(0)
        layer = self.cafile.rootlayer.findlayer(layer_id)
        if layer:
            pos = item.pos()
            layer.position = [str(pos.x()), str(pos.y())]
            scene_rect = item.mapToScene(item.boundingRect()).boundingRect()
            w = scene_rect.width()
            h = scene_rect.height()
            x0, y0 = layer.bounds[0], layer.bounds[1]
            layer.bounds = [x0, y0, str(w), str(h)]
        if hasattr(self, 'currentInspectObject') and self.currentInspectObject == layer:
            for r in range(self.ui.tableWidget.rowCount()):
                label = self.ui.tableWidget.item(r, 0)
                if not label:
                    continue
                key = label.text()
                if key == 'POSITION':
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(' '.join(layer.position)))
                elif key == 'BOUNDS':
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(' '.join(layer.bounds)))
        self.markDirty()

    def onTransformChanged(self, item, transform):
        layer_id = item.data(0)
        layer = self.cafile.rootlayer.findlayer(layer_id)
        if layer:
            scene_rect = item.mapToScene(item.boundingRect()).boundingRect()
            w = scene_rect.width()
            h = scene_rect.height()
            x0, y0 = layer.bounds[0], layer.bounds[1]
            layer.bounds = [x0, y0, str(w), str(h)]
            layer.transform = None
        if hasattr(self, 'currentInspectObject') and self.currentInspectObject == layer:
            for r in range(self.ui.tableWidget.rowCount()):
                label = self.ui.tableWidget.item(r, 0)
                if label and label.text() == 'BOUNDS':
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(' '.join(layer.bounds)))
                    break
            self.renderPreview(self.cafile.rootlayer)
            self.fitPreviewToView()
        self.markDirty()

    def onInspectorChanged(self, item):
        if item.column() != 1:
            return
        obj = getattr(self, 'currentInspectObject', None)
        if obj is None:
            return
        key = self.ui.tableWidget.item(item.row(), 0).text()
        val = item.text()
        parts = key.lower().split()
        xml_key = parts[0] + ''.join(p.capitalize() for p in parts[1:])
        if not hasattr(obj, xml_key):
            return
        orig_val = getattr(obj, xml_key)
        if isinstance(orig_val, list):
            # extract all numbers from the stringified list
            nums = re.findall(r'-?\d+\.?\d*', str(orig_val))
            setattr(obj, xml_key, nums)
        else:
            setattr(obj, xml_key, val)
        self.markDirty()
        if xml_key in ['position', 'bounds']:
            self.renderPreview(self.cafile.rootlayer)
            self.fitPreviewToView()

    def zoomIn(self):
        self.ui.graphicsView.handleZoom(120)

    def zoomOut(self):
        self.ui.graphicsView.handleZoom(-120)

    def keyPressEvent(self, event):
        mods = event.modifiers()
        if (mods & Qt.ControlModifier) or (self.isMacOS and (mods & Qt.MetaModifier)):
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal): # Removed Qt.KeypadPlus
                self.zoomIn()
                return
            if event.key() in (Qt.Key_Minus, Qt.Key_Underscore): # Removed Qt.KeypadMinus
                self.zoomOut()
                return
        super(MainWindow, self).keyPressEvent(event)

    # Run nugget export asynchronously using QProcess
    def _run_nugget_export(self, program, args):
        process = QtCore.QProcess(self)
        process.setProgram(program)
        process.setArguments(args)
        process.finished.connect(self._on_nugget_finished)
        process.errorOccurred.connect(lambda error: QMessageBox.critical(self, "Nugget Error", f"Nugget execution error: {error}"))
        process.start()

    # Handle completion of nugget export process
    def _on_nugget_finished(self, exitCode, exitStatus):
        process = self.sender()
        stdout = bytes(process.readAllStandardOutput()).decode()
        stderr = bytes(process.readAllStandardError()).decode()
        if exitCode == 0:
            self.statusBar().showMessage("Exported to Nugget successfully", 3000)
            self.isDirty = False
        else:
            error_message = f"Nugget execution failed (exit code {exitCode}).\n"
            if stdout:
                error_message += f"stdout:\n{stdout}\n"
            if stderr:
                error_message += f"stderr:\n{stderr}"
            print(error_message)
            QMessageBox.critical(self, "Nugget Error", f"Nugget execution failed. Check console for details.\nError: {stderr or stdout or 'Unknown error'}")

    # Clear the nugget-exports folder at each launch
    def _clear_nugget_exports_cache(self):
        export_dir = os.path.join(self.config_manager.config_dir, 'nugget-exports')
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        os.makedirs(export_dir, exist_ok=True)

    def open_project(self, path):
        """
        Open a .ca project from the given path (used for macOS file association).
        """
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Open Error", f"The file or folder does not exist: {path}")
            return
        self.ui.treeWidget.clear()
        self.ui.statesTreeWidget.clear()
        self.cafilepath = path
        self.setWindowTitle(f"OpenPoster - {os.path.basename(self.cafilepath)}")
        self.ui.filename.setText(self.cafilepath)
        self.ui.filename.setStyleSheet("font-style: normal; color: palette(text); border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 10px;")
        self.showFullPath = True
        self.cafile = CAFile(self.cafilepath)
        self.cachedImages = {}
        self.missing_assets = set()
        rootItem = QTreeWidgetItem([self.cafile.rootlayer.name, "Root", self.cafile.rootlayer.id, ""])
        self.ui.treeWidget.addTopLevelItem(rootItem)
        if len(self.cafile.rootlayer._sublayerorder) > 0:
            self.treeWidgetChildren(rootItem, self.cafile.rootlayer)
        self.populateStatesTreeWidget()
        if hasattr(self._applyAnimation, 'animations'):
            self._applyAnimation.animations.clear()
        self.animations = []
        self.scene.clear()
        self.currentZoom = 1.0
        self.ui.graphicsView.resetTransform()
        self.renderPreview(self.cafile.rootlayer)
        if hasattr(self._applyAnimation, 'animations'):
            self.animations = list(self._applyAnimation.animations)
        self.fitPreviewToView()
        self.isDirty = False
