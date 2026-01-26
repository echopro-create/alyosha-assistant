"""
Alyosha Sidebar 2026
History navigation with glassmorphism
"""
from PyQt6.QtWidgets import (
    QVBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve

from .styles import COLORS, get_font_family
from .icons import IconFactory

class SidebarWidget(QFrame):
    """Collapsible sidebar with chat history"""
    
    session_selected = pyqtSignal(str) # session_id
    new_chat_requested = pyqtSignal()
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.setFixedWidth(0) # Start collapsed
        self.expanded_width = 250
        
        # Style
        c = COLORS["dark"]
        self.setStyleSheet(f"""
            SidebarWidget {{
                background: {c["bg_secondary"]};
                border-right: 1px solid {c["border"]};
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }}
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 8px;
                color: {c["text_secondary"]};
            }}
            QListWidget::item:hover {{
                background: {c["bg_glass_hover"]};
                color: {c["text_primary"]};
            }}
            QListWidget::item:selected {{
                background: {c["bg_tertiary"]};
                color: {c["accent"]};
                border-left: 3px solid {c["accent"]};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        
        # New Chat Button
        new_chat_btn = QPushButton("Новый чат")
        new_chat_btn.setIcon(IconFactory.get_icon("plus", c["text_primary"], 16)) # "plus" currently mapped to "check" placeholder if not exists?
        # Let's use simple text-icon fallback if needed or just text
        # Assuming IconFactory handles missing gracefully (it returns empty icon)
        # We need a "plus" icon in IconFactory. I'll add it later or reuse something.
        # Actually I can just add "plus" to IconFactory now? 
        # For now, let's just use text.
        new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c["accent"]};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-weight: 600;
                font-family: {get_font_family()};
            }}
            QPushButton:hover {{ background: {c["accent_light"]}; }}
        """)
        new_chat_btn.clicked.connect(self.new_chat_requested)
        layout.addWidget(new_chat_btn)
        
        # History Label
        lbl = QLabel("История")
        lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(lbl)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Refresh timer or manual refresh?
        # We'll refresh when opened.
        
    def refresh(self):
        """Reload sessions"""
        self.list_widget.clear()
        sessions = self.session_manager.list_sessions(limit=50)
        
        for sess in sessions:
            item = QListWidgetItem(sess["title"])
            item.setData(Qt.ItemDataRole.UserRole, sess["id"])
            item.setToolTip(f"Обновлено: {sess['updated_at']}")
            self.list_widget.addItem(item)
            
    def toggle(self):
        """Animate open/close"""
        width = self.width()
        target = self.expanded_width if width == 0 else 0
        
        if target > 0:
            self.refresh()
            
        self.anim = QPropertyAnimation(self, b"maximumWidth") # modifying fixedWidth via max? No, fixedWidth logic.
        # QPropertyAnimation usually works on size properties if defined as QProperty.
        # Using separate geometry animation or maximumWidth is easier.
        
        # Let's animate maximumWidth (assuming layout respects it)
        # But I set setFixedWidth in init.
        # Need to unset fixed.
        self.setMinimumWidth(0)
        self.setMaximumWidth(width) # Start from current
        
        self.anim = QPropertyAnimation(self, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setStartValue(width)
        self.anim.setEndValue(target)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self.setFixedWidth) # Hack to force layout update?
        self.anim.start()
        
    def _on_item_clicked(self, item):
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.session_selected.emit(session_id)
        # Auto close on mobile-like selection? No, let user close.
