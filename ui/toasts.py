"""
Alyosha Toast Notifications 2026
Premium in-app notifications
"""
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

from .styles import COLORS, get_font_family
from .icons import IconFactory

class ToastNotification(QWidget):
    """Floating toast notification"""
    
    def __init__(self, text, icon_name="info", type="info", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Colors
        c = COLORS["dark"]
        if type == "error":
            bg = c["error_glow"]
            border = c["error"]
            text_col = c["error"]
        elif type == "success":
            bg = c["success_glow"]
            border = c["success"]
            text_col = c["success"]
        else:
            bg = c["bg_tertiary"]
            border = c["accent"]
            text_col = c["text_primary"]
            
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(IconFactory.get_pixmap(icon_name, text_col, 20))
        layout.addWidget(icon_lbl)
        
        # Text
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"""
            color: {text_col};
            font-size: 14px;
            font-weight: 500;
            font-family: {get_font_family()};
        """)
        layout.addWidget(text_lbl)
        
        # Style
        self.setStyleSheet(f"""
            ToastNotification {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 24px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Animations
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        
        self.anim_in = QPropertyAnimation(self.opacity, b"opacity")
        self.anim_in.setDuration(300)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.anim_out = QPropertyAnimation(self.opacity, b"opacity")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(self.close)
        
        # Life timer
        QTimer.singleShot(3000, self.anim_out.start)
        
    def show_toast(self):
        self.show()
        self.anim_in.start()

class ToastManager:
    """Manages toast positioning"""
    def __init__(self, parent_widget):
        self.parent = parent_widget
        
    def show(self, text, icon="info", type="info"):
        toast = ToastNotification(text, icon, type, self.parent)
        toast.adjustSize()
        
        # Position at bottom center, above input
        p_rect = self.parent.rect()
        x = (p_rect.width() - toast.width()) // 2
        y = p_rect.height() - 100 # Above input
        
        toast.move(x, y)
        toast.show_toast()
