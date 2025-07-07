from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve, QParallelAnimationGroup

class WelcomeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setFixedSize(550, 400)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Top: icon and title
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 20, 0, 0)
        
        self.icon_label = QLabel()
        icon = QIcon(":/assets/openposter.png")
        pixmap = icon.pixmap(QSize(128, 128))
        self.icon_label.setPixmap(pixmap)

        self.title_label = QLabel("Welcome to OpenPoster")
        title_font = self.title_label.font()
        title_font.setPointSize(30)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.version_label = QLabel("Version: v0.0.4 Beta 1") 
        version_font = self.version_label.font()
        version_font.setPointSize(12)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("color: #666666;")
        
        top_layout.addWidget(self.icon_label, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.title_label, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.version_label, alignment=Qt.AlignHCenter)
        top_widget.setLayout(top_layout)
        layout.addWidget(top_widget, stretch=3)

        # Bottom: buttons
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(10)

        self.btn_new = QPushButton("Create New .ca File")
        self.btn_open = QPushButton("Open .ca File")
        self.btn_new.setFixedSize(460, 50)
        self.btn_open.setFixedSize(460, 50)
        
        self.btn_new.setStyleSheet("font-size: 15px; border-radius: 25px;")
        self.btn_open.setStyleSheet("font-size: 15px; border-radius: 25px;")

        bottom_layout.addWidget(self.btn_new)
        bottom_layout.addWidget(self.btn_open)
        bottom_widget.setLayout(bottom_layout)
        layout.addWidget(bottom_widget, stretch=2)

        self.setLayout(layout)

        self.btn_new.clicked.connect(self.on_new)
        self.btn_open.clicked.connect(self.on_open)
        self.result = None

        self.setup_animations()

    def setup_animations(self):
        welcome_widgets = [self.icon_label, self.title_label, self.version_label]
        button_widgets = [self.btn_new, self.btn_open]

        self.welcome_effects = [QGraphicsOpacityEffect(w) for w in welcome_widgets]
        self.button_effects = [QGraphicsOpacityEffect(w) for w in button_widgets]

        for i, w in enumerate(welcome_widgets):
            w.setGraphicsEffect(self.welcome_effects[i])
            self.welcome_effects[i].setOpacity(0.0)

        for i, w in enumerate(button_widgets):
            w.setGraphicsEffect(self.button_effects[i])
            self.button_effects[i].setOpacity(0.0)

        self.main_animation_group = QSequentialAnimationGroup(self)

        welcome_anim_group = QParallelAnimationGroup()
        for effect in self.welcome_effects:
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(800)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            welcome_anim_group.addAnimation(anim)

        buttons_anim_group = QParallelAnimationGroup()
        for effect in self.button_effects:
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(600)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            buttons_anim_group.addAnimation(anim)

        self.main_animation_group.addAnimation(welcome_anim_group)
        self.main_animation_group.addPause(150)
        self.main_animation_group.addAnimation(buttons_anim_group)

    def showEvent(self, event):
        super().showEvent(event)
        self.main_animation_group.start()

    def on_new(self):
        self.result = ("new", None)
        self.accept()

    def on_open(self):
        self.result = ("open", None)
        self.accept()