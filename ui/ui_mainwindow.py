# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget)

from gui.custom_widgets import CustomGraphicsView

class Ui_OpenPoster(object):
    def setupUi(self, OpenPoster):
        if not OpenPoster.objectName():
            OpenPoster.setObjectName(u"OpenPoster")
        OpenPoster.resize(1280, 800)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OpenPoster.sizePolicy().hasHeightForWidth())
        OpenPoster.setSizePolicy(sizePolicy)
        OpenPoster.setMinimumSize(QSize(1280, 800))
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        brush1 = QBrush(QColor(0, 0, 0, 0))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush1)
        brush2 = QBrush(QColor(255, 255, 255, 128))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush2)
#endif
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush2)
#endif
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush2)
#endif
        OpenPoster.setPalette(palette)
        OpenPoster.setWindowTitle(u"OpenPoster")
        OpenPoster.setStyleSheet(u"QWidget {\n"
"    color: palette(text);\n"
"    background-color: transparent;\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QWidget:focus {\n"
"    outline: none;\n"
"}\n"
"\n"
"QWidget [cls=central] {\n"
"    background-color: palette(base);\n"
"	border-radius: 0px;\n"
"	border: 1px solid palette(mid);\n"
"}\n"
"\n"
"QLabel {\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"QToolButton {\n"
"    background-color: palette(button);\n"
"    border: none;\n"
"    color: palette(text);\n"
"    font-size: 14px;\n"
"	min-height: 35px;\n"
"	icon-size: 16px;\n"
"	padding-left: 10px;\n"
"	padding-right: 10px;\n"
"	border-radius: 8px;\n"
"}\n"
"\n"
"QToolButton[cls=sidebarBtn] {\n"
"    background-color: transparent;\n"
"	icon-size: 24px;\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: palette(dark);\n"
"    color: palette(text);\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    background-color: palette(highlight);\n"
"    color: palette(highlighted-text);\n"
"}\n"
"\n"
"QCheckBox {\n"
"	spacing: 8px;\n"
"	font-size: 14px;\n"
"}"
                        "\n"
"\n"
"QRadioButton {\n"
"	spacing: 8px;\n"
"	font-size: 14px;\n"
"}\n"
"\n"
"QLineEdit {\n"
"	border: none;\n"
"	background-color: transparent;\n"
"	color: palette(text);\n"
"	font-size: 14px;\n"
"}\n"
"\n"
"QScrollBar:vertical {\n"
"    background: transparent;\n"
"    width: 8px;\n"
"}\n"
"\n"
"QScrollBar:horizontal {\n"
"    background: transparent;\n"
"    height: 8px;\n"
"}\n"
"\n"
"QScrollBar::handle {\n"
"    background: palette(mid);\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QScrollBar::handle:pressed {\n"
"    background: palette(dark);\n"
"}\n"
"\n"
"QScrollBar::add-line,\n"
"QScrollBar::sub-line {\n"
"    background: none;\n"
"}\n"
"\n"
"QScrollBar::add-page,\n"
"QScrollBar::sub-page {\n"
"    background: none;\n"
"}\n"
"\n"
"QSlider::groove:horizontal {\n"
"    background-color: palette(mid);\n"
"    height: 4px;\n"
"	border-radius: 2px;\n"
"}\n"
"\n"
"QSlider::handle:horizontal {\n"
"    background-color: palette(dark);\n"
"    width: 8px;\n"
"    margin: -8px 0;\n"
"    border-radius: 4px;\n"
""
                        "}\n"
"\n"
"QSlider::handle:horizontal:pressed {\n"
"    background-color: palette(highlight);\n"
"}\n"
"\n"
"QSlider::tick:horizontal {\n"
"    background-color: palette(dark);\n"
"    width: 1px;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: palette(button);\n"
"    color: palette(text);\n"
"    padding: 8px;\n"
"    border: none;\n"
"    border-right: 1px solid rgba(120, 120, 120, 60);\n"
"    border-bottom: none;\n"
"    height: 30px;\n"
"}\n"
"\n"
"QTableView, QTreeView {\n"
"    border: none;\n"
"    selection-background-color: palette(highlight);\n"
"    selection-color: palette(highlighted-text);\n"
"}\n"
"\n"
"QTreeView::item {\n"
"    min-height: 30px;\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QPushButton, QLabel[clickable=\"true\"] {\n"
"    border-radius: 6px;\n"
"    padding: 5px 10px;\n"
"}\n"
"\n"
"QLabel[objectName=\"previewLabel\"] {\n"
"    font-size: 14px; \n"
"    padding: 5px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"editButton\"] {\n"
"    border: none; \n"
"    background-colo"
                        "r: transparent;\n"
"}\n"
"\n"
"QPushButton[objectName=\"editButton\"]:hover {\n"
"    background-color: rgba(128, 128, 128, 30);\n"
"    border-radius: 20px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"editButton\"]:checked {\n"
"    background-color: rgba(0, 120, 215, 50);\n"
"    border-radius: 20px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"playButton\"] {\n"
"    border: none; \n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QPushButton[objectName=\"playButton\"]:hover {\n"
"    background-color: rgba(128, 128, 128, 50);\n"
"    border-radius: 20px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"settingsButton\"] {\n"
"    border: none; \n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QPushButton[objectName=\"settingsButton\"]:hover {\n"
"    background-color: rgba(128, 128, 128, 30);\n"
"    border-radius: 20px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"exportButton\"] {\n"
"    border: 1px solid gray;\n"
"    border-radius: 8px;\n"
"    padding: 5px 10px;\n"
"}\n"
"\n"
"QPushButton[objectName=\"exportButton"
                        "\"]:hover {\n"
"    background-color: rgba(128, 128, 128, 30);\n"
"}\n"
"\n"
"QTableWidget {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"    gridline-color: transparent;\n"
"}\n"
"\n"
"QTableWidget::item { \n"
"    padding: 8px;\n"
"    min-height: 30px;\n"
"}\n"
"\n"
"QTableWidget::item:first-column {\n"
"    border-right: 1px solid rgba(120, 120, 120, 60);\n"
"}\n"
"")
        self.centralwidget = QWidget(OpenPoster)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerWidget = QWidget(self.centralwidget)
        self.headerWidget.setObjectName(u"headerWidget")
        self.headerWidget.setMaximumSize(QSize(16777215, 40))
        self.horizontalLayout_header = QHBoxLayout(self.headerWidget)
        self.horizontalLayout_header.setObjectName(u"horizontalLayout_header")
        self.horizontalLayout_header.setContentsMargins(5, 5, 5, 5)
        self.filename = QLabel(self.headerWidget)
        self.filename.setObjectName(u"filename")
        self.filename.setMinimumSize(QSize(200, 28))
        self.filename.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.filename.setStyleSheet(u"border: 1.5px solid palette(highlight); border-radius: 8px; padding: 3px 8px; color: #666666; font-style: italic;")
        self.filename.setProperty(u"fixedHeight", 30)

        self.horizontalLayout_header.addWidget(self.filename)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_header.addItem(self.horizontalSpacer)

        self.exportButton = QPushButton(self.headerWidget)
        self.exportButton.setObjectName(u"exportButton")
        self.exportButton.setIconSize(QSize(18, 18))
        self.exportButton.setProperty(u"fixedHeight", 30)

        self.horizontalLayout_header.addWidget(self.exportButton)

        self.settingsButton = QPushButton(self.headerWidget)
        self.settingsButton.setObjectName(u"settingsButton")
        self.settingsButton.setIconSize(QSize(18, 18))
        self.settingsButton.setProperty(u"fixedSize", QSize(30, 30))

        self.horizontalLayout_header.addWidget(self.settingsButton)


        self.verticalLayout.addWidget(self.headerWidget)

        self.mainSplitter = QSplitter(self.centralwidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.layersWidget = QWidget(self.mainSplitter)
        self.layersWidget.setObjectName(u"layersWidget")
        self.layersWidget.setMinimumSize(QSize(250, 0))
        self.layersWidget.setStyleSheet(u"border: 1px solid #4B4B4B; border-radius: 4px; padding: 4px;")
        self.layersLayout = QVBoxLayout(self.layersWidget)
        self.layersLayout.setSpacing(0)
        self.layersLayout.setObjectName(u"layersLayout")
        self.layersLayout.setContentsMargins(0, 0, 0, 0)
        self.layersSplitter = QSplitter(self.layersWidget)
        self.layersSplitter.setObjectName(u"layersSplitter")
        self.layersSplitter.setOrientation(Qt.Orientation.Vertical)
        self.layersSection = QWidget(self.layersSplitter)
        self.layersSection.setObjectName(u"layersSection")
        self.layersSectionLayout = QVBoxLayout(self.layersSection)
        self.layersSectionLayout.setObjectName(u"layersSectionLayout")
        self.layersHeaderLayout = QHBoxLayout()
        self.layersHeaderLayout.setObjectName(u"layersHeaderLayout")
        self.layersLabel = QLabel(self.layersSection)
        self.layersLabel.setObjectName(u"layersLabel")

        self.layersHeaderLayout.addWidget(self.layersLabel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layersHeaderLayout.addItem(self.horizontalSpacer_2)

        self.addButton = QPushButton(self.layersSection)
        self.addButton.setObjectName(u"addButton")
        self.addButton.setEnabled(False)
        self.addButton.setMouseTracking(True)
        self.addButton.setIconSize(QSize(24, 24))

        self.layersHeaderLayout.addWidget(self.addButton)


        self.layersSectionLayout.addLayout(self.layersHeaderLayout)

        self.treeWidget = QTreeWidget(self.layersSection)
        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.treeWidget.setIconSize(QSize(24, 24))
        self.treeWidget.setIndentation(20)
        self.treeWidget.setUniformRowHeights(True)
        self.treeWidget.setColumnCount(3)
        self.treeWidget.header().setVisible(True)
        self.treeWidget.header().setMinimumSectionSize(100)
        self.treeWidget.header().setDefaultSectionSize(200)
        self.treeWidget.header().setHighlightSections(True)
        self.treeWidget.header().setStretchLastSection(True)

        self.layersSectionLayout.addWidget(self.treeWidget)

        self.layersSplitter.addWidget(self.layersSection)
        self.statesSection = QWidget(self.layersSplitter)
        self.statesSection.setObjectName(u"statesSection")
        self.statesSectionLayout = QVBoxLayout(self.statesSection)
        self.statesSectionLayout.setObjectName(u"statesSectionLayout")
        self.statesLabel = QLabel(self.statesSection)
        self.statesLabel.setObjectName(u"statesLabel")

        self.statesSectionLayout.addWidget(self.statesLabel)

        self.statesTreeWidget = QTreeWidget(self.statesSection)
        self.statesTreeWidget.setObjectName(u"statesTreeWidget")
        self.statesTreeWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.statesTreeWidget.setIconSize(QSize(24, 24))
        self.statesTreeWidget.setIndentation(20)
        self.statesTreeWidget.setUniformRowHeights(True)
        self.statesTreeWidget.setColumnCount(3)
        self.statesTreeWidget.header().setVisible(True)
        self.statesTreeWidget.header().setMinimumSectionSize(100)
        self.statesTreeWidget.header().setDefaultSectionSize(200)
        self.statesTreeWidget.header().setHighlightSections(True)
        self.statesTreeWidget.header().setStretchLastSection(True)

        self.statesSectionLayout.addWidget(self.statesTreeWidget)

        self.layersSplitter.addWidget(self.statesSection)

        self.layersLayout.addWidget(self.layersSplitter)

        self.mainSplitter.addWidget(self.layersWidget)
        self.previewWidget = QWidget(self.mainSplitter)
        self.previewWidget.setObjectName(u"previewWidget")
        self.previewWidget.setMinimumSize(QSize(400, 0))
        self.previewWidget.setStyleSheet(u"border: 1px solid #4B4B4B; border-radius: 4px; padding: 4px;")
        self.previewLayout = QVBoxLayout(self.previewWidget)
        self.previewLayout.setObjectName(u"previewLayout")
        self.previewHeaderLayout_ui = QHBoxLayout()
        self.previewHeaderLayout_ui.setObjectName(u"previewHeaderLayout_ui")
        self.previewLabel = QLabel(self.previewWidget)
        self.previewLabel.setObjectName(u"previewLabel")

        self.previewHeaderLayout_ui.addWidget(self.previewLabel)

        self.previewHeaderSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.previewHeaderLayout_ui.addItem(self.previewHeaderSpacer)

        self.editButton = QPushButton(self.previewWidget)
        self.editButton.setObjectName(u"editButton")
        self.editButton.setIconSize(QSize(24, 24))
        self.editButton.setCheckable(True)
        self.editButton.setProperty(u"fixedSize", QSize(40, 40))

        self.previewHeaderLayout_ui.addWidget(self.editButton)

        self.playButton = QPushButton(self.previewWidget)
        self.playButton.setObjectName(u"playButton")
        self.playButton.setIconSize(QSize(32, 32))
        self.playButton.setProperty(u"fixedSize", QSize(40, 40))

        self.previewHeaderLayout_ui.addWidget(self.playButton)


        self.previewLayout.addLayout(self.previewHeaderLayout_ui)

        self.graphicsView = CustomGraphicsView(self.previewWidget)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.OpenHandCursor))
        self.graphicsView.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.graphicsView.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.graphicsView.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.graphicsView.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.previewLayout.addWidget(self.graphicsView)

        self.mainSplitter.addWidget(self.previewWidget)
        self.inspectorWidget = QWidget(self.mainSplitter)
        self.inspectorWidget.setObjectName(u"inspectorWidget")
        self.inspectorWidget.setMinimumSize(QSize(250, 0))
        self.inspectorWidget.setStyleSheet(u"border: 1px solid #4B4B4B; border-radius: 4px; padding: 4px;")
        self.inspectorLayout = QVBoxLayout(self.inspectorWidget)
        self.inspectorLayout.setObjectName(u"inspectorLayout")
        self.inspectorLabel = QLabel(self.inspectorWidget)
        self.inspectorLabel.setObjectName(u"inspectorLabel")

        self.inspectorLayout.addWidget(self.inspectorLabel)

        self.tableWidget = QTableWidget(self.inspectorWidget)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setFrameShape(QFrame.Shape.NoFrame)
        self.tableWidget.setFrameShadow(QFrame.Shadow.Plain)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(100)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(120)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setMinimumSectionSize(25)
        self.tableWidget.verticalHeader().setDefaultSectionSize(30)

        self.inspectorLayout.addWidget(self.tableWidget)

        self.mainSplitter.addWidget(self.inspectorWidget)

        self.verticalLayout.addWidget(self.mainSplitter)

        OpenPoster.setCentralWidget(self.centralwidget)

        self.retranslateUi(OpenPoster)

        QMetaObject.connectSlotsByName(OpenPoster)
    # setupUi

    def retranslateUi(self, OpenPoster):
        self.filename.setText(QCoreApplication.translate("OpenPoster", u"No File Open", None))
#if QT_CONFIG(tooltip)
        self.exportButton.setToolTip(QCoreApplication.translate("OpenPoster", u"Export", None))
#endif // QT_CONFIG(tooltip)
        self.exportButton.setText(QCoreApplication.translate("OpenPoster", u"Export", None))
#if QT_CONFIG(tooltip)
        self.settingsButton.setToolTip(QCoreApplication.translate("OpenPoster", u"Settings", None))
#endif // QT_CONFIG(tooltip)
        self.layersLabel.setText(QCoreApplication.translate("OpenPoster", u"Layers", None))
#if QT_CONFIG(tooltip)
        self.addButton.setToolTip(QCoreApplication.translate("OpenPoster", u"Add a new layer", None))
#endif // QT_CONFIG(tooltip)
        ___qtreewidgetitem = self.treeWidget.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("OpenPoster", u"ID", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("OpenPoster", u"Type", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("OpenPoster", u"Name", None));
        self.statesLabel.setText(QCoreApplication.translate("OpenPoster", u"States", None))
        ___qtreewidgetitem1 = self.statesTreeWidget.headerItem()
        ___qtreewidgetitem1.setText(2, QCoreApplication.translate("OpenPoster", u"Value", None));
        ___qtreewidgetitem1.setText(1, QCoreApplication.translate("OpenPoster", u"Type", None));
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("OpenPoster", u"Name", None));
        self.previewLabel.setStyleSheet(QCoreApplication.translate("OpenPoster", u"font-size: 14px; padding: 5px;", None))
        self.previewLabel.setText(QCoreApplication.translate("OpenPoster", u"Preview", None))
#if QT_CONFIG(tooltip)
        self.editButton.setToolTip(QCoreApplication.translate("OpenPoster", u"Toggle Edit Mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.playButton.setToolTip(QCoreApplication.translate("OpenPoster", u"Play/Pause Animations", None))
#endif // QT_CONFIG(tooltip)
        self.inspectorLabel.setText(QCoreApplication.translate("OpenPoster", u"Inspector", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("OpenPoster", u"Key", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("OpenPoster", u"Value", None));
        pass
    # retranslateUi

