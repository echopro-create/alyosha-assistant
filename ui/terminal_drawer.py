
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSlot

from .styles import COLORS

class TerminalDrawer(QWidget):
    """
    Выдвижная панель терминала.
    Отображает логи системы и вывод команд в стиле хакерской консоли.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(250)
        self.setup_ui()
        
    def setup_ui(self):
        c = COLORS["dark"]
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #0d1117; /* GitHub Dark Dimmed-ish */
                border-top: 1px solid {c["border"]};
            }}
            QTextEdit {{
                background-color: transparent;
                border: none;
                color: #38bdf8; /* Cyan terminal text */
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 11px;
                padding: 8px;
            }}
            QLabel {{
                color: {c["text_muted"]};
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                color: {c["text_muted"]};
            }}
            QPushButton:hover {{
                color: {c["text_primary"]};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header bar
        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet(f"background-color: #161b22; border-bottom: 1px solid {c['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        
        title = QLabel("Terminal / Logs")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Log area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        # Initial greeting
        self.append_log("Alyosha Terminal v2.0 initialized...", "SYSTEM")
        
    def clear_logs(self):
        self.text_area.clear()
        
    @pyqtSlot(str, str)
    def append_log(self, message: str, level: str = "INFO"):
        """Append a log message with coloring based on level"""
        # Define colors using CSS or HTML
        color = "#94a3b8" # Default slate
        prefix = ""
        
        if level == "INFO":
            color = "#a5b4fc" # Indigo/Blueish
            prefix = "➜ "
        elif level == "WARNING":
            color = "#fbbf24" # Amber
            prefix = "⚠ "
        elif level == "ERROR" or level == "CRITICAL":
            color = "#f87171" # Red
            prefix = "✖ "
        elif "Executing" in message: # Special handling for commands
            color = "#34d399" # Emerald
            prefix = "$ "
            
        html = f'<span style="color: {color};"><b>[{level}]</b> {prefix}{message}</span>'
        self.text_area.append(html)
        
        # Auto scroll
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())
