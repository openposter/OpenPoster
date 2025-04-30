import sys
import os
import math
from lib.ca_elements.core import CAFile
from PySide6 import QtCore
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QEvent, QVariantAnimation, QKeyCombination, QKeyCombination
from PySide6.QtGui import QPixmap, QImage, QBrush, QPen, QColor, QTransform, QPainter, QLinearGradient, QIcon, QPalette, QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem, QMainWindow, QTableWidgetItem, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem, QApplication, QHeaderView, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QTreeWidget, QWidget, QGraphicsItemAnimation
from ui.ui_mainwindow import Ui_OpenPoster
from .custom_widgets import CustomGraphicsView, CheckerboardGraphicsScene
import PySide6.QtCore as QtCore
import platform
import webbrowser

import resources_rc

# temporary code split for reading
from ._formatter import Format
from ._parse import Parse
from ._applyanimation import ApplyAnimation
from ._assets import Assets

from .config_manager import ConfigManager
from .settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.scene: CheckerboardGraphicsScene = None

        # config manager
        self.config_manager = ConfigManager()

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
        
        self.animations_playing = False
        self.animations = []
        
        # set up keyboard shortcuts
        self.setupShortcuts()

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
        self.isDarkMode = False
    
    # themes section
    def detectDarkMode(self):
        previous_dark_mode = self.isDarkMode if hasattr(self, 'isDarkMode') else False
        
        try:
            app = QApplication.instance()
            if app:
                windowText = app.palette().color(QPalette.Active, QPalette.WindowText)
                self.isDarkMode = windowText.lightness() > 128
        except:
            self.isDarkMode = False

        if hasattr(self, 'ui') and previous_dark_mode != self.isDarkMode:
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
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.ApplicationPaletteChange:
            self.updateAppearanceForMac()
        return super(MainWindow, self).eventFilter(obj, event)
            
    def updateAppearanceForMac(self):
        previous_dark_mode = self.isDarkMode
        self.isDarkMode = False
        
        try:
            from Foundation import NSUserDefaults # type: ignore
            appleInterfaceStyle = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            self.isDarkMode = appleInterfaceStyle == "Dark"
        except:
            app = QApplication.instance()
            if app:
                windowText = app.palette().color(QPalette.Active, QPalette.WindowText)
                self.isDarkMode = windowText.lightness() > 128
        
        if self.isDarkMode:
            self.applyDarkModeStyles()
            if hasattr(self, 'editButton'):
                self.editButton.setIcon(self.editIconWhite)
            if hasattr(self, 'playButton'):
                if self.animations_playing:
                    self.playButton.setIcon(self.pauseIconWhite)
                else:
                    self.playButton.setIcon(self.playIconWhite)
            if hasattr(self, 'settingsButton'):
                self.settingsButton.setIcon(self.settingsIconWhite)
            if hasattr(self, 'discordButton'):
                self.discordButton.setIcon(self.discordIconWhite)
        else:
            self.applyLightModeStyles()
            if hasattr(self, 'editButton'):
                self.editButton.setIcon(self.editIcon)
            if hasattr(self, 'playButton'):
                if self.animations_playing:
                    self.playButton.setIcon(self.pauseIcon)
                else:
                    self.playButton.setIcon(self.playIcon)
            if hasattr(self, 'settingsButton'):
                self.settingsButton.setIcon(self.settingsIcon)
            if hasattr(self, 'discordButton'):
                self.discordButton.setIcon(self.discordIcon)
        
        if previous_dark_mode != self.isDarkMode:
            self.updateCategoryHeaders()
    
    def applyDarkModeStyles(self):
        scene = self.scene if hasattr(self, 'scene') else None
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(50, 50, 50), QColor(40, 40, 40))
            scene.update()
            
        if hasattr(self, 'playButton'):
            self.playButton.setStyleSheet("""
                QPushButton { 
                    border: none; 
                    background-color: transparent;
                    color: rgba(255, 255, 255, 150);
                }
                QPushButton:hover { 
                    background-color: rgba(128, 128, 128, 50);
                    border-radius: 20px;
                }
            """)
            
        if hasattr(self, 'editButton'):
            self.editButton.setStyleSheet("""
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
            """)
            
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
                background-color: palette(button);
                color: palette(text);
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(180, 180, 180, 60);
                border-bottom: none;
            }
        """)
    
    def applyLightModeStyles(self):
        scene = self.scene if hasattr(self, 'scene') else None
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setBackgroundColor(QColor(240, 240, 240), QColor(220, 220, 220))
            scene.update()
            
        if hasattr(self, 'playButton'):
            self.playButton.setStyleSheet("""
                QPushButton { 
                    border: none; 
                    background-color: transparent;
                    color: rgba(0, 0, 0, 150);
                }
                QPushButton:hover { 
                    background-color: rgba(128, 128, 128, 30);
                    border-radius: 20px;
                }
            """)
            
        if hasattr(self, 'editButton'):
            self.editButton.setStyleSheet("""
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
            """)
            
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
                background-color: palette(button);
                color: palette(text);
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(120, 120, 120, 60);
                border-bottom: none;
            }
        """)

    # gui loader section
    def initUI(self):
        
        if not hasattr(self.ui, 'previewLabel'):
            self.ui.previewLabel = QLabel(self.ui.previewWidget)
            self.ui.previewLabel.setObjectName("previewLabel")
            self.ui.previewLabel.setText("Preview")
        
        self.previewHeaderLayout = QHBoxLayout()
        self.previewHeaderLayout.setContentsMargins(0, 0, 0, 0)
        self.previewHeaderLayout.setSpacing(10)
        
        self.ui.previewLabel.setStyleSheet("font-size: 14px; padding: 5px;")
        self.previewHeaderLayout.addWidget(self.ui.previewLabel)
        
        self.previewHeaderLayout.addStretch()
        
        self.editButton = QPushButton(self.ui.previewWidget)
        self.editButton.setObjectName("editButton")
        self.editButton.setIcon(self.editIconWhite if self.isDarkMode else self.editIcon)
        self.editButton.setToolTip("Toggle Edit Mode")
        self.editButton.setFixedSize(40, 40)
        self.editButton.setIconSize(QSize(24, 24))
        self.editButton.setCheckable(True)
        self.editButton.setStyleSheet("""
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
        """)
        self.editButton.clicked.connect(self.toggleEditMode)
        self.previewHeaderLayout.addWidget(self.editButton)
        
        self.playButton = QPushButton(self.ui.previewWidget)
        self.playButton.setObjectName("playButton")
        self.playButton.setIcon(self.playIconWhite if self.isDarkMode else self.playIcon)
        self.playButton.setToolTip("Play/Pause Animations")
        self.playButton.setFixedSize(40, 40)
        self.playButton.setIconSize(QSize(32, 32))
        self.playButton.setStyleSheet("""
            QPushButton { 
                border: none; 
                background-color: transparent;
                color: rgba(255, 255, 255, 150);
            }
            QPushButton:hover { 
                background-color: rgba(128, 128, 128, 50);
                border-radius: 20px;
            }
        """)
        self.playButton.clicked.connect(self.toggleAnimations)
        self.previewHeaderLayout.addWidget(self.playButton)
        
        self.ui.previewLayout.removeWidget(self.ui.previewLabel)
        self.ui.previewLayout.insertLayout(0, self.previewHeaderLayout)
        
        self.settingsButton = QPushButton(self.ui.headerWidget)
        self.settingsButton.setObjectName("settingsButton")
        self.settingsButton.setIcon(self.settingsIconWhite if self.isDarkMode else self.settingsIcon)
        self.settingsButton.setToolTip("Settings")
        self.settingsButton.setFixedSize(40, 40)
        self.settingsButton.setIconSize(QSize(24, 24))
        self.settingsButton.setStyleSheet("""
            QPushButton { 
                border: none; 
                background-color: transparent;
            }
            QPushButton:hover { 
                background-color: rgba(128, 128, 128, 30);
                border-radius: 20px;
            }
        """)
        self.settingsButton.clicked.connect(self.showSettingsDialog)
        
        self.discordButton = QPushButton(self.ui.headerWidget)
        self.discordButton.setObjectName("discordButton")
        self.discordButton.setIcon(self.discordIconWhite if self.isDarkMode else self.discordIcon)
        self.discordButton.setToolTip("Open Discord")
        self.discordButton.setFixedSize(40, 40)
        self.discordButton.setIconSize(QSize(24, 24))
        self.discordButton.setStyleSheet("""
            QPushButton { 
                border: none; 
                background-color: transparent;
            }
            QPushButton:hover { 
                background-color: rgba(128, 128, 128, 30);
                border-radius: 20px;
            }
        """)
        self.discordButton.clicked.connect(self.openDiscord)
        
        self.ui.horizontalLayout_header.addWidget(self.discordButton)
        self.ui.horizontalLayout_header.addWidget(self.settingsButton)
        
        self.ui.openFile.clicked.connect(self.openFile)
        self.ui.treeWidget.currentItemChanged.connect(self.openInInspector)
        self.ui.statesTreeWidget.currentItemChanged.connect(self.openStateInInspector)
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Key", "Value"])
        self.ui.filename.mousePressEvent = self.toggleFilenameDisplay
        self.showFullPath = True
        
        self.ui.tableWidget.verticalHeader().setVisible(False) 
        self.ui.tableWidget.setShowGrid(False) 
        self.ui.tableWidget.setFrameStyle(0)
        self.ui.tableWidget.setStyleSheet("""
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
        """)
        header_font = self.ui.tableWidget.horizontalHeader().font()
        header_font.setPointSize(header_font.pointSize() + 1)
        self.ui.tableWidget.horizontalHeader().setFont(header_font)
        self.ui.tableWidget.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: palette(button);
                color: palette(text);
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(120, 120, 120, 60);
                border-bottom: none;
            }
        """)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.scene = CheckerboardGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        
        self.ui.graphicsView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.graphicsView.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.ui.graphicsView.setTransformationAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ui.graphicsView.setResizeAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ui.graphicsView.setViewportUpdateMode(self.ui.graphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        self.ui.graphicsView.minZoom = 0.05
        self.ui.graphicsView.maxZoom = 10.0
        self.ui.graphicsView.contentFittingZoom = 0.05
        
        self.ui.graphicsView.setCursor(Qt.OpenHandCursor)
        
        self.ui.mainSplitter.splitterMoved.connect(lambda: self.saveSplitterSizes())
        self.ui.layersSplitter.splitterMoved.connect(lambda: self.saveSplitterSizes())
        
        self.loadSplitterSizes()
        
        self.currentSelectedItem = None
        self.cachedImages = {}
        self.currentZoom = 1.0

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
            self.ui.filename.setStyleSheet("border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 5px;")
            self.showFullPath = True
            self.cafile = CAFile(self.cafilepath)
            self.cachedImages = {}
            self.missing_assets = set()
            
            rootItem = QTreeWidgetItem([self.cafile.rootlayer.name, "Root", self.cafile.rootlayer.id, ""])
            self.ui.treeWidget.addTopLevelItem(rootItem)

            if len(self.cafile.rootlayer._sublayerorder) > 0:
                self.treeWidgetChildren(rootItem, self.cafile.rootlayer)
            
            self.populateStatesTreeWidget()
            
            self.scene.clear()
            self.currentZoom = 1.0
            self.ui.graphicsView.resetTransform()
            self.renderPreview(self.cafile.rootlayer)
            self.fitPreviewToView()
        else:
            self.ui.filename.setText("No File Open")
            self.ui.filename.setStyleSheet("border: 1.5px solid palette(highlight); border-radius: 8px; padding: 5px 5px; color: #666666; font-style: italic;")

    def fitPreviewToView(self):
        if not hasattr(self, 'cafilepath') or not self.cafilepath:
            return
            
        all_items_rect = self.scene.itemsBoundingRect()
        
        if all_items_rect.isEmpty():
            return
            
        all_items_rect.adjust(-30, -30, 30, 30)
        
        self.ui.graphicsView.updateContentFittingZoom(all_items_rect)
        
        self.ui.graphicsView.fitInView(all_items_rect, Qt.KeepAspectRatio)
        
        transform = self.ui.graphicsView.transform()
        self.currentZoom = transform.m11()

    # only called like once
    def treeWidgetChildren(self, item, layer):
        for id in layer._sublayerorder:
            sublayer = layer.sublayers.get(id)
            childItem = QTreeWidgetItem([sublayer.name, "Layer", sublayer.id, layer.id])
            
            if hasattr(self, 'missing_assets') and hasattr(sublayer, '_content') and sublayer._content is not None:
                if hasattr(sublayer, 'content') and hasattr(sublayer.content, 'src'):
                    if sublayer.content.src in self.missing_assets:
                        childItem.setText(0, "⚠️ " + sublayer.name)
                        childItem.setForeground(0, QColor(255, 0, 0))
            
            item.addChild(childItem)

            if len(sublayer._sublayerorder) > 0:
                self.treeWidgetChildren(childItem, sublayer)
            if sublayer._animations is not None:
                for animation in sublayer.animations:
                    animItem = QTreeWidgetItem([animation.keyPath, "Animation", "", sublayer.id])
                    childItem.addChild(animItem)

    # inspector section
    def openInInspector(self, current, _):
        if current is None:
            return
            
        self.currentSelectedItem = current
        self.ui.tableWidget.setRowCount(0)
        row_index = 0
        
        element_type = current.text(1)
        if element_type == "Animation":
            parent = self.cafile.rootlayer.findlayer(current.text(3))
            element = parent.findanimation(current.text(0))
            if element:
                row_index = self.add_category_header("Basic Info", row_index)
                
                self.add_inspector_row("NAME", current.text(0), row_index)
                row_index += 1
                
                self.add_inspector_row("TYPE", element.type, row_index)
                row_index += 1
                
                self.add_inspector_row("KEYPATH", element.keyPath, row_index)
                row_index += 1
                
                timing_properties = False
                if (hasattr(element, "duration") and element.duration) or \
                   (hasattr(element, "beginTime") and element.beginTime) or \
                   (hasattr(element, "fillMode") and element.fillMode) or \
                   (hasattr(element, "removedOnCompletion") and element.removedOnCompletion) or \
                   (hasattr(element, "repeatCount") and element.repeatCount) or \
                   (hasattr(element, "calculationMode") and element.calculationMode):
                    row_index = self.add_category_header("Timing", row_index)
                    timing_properties = True
                
                if hasattr(element, "duration") and element.duration:
                    self.add_inspector_row("DURATION", self.formatFloat(element.duration), row_index)
                    row_index += 1
                
                if hasattr(element, "beginTime") and element.beginTime:
                    self.add_inspector_row("BEGIN TIME", self.formatFloat(element.beginTime), row_index)
                    row_index += 1
                
                if hasattr(element, "fillMode") and element.fillMode:
                    self.add_inspector_row("FILL MODE", element.fillMode, row_index)
                    row_index += 1
                
                if hasattr(element, "removedOnCompletion") and element.removedOnCompletion: # Due tomorrow, do tomorrow' Use a bool
                    self.add_inspector_row("REMOVED ON COMPLETION", element.removedOnCompletion, row_index)
                    row_index += 1
                
                if hasattr(element, "repeatCount") and element.repeatCount:
                    self.add_inspector_row("REPEAT COUNT", self.formatFloat(element.repeatCount), row_index)
                    row_index += 1
                
                if hasattr(element, "calculationMode") and element.calculationMode:
                    self.add_inspector_row("CALCULATION MODE", element.calculationMode, row_index)
                    row_index += 1
                
                if element.type == "CASpringAnimation":
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
                        self.add_inspector_row("AUTO RECALCULATES DURATION", 
                                             element.mica_autorecalculatesDuration, row_index)
                        row_index += 1
                
                if element.type == "CAKeyframeAnimation":
                    row_index = self.add_category_header("Keyframe Data", row_index)
                    
                    if hasattr(element, "values") and element.values:
                        values_str = ", ".join([self.formatFloat(value.value) for value in element.values])
                        self.add_inspector_row("VALUES", values_str, row_index)
                        row_index += 1
                    
                    if hasattr(element, "keyTimes") and element.keyTimes:
                        times_str = ", ".join([self.formatFloat(time.value) for time in element.keyTimes])
                        self.add_inspector_row("KEY TIMES", times_str, row_index)
                        row_index += 1
                    
                    if hasattr(element, "timingFunctions") and element.timingFunctions:
                        self.add_inspector_row("TIMING FUNCTIONS", str(len(element.timingFunctions)), row_index)
                        row_index += 1
                    
                    if hasattr(element, "path") and element.path:
                        self.add_inspector_row("PATH", "Path Animation", row_index)
                        row_index += 1
                
                if element.type == "CAMatchMoveAnimation":
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
                
                if element.type == "LKAnimationGroup":
                    row_index = self.add_category_header("Animation Group", row_index)
                    
                    if hasattr(element, "animations") and element.animations:
                        self.add_inspector_row("SUB ANIMATIONS", str(len(element.animations)), row_index)
                        row_index += 1
                
                self.highlightAnimationInPreview(parent, element)
                
        elif element_type == "Layer" or element_type == "Root":
            if element_type == "Layer":
                element = self.cafile.rootlayer.findlayer(current.text(2))
            else:
                element = self.cafile.rootlayer
                
            if element:
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
                
                if hasattr(element, "position") and element.position:
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
        self.scene.clear()
        
        bounds = QRectF(0, 0, 1000, 1000)
        if hasattr(root_layer, "bounds") and root_layer.bounds:
            try:
                x = float(root_layer.bounds[0])
                y = float(root_layer.bounds[1])
                w = float(root_layer.bounds[2])
                h = float(root_layer.bounds[3])
                bounds = QRectF(x, y, w, h)
            except (ValueError, IndexError):
                pass
        
        border_rect = QGraphicsRectItem(bounds)
        border_rect.setPen(QPen(QColor(0, 0, 0), 2))
        border_rect.setBrush(QBrush(Qt.transparent))
        self.scene.addItem(border_rect)
        
        base_state = None
        if hasattr(root_layer, "states") and root_layer.states and "Base State" in root_layer.states:
            base_state = root_layer.states["Base State"]
        
        root_pos = QPointF(0, 0)
        if hasattr(root_layer, "position") and root_layer.position:
            try:
                root_pos = QPointF(float(root_layer.position[0]), float(root_layer.position[1]))
            except (ValueError, IndexError):
                pass
        
        self.renderLayer(root_layer, root_pos, QTransform(), base_state, target_state)
        
        all_items_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(all_items_rect)
        
    def renderLayer(self, layer, parent_pos, parent_transform, base_state=None, target_state=None):
        if hasattr(layer, "hidden") and layer.hidden:
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

                    scale_factor = 1.0
                    if pixmap.width() > bounds.width() or pixmap.height() > bounds.height():
                        scale_x = bounds.width() / pixmap.width() if pixmap.width() > 0 else 1.0
                        scale_y = bounds.height() / pixmap.height() if pixmap.height() > 0 else 1.0
                        scale_factor = min(scale_x, scale_y)

                    item_transform = QTransform()
                    item_transform.scale(scale_factor, scale_factor)
                    pixmap_item.setTransform(item_transform * transform)

                    scaled_width = pixmap.width() * scale_factor
                    scaled_height = pixmap.height() * scale_factor
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

    # pause and play section
    def toggleAnimations(self):
        if not hasattr(self, 'animations_playing'):
            self.animations_playing = False
            
        self.animations_playing = not self.animations_playing
            
        if self.animations_playing:
            if self.isDarkMode:
                self.playButton.setIcon(self.pauseIconWhite)
            else:
                self.playButton.setIcon(self.pauseIcon)
                
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
        else:
            if self.isDarkMode:
                self.playButton.setIcon(self.playIconWhite)
            else:
                self.playButton.setIcon(self.playIcon)
                
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
        settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut.activated.connect(self.showSettingsDialog)
        
        if self.isMacOS:
            alt_settings_shortcut = QShortcut(QKeySequence("Meta+,"), self)
            alt_settings_shortcut.activated.connect(self.showSettingsDialog)
    
    # settings section
    def showSettingsDialog(self):
        dialog = SettingsDialog(self, self.config_manager)
        dialog.exec()
    
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
        self.saveSplitterSizes()
        self.saveWindowGeometry() 
        super().closeEvent(event)

    def openDiscord(self):
        webbrowser.open("https://discord.gg/t3abQJjHm6")
