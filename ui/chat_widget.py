"""
Alyosha Chat Widget 2026
Premium чат-интерфейс с spring-анимациями и 3D-эффектами
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QLineEdit, QPushButton, QFrame, QSpacerItem, 
    QSizePolicy, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, 
    QTimer, QSequentialAnimationGroup, QParallelAnimationGroup,
    QPoint, QRect, QAbstractAnimation
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPainterPath, QPixmap, 
    QImage, QBrush, QIcon, QLinearGradient
)

from .styles import (
    get_chat_widget_style, get_input_style, 
    get_button_style, get_message_bubble_style,
    get_role_label_style, get_confirmation_style, COLORS
)


class AvatarWidget(QFrame):
    """Анимированный аватар (ассистент или пользователь)"""
    
    def __init__(self, role: str = "assistant", parent=None):
        super().__init__(parent)
        
        self.role = role
        
        self.size_val = 32
        self.setFixedSize(self.size_val, self.size_val)
        
        # Load correct avatar path
        import config
        import os
        
        if role == "user":
            avatar_path = str(config.USER_AVATAR_PATH)
            glow_color = QColor(14, 165, 233, 180) # Cyan/Blue for user
        else:
            # Try png then jpg
            avatar_path_png = os.path.join(str(config.ASSETS_DIR), "avatar.png")
            avatar_path_jpg = os.path.join(str(config.ASSETS_DIR), "avatar.jpg")
            avatar_path = avatar_path_png if os.path.exists(avatar_path_png) else avatar_path_jpg
            glow_color = QColor(14, 165, 233, 180) # Purple for assistant
        
        if os.path.exists(avatar_path):
            img = QImage(avatar_path)
            sq_img = img.scaled(self.size_val, self.size_val, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            self.pixmap = QPixmap(self.size())
            self.pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(self.pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Glow border ring
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawEllipse(0, 0, self.size_val, self.size_val)
            
            # Masked image
            path = QPainterPath()
            border_w = 2 
            path.addEllipse(border_w, border_w, self.size_val - border_w * 2, self.size_val - border_w * 2)
            painter.setClipPath(path)
            
            # Center image
            offset_x = (sq_img.width() - self.size_val) // 2
            offset_y = (sq_img.height() - self.size_val) // 2
            painter.drawImage(0, 0, sq_img, offset_x, offset_y, self.size_val, self.size_val)
            painter.end()
            
            self.setStyleSheet("border: none;")
            self.img_label = QLabel(self)
            self.img_label.setPixmap(self.pixmap)
            self.img_label.setFixedSize(self.size_val, self.size_val)
        else:
            # Fallback gradient
            self.setStyleSheet(f"""
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 {'#0EA5E9' if role == 'user' else '#8B5CF6'},
                    stop:0.5 {'#22D3EE' if role == 'user' else '#EC4899'},
                    stop:1 {'#3B82F6' if role == 'user' else '#3B82F6'}
                );
                border: none;
                border-radius: {self.size_val//2}px;
            """)
        
        # Outer glow effect matching 2026 aesthetics
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(glow_color if 'glow_color' in locals() else QColor(14, 165, 233, 120))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)


class TypingIndicator(QFrame):
    """Индикатор печати с анимированными точками"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            background: {COLORS['dark']['bg_glass']};
            border: 1px solid {COLORS['dark']['border']};
            border-radius: 16px;
            padding: 8px 12px;
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {COLORS['dark']['accent']}; font-size: 10px;")
            layout.addWidget(dot)
            self.dots.append(dot)
        
        # Animation
        self.current_dot = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(300)
    
    def _animate(self):
        """Анимация точек"""
        for i, dot in enumerate(self.dots):
            if i == self.current_dot:
                dot.setStyleSheet(f"color: {COLORS['dark']['accent']}; font-size: 12px;")
            else:
                dot.setStyleSheet(f"color: {COLORS['dark']['text_muted']}; font-size: 10px;")
        
        self.current_dot = (self.current_dot + 1) % 3
    
    def stop(self):
        """Остановить анимацию"""
        self.timer.stop()


class MessageBubble(QFrame):
    """Пузырёк сообщения с 3D-эффектами и spring-анимацией"""
    
    def __init__(self, text: str, role: str = "user", parent=None):
        super().__init__(parent)
        
        self.role = role
        self._raw_text = text  # Store raw text for copying
        self.setObjectName(f"{role}Bubble")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        
        # Horizontal container for avatar + bubble
        h_container = QHBoxLayout()
        h_container.setContentsMargins(0, 0, 0, 0)
        h_container.setSpacing(10)
        
        # Message container — dynamic width based on content
        self.bubble = QFrame()
        self.bubble.setStyleSheet(get_message_bubble_style(role))
        # MinimumExpanding = shrink to content but can grow if needed
        self.bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.bubble.setMinimumWidth(120)  # Minimum for very short messages
        # Max width will be set dynamically in resizeEvent based on parent width
        
        # Add shadow to bubble for 3D effect
        shadow = QGraphicsDropShadowEffect()
        if role == "user":
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(14, 165, 233, 50))
            shadow.setOffset(0, 4)
        else:
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(0, 3)
        self.bubble.setGraphicsEffect(shadow)
        
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)  # Proper padding for readability
        bubble_layout.setSpacing(6)
        
        # Header with role label and copy button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)
        
        # Role label
        if role == "assistant":
            role_label = QLabel("АЛЁША")
            role_label.setStyleSheet(get_role_label_style(role))
            header.addWidget(role_label)
        elif role == "system":
            role_label = QLabel("СИСТЕМА")
            role_label.setStyleSheet(get_role_label_style(role))
            header.addWidget(role_label)
        
        header.addStretch()
        
        # Copy button (hidden by default)
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(24, 24)
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setToolTip("Копировать")
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """)
        self.copy_button.clicked.connect(self._copy_text)
        self.copy_button.hide()  # Hidden by default
        header.addWidget(self.copy_button)
        
        bubble_layout.addLayout(header)
        
        # Message text
        message_label = QLabel(self._markdown_to_html(text))
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_label.setStyleSheet("background: transparent; border: none; padding: 0; margin: 0;")
        bubble_layout.addWidget(message_label)
        
        # Alignment with avatar — use stretch factors for proper width distribution
        if role == "user":
            h_container.addStretch(1)  # Push to right
            h_container.addWidget(self.bubble, 3)  # Give bubble weight
            # User Avatar on the right
            avatar = AvatarWidget(role="user")
            h_container.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)
        elif role == "assistant":
            # Avatar for assistant
            avatar = AvatarWidget(role="assistant")
            h_container.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)
            h_container.addWidget(self.bubble, 3)  # Give bubble weight
            h_container.addStretch(1)  # Balance on right
        else:  # system
            h_container.addWidget(self.bubble, 1)
        
        layout.addLayout(h_container)
        
        # Opacity effect for fade-in animation (no height manipulation!)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
    
    def enterEvent(self, event):
        """Show copy button on hover"""
        self.copy_button.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hide copy button when not hovering"""
        self.copy_button.hide()
        super().leaveEvent(event)
    
    def _copy_text(self):
        """Copy message text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._raw_text)
        # Visual feedback
        self.copy_button.setText("✓")
        self.copy_button.setToolTip("Скопировано!")
        QTimer.singleShot(1500, lambda: (
            self.copy_button.setText("📋"),
            self.copy_button.setToolTip("Копировать")
        ))
    
    def _markdown_to_html(self, text: str) -> str:
        """Расширенная конвертация Markdown -> HTML для QLabel"""
        import re
        
        # Escaping HTML special chars (minimal, before processing)
        text = text.replace("&", "&amp;")
        
        # Process code blocks FIRST (before escaping < >)
        def format_code_block(match):
            lang = match.group(1) or ""
            code = match.group(2)
            # Escape HTML in code
            code = code.replace("<", "&lt;").replace(">", "&gt;")
            # Simple syntax highlighting by language
            if lang.lower() in ["python", "py"]:
                # Python keywords
                keywords = ["def", "class", "import", "from", "return", "if", "else", "elif", 
                           "for", "while", "try", "except", "with", "as", "in", "not", "and", "or",
                           "True", "False", "None", "self", "async", "await", "lambda", "yield"]
                for kw in keywords:
                    code = re.sub(rf'\b({kw})\b', r'<font color="#FF79C6">\1</font>', code)
                # Strings
                code = re.sub(r'(".*?")', r'<font color="#F1FA8C">\1</font>', code)
                code = re.sub(r"('.*?')", r'<font color="#F1FA8C">\1</font>', code)
                # Comments  
                code = re.sub(r'(#.*?)(?=<br>|$)', r'<font color="#6272A4">\1</font>', code)
            elif lang.lower() in ["bash", "sh", "shell"]:
                # Bash commands
                code = re.sub(r'^(\w+)', r'<font color="#50FA7B">\1</font>', code)
            elif lang.lower() in ["js", "javascript"]:
                keywords = ["const", "let", "var", "function", "return", "if", "else", "for", 
                           "while", "class", "new", "this", "async", "await", "import", "export"]
                for kw in keywords:
                    code = re.sub(rf'\b({kw})\b', r'<font color="#FF79C6">\1</font>', code)
            
            return f'<pre style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 8px; font-family: monospace; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1);">{code}</pre>'
        
        text = re.sub(r'```(\w*)\n?(.*?)```', format_code_block, text, flags=re.DOTALL)
        
        # Now escape remaining < > (outside code blocks)
        # Split by <pre> to preserve code blocks
        parts = re.split(r'(<pre.*?</pre>)', text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if not part.startswith('<pre'):
                parts[i] = part.replace("<", "&lt;").replace(">", "&gt;")
        text = ''.join(parts)
        
        # Tables: | col1 | col2 |
        def format_table(match):
            rows = match.group(0).strip().split('\n')
            html = '<table style="border-collapse: collapse; margin: 8px 0; width: 100%;">'
            for i, row in enumerate(rows):
                if '---' in row:
                    continue  # Skip separator row
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if not cells:
                    continue
                tag = 'th' if i == 0 else 'td'
                style = 'border: 1px solid rgba(255,255,255,0.2); padding: 6px 10px; text-align: left;'
                if i == 0:
                    style += ' background: rgba(255,255,255,0.05); font-weight: 600;'
                html += '<tr>'
                for cell in cells:
                    html += f'<{tag} style="{style}">{cell}</{tag}>'
                html += '</tr>'
            html += '</table>'
            return html
        
        text = re.sub(r'(\|.+\|[\n\r]*)+', format_table, text)
        
        # Horizontal rule
        text = re.sub(r'^---+$', '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.2); margin: 12px 0;">', text, flags=re.MULTILINE)
        
        # Bold **text** and __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Italic *text* and _text_ (but not inside words)
        text = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<i>\1</i>', text)
        
        # Code inline `code`
        text = re.sub(r'`([^`]+)`', r'<font face="monospace" color="#FCA5A5" style="background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 4px;"><b>\1</b></font>', text)
        
        # Lists - unordered (- or *)
        lines = text.split('\n')
        in_ul = False
        in_ol = False
        result_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Unordered list
            if re.match(r'^[-*]\s+', stripped):
                if not in_ul:
                    if in_ol:
                        result_lines.append('</ol>')
                        in_ol = False
                    result_lines.append('<ul style="margin: 6px 0; padding-left: 20px;">')
                    in_ul = True
                content = re.sub(r'^[-*]\s+', '', stripped)
                result_lines.append(f'<li style="margin: 3px 0;">{content}</li>')
            # Ordered list
            elif re.match(r'^\d+\.\s+', stripped):
                if not in_ol:
                    if in_ul:
                        result_lines.append('</ul>')
                        in_ul = False
                    result_lines.append('<ol style="margin: 6px 0; padding-left: 20px;">')
                    in_ol = True
                content = re.sub(r'^\d+\.\s+', '', stripped)
                result_lines.append(f'<li style="margin: 3px 0;">{content}</li>')
            else:
                if in_ul:
                    result_lines.append('</ul>')
                    in_ul = False
                if in_ol:
                    result_lines.append('</ol>')
                    in_ol = False
                result_lines.append(line)
        
        if in_ul:
            result_lines.append('</ul>')
        if in_ol:
            result_lines.append('</ol>')
        
        text = '\n'.join(result_lines)
        
        # New lines (but not inside lists/tables/pre)
        text = text.replace("\n", "<br>")
        # Clean up extra <br> around block elements
        text = re.sub(r'<br>\s*(</?(?:ul|ol|li|table|tr|td|th|pre|hr))', r'\1', text)
        text = re.sub(r'(</(?:ul|ol|li|table|tr|td|th|pre|hr)>)\s*<br>', r'\1', text)
        
        return text
    
    def resizeEvent(self, event):
        """Handle resize — set dynamic max-width based on parent"""
        super().resizeEvent(event)
        # Calculate 80% of available width for modern chat feel
        if self.parentWidget():
            available_width = self.parentWidget().width()
            # 80% of parent, but cap at 600px for readability
            max_w = min(int(available_width * 0.80), 600)
            # Minimum 200px for very narrow windows
            max_w = max(max_w, 200)
            if hasattr(self, 'bubble'):
                self.bubble.setMaximumWidth(max_w)
    
    def animate_in(self):
        """Smooth opacity fade-in animation (no height manipulation for stability)"""
        # Simple opacity fade — no layout thrashing
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_anim.start()


class ChatWidget(QWidget):
    """Виджет чата с прокруткой и вводом — premium 2026"""
    
    message_sent = pyqtSignal(str)
    voice_button_clicked = pyqtSignal()  # Signal for voice button (toggle mode)
    voice_button_pressed = pyqtSignal()  # Push-to-talk: start recording
    voice_button_released = pyqtSignal()  # Push-to-talk: stop and process
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.typing_indicator = None
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Messages scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(get_chat_widget_style())
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(4, 8, 4, 8)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Input area with glow effect
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(8, 0, 8, 8)
        # Voice button (microphone) - 2026 minimal style
        self.voice_button = QPushButton("🎤")  # Clean mic icon
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setFixedSize(46, 46)
        self.voice_button.setStyleSheet(f"""
            QPushButton#voiceButton {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 23px;
                font-size: 18px;
            }}
            QPushButton#voiceButton:hover {{
                background: rgba(255, 255, 255, 0.10);
                border-color: rgba(255, 255, 255, 0.15);
            }}
            QPushButton#voiceButton:pressed {{
                background: rgba(14, 165, 233, 0.20);
                border-color: rgba(14, 165, 233, 0.30);
            }}
        """)
        self.voice_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_button.setToolTip("Голосовой ввод (удерживай для записи)")
        
        # Push-to-talk: override mouse events
        self.voice_button.mousePressEvent = self._on_voice_press
        self.voice_button.mouseReleaseEvent = self._on_voice_release
        self._voice_is_pressed = False
        
        # Add subtle glow to voice button - Cyan theme
        voice_shadow = QGraphicsDropShadowEffect()
        voice_shadow.setBlurRadius(12)
        voice_shadow.setColor(QColor(14, 165, 233, 60))  # Cyan glow
        voice_shadow.setOffset(0, 2)
        self.voice_button.setGraphicsEffect(voice_shadow)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Напиши сообщение...")
        self.input_field.setStyleSheet(get_input_style())
        self.input_field.returnPressed.connect(self._send_message)
        
        # Add subtle glow on focus
        # FIXME: Shadow effect might be causing visibility issues
        # self.input_shadow = QGraphicsDropShadowEffect()
        # self.input_shadow.setBlurRadius(0)
        # self.input_shadow.setColor(QColor(14, 165, 233, 0))
        # self.input_shadow.setOffset(0, 0)
        # self.input_field.setGraphicsEffect(self.input_shadow)
        
        # self.input_field.focusInEvent = self._on_input_focus_in
        # self.input_field.focusOutEvent = self._on_input_focus_out
        
        # Send button with gradient
        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(46, 46) # Slightly smaller for more elegance
        self.send_button.setStyleSheet(get_button_style())
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self._send_message)
        
        # Button shadow
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(16)
        btn_shadow.setColor(QColor(14, 165, 233, 80))
        btn_shadow.setOffset(0, 4)
        self.send_button.setGraphicsEffect(btn_shadow)
        
        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        # Ensure vertical centering
        input_layout.setAlignment(self.send_button, Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(input_container)
    
    def _on_input_focus_in(self, event):
        """Анимация при фокусе на input"""
        QLineEdit.focusInEvent(self.input_field, event)
        
        # Animate glow
        self.glow_anim = QPropertyAnimation(self.input_shadow, b"blurRadius")
        self.glow_anim.setDuration(200)
        self.glow_anim.setStartValue(0)
        self.glow_anim.setEndValue(20)
        self.glow_anim.start()
        
        self.input_shadow.setColor(QColor(14, 165, 233, 60))
    
    def _on_input_focus_out(self, event):
        """Анимация при потере фокуса"""
        QLineEdit.focusOutEvent(self.input_field, event)
        
        # Animate glow out
        self.glow_anim = QPropertyAnimation(self.input_shadow, b"blurRadius")
        self.glow_anim.setDuration(200)
        self.glow_anim.setStartValue(20)
        self.glow_anim.setEndValue(0)
        self.glow_anim.start()
    
    def add_message(self, text: str, role: str = "user"):
        """Добавить сообщение в чат"""
        # Remove typing indicator if present
        self._hide_typing_indicator()
        
        # Track message for session history
        if not hasattr(self, '_messages_data'):
            self._messages_data = []
        self._messages_data.append({"role": role, "content": text})
        
        # Insert before stretch
        bubble = MessageBubble(text, role, self.messages_widget)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # Animate in
        QTimer.singleShot(20, bubble.animate_in)
        
        # Scroll to bottom (wait for layout to settle, faster now without height anim)
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def show_typing_indicator(self):
        """Показать индикатор печати"""
        if self.typing_indicator is None:
            self.typing_indicator = TypingIndicator(self.messages_widget)
            
            # Container for alignment
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(46, 4, 0, 4)  # Offset for avatar
            container_layout.addWidget(self.typing_indicator)
            container_layout.addStretch()
            
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
            self._scroll_to_bottom()
    
    def _hide_typing_indicator(self):
        """Скрыть индикатор печати"""
        if self.typing_indicator:
            self.typing_indicator.stop()
            parent = self.typing_indicator.parent()
            if parent:
                parent.deleteLater()
            self.typing_indicator = None
    
    def _send_message(self):
        """Отправить сообщение"""
        text = self.input_field.text().strip()
        if text:
            self.add_message(text, "user")
            self.input_field.clear()
            self.message_sent.emit(text)
            # Play send sound
            try:
                from src.audio import AudioPlayer
                AudioPlayer().play_send_sound()
            except Exception:
                pass  # Sound is optional
    
    def _on_voice_click(self):
        """Handle voice button click (legacy toggle mode)"""
        self.voice_button_clicked.emit()
    
    def _on_voice_press(self, event):
        """Push-to-talk: start recording on press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._voice_is_pressed = True
            self.voice_button_pressed.emit()
            # Visual feedback: show active state
            self.voice_button.setStyleSheet(f"""
                QPushButton#voiceButton {{
                    background: {COLORS['dark']['accent']}44;
                    border: 2px solid {COLORS['dark']['accent']};
                    border-radius: 23px;
                    font-size: 20px;
                }}
            """)
    
    def _on_voice_release(self, event):
        """Push-to-talk: stop recording on release"""
        if event.button() == Qt.MouseButton.LeftButton and self._voice_is_pressed:
            self._voice_is_pressed = False
            self.voice_button_released.emit()
            # Reset visual state
            self.voice_button.setStyleSheet(f"""
                QPushButton#voiceButton {{
                    background: {COLORS['dark']['bg_glass']};
                    border: 1px solid {COLORS['dark']['border']};
                    border-radius: 23px;
                    font-size: 20px;
                }}
                QPushButton#voiceButton:hover {{
                    background: {COLORS['dark']['bg_glass_hover']};
                    border-color: {COLORS['dark']['accent']};
                }}
            """)
    
    def _scroll_to_bottom(self):
        """Прокрутить к последнему сообщению"""
        scrollbar = self.scroll_area.verticalScrollBar()
        
        # Smooth scroll animation
        self.scroll_anim = QPropertyAnimation(scrollbar, b"value")
        self.scroll_anim.setDuration(200)
        self.scroll_anim.setStartValue(scrollbar.value())
        self.scroll_anim.setEndValue(scrollbar.maximum())
        self.scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_anim.start()
    
    def clear_messages(self):
        """Очистить все сообщения"""
        self._messages_data = []  # Clear internal list too
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def get_messages(self) -> list[dict]:
        """Получить все сообщения для сохранения"""
        return getattr(self, '_messages_data', []).copy()
    
    def load_messages(self, messages: list[dict], animate: bool = False):
        """Загрузить сообщения из истории"""
        self.clear_messages()
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Add without animation for faster loading
            bubble = MessageBubble(content, role, self.messages_widget)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
            if not animate:
                # Set opacity to 1 directly for instant display
                bubble.opacity_effect.setOpacity(1.0)
            else:
                QTimer.singleShot(20, bubble.animate_in)
        
        # Update internal message list
        self._messages_data = messages.copy()
        
        # Scroll to bottom after loading
        QTimer.singleShot(100, self._scroll_to_bottom)


class ConfirmationDialog(QFrame):
    """Диалог подтверждения опасных команд — premium 2026"""
    
    confirmed = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(self, command: str, parent=None):
        super().__init__(parent)
        
        self.command = command
        self.countdown = 5  # Seconds before confirm is enabled
        
        self.setObjectName("confirmationDialog")
        self.setStyleSheet(get_confirmation_style())
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(239, 68, 68, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Warning header
        header = QHBoxLayout()
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 20px; background: transparent;")
        header.addWidget(warning_icon)
        
        title = QLabel("Опасная команда")
        title.setStyleSheet(f"""
            color: #FCA5A5; 
            font-size: 15px; 
            font-weight: 700;
            letter-spacing: 0.3px;
            background: transparent;
        """)
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Smart explanation based on command
        explanation = self._get_smart_explanation(command)
        explain_label = QLabel(explanation)
        explain_label.setWordWrap(True)
        explain_label.setStyleSheet(f"""
            color: #FFD93D;
            font-size: 13px;
            font-weight: 500;
            background: rgba(255, 217, 61, 0.1);
            border-radius: 8px;
            padding: 10px;
            margin: 4px 0;
        """)
        layout.addWidget(explain_label)
        
        # Command display
        cmd_container = QFrame()
        cmd_container.setStyleSheet(f"""
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px;
        """)
        cmd_layout = QVBoxLayout(cmd_container)
        cmd_layout.setContentsMargins(0, 0, 0, 0)
        
        cmd_label = QLabel(command)
        cmd_label.setWordWrap(True)
        cmd_label.setStyleSheet(f"""
            color: #FFFFFF; 
            font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace; 
            font-size: 13px;
            background: transparent;
            padding: 8px;
        """)
        cmd_layout.addWidget(cmd_label)
        
        layout.addWidget(cmd_container)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self._cancel)
        
        self.confirm_btn = QPushButton(f"Подождите ({self.countdown}с)...")
        self.confirm_btn.setObjectName("dangerButton")
        self.confirm_btn.setStyleSheet(f"""
            QPushButton#dangerButton {{
                background: rgba(100, 100, 100, 0.5);
                color: #888;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Start countdown timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_countdown)
        self.timer.start(1000)
        
        # Entry animation
        self.setMaximumHeight(0)
        QTimer.singleShot(10, self._animate_in)
    
    def _get_smart_explanation(self, command: str) -> str:
        """Генерировать умное объяснение последствий команды"""
        cmd_lower = command.lower()
        
        if 'rm ' in cmd_lower:
            if '-rf' in cmd_lower or '-r' in cmd_lower:
                return "🗑️ Это УДАЛИТ файлы и папки рекурсивно. Отменить будет НЕВОЗМОЖНО."
            return "🗑️ Это удалит файлы. Отменить будет невозможно."
        
        if 'dd ' in cmd_lower:
            return "💾 Это ПЕРЕЗАПИШЕТ содержимое диска. Все данные на целевом устройстве будут УНИЧТОЖЕНЫ."
        
        if 'mkfs' in cmd_lower:
            return "💿 Это создаст новую файловую систему, УДАЛИВ все данные на разделе."
        
        if 'reboot' in cmd_lower:
            return "🔄 Система будет ПЕРЕЗАГРУЖЕНА. Несохранённые данные могут быть потеряны."
        
        if 'shutdown' in cmd_lower or 'poweroff' in cmd_lower:
            return "⏻ Система будет ВЫКЛЮЧЕНА. Сохраните все открытые файлы."
        
        if 'apt ' in cmd_lower and ('remove' in cmd_lower or 'purge' in cmd_lower):
            return "📦 Это УДАЛИТ программы из системы. Возможно потребуется переустановка."
        
        if 'fdisk' in cmd_lower or 'parted' in cmd_lower:
            return "💽 Это изменит таблицу разделов диска. Данные могут быть ПОТЕРЯНЫ."
        
        return "⚠️ Эта команда может внести необратимые изменения в систему."
    
    def _update_countdown(self):
        """Обновить обратный отсчёт"""
        self.countdown -= 1
        
        if self.countdown <= 0:
            self.timer.stop()
            self.confirm_btn.setText("Выполнить")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.confirm_btn.setStyleSheet(f"""
                QPushButton#dangerButton {{
                    background: rgba(239, 68, 68, 0.3);
                    color: #FCA5A5;
                    border: 1px solid rgba(239, 68, 68, 0.5);
                    border-radius: 12px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton#dangerButton:hover {{
                    background: rgba(239, 68, 68, 0.5);
                }}
            """)
            self.confirm_btn.clicked.connect(self._confirm)
        else:
            self.confirm_btn.setText(f"Подождите ({self.countdown}с)...")
    
    def _animate_in(self):
        """Анимация появления"""
        self.setMaximumHeight(16777215)
        target = self.sizeHint().height()
        self.setMaximumHeight(0)
        
        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(target + 20)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()
    
    def _confirm(self):
        """Подтвердить"""
        self.timer.stop()
        self.confirmed.emit()
        self._animate_out()
    
    def _cancel(self):
        """Отменить"""
        self.timer.stop()
        self.cancelled.emit()
        self._animate_out()
    
    def _animate_out(self):
        """Анимация исчезновения"""
        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(200)
        self.anim.setStartValue(self.height())
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()
