"""
Alyosha Keyboard Shortcuts Overlay
Визуальный оверлей с горячими клавишами при первом запуске
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from .styles import COLORS


class KeyboardShortcutsOverlay(QFrame):
    """Оверлей с горячими клавишами"""
    
    dismissed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("shortcutsOverlay")
        self.setStyleSheet(f"""
            QFrame#shortcutsOverlay {{
                background: rgba(0, 0, 0, 0.85);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("⌨️ Горячие клавиши")
        title.setStyleSheet(f"""
            color: {COLORS['dark']['text_primary']};
            font-size: 18px;
            font-weight: 700;
            font-family: 'Montserrat', 'Outfit', sans-serif;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Shortcuts list
        shortcuts = [
            ("Ctrl+Shift+Space", "Показать/Скрыть окно"),
            ("Ctrl+L", "Фокус на ввод"),
            ("Enter", "Отправить сообщение"),
            ("🎤 Удерживать", "Голосовой ввод"),
            ("«Алёша»", "Wake word активация"),
        ]
        
        for key, desc in shortcuts:
            row = QHBoxLayout()
            row.setSpacing(16)
            
            key_label = QLabel(key)
            key_label.setStyleSheet(f"""
                background: rgba(255, 255, 255, 0.1);
                color: {COLORS['dark']['accent']};
                font-size: 12px;
                font-weight: 600;
                font-family: 'SF Mono', 'JetBrains Mono', monospace;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            """)
            key_label.setFixedWidth(140)
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"""
                color: {COLORS['dark']['text_secondary']};
                font-size: 13px;
                font-family: 'Ubuntu', sans-serif;
            """)
            
            row.addWidget(key_label)
            row.addWidget(desc_label)
            row.addStretch()
            
            layout.addLayout(row)
        
        # Dismiss button
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        
        self.dismiss_btn = QPushButton("Понятно!")
        self.dismiss_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['dark']['accent']};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['dark']['accent_light']};
            }}
        """)
        self.dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dismiss_btn.clicked.connect(self._dismiss)
        btn_container.addWidget(self.dismiss_btn)
        
        btn_container.addStretch()
        layout.addLayout(btn_container)
        
        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        QTimer.singleShot(100, self._animate_in)
    
    def _animate_in(self):
        """Анимация появления"""
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
    
    def _dismiss(self):
        """Закрыть оверлей"""
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(lambda: (self.dismissed.emit(), self.deleteLater()))
        self.anim.start()
