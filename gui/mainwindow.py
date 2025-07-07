import sys
import os
import math
from lib.ca_elements.core import CAFile, CALayer
from PySide6 import QtCore
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QEvent, QVariantAnimation, QKeyCombination, QKeyCombination, QTimer, QSettings, QStandardPaths, QDir, QObject, QProcess, QByteArray, QBuffer, QIODevice, QXmlStreamReader, QPoint, QMimeData, QRegularExpression, QTranslator
from PySide6.QtGui import QPixmap, QImage, QBrush, QPen, QColor, QTransform, QPainter, QLinearGradient, QIcon, QPalette, QFont, QShortcut, QKeySequence, QAction, QCursor, QDesktopServices
from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem, QMainWindow, QTableWidgetItem, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem, QApplication, QHeaderView, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QTreeWidget, QWidget, QGraphicsItemAnimation, QMessageBox, QDialog, QColorDialog, QProgressDialog, QSizePolicy, QSplitter, QFrame, QToolButton, QGraphicsView, QGraphicsScene, QStyleFactory, QSpacerItem, QMenu, QLineEdit, QTableWidget, QTableWidgetItem, QSystemTrayIcon, QGraphicsProxyWidget, QGraphicsDropShadowEffect, QMenu, QTreeWidgetItemIterator, QInputDialog, QSlider, QTextEdit
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
from .theme_manager import ThemeManager
from .preview_renderer import PreviewRenderer

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
        self.initAssetFinder()
        self.bindOperationFunctions()
        self.loadIconResources()

        self.ui = Ui_OpenPoster()
        self.ui.setupUi(self)
        
        self.isMacOS = platform.system() == "Darwin"
        self.theme_manager = ThemeManager(self.config_manager, self)
        self.theme_manager.load_theme()
        
        self.initUI()
        
        self.preview = PreviewRenderer(self)
        
        # Restore window geometry
        self.loadWindowGeometry()
        
        # set up keyboard shortcuts
        self.setupShortcuts()
        self.isDirty = False
        
        # print(f"OpenPoster v{__version__} started") # Commented out startup message

    # app resources
    def initAssetFinder(self):
        if hasattr(sys, '_MEIPASS'):
            self.app_base_path = sys._MEIPASS
        else:
            self.app_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        
        self.cachedImages = {}
        self.missing_assets = set()
        self.cafilepath = "" 

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

        self._assets = Assets()
        self.findAssetPath = self._assets.findAssetPath
        self.loadImage = self._assets.loadImage

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
        self.addIcon = QIcon(":/icons/add.svg")
        self.addIconWhite = QIcon(":/icons/add-white.svg")
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

        if hasattr(self.ui, 'addButton'):
            self.ui.addButton.setIcon(self.addIconWhite if self.isDarkMode else self.addIcon)

    def loadThemeFromConfig(self):
        theme = self.config_manager.get_config("ui_theme", "dark")
        self.isDarkMode = theme == "dark"
        if self.isDarkMode:
            self.applyDarkModeStyles()
        else:
            self.applyLightModeStyles()
        self.updateButtonIcons()
        self.theme_manager.update_category_headers()

    def applyDarkModeStyles(self):
        # Delegated to ThemeManager
        self.theme_manager.apply_dark_mode_styles()

    def applyLightModeStyles(self):
        # Delegated to ThemeManager
        self.theme_manager.apply_light_mode_styles()

    def _get_all_layer_names(self, layer):
        names = set()
        if hasattr(layer, 'name') and layer.name:
            names.add(layer.name)
        if hasattr(layer, 'sublayers'):
            for sublayer in layer.sublayers.values():
                names.update(self._get_all_layer_names(sublayer))
        return names

    def _generate_unique_layer_name(self, base_name):
        if not hasattr(self, 'cafile') or not self.cafile:
            return base_name

        all_names = self._get_all_layer_names(self.cafile.rootlayer)
        
        if base_name not in all_names:
            return base_name
        
        counter = 2
        while True:
            new_name = f"{base_name} {counter}"
            if new_name not in all_names:
                return new_name
            counter += 1

    def addlayer(self, **kwargs):
        if not hasattr(self, 'cafilepath') or not self.cafilepath:
            self.create_themed_message_box(
                QMessageBox.Warning,
                "No File Open", 
                "Please open or create a file before adding a layer."
            ).exec()
            return

        base_name = kwargs.get("name", "New Layer")
        unique_name = self._generate_unique_layer_name(base_name)
        kwargs['name'] = unique_name
        kwargs['id'] = unique_name

        layer = CALayer(**kwargs)
        layer_type = kwargs.get("type")

        root_layer = self.cafile.rootlayer
        if root_layer and hasattr(root_layer, 'bounds') and len(root_layer.bounds) == 4:
            try:
                root_bounds = [float(b) for b in root_layer.bounds]
                root_width = root_bounds[2]
                root_height = root_bounds[3]

                new_height = root_height * 0.3
                
                if root_height > 0:
                    aspect_ratio = root_width / root_height
                    new_width = new_height * aspect_ratio
                else:
                    new_width = root_width * 0.3

                center_x = root_width / 2
                center_y = root_height / 2

                layer.bounds = ['0', '0', str(new_width), str(new_height)]
                layer.position = [str(center_x), str(center_y)]
                layer.scale_factor = 0.3
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not get root layer bounds to resize new layer: {e}")
                pass

        if layer_type == "text":
            text, ok = QInputDialog.getText(self, "New Text Layer", "Enter text:", QLineEdit.Normal, getattr(layer, "string", ""))
            if not ok or not text:
                return
            layer.string = text
            
            if not hasattr(layer, "fontSize") or not layer.fontSize:
                root_height = float(root_layer.bounds[3])
                default_font_size = int(root_height * 0.05 * 2)
                layer.fontSize = str(default_font_size)
            if not hasattr(layer, "fontFamily") or not layer.fontFamily:
                layer.fontFamily = "Helvetica"
            if not hasattr(layer, "alignmentMode") or not layer.alignmentMode:
                layer.alignmentMode = "center"
            if not hasattr(layer, "color") or not layer.color:
                layer.color = "255 255 255"
                
        elif layer_type == "image":
            image_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
            if not image_path:
                return
            
            try:
                image = QImage(image_path)
                if not image.isNull():
                    img_width = image.width()
                    img_height = image.height()
                    
                    if img_height > 0:
                        current_height = float(layer.bounds[3])
                        
                        aspect_ratio = img_width / img_height
                        new_width = current_height * aspect_ratio
                        
                        layer.bounds[2] = str(new_width)
            except Exception as e:
                print(f"Could not resize image based on aspect ratio: {e}")

            layer.content.src = image_path

        if hasattr(self, "currentInspectObject"):
            element = self.currentInspectObject
        else:
            element = self.cafile.rootlayer

        element.addlayer(layer)
        self.ui.treeWidget.clear()
        self.populateLayersTreeWidget()
        self.renderPreview(self.cafile.rootlayer)
        self.markDirty()

    # gui loader section
    def initUI(self):
        # Connect signals and set dynamic properties.

        if hasattr(self.ui, 'editButton'):
            self.ui.editButton.hide()
            self.ui.editButton.setEnabled(False)
        
        self.ui.playButton.setIcon(self.playIconWhite if self.isDarkMode else self.playIcon) 
        self.ui.playButton.clicked.connect(self.toggleAnimations)
        
        self.ui.settingsButton.setIcon(self.settingsIconWhite if self.isDarkMode else self.settingsIcon)
        self.ui.settingsButton.clicked.connect(self.showSettingsDialog)
        
        self.ui.exportButton.setIcon(self.exportIconWhite if self.isDarkMode else self.exportIcon)
        self.ui.exportButton.clicked.connect(self.exportFile)

        self.ui.addButton.setIcon(self.addIconWhite if self.isDarkMode else self.addIcon)
        self.ui.addButton.setStyleSheet("QPushButton::menu-indicator { width: 0px; image: none; }")

        # i know we said we would make ui in QDesigner but i cant figure out how to do this sooo - retron
        self.add_menu_ui = QMenu(self)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.add_menu_ui.setGraphicsEffect(shadow)

        self.addMenuBasicAction = QAction(self)
        self.addMenuBasicAction.setText("Basic Layer")
        self.addMenuTextAction = QAction(self)
        self.addMenuTextAction.setText("Text Layer")
        self.addMenuImageAction = QAction(self)
        self.addMenuImageAction.setText("Image Layer")

        self.add_menu_ui.addAction(self.addMenuBasicAction)
        self.addMenuBasicAction.triggered.connect(lambda: self.addlayer())
        self.add_menu_ui.addAction(self.addMenuTextAction)
        self.addMenuTextAction.triggered.connect(lambda: self.addlayer(name="New Text Layer",type="text"))
        self.add_menu_ui.addAction(self.addMenuImageAction)
        self.addMenuImageAction.triggered.connect(lambda: self.addlayer(name="New Image Layer",type="image"))

        self.ui.addButton.setMenu(self.add_menu_ui)
        self.ui.addButton.setEnabled(True)

        self.ui.openFile.clicked.connect(self.openFile)
        self.ui.treeWidget.currentItemChanged.connect(self.openInInspector)
        self.ui.statesTreeWidget.currentItemChanged.connect(self.openStateInInspector)
        self.ui.tableWidget.itemChanged.connect(self.onInspectorChanged)
        self.ui.tableWidget.verticalHeader().setDefaultSectionSize(self.ui.tableWidget.fontMetrics().height() * 2.5)
        self.ui.filename.mousePressEvent = self.toggleFilenameDisplay
        self.showFullPath = True
        
        self.scene = CheckerboardGraphicsScene()
        # Initialize animation helper now that scene exists
        from ._applyanimation import ApplyAnimation
        self._applyAnimation = ApplyAnimation(self.scene)
        self.applyAnimationsToPreview = self._applyAnimation.applyAnimationsToPreview
        self.applyKeyframeAnimationToItem = self._applyAnimation.applyKeyframeAnimationToItem
        self.applyTransitionAnimationToPreview = self._applyAnimation.applyTransitionAnimationToPreview
        self.applySpringAnimationToItem = self._applyAnimation.applySpringAnimationToItem
        orig_make_item = self.scene.makeItemEditable
        def makeItemEditable(item):
            editable = orig_make_item(item)
            if editable:
                editable.itemChanged.connect(self.onItemMoved)
                editable.editFinished.connect(self.onTransformChanged)
            return editable
        self.scene.makeItemEditable = makeItemEditable
        self.ui.graphicsView.setScene(self.scene)
        
        self.ui.graphicsView.setEditMode(True)

        self.scene.itemSelectedOnCanvas.connect(self.selectLayerInTree)
        
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

    def updateFilenameDisplay(self):
        display_mode = self.config_manager.get_filename_display_mode()
        
        if not hasattr(self, 'cafilepath') or not self.cafilepath:
            self.ui.filename.setText("No File Open")
            font = self.ui.filename.font()
            font.setItalic(True)
            self.ui.filename.setFont(font)
            return

        font = self.ui.filename.font()
        font.setItalic(False)
        self.ui.filename.setFont(font)

        if display_mode == "File Name":
            self.ui.filename.setText(os.path.basename(self.cafilepath))
            self.ui.filename.mousePressEvent = None
        elif display_mode == "File Path":
            self.ui.filename.setText(self.cafilepath)
            self.ui.filename.mousePressEvent = None
        else:
            if getattr(self, 'showFullPath', True):
                self.ui.filename.setText(self.cafilepath)
            else:
                self.ui.filename.setText(os.path.basename(self.cafilepath))
            self.ui.filename.mousePressEvent = self.toggleFilenameDisplay

    def openFile(self):
        self.ui.treeWidget.clear()
        self.ui.statesTreeWidget.clear()
        if sys.platform == "darwin":
            self.cafilepath = QFileDialog.getOpenFileName(
                self, "Select .ca File", "", "Core Animation Files (*.ca)")[0]
        else:
            self.cafilepath = QFileDialog.getExistingDirectory(
                self, "Select .ca File", "", QFileDialog.ShowDirsOnly
            )
        
        if self.cafilepath:
            self.open_ca_file(self.cafilepath)
        
        self.updateFilenameDisplay()

    def open_ca_file(self, path):
        try:
            ca_file = CAFile(path)
            self.cafile = ca_file
            self.cafilepath = path
            self.populateLayersTreeWidget()
            self.populateStatesTreeWidget()
            self.renderPreview(self.cafile.rootlayer)
            self.fitPreviewToView()
            self.isDirty = False
            self.ui.addButton.setEnabled(True)
            self.updateFilenameDisplay()
        except Exception as e:
            self.create_themed_message_box(
                QMessageBox.Critical, 
                "Error", 
                f"Could not open file: {e}"
            ).exec()
            self.markDirty()

    def populateLayersTreeWidget(self):
        if hasattr(self, 'cafile') and self.cafile and self.cafile.rootlayer:
            rootItem = QTreeWidgetItem([self.cafile.rootlayer.name, "Root", self.cafile.rootlayer.id, ""])
            self.ui.treeWidget.addTopLevelItem(rootItem)
            if len(self.cafile.rootlayer._sublayerorder) > 0:
                self.treeWidgetChildren(rootItem, self.cafile.rootlayer)

        self.ui.addButton.setEnabled(hasattr(self, 'cafile') and self.cafile is not None)

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
            if hasattr(self.scene, 'currentEditableItem') and self.scene.currentEditableItem:
                self.scene.currentEditableItem.removeBoundingBox()
                self.scene.currentEditableItem = None
            self.ui.tableWidget.blockSignals(True)
            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget.blockSignals(False)
            self.currentInspectObject = None
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

                if hasattr(self, 'scene') and self.scene:
                    for item_in_scene in self.scene.items():
                        if hasattr(item_in_scene, 'data') and item_in_scene.data(0) == element.id and item_in_scene.data(1) == "Layer":
                            editable_item = self.scene.makeItemEditable(item_in_scene)
                            if editable_item:
                                if hasattr(self.scene, 'currentEditableItem') and self.scene.currentEditableItem and self.scene.currentEditableItem != editable_item:
                                    self.scene.currentEditableItem.removeBoundingBox()
                                editable_item.setupBoundingBox()
                                self.scene.currentEditableItem = editable_item
                            break

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
                    
                    if element.id != self.cafile.rootlayer.id:
                        if not hasattr(element, "scale_factor"):
                            element.scale_factor = 1.0
                        self.add_inspector_row("SCALE", str(element.scale_factor), row_index)
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
                    try:
                        opacity_percent = int(float(element.opacity) * 100)
                        self.add_inspector_row("OPACITY", str(opacity_percent), row_index)
                    except (ValueError, TypeError):
                        self.add_inspector_row("OPACITY", "100", row_index)
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
        
        if key == "SCALE":
            slider_widget = QWidget()
            slider_layout = QHBoxLayout(slider_widget)
            slider_layout.setContentsMargins(2, 2, 2, 2)
            
            scale_slider = QSlider(Qt.Horizontal)
            scale_slider.setMinimum(10)  # 10% scale
            scale_slider.setMaximum(200)  # 200% scale

            current_scale = float(value_str)
            scale_slider.setValue(int(current_scale * 100))
            scale_slider.setTickPosition(QSlider.TicksBelow)
            scale_slider.setTickInterval(10)
            
            scale_label = QLabel(f"{int(current_scale * 100)}%")
            
            def update_scale_label(value):
                scale_label.setText(f"{value}%")
                
            update_timer = QTimer()
            update_timer.setSingleShot(True)
            update_timer.setInterval(50)
                
            def apply_scale(value):
                scale_factor = value / 100.0
                if hasattr(self, 'currentInspectObject') and self.currentInspectObject:
                    layer = self.currentInspectObject
                    if hasattr(layer, 'bounds'):
                        try:
                            layer.scale_factor = scale_factor
                            
                            root_layer = self.cafile.rootlayer
                            root_width = float(root_layer.bounds[2])
                            root_height = float(root_layer.bounds[3])
                            
                            is_text_layer = hasattr(layer, "layer_class") and layer.layer_class == "CATextLayer"
                            
                            if is_text_layer:
                                base_font_size = root_height * 0.05
                                new_font_size = base_font_size * scale_factor
                                
                                if hasattr(layer, "fontSize"):
                                    layer.fontSize = str(int(new_font_size))
                            else:
                                target_height = root_height * scale_factor
                                
                                current_width = float(layer.bounds[2])
                                current_height = float(layer.bounds[3])
                                aspect_ratio = current_width / current_height if current_height > 0 else 1.0

                                target_width = target_height * aspect_ratio

                                layer.bounds[2] = str(target_width)
                                layer.bounds[3] = str(target_height)

                            if not update_timer.isActive():
                                update_timer.timeout.connect(lambda: self.renderPreview(self.cafile.rootlayer))
                                update_timer.start()
                                
                            self.markDirty()
                        except (ValueError, IndexError) as e:
                            print(f"Error applying scale: {e}")
            
            scale_slider.valueChanged.connect(update_scale_label)

            scale_slider.valueChanged.connect(lambda value: apply_scale(value))
            scale_slider.sliderReleased.connect(lambda: self.renderPreview(self.cafile.rootlayer))
            
            slider_layout.addWidget(scale_slider)
            slider_layout.addWidget(scale_label)
            
            self.ui.tableWidget.setCellWidget(row_index, 1, slider_widget)
        elif isinstance(value, bool) or (isinstance(value_str, str) and value_str.lower() in ["yes", "no", "true", "false"]):
            if isinstance(value, bool):
                display_value = "Yes" if value else "No"
            else:
                display_value = value_str.capitalize()
            value_item = QTableWidgetItem(display_value)
            self.ui.tableWidget.setItem(row_index, 1, value_item)
            
        elif isinstance(value, (int, float)) or value_str.replace(".", "", 1).replace("-", "", 1).isdigit():
            value_item = QTableWidgetItem(self.formatFloat(value) if isinstance(value, (float)) else str(value))
            self.ui.tableWidget.setItem(row_index, 1, value_item)
            
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
            self.ui.tableWidget.setItem(row_index, 1, value_item)
                
        elif isinstance(value_str, str) and " " in value_str and all(p.replace(".", "", 1).replace("-", "", 1).isdigit() for p in value_str.split()):
            try:
                parts = value_str.split()
                if len(parts) == 2:
                    value_item = QTableWidgetItem(f"X: {self.formatFloat(float(parts[0]))}, Y: {self.formatFloat(float(parts[1]))}")
                elif len(parts) == 4:
                    if key == "BOUNDS":
                        value_item = QTableWidgetItem(f"W: {self.formatFloat(float(parts[2]))}, H: {self.formatFloat(float(parts[3]))}")
                    else:
                        value_item = QTableWidgetItem(f"X: {self.formatFloat(float(parts[0]))}, Y: {self.formatFloat(float(parts[1]))}, " +
                                                     f"W: {self.formatFloat(float(parts[2]))}, H: {self.formatFloat(float(parts[3]))}")
                elif len(parts) == 6:
                    value_item = QTableWidgetItem(f"[{self.formatFloat(float(parts[0]))} {self.formatFloat(float(parts[1]))} " +
                                                 f"{self.formatFloat(float(parts[2]))} {self.formatFloat(float(parts[3]))} " +
                                                 f"{self.formatFloat(float(parts[4]))} {self.formatFloat(float(parts[5]))}]")
                else:
                    value_item = QTableWidgetItem(self.formatPoint(value_str))
                self.ui.tableWidget.setItem(row_index, 1, value_item)
            except:
                value_item = QTableWidgetItem(value_str)
                self.ui.tableWidget.setItem(row_index, 1, value_item)
                
        else:
            value_item = QTableWidgetItem(value_str)
            self.ui.tableWidget.setItem(row_index, 1, value_item)
    
    # preview section
    def renderPreview(self, root_layer, target_state=None):
        anims = self.preview.render_preview(root_layer, target_state)
        self.animations = anims
        return anims

    def renderLayer(self, layer, parent_pos, parent_transform, base_state=None, target_state=None):
        return self.preview.render_layer(layer, parent_pos, parent_transform, base_state, target_state)
    
    def applyDefaultAnimationsToLayer(self, layer, item):
        return self.preview.apply_default_animations(layer, item)
    
    def highlightLayerInPreview(self, layer):
        return self.preview.highlight_layer(layer)
    
    def highlightAnimationInPreview(self, layer, animation):
        return self.preview.highlight_animation(layer, animation)

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

        delete_layer_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_layer_shortcut.activated.connect(self.delete_selected_layer)
        self.shortcuts_list.append(delete_layer_shortcut)

    # settings section
    def showSettingsDialog(self):
        if hasattr(self, 'config_manager'):
            settings_dialog = SettingsDialog(self, self.config_manager)
            settings_dialog.exec()
            self.setupShortcuts()

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
            msg = self.create_themed_message_box(
                QMessageBox.Question, 
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to discard them and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            pix = QPixmap(":/assets/openposter.png")
            msg.setIconPixmap(pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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

        if hasattr(self, 'newfile_name') and self.newfile_name:
            docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            if not docs:
                docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
            initial_path = os.path.join(docs, f"{self.newfile_name}.ca")
        else:
            initial_path = self.cafilepath if hasattr(self, 'cafilepath') and self.cafilepath else QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            if not initial_path:
                initial_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)

        path, _ = QFileDialog.getSaveFileName(self, "Save As...", initial_path, "Core Animation Bundle (*.ca)")
        
        if not path:
            return False # User cancelled
            
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
        if not hasattr(self, 'cafile') or not self.cafile:
            self.create_themed_message_box(
                QMessageBox.Warning,
                "No File Open", 
                "Please open a file before exporting."
            ).exec()
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
        if not layer_id: return
        layer = self.cafile.rootlayer.findlayer(layer_id)
        if layer:
            pos = item.pos()
            
            scene_rect = item.sceneBoundingRect()
            w = scene_rect.width()
            h = scene_rect.height()
            
            x0, y0 = (float(b) for b in layer.bounds[:2])
            
            layer.bounds = [str(x0), str(y0), str(w), str(h)]

            layer.position = [str(pos.x()), str(pos.y())]

            m11 = item.transform().m11()
            m12 = item.transform().m12()
            m21 = item.transform().m21()
            m22 = item.transform().m22()
            dx = item.transform().dx()
            dy = item.transform().dy()
            layer.transform = f"{m11} {m12} {m21} {m22} {dx} {dy}"

        if hasattr(self, 'currentInspectObject') and self.currentInspectObject == layer:
            self.ui.tableWidget.blockSignals(True)
            for r in range(self.ui.tableWidget.rowCount()):
                label = self.ui.tableWidget.item(r, 0)
                if not label:
                    continue
                key = label.text()
                if key == 'POSITION':
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(' '.join(layer.position)))
                elif key == 'BOUNDS':
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(' '.join(layer.bounds)))
                elif key == 'TRANSFORM' and layer.transform:
                    self.ui.tableWidget.item(r, 1).setText(self.formatPoint(layer.transform))
            self.ui.tableWidget.blockSignals(False)
        self.markDirty()

    def onTransformChanged(self, item):
        self.markDirty()

    def onInspectorChanged(self, item):
        if not self.currentInspectObject or not self.ui.tableWidget.isEnabled():
            return

        row = item.row()
        key_item = self.ui.tableWidget.item(row, 0)
        if not key_item:
            return

        key = key_item.text()
        value = item.text()

        if hasattr(self, 'currentInspectObject') and self.currentInspectObject:
            if self.currentInspectObject.__class__.__name__ == "CALayer":
                if key == 'NAME':
                    self.currentInspectObject.name = value
                    # Update tree widget
                    selected_item = self.ui.treeWidget.currentItem()
                    if selected_item:
                        selected_item.setText(0, value)
                elif key == 'POSITION':
                    self.currentInspectObject.position = value.split(" ")
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'BOUNDS':
                    self.currentInspectObject.bounds = value.split(" ")
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'ANCHOR POINT':
                    self.currentInspectObject.anchorPoint = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'Z-POSITION':
                    self.currentInspectObject.zPosition = value
                elif key == 'OPACITY':
                    try:
                        clean_value = item.text().strip().replace('%', '')
                        if not clean_value:
                            return

                        percent_val = float(clean_value)
                        backend_val = max(0.0, min(100.0, percent_val)) / 100.0
                        
                        self.currentInspectObject.opacity = f"{backend_val:.2f}"
                        
                        self.ui.tableWidget.blockSignals(True)
                        item.setText(str(int(backend_val * 100)))
                        self.ui.tableWidget.blockSignals(False)
                        
                        self.renderPreview(self.cafile.rootlayer)
                    except ValueError:
                        pass
                elif key == 'BACKGROUND COLOR':
                    color = QColorDialog.getColor(self.parseColor(item.text()), self, "Select Color")
                    if color.isValid():
                        color_str = f"{color.redF()} {color.greenF()} {color.blueF()} {color.alphaF()}"
                        self.currentInspectObject.backgroundColor = color_str
                        item.setText(self.formatColor(color_str))
                        self.renderPreview(self.cafile.rootlayer)
                elif key == 'CORNER RADIUS':
                    self.currentInspectObject.cornerRadius = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'STRING':
                    self.currentInspectObject.string = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'FONT SIZE':
                    self.currentInspectObject.fontSize = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'FONT FAMILY':
                    self.currentInspectObject.fontFamily = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'ALIGNMENT MODE':
                    self.currentInspectObject.alignmentMode = value
                    self.renderPreview(self.cafile.rootlayer)
                elif key == 'COLOR':
                    self.currentInspectObject.color = value
                    self.renderPreview(self.cafile.rootlayer)
                
            self.markDirty()

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
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            focused_widget = QApplication.focusWidget()
            if not isinstance(focused_widget, (QLineEdit, QTextEdit)):
                self.delete_selected_layer()
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
        
    def selectLayerInTree(self, layer_id: str):
        if not hasattr(self, 'ui') or not self.ui.treeWidget:
            return
        
        iterator = QTreeWidgetItemIterator(self.ui.treeWidget)
        while iterator.value():
            item = iterator.value()
            if item and item.text(2) == layer_id:
                self.ui.treeWidget.setCurrentItem(item)
                self.openInInspector(item, None)
                return
            iterator += 1

    def _run_nugget_export(self, program, args):
        process = QtCore.QProcess(self)
        process.setProgram(program)
        process.setArguments(args)
        process.finished.connect(self._on_nugget_finished)
        process.errorOccurred.connect(lambda error: QMessageBox.critical(self, "Nugget Error", f"Nugget execution error: {error}"))
        process.start()

        process.errorOccurred.connect(lambda error: QMessageBox.critical(self, "Nugget Error", f"Nugget execution error: {error}"))
        process.start()

    def create_themed_message_box(self, icon, title, text, buttons=QMessageBox.Ok, parent=None):
        msg_box = QMessageBox(icon, title, text, buttons, parent or self)
        
        if hasattr(self, '_current_qss'):
            msg_box.setStyleSheet(self._current_qss)
            
        return msg_box

    def delete_selected_layer(self):
        selected_items = self.ui.treeWidget.selectedItems()
        if not selected_items:
            return

        selected_item = selected_items[0]
        layer_id = selected_item.text(2)

        if not layer_id or not hasattr(self, 'cafile') or not self.cafile:
            return

        if layer_id == self.cafile.rootlayer.id:
            return

        reply = QMessageBox.question(self, 'Delete Layer',
                                     f"Are you sure you want to delete the layer '{selected_item.text(0)}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.cafile.rootlayer.removelayer(layer_id):
                (selected_item.parent() or self.ui.treeWidget.invisibleRootItem()).removeChild(selected_item)

                if hasattr(self, 'currentInspectObject') and self.currentInspectObject and self.currentInspectObject.id == layer_id:
                    self.ui.tableWidget.setRowCount(0)
                    self.currentInspectObject = None
                
                self.renderPreview(self.cafile.rootlayer)
                self.markDirty()