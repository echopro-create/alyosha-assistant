"""
Alyosha Main Controller
Главный контроллер ассистента
"""
import threading
import time
import numpy as np
import logging
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal

from .llm import LLM

logger = logging.getLogger(__name__)
from .wake_word import WakeWordDetector
from .stt import STT
from .tts import TTS
from .memory import Memory
from .personal_memory import PersonalMemory
from .executor import CommandExecutor
from .audio import AudioStream, AudioRecorder, AudioPlayer, StreamPlayer
from .system import SystemControl
from .tools import Tools
import config


class AssistantState(Enum):
    """Состояния ассистента"""
    IDLE = auto()          # Ожидание wake word
    LISTENING = auto()      # Запись голоса
    THINKING = auto()       # Обработка запроса
    SPEAKING = auto()       # Воспроизведение ответа
    ERROR = auto()          # Ошибка


class Assistant(QObject):
    """Главный контроллер голосового ассистента"""
    
    # Signals for UI updates
    state_changed = pyqtSignal(AssistantState)
    audio_level_changed = pyqtSignal(float)
    message_received = pyqtSignal(str, str)  # role, content
    error_occurred = pyqtSignal(str)
    confirmation_required = pyqtSignal(str)  # command
    model_changed = pyqtSignal(str, str)     # mode (Auto/Manual), model_name
    barge_in_occurred = pyqtSignal()         # TTS was interrupted
    wake_word_detected = pyqtSignal()        # Wake word "Алёша" heard
    
    def __init__(self):
        super().__init__()
        
        self.state = AssistantState.IDLE
        
        # Core components
        self.llm = LLM()
        self.wake_word = WakeWordDetector()
        self.stt = STT()
        self.tts = TTS()
        self.memory = Memory()
        self.personal_memory = PersonalMemory()
        self.executor = CommandExecutor()
        
        # Audio components
        self.audio_stream = None
        self.audio_recorder = AudioRecorder()
        self.audio_player = AudioPlayer()
        self.stream_player = StreamPlayer()
        
        # Recording state
        self.is_recording = False
        self.silence_start = None
        self.max_silence = 2.0  # seconds
        self.min_recording = 0.5  # seconds
        self.recording_start = 0
        self.speaking_start = 0
        self.noise_floor = 0.1  # Initial noise floor assumption
        self.input_mode = "text"  # "text" or "voice" - controls TTS output
        
        # Threading
        self._running = False
        self._lock = threading.Lock()
    
    def load_models(self) -> tuple[bool, list[str]]:
        """Загрузить все модели"""
        errors = []
        
        # Load wake word detector
        if not self.wake_word.load():
            errors.append("Не удалось загрузить модель Vosk")
        
        # Load STT
        if not self.stt.load():
            errors.append("Не удалось загрузить модель Whisper")
        
        # Load TTS (optional, not critical)
        self.tts.load()  # Always returns True now, just logs if disabled
        
        return len(errors) == 0, errors
    
    def start(self):
        """Запустить ассистента"""
        self._running = True
        
        # Start audio stream
        self.audio_stream = AudioStream(self._audio_callback)
        self.audio_stream.start()
        
        self._set_state(AssistantState.IDLE)
    
    def stop(self):
        """Остановить ассистента"""
        self._running = False
        
        if self.audio_stream:
            self.audio_stream.stop()
        
        self.audio_player.stop()
    
    def process_text(self, text: str):
        """Обработать текстовый запрос (text mode - no TTS)"""
        self.input_mode = "text"
        threading.Thread(target=self._process_request, args=(text,), daemon=True).start()
    
    def start_voice_recording(self):
        """Start voice recording manually (from voice button)"""
        if self.state == AssistantState.IDLE:
            logger.info("Voice button pressed - starting recording")
            self._start_listening()
        elif self.state == AssistantState.LISTENING:
            # Already listening, stop recording (toggle behavior)
            logger.info("Voice button pressed while listening - stopping")
            self._stop_listening()
    
    def stop_voice_recording(self):
        """Stop voice recording manually (push-to-talk release)"""
        if self.state == AssistantState.LISTENING:
            logger.info("Voice button released - stopping recording")
            self._stop_listening()
    
    def confirm_command(self):
        """Подтвердить опасную команду"""
        success, output = self.executor.confirm_pending()
        if success:
            self.message_received.emit("system", f"Команда выполнена:\n{output}")
        else:
            self.message_received.emit("system", output)
    
    def cancel_command(self):
        """Отменить опасную команду"""
        self.executor.cancel_pending()
        self.message_received.emit("system", "Команда отменена.")
    
    def _set_state(self, state: AssistantState):
        """Изменить состояние"""
        with self._lock:
            self.state = state
        self.state_changed.emit(state)
    
    def _audio_callback(self, audio_chunk: np.ndarray, level: float):
        """Callback для обработки аудио"""
        if not self._running:
            return
        
        # Emit audio level for visualization
        self.audio_level_changed.emit(level)
        
        current_state = self.state
        
        # Check VAD lazily
        is_speech = False
        if getattr(self, 'wake_word', None) and getattr(self.wake_word, 'vad', None):
             is_speech = self.wake_word.vad.is_speech(audio_chunk)
        elif getattr(self, 'vad', None):
             is_speech = self.vad.is_speech(audio_chunk)
        else:
             from src.vad import VoiceActivityDetector
             self.vad = VoiceActivityDetector()
             is_speech = self.vad.is_speech(audio_chunk)

        if current_state == AssistantState.IDLE:
            # Check for wake word
            if self.wake_word.detect(audio_chunk):
                self.wake_word_detected.emit()  # Notify UI for pulsation effect
                self._start_listening()
        
        elif current_state == AssistantState.SPEAKING:
            # Barge-in logic (VAD based)
            if self.speaking_start and (time.time() - self.speaking_start < 1.0):
                return
            
            if is_speech:
                logger.info("Barge-in detected (Human Voice), stopping TTS")
                self.barge_in_occurred.emit()  # Notify UI for visual feedback
                self.stop_speaking()
                self._start_listening()
        
        elif current_state == AssistantState.LISTENING:
            self.audio_recorder.add_chunk(audio_chunk)
            current_level = self.audio_recorder.get_audio_level(audio_chunk)
            
            # Adaptive Noise Cancellation Logic 2026
            # Update noise floor (slowly adapt to environment)
            self.noise_floor = self.noise_floor * 0.99 + current_level * 0.01
            
            # Dynamic threshold: meaningful jump above floor
            threshold = self.noise_floor + 0.15 
            
            # Debug
            if time.time() % 2 < 0.2:
                 logger.debug(f"Lvl:{current_level:.2f} Floor:{self.noise_floor:.2f} Thr:{threshold:.2f}")

            # Silence detection
            if current_level < threshold:
                if self.silence_start is None:
                    self.silence_start = time.time()
                
                # Dynamic silence duration: faster stop if we have enough audio
                duration = time.time() - self.recording_start
                silence_duration = time.time() - self.silence_start
                
                required_silence = 1.5 if duration < 3.0 else 0.8 # Stop faster if long sentence
                
                if silence_duration > required_silence:
                    if duration > self.min_recording:
                        logger.info(f"Silence detected ({silence_duration:.1f}s), stopping.")
                        self._stop_listening()
            else:
                self.silence_start = None
                
            # Hard timeout 10s
            # Hard timeout 10s
            if time.time() - self.recording_start > 10.0:
                 self._stop_listening()

    def _start_listening(self):
        """Начать запись (voice mode - TTS enabled)"""
        self.input_mode = "voice"
        self._set_state(AssistantState.LISTENING)
        self.audio_recorder.start_recording()
        self.silence_start = None
        self.recording_start = time.time()
    
    def _stop_listening(self):
        """Остановить запись и обработать"""
        audio = self.audio_recorder.stop_recording()
        self._set_state(AssistantState.THINKING)
        
        # Process in background thread
        threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()
    
    def _process_audio(self, audio: np.ndarray):
        """Обработать записанное аудио"""
        if len(audio) == 0:
            self._set_state(AssistantState.IDLE)
            return
        
        # Transcribe
        text = self.stt.transcribe(audio)
        
        if not text.strip():
            self._set_state(AssistantState.IDLE)
            return
        
        # Emit user message
        self.message_received.emit("user", text)
        
        # Process request
        self._process_request(text)
    
    def _process_request(self, text: str, image_path: str = ""):
        """Обработка запроса с поддержкой Thinking Loop (итеративное использование инструментов)"""
        self._set_state(AssistantState.THINKING)
        self.memory.add_user_message(text)
        
        attempts = 0
        max_attempts = 3
        current_text = text
        current_image = image_path
        
        try:
            while attempts < max_attempts:
                attempts += 1
                
                # Get response from LLM with user profile
                context = self.memory.get_context()
                user_profile = self.personal_memory.get_summary_for_llm()
                response = self.llm.chat(current_text, context, current_image, user_profile)
                
                # Update UI model indicator
                mode = "Manual" if self.llm.forced_model else "Auto"
                model_disp = "3 Pro" if "pro" in self.llm.active_model else "3 Flash"
                self.model_changed.emit(mode, model_disp)

                message = response.get("message", "")
                command = response.get("command", "")
                
                if not message and not command:
                    if attempts == 1:
                        self.message_received.emit("assistant", "Я не знаю, что на это ответить.")
                    break
                
                # Silent Mode: If the assistant sends a command WITHOUT a message,
                # it means he's "thinking" or "gathering info".
                is_silent = not message.strip()
                
                # Check for "Silent Data Tools" (explicitly defined)
                data_tools = ["tool:weather", "tool:currency", "tool:calculate"]
                is_data_tool = any(command.startswith(tool) for tool in data_tools)
                
                if is_silent or is_data_tool:
                    # SILENT EXECUTION
                    logger.info(f"Thinking Loop: Silent execution of {command}")
                    tool_output = self._execute_tool(command) if command.startswith("tool:") else self.executor.execute(command)[1]
                    
                    # Feed result back to memory for the next iteration
                    self.memory.add_system_message(f"Результат {command}: {tool_output}")
                    
                    # Continue thinking with the new info
                    current_text = "Инструмент выполнен. Теперь дай окончательный ответ пользователю на основе полученных данных."
                    current_image = "" 
                    continue

                # Vision Flow (also iterative)
                if command == "tool:vision":
                    self.message_received.emit("system", "Анализирую экран...")
                    screenshot_path = SystemControl.take_screenshot()
                    
                    if screenshot_path:
                        # Continue thinking with the image
                        current_text = "Вот скриншот экрана. Проанализируй его и ответь на мой запрос."
                        current_image = screenshot_path
                        # Note: we don't 'continue' here because we want the next 'chat' call to handle it
                        # But wait, we DO need to call llm.chat again.
                        attempts -= 1 # Don't count vision as a full thought attempt
                        # Since we want to pass current_image to next loop
                        continue
                    else:
                        self.message_received.emit("assistant", "Не удалось сделать скриншот.")
                        break

                # If we reach here, it's either an Action tool (bash, browse, volume) or just a message
                
                # Add to memory
                self.memory.add_assistant_message(message, command)
                
                # Emit assistant message
                if message and message.strip():
                    self.message_received.emit("assistant", message)
                
                # Execute Action command if present
                if command:
                    # Non-silent tools
                    if command.startswith("tool:"):
                        # notify, volume, browse
                        tool_output = self._execute_tool(command)
                        if tool_output:
                            self.message_received.emit("system", f"Инструмент:\n{tool_output}")
                    else:
                        # Regular system command
                        is_valid, validation_msg = self.executor.validate(command)
                        
                        if not is_valid:
                            if self.executor.pending_command:
                                self.confirmation_required.emit(command)
                            else:
                                self.message_received.emit("system", validation_msg)
                        else:
                            success, output = self.executor.execute(command)
                            # Track command in personal memory for statistics
                            self.personal_memory.track_command(command)
                            if output:
                                self.message_received.emit("system", f"Результат:\n{output}")
                
                # Finalize request
                break
            
            # Speak final response
            if message:
                self._speak(message)
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.error_occurred.emit(f"Ошибка обработки: {str(e)}")
            self._set_state(AssistantState.IDLE)

    def _execute_tool(self, command: str) -> str:
        """Выполнить внутренний инструмент"""
        try:
            parts = command.replace("tool:", "").strip().split(" ", 1)
            tool_name = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            if tool_name == "calculate":
                return f"Результат: {Tools.calculate(args)}"
            elif tool_name == "browse":
                return Tools.open_browser(args)
            elif tool_name == "weather":
                return Tools.get_weather(args)
            elif tool_name == "currency":
                # Expecting "BASE TARGET"
                parts = args.split(" ")
                base = parts[0] if len(parts) > 0 else "EUR"
                target = parts[1] if len(parts) > 1 else "USD"
                return Tools.get_currency(base, target)
            elif tool_name == "notify":
                if "|" in args:
                    title, msg = args.split("|", 1)
                else:
                    title, msg = "Алёша", args
                SystemControl.notify(title.strip(), msg.strip())
                return "Уведомление отправлено"
            elif tool_name == "volume":
                try:
                    vol = int(args.replace("%", "").strip())
                    SystemControl.set_volume(vol)
                    return f"Громкость установлена на {vol}%"
                except ValueError:
                    return "Ошибка: укажите число для громкости"
            else:
                return f"Неизвестный инструмент: {tool_name}"
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return f"Ошибка инструмента: {e}"

    def _speak(self, text: str):
        """Воспроизвести ответ (only if input was voice)"""
        if not text.strip():
            self._set_state(AssistantState.IDLE)
            return
        
        # Only speak if input was via voice (wake word or voice button)
        if self.input_mode != "voice":
            logger.info("Text input mode - skipping TTS")
            self._set_state(AssistantState.IDLE)
            return
        
        self._set_state(AssistantState.SPEAKING)
        self.speaking_start = time.time()
        logger.info(f"Speaking: {text[:30]}...")
        
        try:
            # Generate full audio (more reliable than streaming)
            audio_bytes = self.tts.synthesize(text)
            
            if audio_bytes:
                # Play using ffplay (handles both WAV and MP3)
                audio_format = self.tts.output_format  # "wav" or "mp3"
                self._play_audio(audio_bytes, audio_format)
            else:
                logger.warning("No audio generated")

        except Exception as e:
            logger.error(f"Speech error: {e}")
        
        self._set_state(AssistantState.IDLE)
        logger.info("Finished speaking")

    def stop_speaking(self):
        """Остановить речь"""
        if hasattr(self, 'current_playback_process') and self.current_playback_process:
            try:
                self.current_playback_process.terminate()
                self.current_playback_process.wait(timeout=0.2)
            except Exception:
                self.current_playback_process.kill()
            self.current_playback_process = None
        self._set_state(AssistantState.IDLE)
    
    def _play_audio(self, audio_bytes: bytes, audio_format: str = "wav"):
        """Воспроизвести аудио (WAV или MP3, прерываемо)"""
        try:
            import tempfile
            import subprocess
            
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            # Use Popen instead of run to be non-blocking/interruptible
            self.current_playback_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for finish loop (blocking this thread but checking for interruption)
            while self.current_playback_process and self.current_playback_process.poll() is None:
                if self.state != AssistantState.SPEAKING:
                    # External interruption
                    if self.current_playback_process:
                        self.current_playback_process.terminate()
                    break
                time.sleep(0.05)
                
            self.current_playback_process = None
            
            # Cleanup temp file
            try:
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
                
        except Exception as e:
            logger.error(f"Playback error: {e}")
    def set_forced_model(self, mode: str):
        """
        Установить принудительную модель
        mode: "auto", "flash", or "pro"
        """
        if mode == "auto":
            self.llm.forced_model = None
        else:
            self.llm.forced_model = mode
        
        # Emit initial signal for UI update
        mode_str = "Auto" if not self.llm.forced_model else "Manual"
        model_disp = "3 Pro" if mode == "pro" else "3 Flash"
        self.model_changed.emit(mode_str, model_disp)
