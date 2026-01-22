"""
Alyosha Main Window 2026
Премиальное frameless окно с glassmorphism
"""
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QApplication, QFrame, QStackedWidget,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QPoint, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase, QShortcut, QKeySequence, QColor, QAction, QIcon

from .styles import (
    get_main_window_style, get_button_style, get_title_style, 
    get_status_label_style, get_control_button_style, COLORS,
    get_model_badge_style
)

class ClickableLabel(QLabel):
    """QLabel с поддержкой кликов и hover-эффектов через стили"""
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)
from .chat_widget import ChatWidget, ConfirmationDialog
from .background_canvas import BackgroundCanvas
from src.assistant import Assistant, AssistantState
from src.session_manager import SessionManager
import config


class LoaderThread(QThread):
    """Фоновая загрузка моделей"""
    finished = pyqtSignal(bool, list) # success, errors
    
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        
    def run(self):
        success, errors = self.assistant.load_models()
        self.finished.emit(success, errors)


class MainWindow(QMainWindow):
    """Главное окно ассистента — 2026 Edition"""
    
    def __init__(self):
        super().__init__()
        
        self.assistant = None
        self.drag_position = None
        self.session_manager = SessionManager()
        
        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tray()
        self.setup_animations()
    
    def setup_window(self):
        """Настройка окна"""
        self.setWindowTitle("Алёша")
        self.setMinimumSize(400, 500)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # Frameless window with transparency
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        # Resize state
        self._resizing = False
        self._resize_margin = 8  # Small margin for precise edge detection
        self._resize_cursor = None
        
        # Apply style
        self.setStyleSheet(get_main_window_style())
        
        # Set window icon
        if config.ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(config.ICON_PATH)))
    
    def setup_tray(self):
        """Настройка системного трея"""
        self.tray_icon = QSystemTrayIcon(self)
        
        if config.ICON_PATH.exists():
            self.tray_icon.setIcon(QIcon(str(config.ICON_PATH)))
        else:
            # Fallback if no icon
            pass 
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Показать/Скрыть", self)
        show_action.triggered.connect(self._toggle_visibility)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """Обработка клика по иконке трея"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _quit_application(self):
        """Полный выход из приложения"""
        self._save_session()
        self.stop_assistant()
        QApplication.quit()
    
    def setup_ui(self):
        """Настройка UI"""
        # Outer container to allow shadow space
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        container.setMouseTracking(True)
        # Forward events for resizing logic
        container.mousePressEvent = self.mousePressEvent
        container.mouseMoveEvent = self.mouseMoveEvent
        container.mouseReleaseEvent = self.mouseReleaseEvent
        self.setCentralWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15) # Space for shadow
        
        # Main frame with background and rounding
        central = QFrame()
        central.setObjectName("centralWidget")
        self.setStyleSheet(get_main_window_style())
        container_layout.addWidget(central)
        
        # Add shadow effect to main frame
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        central.setGraphicsEffect(shadow)
        
        shadow.setOffset(0, 4)
        central.setGraphicsEffect(shadow)
        
        # Use a stacked layout approach: background + content overlay
        from PyQt6.QtWidgets import QStackedLayout
        
        # Stack layout to layer background under content
        stack = QStackedLayout(central)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        
        # Background canvas (animated)
        self.background = BackgroundCanvas()
        stack.addWidget(self.background)
        
        # Content layer
        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        content.setCursor(Qt.CursorShape.ArrowCursor)  # Override resize cursor in content
        stack.addWidget(content)
        stack.setCurrentWidget(content)  # Content on top
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Chat (main content - full vertical space)
        self.chat = ChatWidget()
        self.chat.message_sent.connect(self._on_text_message)
        self.chat.voice_button_clicked.connect(self._on_voice_button)
        self.chat.voice_button_pressed.connect(self._on_voice_start)
        self.chat.voice_button_released.connect(self._on_voice_stop)
        layout.addWidget(self.chat, stretch=1)
        # Status label is now in header (created in _create_header)
    
    def _create_header(self) -> QWidget:
        """Создать заголовок — premium 2026"""
        header = QWidget()
        header.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)
        
        title = QLabel("Алёша")
        title.setStyleSheet(get_title_style())
        header_layout.addWidget(title)
        
        # Spacing after title
        header_layout.addSpacing(4)
        
        # Status chip (compact inline status)
        self.status_label = QLabel("Ожидание...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {COLORS['dark']['text_muted']};
            font-size: 11px;
            font-weight: 600;
            font-family: 'Montserrat', 'Outfit', 'Ubuntu', sans-serif;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            background: {COLORS['dark']['bg_glass']};
            border: 1px solid {COLORS['dark']['border']};
            border-radius: 10px;
        """)
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addStretch()
        
        # Model Indicator Badge - 2026 subtle glass style
        self.model_badge = ClickableLabel("3 Flash")
        self.model_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.model_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        # Subtle glass - same as status chip, just different color tint
        self.model_badge.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.85);
            font-size: 11px;
            font-weight: 600;
            font-family: 'SF Pro Text', 'Montserrat', 'Outfit', sans-serif;
            letter-spacing: 0.3px;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
        """)
        self.model_badge.clicked.connect(self._show_model_menu)
        header_layout.addWidget(self.model_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Control buttons container
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # Minimize button
        min_btn = QPushButton("─")
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet(get_control_button_style())
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setToolTip("Свернуть")
        controls_layout.addWidget(min_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(get_control_button_style())
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)  # Hide instead of close
        close_btn.setToolTip("Скрыть (в трей)")
        controls_layout.addWidget(close_btn)
        
        # Add some spacing before controls
        header_layout.addSpacing(8)
        header_layout.addWidget(controls)
        
        return header
    
    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # Toggle visibility
        toggle = QShortcut(QKeySequence("Ctrl+Shift+Space"), self)
        toggle.activated.connect(self._toggle_visibility)
        
        # Focus input
        focus = QShortcut(QKeySequence("Ctrl+L"), self)
        focus.activated.connect(lambda: self.chat.input_field.setFocus())
    
    def setup_animations(self):
        """Настройка анимаций"""
        # Status label fade
        self.status_opacity = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(self.status_opacity)
        
        self.status_fade = QPropertyAnimation(self.status_opacity, b"opacity")
        self.status_fade.setDuration(300)
        self.status_fade.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def init_assistant(self):
        """Инициализировать ассистента асинхронно"""
        # Validate config first
        valid, errors = config.validate_config()
        if not valid:
            self.chat.add_message("Ошибка конфигурации:\n" + "\n".join(errors), "system")
            return
        
        # Create assistant
        self.assistant = Assistant()
        
        # Connect signals
        self.assistant.state_changed.connect(self._on_state_changed)
        self.assistant.audio_level_changed.connect(self._on_audio_level)
        self.assistant.message_received.connect(self._on_message)
        self.assistant.error_occurred.connect(self._on_error)
        self.assistant.confirmation_required.connect(self._on_confirmation)
        self.assistant.model_changed.connect(self._update_model_badge)
        self.assistant.barge_in_occurred.connect(self._on_barge_in)
        self.assistant.wake_word_detected.connect(self._on_wake_word)
        
        # Start loading in background
        self.status_label.setText("Загрузка...")
        
        self.loader_thread = LoaderThread(self.assistant)
        self.loader_thread.finished.connect(self._on_loading_finished)
        self.loader_thread.start()
        
    def _on_loading_finished(self, success, errors):
        """Загрузка завершена"""
        if not success:
            self.chat.add_message("Не удалось загрузить модели:\n" + "\n".join(errors), "system")
            self.status_label.setText("Ошибка загрузки")
            return
            
        self.status_label.setText("Готов")
        self.start_assistant()
        
    def start_assistant(self):
        """Запустить ассистента"""
        if self.assistant:
            self.assistant.start()
            self._check_first_run()

    def _check_first_run(self):
        """Проверка первого запуска"""
        flag_file = config.DATA_DIR / ".onboarding_shown"
        if not flag_file.exists():
            self.show_onboarding()
            flag_file.touch()
            self.session_manager.create_session()
        else:
            # Try to load last session
            if self.session_manager.load_latest_session():
                messages = self.session_manager.get_messages()
                if messages:
                    self.chat.load_messages(messages)
                    self.chat.add_message("Продолжаем. Что дальше?", "assistant")
                else:
                    self.chat.add_message("Привет, я Алёша. Что на этот раз?", "assistant")
            else:
                self.session_manager.create_session()
                self.chat.add_message("Привет, я Алёша. Что на этот раз?", "assistant")

    def show_onboarding(self):
        """Показать обучение"""
        QTimer.singleShot(1000, lambda: self.chat.add_message(
            "👋 **Привет! Я Алёша.**\n\n"
            "Я твой новый дерзкий ассистент с характером.\n"
            "Вот что я умею:\n\n"
            "1. **Управлять системой**: `громкость 50%`, `открой firefox`\n"
            "2. **Инструменты**: `посчитай 2+2`, `найди котиков`\n"
            "3. **Болтать**: просто скажи что-нибудь\n\n"
            "Для активации скажи **«Алёша»** или нажми `Ctrl+Shift+Space`.",
            "assistant"
        ))
        # Show keyboard shortcuts overlay
        QTimer.singleShot(1500, self._show_shortcuts_overlay)
    
    def _show_shortcuts_overlay(self):
        """Показать оверлей горячих клавиш"""
        from .keyboard_overlay import KeyboardShortcutsOverlay
        self.shortcuts_overlay = KeyboardShortcutsOverlay(self)
        # Center in window
        self.shortcuts_overlay.adjustSize()
        x = (self.width() - self.shortcuts_overlay.width()) // 2
        y = (self.height() - self.shortcuts_overlay.height()) // 2
        self.shortcuts_overlay.move(x, y)
        self.shortcuts_overlay.show()

    def stop_assistant(self):
        """Остановить ассистента"""
        if self.assistant:
            self.assistant.stop()
    
    @pyqtSlot(AssistantState)
    def _on_state_changed(self, state: AssistantState):
        """Обработка изменения состояния"""
        # Compact state texts for header chip
        state_texts = {
            AssistantState.IDLE: "Ожидание",
            AssistantState.LISTENING: "🎤 Слушаю",
            AssistantState.THINKING: "💭 Думаю",
            AssistantState.SPEAKING: "🔊 Говорю",
            AssistantState.ERROR: "⚠️ Ошибка",
        }
        
        # State colors for compact chip (text, bg, border)
        state_colors = {
            AssistantState.IDLE: (COLORS['dark']['text_muted'], COLORS['dark']['bg_glass'], COLORS['dark']['border']),
            AssistantState.LISTENING: (COLORS['dark']['accent'], "rgba(14, 165, 233, 0.15)", "rgba(14, 165, 233, 0.4)"),
            AssistantState.THINKING: (COLORS['dark']['warning'], "rgba(245, 158, 11, 0.15)", "rgba(245, 158, 11, 0.4)"),
            AssistantState.SPEAKING: (COLORS['dark']['success'], "rgba(14, 165, 233, 0.15)", "rgba(14, 165, 233, 0.4)"),
            AssistantState.ERROR: (COLORS['dark']['error'], "rgba(239, 68, 68, 0.15)", "rgba(239, 68, 68, 0.4)"),
        }
        
        text_color, bg_color, border_color = state_colors.get(state, state_colors[AssistantState.IDLE])
        
        self.status_label.setText(state_texts.get(state, ""))
        self.status_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 11px;
            font-weight: 600;
            font-family: 'Montserrat', 'Outfit', 'Ubuntu', sans-serif;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            background: {bg_color};
            border: 1px solid {border_color};
            border-radius: 10px;
        """)
        
        # Show/hide typing indicator in chat
        if state == AssistantState.THINKING:
            self.chat.show_typing_indicator()
        else:
            self.chat._hide_typing_indicator()
        
        # Play beep when starting to listen
        if state == AssistantState.LISTENING:
            # We need to access audio player, which is in assistant.stream_player? 
            # No, stream_player is for TTS. We need a general AudioPlayer or reuse.
            # Let's create a temporary AudioPlayer for beep or access it if available.
            # Better: Assistant should have an AudioPlayer.
            # But we can instantiate one here cheaply or use static method.
            from src.audio import AudioPlayer
            AudioPlayer().play_beep()
    
    @pyqtSlot(float)
    def _on_audio_level(self, level: float):
        """Обработка уровня громкости (currently no visual for this)"""
        pass  # Waveform removed - audio level visualization disabled
    
    @pyqtSlot(str, str)
    def _on_message(self, role: str, content: str):
        """Обработка нового сообщения"""
        print(f"[UI] Message received: {role} -> '{content}'")
        self.chat.add_message(content, role)
        # Track in session manager
        self.session_manager.add_message(role, content)
        # Play receive sound for assistant messages
        if role == "assistant":
            try:
                from src.audio import AudioPlayer
                AudioPlayer().play_receive_sound()
            except Exception:
                pass  # Sound is optional
    
    def _save_session(self):
        """Сохранить текущую сессию"""
        messages = self.chat.get_messages()
        if messages:
            # Update session manager with current messages
            self.session_manager.messages = messages
            self.session_manager.save_session()
    
    @pyqtSlot()
    def _on_barge_in(self):
        """Визуальный feedback при прерывании TTS"""
        # Flash the status label with warning color
        original_style = self.status_label.styleSheet()
        flash_style = f"""
            color: {COLORS['dark']['warning']};
            font-size: 11px;
            font-weight: 600;
            font-family: 'Montserrat', 'Outfit', 'Ubuntu', sans-serif;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            background: rgba(245, 158, 11, 0.25);
            border: 1px solid rgba(245, 158, 11, 0.5);
            border-radius: 10px;
        """
        self.status_label.setText("⚡ Прервано")
        self.status_label.setStyleSheet(flash_style)
        
        # Reset after 800ms
        QTimer.singleShot(800, lambda: self.status_label.setStyleSheet(original_style))
    
    @pyqtSlot()
    def _on_wake_word(self):
        """Визуальная пульсация при обнаружении wake word"""
        # Pulsation effect with cyan glow
        pulse_style = f"""
            color: {COLORS['dark']['accent_light']};
            font-size: 11px;
            font-weight: 600;
            font-family: 'Montserrat', 'Outfit', 'Ubuntu', sans-serif;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            background: rgba(14, 165, 233, 0.35);
            border: 2px solid rgba(56, 189, 248, 0.7);
            border-radius: 10px;
        """
        original_style = self.status_label.styleSheet()
        self.status_label.setText("✨ Алёша слушает...")
        self.status_label.setStyleSheet(pulse_style)
        
        # First pulse - fade down
        QTimer.singleShot(150, lambda: self.status_label.setStyleSheet(pulse_style.replace("0.35", "0.15").replace("0.7", "0.4")))
        # Second pulse - fade up
        QTimer.singleShot(300, lambda: self.status_label.setStyleSheet(pulse_style))
        # Third pulse - fade down
        QTimer.singleShot(450, lambda: self.status_label.setStyleSheet(pulse_style.replace("0.35", "0.20").replace("0.7", "0.5")))
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """Обработка ошибки"""
        self.chat.add_message(f"Ошибка: {error}", "system")
        try:
            from src.audio import AudioPlayer
            AudioPlayer().play_error_sound()
        except Exception:
            pass
    
    @pyqtSlot(str)
    def _on_confirmation(self, command: str):
        """Показать диалог подтверждения"""
        dialog = ConfirmationDialog(command, self.chat)
        dialog.confirmed.connect(self._confirm_command)
        dialog.cancelled.connect(self._cancel_command)
        self.chat.messages_layout.insertWidget(self.chat.messages_layout.count() - 1, dialog)
    
    def _confirm_command(self):
        """Подтвердить команду"""
        if self.assistant:
            self.assistant.confirm_command()
            try:
                from src.audio import AudioPlayer
                AudioPlayer().play_success_sound()
            except Exception:
                pass
    
    def _cancel_command(self):
        """Отменить команду"""
        if self.assistant:
            self.assistant.cancel_command()
    
    def _on_text_message(self, text: str):
        """Обработка текстового сообщения"""
        if self.assistant:
            self.assistant.process_text(text)
    
    def _on_voice_button(self):
        """Handle voice button click - start voice recording (legacy toggle)"""
        if self.assistant:
            self.assistant.start_voice_recording()
    
    def _on_voice_start(self):
        """Push-to-talk: start recording on button press"""
        if self.assistant:
            self.assistant.start_voice_recording()
    
    def _on_voice_stop(self):
        """Push-to-talk: stop recording on button release"""
        if self.assistant:
            self.assistant.stop_voice_recording()
    
    def _toggle_visibility(self):
        """Переключить видимость окна"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.chat.input_field.setFocus()
    
    # Window resizing and dragging
    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            margin = self._resize_margin
            w, h = self.width(), self.height()
            
            # Check for resize edges
            on_right = pos.x() >= w - margin
            on_bottom = pos.y() >= h - margin
            on_left = pos.x() <= margin
            on_top = pos.y() <= margin
            
            if on_right or on_bottom or on_left or on_top:
                self._resizing = True
                self._resize_edge = (on_left, on_top, on_right, on_bottom)
            else:
                self._resizing = False
                # Drag logic
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши"""
        pos = event.position().toPoint()
        margin = self._resize_margin
        w, h = self.width(), self.height()
        
        if not self._resizing:
            # Update cursor for edges
            on_right = pos.x() >= w - margin
            on_bottom = pos.y() >= h - margin
            on_left = pos.x() <= margin
            on_top = pos.y() <= margin
            
            if (on_left and on_top) or (on_right and on_bottom):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif (on_right and on_top) or (on_left and on_bottom):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif on_left or on_right:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif on_top or on_bottom:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                
            # Perform drag
            if self.drag_position is not None:
                self.move(event.globalPosition().toPoint() - self.drag_position)
        else:
            # Perform resize
            left, top, right, bottom = self._resize_edge
            gp = event.globalPosition().toPoint()
            rect = self.geometry()
            
            if right:
                rect.setRight(gp.x())
            if bottom:
                rect.setBottom(gp.y())
            if left:
                width = rect.right() - gp.x()
                if width >= self.minimumWidth():
                    rect.setLeft(gp.x())
            if top:
                height = rect.bottom() - gp.y()
                if height >= self.minimumHeight():
                    rect.setTop(gp.y())
            
            if rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight():
                self.setGeometry(rect)
                
        event.accept()

    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши"""
        self.drag_position = None
        self._resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()
    
    def resizeEvent(self, event):
        """Обновление при изменении размера"""
        super().resizeEvent(event)
        # Note: We don't use setMask anymore as polygon masks create jagged edges
        # Rounded corners are handled by background_canvas drawing and CSS border-radius

    def _update_model_badge(self, mode: str, model_name: str):
        """Обновить индикатор модели"""
        if hasattr(self, 'model_badge'):
            self.model_badge.setText(f"{mode}: {model_name}")
            self.model_badge.setStyleSheet(get_model_badge_style(mode))
            self.model_badge.show() # Force visibility
            self.model_badge.update() # Force repaint

    def _show_model_menu(self):
        """Показать меню выбора модели"""
        if not self.assistant:
            # Optional: show toast or just ignore if not loaded
            return
            
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['dark']['bg_glass']};
                border: 1px solid {COLORS['dark']['border']};
                color: {COLORS['dark']['text_primary']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
                font-family: 'Ubuntu', sans-serif;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['dark']['accent']}44;
            }}
        """)
        
        auto_action = menu.addAction("🤖 Auto (Smart)")
        auto_action.triggered.connect(lambda: self.assistant.set_forced_model("auto"))
        
        menu.addSeparator()
        
        flash_action = menu.addAction("⚡ Gemini 3 Flash")
        flash_action.triggered.connect(lambda: self.assistant.set_forced_model("flash"))
        
        pro_action = menu.addAction("🧠 Gemini 3 Pro")
        pro_action.triggered.connect(lambda: self.assistant.set_forced_model("pro"))
        
        # Position menu below label
        pos = self.model_badge.mapToGlobal(self.model_badge.rect().bottomLeft())
        menu.exec(pos)

    def closeEvent(self, event):
        """Закрытие окна — минимизация в трей"""
        event.ignore()
        self.hide()
