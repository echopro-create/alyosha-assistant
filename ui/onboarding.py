"""
Alyosha Onboarding 2026
Modern graphical welcome tour
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation
from PyQt6.QtGui import QColor, QPalette

from .styles import COLORS, get_font_family
from .icons import IconFactory

class OnboardingSlide(QWidget):
    def __init__(self, title, description, icon_name=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Icon
        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Large icon
            pix = IconFactory.get_pixmap(icon_name, COLORS["dark"]["accent"], 80)
            icon_lbl.setPixmap(pix)
            layout.addWidget(icon_lbl)
            
        # Title
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"""
            color: {COLORS['dark']['text_primary']};
            font-size: 24px;
            font-weight: 700;
            font-family: {get_font_family()};
        """)
        layout.addWidget(title_lbl)
        
        # Desc
        desc_lbl = QLabel(description)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setFixedWidth(300)
        desc_lbl.setStyleSheet(f"""
            color: {COLORS['dark']['text_secondary']};
            font-size: 15px;
            line-height: 1.5;
            font-family: {get_font_family()};
        """)
        layout.addWidget(desc_lbl)

class OnboardingOverlay(QWidget):
    """Full window overlay for onboarding"""
    
    finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Background
        self.setAutoFillBackground(True)
        pal = self.palette()
        c = QColor(COLORS["dark"]["bg_primary"])
        c.setAlpha(245) # Almost opaque
        pal.setColor(QPalette.ColorRole.Window, c)
        self.setPalette(pal)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 60, 40, 40)
        
        # Slides
        self.stack = QStackedWidget()
        
        # Slide 1: Welcome
        self.stack.addWidget(OnboardingSlide(
            "Привет, я Алёша",
            "Твой новый голосовой ассистент.\nУмный, дерзкий и полезный.",
            "user" # Placeholder for logo
        ))
        
        # Slide 2: Features
        self.stack.addWidget(OnboardingSlide(
            "Полный контроль",
            "Управляй системой, запускай приложения и ищи информацию голосом.",
            "cpu"
        ))
        
        # Slide 3: Privacy
        self.stack.addWidget(OnboardingSlide(
            "Приватно и безопасно",
            "Твои данные остаются с тобой. Настрой API ключи для максимальной точности.",
            "check"
        ))
        
        layout.addWidget(self.stack, stretch=1)
        
        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(20)
        
        # Indicators
        self.indicators = []
        ind_container = QHBoxLayout()
        ind_container.setSpacing(8)
        for i in range(3):
            ind = QLabel()
            ind.setFixedSize(8, 8)
            ind.setStyleSheet(self._get_indicator_style(i == 0))
            ind_container.addWidget(ind)
            self.indicators.append(ind)
        
        controls.addLayout(ind_container)
        controls.addStretch()
        
        self.next_btn = QPushButton("Далее")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['dark']['accent_dark']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 30px;
                font-weight: 600;
                font-size: 15px;
                font-family: {get_font_family()};
            }}
            QPushButton:hover {{ background: {COLORS['dark']['accent']}; }}
        """)
        self.next_btn.clicked.connect(self._next_slide)
        controls.addWidget(self.next_btn)
        
        layout.addLayout(controls)
        
        self.current_idx = 0
    
    def _get_indicator_style(self, active):
        color = COLORS['dark']['accent'] if active else COLORS['dark']['bg_tertiary']
        return f"background: {color}; border-radius: 4px;"
        
    def _next_slide(self):
        if self.current_idx < 2:
            self.current_idx += 1
            self.stack.setCurrentIndex(self.current_idx)
            
            # Update indicators
            for i, ind in enumerate(self.indicators):
                ind.setStyleSheet(self._get_indicator_style(i == self.current_idx))
                
            if self.current_idx == 2:
                self.next_btn.setText("Начать")
        else:
            self._finish()
            
    def _finish(self):
        # Fade out animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._close_overlay)
        self.anim.start()
        
    def _close_overlay(self):
        self.close()
        self.finished.emit()
        self.deleteLater()
