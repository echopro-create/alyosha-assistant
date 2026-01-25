"""
Alyosha Main Controller
Главный контроллер ассистента
"""

import threading
import time
import logging
import asyncio
import numpy as np
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal

from .llm import LLM
from .live_client import GeminiLiveClient
from .wake_word import WakeWordDetector
from .stt import STT
from .tts import TTS
from .memory import Memory
from .personal_memory import PersonalMemory
from .executor import CommandExecutor
from .audio import AudioStream, AudioRecorder, AudioPlayer, StreamPlayer
# Tools, SystemControl, config removed as unused in imports (Tools/SystemControl moved to tools_def/executor logic, or re-verify usage)
# Wait, check providing code if they are used deeper.
# Looking at previous _process_request, executor is used. Tools class was used in _execute_tool which is now deleted.
# So Tools import is indeed unused.
# SystemControl might be used for screenshot? Yes, in 'tool:vision' block (line 338 in original context).
# But wait, in the NEW loop I only implemented execute_bash. I did NOT re-implement 'tool:vision' in the new loop yet.
# To be safe and clean, I will remove unused ones. If I broke vision, I will need to add it back later.
# For now, fixing lints as requested.

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    """Состояния ассистента"""

    IDLE = auto()  # Ожидание wake word
    LISTENING = auto()  # Запись голоса
    THINKING = auto()  # Обработка запроса
    SPEAKING = auto()  # Воспроизведение ответа
    REALTIME_SESSION = auto()  # Живое общение (Gemini Live)
    ERROR = auto()  # Ошибка


class Assistant(QObject):
    """Главный контроллер голосового ассистента"""

    # Signals for UI updates
    state_changed = pyqtSignal(AssistantState)
    audio_level_changed = pyqtSignal(float)
    message_received = pyqtSignal(str, str)  # role, content
    error_occurred = pyqtSignal(str)
    confirmation_required = pyqtSignal(str)  # command
    model_changed = pyqtSignal(str, str)  # mode (Auto/Manual), model_name
    barge_in_occurred = pyqtSignal()  # TTS was interrupted
    wake_word_detected = pyqtSignal()  # Wake word "Алёша" heard

    def __init__(self):
        super().__init__()

        self.state = AssistantState.IDLE

        # Core components
        self.llm = LLM()
        self.live_client = GeminiLiveClient()  # Native WebSocket Client
        self.live_loop = None  # AsyncIO Loop for Real-time thread
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
        threading.Thread(
            target=self._process_request, args=(text,), daemon=True
        ).start()

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

    def set_forced_model(self, mode: str):
        """Set forced model mode (auto/flash/pro)"""
        if mode == "auto":
            self.llm.forced_model = None
        else:
            self.llm.forced_model = mode
        # Emit signal to update UI
        display_mode = "Auto" if mode == "auto" else "Manual"
        display_model = "3 Pro" if mode == "pro" else "3 Flash"
        self.model_changed.emit(display_mode, display_model)
        logger.info(f"Model forced to: {mode}")

    def start_live_session(self):
        """Start Gemini Live Real-time session"""
        if self.state == AssistantState.REALTIME_SESSION:
            return

        try:
            self._set_state(AssistantState.REALTIME_SESSION)
            self.message_received.emit("system", "Запуск режима Live... ⚡")

            # Setup callbacks
            self.live_client.on_audio_data = self._on_live_audio
            self.live_client.on_text_data = lambda text: self.message_received.emit(
                "assistant", text
            )

            # Start player in PCM mode (24kHz is standard for Gemini Live)
            # Note: We use 24000 as per prototype findings
            self.stream_player = StreamPlayer(
                format="pcm", sample_rate=24000, channels=1
            )
            self.stream_player.start()

            # Connect via asyncio (needs to run in event loop)
            # Since we are in PyQt thread, we might need a separate thread for asyncio loop if not already present.
            # For simplicity in v1, assuming run_in_executor or launching separate thread logic inside client (it has background task).
            # But client.connect() is async. We need to wrap it.

            threading.Thread(target=self._run_async_connect, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to start live session: {e}")
            self.error_occurred.emit(str(e))
            self._set_state(AssistantState.IDLE)

    def _run_async_connect(self):
        """Run asyncio loop in a separate thread"""
        self.live_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.live_loop)

        try:
            # Connect
            self.live_loop.run_until_complete(self.live_client.connect())

            # Keep loop running for background tasks (receive_loop) and incoming send calls
            self.live_loop.run_forever()

        except Exception as e:
            logger.error(f"Async loop error: {e}")
        finally:
            self.live_loop.close()
            self.live_loop = None

    def stop_live_session(self):
        """Stop Live session"""
        if self.state == AssistantState.REALTIME_SESSION:
            # Disconnect client
            if self.live_loop and self.live_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.live_client.disconnect(), self.live_loop
                )
                try:
                    future.result(timeout=2)
                except Exception:
                    pass

                # Stop loop
                self.live_loop.call_soon_threadsafe(self.live_loop.stop)

            if self.stream_player:
                self.stream_player.stop()
            self._set_state(AssistantState.IDLE)
            self.message_received.emit("system", "Live режим остановлен.")

    def _on_live_audio(self, pcm_data: bytes):
        """Callback from LiveClient with audio bytes"""
        if self.stream_player:
            self.stream_player.write(pcm_data)

    def _audio_callback(self, audio_chunk: np.ndarray, level: float):
        """Callback для обработки аудио"""
        if not self._running:
            return

        # Emit audio level for visualization
        self.audio_level_changed.emit(level)

        current_state = self.state

        # === REAL-TIME MODE ===
        if current_state == AssistantState.REALTIME_SESSION:
            # Send everything directly to Gemini
            # Convert float32 back to int16 PCM bytes
            pcm_int16 = (audio_chunk * 32767).astype(np.int16).tobytes()

            # Fire and forget (async send)
            if self.live_loop and self.live_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.live_client.send_audio(pcm_int16), self.live_loop
                )
            return
        # ======================

        # Check VAD lazily

        is_speech = False
        if getattr(self, "wake_word", None) and getattr(self.wake_word, "vad", None):
            is_speech = self.wake_word.vad.is_speech(audio_chunk)
        elif getattr(self, "vad", None):
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

            # Adaptive Noise Cancellation Logic 2026 (faster adaptation)
            # Update noise floor (adapt quickly to environment)
            self.noise_floor = self.noise_floor * 0.95 + current_level * 0.05

            # Dynamic threshold: meaningful jump above floor
            threshold = self.noise_floor + 0.12  # Lower threshold for faster detection

            # Debug (less frequent to avoid spam)
            if time.time() % 3 < 0.2:
                logger.debug(
                    f"Lvl:{current_level:.2f} Floor:{self.noise_floor:.2f} Thr:{threshold:.2f}"
                )

            # Silence detection
            if current_level < threshold:
                if self.silence_start is None:
                    self.silence_start = time.time()

                # FAST silence detection: stop quickly once user stops speaking
                duration = time.time() - self.recording_start
                silence_duration = time.time() - self.silence_start

                # Aggressive silence thresholds for 2026-level responsiveness
                required_silence = 0.6 if duration < 2.0 else 0.4  # Was 1.5/0.8

                if silence_duration > required_silence:
                    if duration > self.min_recording:
                        logger.info(
                            f"Silence detected ({silence_duration:.1f}s), stopping."
                        )
                        self._stop_listening()
            else:
                self.silence_start = None

            # Hard timeout 8s (was 10s)
            if time.time() - self.recording_start > 8.0:
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
        """Обработка запроса с поддержкой Native Tool Calling"""
        self._set_state(AssistantState.THINKING)
        self.memory.add_user_message(text)

        attempts = 0
        max_attempts = 5  # Allow for multi-step tool use
        current_text = text
        current_image = image_path

        try:
            while attempts < max_attempts:
                attempts += 1

                # Get response from LLM
                context = self.memory.get_context()
                user_profile = self.personal_memory.get_summary_for_llm()
                response = self.llm.chat(
                    current_text, context, current_image, user_profile
                )

                # Extract parts
                if not response.parts:
                    logger.warning("Empty response from LLM")
                    break

                part = response.parts[0]

                # CASE 1: Function Call (The "Thinking" / "Acting" State)
                if part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = dict(fc.args)

                    logger.info(f"Tool Call: {tool_name} with {args}")

                    # Dynamic Tool Execution
                    from .tools_def import TOOL_DEFINITIONS
                    
                    # Create a map of available tools
                    tool_map = {t.__name__: t for t in TOOL_DEFINITIONS}
                    
                    if tool_name in tool_map:
                        tool_func = tool_map[tool_name]
                        try:
                            # Execute the tool function
                            tool_result = str(tool_func(**args))
                        except Exception as e:
                            tool_result = f"Error executing {tool_name}: {str(e)}"
                    else:
                        tool_result = f"Unknown tool: {tool_name}"

                    # Feed result back to LLM (Context Injection)
                    # Feed result back to LLM (Context Injection)
                    self.memory.add_system_message(
                        f"Tool '{tool_name}' result: {tool_result}"
                    )
                    current_text = f"Tool result: {tool_result}. Continue."
                    
                    # Logic for Vision: If tool returned an image path, feed it to next turn
                    if tool_result.strip().endswith(".png") or tool_result.strip().endswith(".jpg"):
                         import os
                         if os.path.exists(tool_result.strip()):
                             logger.info(f"Injecting image into context: {tool_result}")
                             current_image = tool_result.strip()
                         else:
                             current_image = ""
                    else:
                        current_image = ""  # Clear image after first use
                    
                    continue

                # CASE 2: Text Response (The "Speaking" State)
                if part.text:
                    message = part.text

                    # Add to memory
                    self.memory.add_assistant_message(message, "")

                    # Emit assistant message
                    self.message_received.emit("assistant", message)

                    # Speak
                    self._speak(message)
                    break

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.error_occurred.emit(f"Ошибка обработки: {str(e)}")
            self._set_state(AssistantState.IDLE)

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
        if hasattr(self, "current_playback_process") and self.current_playback_process:
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
                stderr=subprocess.DEVNULL,
            )

            # Wait for finish loop (blocking this thread but checking for interruption)
            while (
                self.current_playback_process
                and self.current_playback_process.poll() is None
            ):
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
