"""
Alyosha Main Window 2026
Премиальное frameless окно с glassmorphism
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QSystemTrayIcon,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSlot,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QShortcut,
    QKeySequence,
    QColor,
    QAction,
    QIcon,
)

from .styles import (
    get_main_window_style,
    get_title_style,
    get_control_button_style,
    COLORS,
    get_model_badge_style,
    get_status_label_style,  # Added import
)
from .chat_widget import ChatWidget, ConfirmationDialog
from .icons import IconFactory
from .settings_window import SettingsWindow
from .waveform import WaveformWidget
from .onboarding import OnboardingOverlay
from .toasts import ToastManager
from .sidebar import SidebarWidget
from src.assistant import Assistant, AssistantState
from src.session_manager import SessionManager
import config
import logging
from src.logging_utils import QLogHandler
from .terminal_drawer import TerminalDrawer


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


class LoaderThread(QThread):
    """Фоновая загрузка моделей"""

    finished = pyqtSignal(bool, list)  # success, errors

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
        
        # Init Logger
        self.log_handler = QLogHandler()
        logging.getLogger().addHandler(self.log_handler)

        self.assistant = None
        self.drag_position = None
        self.session_manager = SessionManager()

        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tray()
        self.setup_animations()
        
        # Connect logger to terminal
        self.log_handler.emitter.log_signal.connect(self.terminal.append_log)
        
        # Load assistant
        self._load_assistant()

    def setup_window(self):
        """Настройка окна"""
        self.setWindowTitle("Алёша")
        self.setMinimumSize(400, 500)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # Frameless window with transparency
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
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
        # Initialize toast manager
        self.toast_manager = None # Will init after central widget
        
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
        container_layout.setContentsMargins(15, 15, 15, 15)  # Space for shadow

        # Main frame with background and rounding
        central = QFrame()
        central.setObjectName("centralWidget")
        self.setStyleSheet(get_main_window_style())
        container_layout.addWidget(central)
        
        # Init toast manager with container as parent
        self.toast_manager = ToastManager(central)

        # Add shadow effect to main frame
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        central.setGraphicsEffect(shadow)

        # Main Horizontal Layout (Sidebar + Content)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget(self.session_manager)
        self.sidebar.session_selected.connect(self._load_session)
        self.sidebar.new_chat_requested.connect(self._start_new_chat)
        main_layout.addWidget(self.sidebar)

        # Content Area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 8)
        content_layout.setSpacing(8)
        
        main_layout.addWidget(content)

        # Header
        header = self._create_header()
        content_layout.addWidget(header)
        
        # Waveform (hidden by default)
        self.waveform = WaveformWidget()
        self.waveform.hide()
        content_layout.addWidget(self.waveform)

        # Chat (main content - full vertical space)
        self.chat = ChatWidget()
        content_layout.addWidget(self.chat)
        
        # Terminal Drawer (Hidden by default)
        self.terminal = TerminalDrawer()
        self.terminal.hide()
        content_layout.addWidget(self.terminal)

        # Input Area (Floating at bottom)
        self.chat.message_sent.connect(self._on_text_message)
        self.chat.voice_button_clicked.connect(self._on_voice_button)
        self.chat.voice_button_pressed.connect(self._on_voice_start)
        self.chat.voice_button_released.connect(self._on_voice_stop)
        content_layout.addWidget(self.chat, stretch=1)
        # Status label is now in header (created in _create_header)

    def _create_header(self) -> QWidget:
        """Создать заголовок — premium 2026"""
        header = QWidget()
        header.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(8)

        title = QLabel("Алёша")
        title.setStyleSheet(get_title_style())
        
        # Menu Button
        menu_btn = QPushButton()
        menu_btn.setFixedSize(32, 32)
        menu_btn.setIcon(IconFactory.get_icon("menu", COLORS["dark"]["text_secondary"], 20))
        menu_btn.setStyleSheet(get_control_button_style())
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.clicked.connect(lambda: self.sidebar.toggle())
        header_layout.addWidget(menu_btn)
        
        header_layout.addWidget(title)
        
        # Spacing after title
        header_layout.addSpacing(8)
        

        
        # Flexible spacer to push everything else to the right
        header_layout.addStretch(1)
        
        # Status chip (responsive - can shrink or disappear)
        self.status_label = QLabel("ОЖИДАНИЕ")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(get_status_label_style("idle"))
        
        # Allow status to shrink freely (Ignored = can shrink to 0)
        # We give it a stretch factor of 0 so it doesn't fight with the spacer
        status_sp = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.status_label.setSizePolicy(status_sp)
        self.status_label.setMinimumWidth(0)
        
        # Add with stretch 0 so it doesn't take extra space, just what it needs up to limit
        header_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Container for right-side controls (Live, Badge, Buttons)
        # Using a layout with higher priority or specific alignment
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        
        # Live Mode Button
        self.live_btn = QPushButton(" Live")
        self.live_btn.setIcon(IconFactory.get_icon("mic", COLORS["dark"]["text_muted"], 16))
        self.live_btn.setCheckable(True)
        self.live_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.live_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS["dark"]["text_muted"]};
                background: transparent;
                border: 1px solid {COLORS["dark"]["border"]};
                border-radius: 10px;
                padding: 4px 8px; /* Compact padding */
                font-weight: 600;
                font-family: 'Inter', sans-serif;
            }}
            QPushButton:hover {{
                background: {COLORS["dark"]["bg_glass_hover"]};
                color: {COLORS["dark"]["text_primary"]};
            }}
            QPushButton:checked {{
                background: {COLORS["dark"]["accent"]}33;
                border: 1px solid {COLORS["dark"]["accent"]};
                color: {COLORS["dark"]["accent"]};
            }}
        """)
        self.live_btn.clicked.connect(self._toggle_live_mode)
        # Prevent shrinking below content size
        self.live_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(self.live_btn)

        # Model Indicator Badge
        self.model_badge = ClickableLabel("3 Flash")
        self.model_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.model_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_badge.setStyleSheet(get_model_badge_style("Auto"))
        self.model_badge.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.model_badge.clicked.connect(self._show_model_menu)
        right_layout.addWidget(self.model_badge)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(2) # Tighter spacing
        
        for icon_name, handler, tooltip in [
            ("terminal", self._toggle_terminal, "Терминал"),
            ("settings", self._show_settings, "Настройки"),
            ("minus", self.showMinimized, "Свернуть"),
            ("x", self.hide, "Скрыть")
        ]:
            if icon_name == "terminal":
                # Special styling for terminal button maybe? For now standard.
                pass
                
            btn = QPushButton()
            btn.setFixedSize(28, 28) # Smaller buttons
            btn.setIcon(IconFactory.get_icon(icon_name, COLORS["dark"]["text_muted"], 18))
            btn.setStyleSheet(get_control_button_style())
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(handler)
            btn.setToolTip(tooltip)
            if icon_name == "x":
                btn.setObjectName("closeButton")
            controls_layout.addWidget(btn)
        
        right_layout.addLayout(controls_layout)
        
        # Add right container with priority
        header_layout.addWidget(right_container, 0, Qt.AlignmentFlag.AlignRight)
        
        return header

    def _toggle_terminal(self):
        """Переключить видимость терминала"""
        if self.terminal.isVisible():
            self.terminal.hide()
        else:
            self.terminal.show()
            # Scroll to bottom
            sb = self.terminal.text_area.verticalScrollBar()
            sb.setValue(sb.maximum())

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

    def _load_assistant(self):
        """Инициализировать ассистента асинхронно"""
        # Validate config first
        valid, errors = config.validate_config()
        if not valid:
            self.chat.add_message(
                "Ошибка конфигурации:\n" + "\n".join(errors), "system"
            )
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
            self.chat.add_message(
                "Не удалось загрузить модели:\n" + "\n".join(errors), "system"
            )
            self.status_label.setText("Ошибка загрузки")
            return

        self.status_label.setText("Готов")
        self.start_assistant()

    def start_assistant(self):
        """Запустить ассистента"""
        if self.assistant:
            self.assistant.start()
            self._check_first_run()
            # Start autosave timer (every 30 seconds)
            self.autosave_timer = QTimer(self)
            self.autosave_timer.timeout.connect(self._save_session)
            self.autosave_timer.start(30000)  # 30 seconds

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
                    self.chat.add_message(
                        "Привет, я Алёша. Что на этот раз?", "assistant"
                    )
            else:
                self.session_manager.create_session()
                self.chat.add_message("Привет, я Алёша. Что на этот раз?", "assistant")

    def show_onboarding(self):
        """Показать красивое графическое обучение"""
        # Close existing if present
        if hasattr(self, 'onboarding_overlay') and self.onboarding_overlay:
            self.onboarding_overlay.close()
            
        self.onboarding_overlay = OnboardingOverlay(self.centralWidget())
        self.onboarding_overlay.resize(self.centralWidget().size())
        self.onboarding_overlay.show()
        
        # When finished, show keyboard tips
        self.onboarding_overlay.finished.connect(lambda: QTimer.singleShot(500, self._show_shortcuts_overlay))

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
        # Map enum to style keys
        state_map = {
            AssistantState.IDLE: "idle",
            AssistantState.LISTENING: "listening",
            AssistantState.THINKING: "thinking",
            AssistantState.SPEAKING: "speaking",
            AssistantState.ERROR: "error",
        }
        
        # State texts (Uppercase for premium feel)
        state_texts = {
            AssistantState.IDLE: "ОЖИДАНИЕ",
            AssistantState.LISTENING: "СЛУШАЮ...",
            AssistantState.THINKING: "ДУМАЮ...",
            AssistantState.SPEAKING: "ГОВОРЮ",
            AssistantState.ERROR: "ОШИБКА",
        }

        self.status_label.setText(state_texts.get(state, ""))
        self.status_label.setStyleSheet(get_status_label_style(state_map.get(state, "idle")))

        # Show/hide typing indicator in chat
        if state == AssistantState.THINKING:
            self.chat.show_typing_indicator()
        else:
            self.chat._hide_typing_indicator()
            
        # Update Waveform
        is_active = state in [AssistantState.LISTENING, AssistantState.THINKING, AssistantState.SPEAKING]
        
        self.waveform.set_state(
            listening=(state == AssistantState.LISTENING),
            thinking=(state == AssistantState.THINKING),
            speaking=(state == AssistantState.SPEAKING)
        )
        
        if is_active:
            if not self.waveform.isVisible():
                self.waveform.show()
                self.waveform.start_animation()
        else:
            if self.waveform.isVisible():
                # self.waveform.hide() # Optional: keep visible but flat?
                # Better UX: Hide when idle to keep clean interface
                self.waveform.hide()
                self.waveform.stop_animation()

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
        """Обработка уровня громкости"""
        if self.waveform.isVisible():
            self.waveform.set_audio_level(level)

    @pyqtSlot(str, str)
    def _on_message(self, role: str, content: str):
        """Обработка нового сообщения"""
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
        original_style = self.status_label.styleSheet()
        # Flash the status label with warning color
        c = COLORS["dark"]
        flash_style = f"""
            color: {c["warning"]};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.05em;
            padding: 4px 10px;
            background: {c["warning_glow"]};
            border: 1px solid {c["warning"]};
            border-radius: 10px;
            text-transform: uppercase;
        """
        self.status_label.setText("ПРЕРВАНО")
        self.status_label.setStyleSheet(flash_style)

        # Reset after 800ms
        QTimer.singleShot(800, lambda: self.status_label.setStyleSheet(original_style))

    @pyqtSlot()
    def _on_wake_word(self):
        """Визуальная пульсация при обнаружении wake word"""
        # Pulsation effect with cyan glow
        c = COLORS["dark"]
        pulse_style = f"""
            color: {c["accent_light"]};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.05em;
            padding: 4px 10px;
            background: {c["accent_glow"]};
            border: 1px solid {c["accent"]};
            border-radius: 10px;
            text-transform: uppercase;
        """
        self.status_label.setText("АЛЁША")
        self.status_label.setStyleSheet(pulse_style)

        # First pulse - fade down
        QTimer.singleShot(
            150,
            lambda: self.status_label.setStyleSheet(
                pulse_style.replace("0.35", "0.15").replace("0.7", "0.4")
            ),
        )
        # Second pulse - fade up
        QTimer.singleShot(300, lambda: self.status_label.setStyleSheet(pulse_style))
        # Third pulse - fade down
        QTimer.singleShot(
            450,
            lambda: self.status_label.setStyleSheet(
                pulse_style.replace("0.35", "0.20").replace("0.7", "0.5")
            ),
        )

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
        # Store reference to prevent GC
        self.active_dialog = ConfirmationDialog(command, self.chat)
        self.active_dialog.confirmed.connect(self._confirm_command)
        self.active_dialog.cancelled.connect(self._cancel_command)

        # Add to chat layout
        self.chat.messages_layout.insertWidget(
            self.chat.messages_layout.count() - 1, self.active_dialog
        )

    def _confirm_command(self):
        """Подтвердить команду"""
        self.active_dialog = None
        if self.assistant:
            self.assistant.confirm_command()
            try:
                from src.audio import AudioPlayer

                AudioPlayer().play_success_sound()
            except Exception:
                pass

    def _cancel_command(self):
        """Отменить команду"""
        self.active_dialog = None
        if self.assistant:
            self.assistant.cancel_command()

    def _on_text_message(self, text: str):
        """Обработка текстового сообщения"""
        # Save to session history
        self.session_manager.add_message("user", text)

        if self.assistant:
            self.assistant.process_text(text)

    def _on_voice_button(self):
        """Handle voice button click - start voice recording (legacy toggle)"""
        if self.assistant:
            self.assistant.start_voice_recording()

    def _on_voice_start(self):
        """Push-to-talk: start recording on button press"""
        if self.assistant:
            # Play beep when starting voice recording
            try:
                from src.audio import AudioPlayer

                AudioPlayer().play_beep()
            except Exception:
                pass
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
                self.drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
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

            if (
                rect.width() >= self.minimumWidth()
                and rect.height() >= self.minimumHeight()
            ):
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
        # Resize overlay if active
        if hasattr(self, 'onboarding_overlay') and self.onboarding_overlay and self.onboarding_overlay.isVisible():
             self.onboarding_overlay.resize(self.centralWidget().size())
             
        # Note: We don't use setMask anymore as polygon masks create jagged edges
        # Rounded corners are handled by background_canvas drawing and CSS border-radius

    def _update_model_badge(self, mode: str, model_name: str):
        """Обновить индикатор модели"""
        if hasattr(self, "model_badge"):
            self.model_badge.setText(f"{mode}: {model_name}")
            self.model_badge.setStyleSheet(get_model_badge_style(mode))
            self.model_badge.show()  # Force visibility
            self.model_badge.update()  # Force repaint

    def _show_model_menu(self):
        """Показать меню выбора модели"""
        if not self.assistant:
            # Optional: show toast or just ignore if not loaded
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS["dark"]["bg_glass"]};
                border: 1px solid {COLORS["dark"]["border"]};
                color: {COLORS["dark"]["text_primary"]};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
                font-family: 'Ubuntu', sans-serif;
            }}
            QMenu::item:selected {{
                background-color: {COLORS["dark"]["accent"]}44;
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

    def _show_settings(self):
        """Показать окно настроек"""
        # Close existing if open
        if hasattr(self, 'settings_window') and self.settings_window:
            self.settings_window.close()
            
        self.settings_window = SettingsWindow(self)
        self.settings_window.settings_saved.connect(self._on_settings_saved)
        
        # Center relative to main window
        x = self.x() + (self.width() - self.settings_window.width()) // 2
        y = self.y() + (self.height() - self.settings_window.height()) // 2
        self.settings_window.move(x, y)
        self.settings_window.show()

    def _on_settings_saved(self):
        """Настройки сохранены — перезагрузка или уведомление"""
        self.toast_manager.show("Настройки сохранены", "check", "success")
        self.status_label.setText("Restart Required")

    def _load_session(self, session_id: str):
        """Загрузить сессию из истории"""
        if self.session_manager.load_session(session_id):
            messages = self.session_manager.get_messages()
            self.chat.load_messages(messages, animate=False)
            # Close sidebar on mobile-like view? No, keep it open or let user close.
            
    def _start_new_chat(self):
        """Начать новый чат"""
        self.session_manager.create_session()
        self.chat.clear_messages()
        self.chat.add_message("Привет, я Алёша. Что на этот раз?", "assistant")

    def _toggle_live_mode(self):
        """Переключение режима Live"""
        if not self.assistant:
            return

        if self.live_btn.isChecked():
            self.assistant.start_live_session()
        else:
            self.assistant.stop_live_session()

    def closeEvent(self, event):
        """Закрытие окна — минимизация в трей"""
        event.ignore()
        self.hide()
