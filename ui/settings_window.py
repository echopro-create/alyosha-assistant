"""
Alyosha Settings Window 2026
Premium configuration interface
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QComboBox,
    QScrollArea, QDialog, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .styles import COLORS, get_font_family, get_input_style
from .icons import IconFactory
import config

class ModernInput(QLineEdit):
    def __init__(self, placeholder="", parent=None, is_password=False):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setStyleSheet(get_input_style())

class SettingsSection(QFrame):
    """Section container with title"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 24)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {COLORS['dark']['accent']};
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-family: {get_font_family()};
        """)
        layout.addWidget(title_lbl)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        layout.addWidget(self.content)
        
    def add_widget(self, label_text, widget, help_text=None):
        container = QWidget()
        h_layout = QVBoxLayout(container) # Stacked vertical for mobile-like feel
        h_layout.setSpacing(6)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        if label_text:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"""
                color: {COLORS['dark']['text_secondary']};
                font-size: 13px;
                font-weight: 500;
                font-family: {get_font_family()};
            """)
            h_layout.addWidget(lbl)
            
        h_layout.addWidget(widget)
        
        if help_text:
            help_lbl = QLabel(help_text)
            help_lbl.setWordWrap(True)
            help_lbl.setStyleSheet(f"""
                color: {COLORS['dark']['text_muted']};
                font-size: 11px;
                font-family: {get_font_family()};
                margin-top: -4px;
            """)
            h_layout.addWidget(help_lbl)
            
        self.content_layout.addWidget(container)

class SettingsWindow(QDialog):
    """Modern Frameless Settings Window"""
    
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(500, 650)
        
        # Main layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        
        # Background Frame
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("settingsFrame")
        c = COLORS["dark"]
        self.bg_frame.setStyleSheet(f"""
            QFrame#settingsFrame {{
                background: {c["bg_secondary"]};
                border: 1px solid {c["border"]};
                border-radius: 20px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.bg_frame.setGraphicsEffect(shadow)
        
        outer_layout.addWidget(self.bg_frame)
        
        # Content Layout
        self.layout = QVBoxLayout(self.bg_frame)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setup_header()
        self.setup_content()
        self.setup_footer()
        
        # Load current values
        self.load_settings()
        
        # Drag support
        self.drag_pos = None

    def setup_header(self):
        c = COLORS["dark"]
        header = QFrame()
        header.setStyleSheet(f"""
            border-bottom: 1px solid {c["border"]};
            background: {c["bg_primary"]};
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 20, 24, 20)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(IconFactory.get_pixmap("settings", c["accent"], 24))
        h_layout.addWidget(icon_lbl)
        
        # Title
        title = QLabel("Настройки")
        title.setStyleSheet(f"""
            color: {c["text_primary"]};
            font-size: 18px;
            font-weight: 600;
            font-family: {get_font_family()};
        """)
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        # Close Button
        close_btn = QPushButton()
        close_btn.setIcon(IconFactory.get_icon("x", c["text_muted"], 20))
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent; border: none; border-radius: 16px;")
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)
        
        self.layout.addWidget(header)

    def setup_content(self):
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        # Container
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(30, 30, 30, 30)
        v_layout.setSpacing(10)
        
        # --- API Section ---
        api_sec = SettingsSection("API Ключи (Restart Required)")
        
        self.gemini_key = ModernInput(placeholder="AIza...", is_password=True)
        api_sec.add_widget("Gemini API Key (Google)", self.gemini_key, 
                         "Основной интеллект ассистента. Бесплатно: aistudio.google.com")
        
        self.eleven_key = ModernInput(placeholder="sk_...", is_password=True)
        api_sec.add_widget("ElevenLabs API Key (Optional)", self.eleven_key, 
                         "Для премиального голоса. Если пусто — используется системный голос.")
        
        v_layout.addWidget(api_sec)
        
        # --- Voice Section ---
        voice_sec = SettingsSection("Голос и Аудио")
        
        self.voice_engine = QComboBox()
        self.voice_engine.addItems(["Auto (Smart Choice)", "ElevenLabs (Premium)", "Piper (Offline)"])
        self.voice_engine.setStyleSheet(self._get_combo_style())
        voice_sec.add_widget("Движок синтеза речи", self.voice_engine)
        
        v_layout.addWidget(voice_sec)
        
        v_layout.addStretch()
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def setup_footer(self):
        c = COLORS["dark"]
        footer = QFrame()
        footer.setStyleSheet(f"""
            border-top: 1px solid {c["border"]};
            background: {c["bg_primary"]};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
        """)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(24, 20, 24, 20)
        f_layout.addStretch()
        
        # Cancel
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                color: {c["text_secondary"]};
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
                font-family: {get_font_family()};
            }}
            QPushButton:hover {{ color: {c["text_primary"]}; }}
        """)
        cancel_btn.clicked.connect(self.close)
        f_layout.addWidget(cancel_btn)
        
        # Save
        save_btn = QPushButton("Сохранить")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c["accent_dark"]};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 24px;
                font-family: {get_font_family()};
            }}
            QPushButton:hover {{ background: {c["accent"]}; }}
            QPushButton:pressed {{ background: {c["accent_dark"]}; opacity: 0.8; }}
        """)
        save_btn.clicked.connect(self.save_settings)
        f_layout.addWidget(save_btn)
        
        self.layout.addWidget(footer)

    def _get_combo_style(self):
        c = COLORS["dark"]
        return f"""
            QComboBox {{
                background: {c["bg_tertiary"]};
                border: 1px solid {c["border"]};
                border-radius: 10px;
                padding: 8px 12px;
                color: {c["text_primary"]};
                font-family: {get_font_family()};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ 
                image: none; 
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {c["text_muted"]};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {c["bg_secondary"]};
                selection-background-color: {c["accent"]};
                color: {c["text_primary"]};
                border: 1px solid {c["border"]};
            }}
        """

    def load_settings(self):
        # Load from config/env
        self.gemini_key.setText(config.GEMINI_API_KEY)
        self.eleven_key.setText(config.ELEVENLABS_API_KEY)
        
        mode = "Auto (Smart Choice)"
        if config.TTS_ENGINE == "elevenlabs":
            mode = "ElevenLabs (Premium)"
        elif config.TTS_ENGINE == "piper":
            mode = "Piper (Offline)"
        self.voice_engine.setCurrentText(mode)

    def save_settings(self):
        # Read values
        gemini = self.gemini_key.text().strip()
        eleven = self.eleven_key.text().strip()
        
        engine_str = self.voice_engine.currentText()
        engine_val = "auto"
        if "ElevenLabs" in engine_str:
            engine_val = "elevenlabs"
        elif "Piper" in engine_str:
            engine_val = "piper"
            
        try:
            with open(".env", "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
            
        keys_updated = {"GEMINI_API_KEY": False, "ELEVENLABS_API_KEY": False, "TTS_ENGINE": False}
        
        final_lines = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("GEMINI_API_KEY="):
                final_lines.append(f"GEMINI_API_KEY={gemini}\n")
                keys_updated["GEMINI_API_KEY"] = True
            elif line_stripped.startswith("ELEVENLABS_API_KEY="):
                final_lines.append(f"ELEVENLABS_API_KEY={eleven}\n")
                keys_updated["ELEVENLABS_API_KEY"] = True
            elif line_stripped.startswith("TTS_ENGINE="):
                final_lines.append(f"TTS_ENGINE={engine_val}\n")
                keys_updated["TTS_ENGINE"] = True
            else:
                final_lines.append(line)
        
        # Append if not found
        if not keys_updated["GEMINI_API_KEY"]:
            final_lines.append(f"GEMINI_API_KEY={gemini}\n")
        if not keys_updated["ELEVENLABS_API_KEY"]:
            final_lines.append(f"ELEVENLABS_API_KEY={eleven}\n")
        if not keys_updated["TTS_ENGINE"]:
            final_lines.append(f"TTS_ENGINE={engine_val}\n")
            
        with open(".env", "w") as f:
            f.writelines(final_lines)
            
        # Update config runtime
        config.GEMINI_API_KEY = gemini
        config.ELEVENLABS_API_KEY = eleven
        config.TTS_ENGINE = engine_val
            
        self.settings_saved.emit()
        self.close()

    # Drag window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
