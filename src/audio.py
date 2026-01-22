"""
Alyosha Audio Utilities
Запись и воспроизведение аудио
"""
import numpy as np
import sounddevice as sd
from collections import deque
import config


class AudioRecorder:
    """Запись аудио с микрофона"""
    
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.channels = config.CHANNELS
        self.chunk_size = config.CHUNK_SIZE
        self.is_recording = False
        self.audio_buffer = []
    
    def start_recording(self):
        """Начать запись"""
        self.is_recording = True
        self.audio_buffer = []
    
    def stop_recording(self) -> np.ndarray:
        """Остановить запись и вернуть аудио"""
        self.is_recording = False
        if self.audio_buffer:
            return np.concatenate(self.audio_buffer)
        return np.array([], dtype=np.float32)
    
    def add_chunk(self, chunk: np.ndarray):
        """Добавить чанк аудио в буфер"""
        if self.is_recording:
            self.audio_buffer.append(chunk.copy())
    
    def get_audio_level(self, chunk: np.ndarray) -> float:
        """Получить уровень громкости (0-1)"""
        if len(chunk) == 0:
            return 0.0
        # RMS of int16
        rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
        # Normalize int16 (0-32768) to float (0-1)
        normalized_rms = rms / 32768.0
        # Scale for sensitivity (silence is usually < 0.01 normalized)
        return min(1.0, normalized_rms * 5.0)


import subprocess

class AudioPlayer:
    """Воспроизведение аудио"""
    
    def __init__(self):
        self.sample_rate = 44100  # ElevenLabs default
    
    def play(self, audio_data: np.ndarray, sample_rate: int = None):
        """Воспроизвести аудио"""
        sr = sample_rate or self.sample_rate
        sd.play(audio_data, sr)
        sd.wait()
    
    def play_bytes(self, audio_bytes: bytes, sample_rate: int = 44100):
        """Воспроизвести аудио из bytes"""
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        self.play(audio_data, sample_rate)
    
    def stop(self):
        """Остановить воспроизведение"""
        sd.stop()

    def play_beep(self):
        """Воспроизвести системный звук (бип)"""
        # Generate 440Hz sine wave for 0.2s
        duration = 0.2
        frequency = 880  # Hz (High pitch beep)
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        note = np.sin(frequency * t * 2 * np.pi) * 0.3  # 0.3 amplitude
        
        # Apply fade out to avoid clicking
        fade_out = np.linspace(1, 0, 1000)
        note[-1000:] *= fade_out
        
        # Play asynchronously
        sd.play(note.astype(np.float32), self.sample_rate)
    
    def play_send_sound(self):
        """Воспроизвести звук отправки сообщения (короткий свуш)"""
        duration = 0.1
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Rising swoosh: frequency sweep 400 -> 800 Hz
        freq_start, freq_end = 400, 800
        freq = np.linspace(freq_start, freq_end, len(t))
        note = np.sin(np.cumsum(freq) * 2 * np.pi / self.sample_rate) * 0.2
        
        # Apply envelope (quick attack, slow decay)
        envelope = np.exp(-t * 20)
        note *= envelope
        
        sd.play(note.astype(np.float32), self.sample_rate)
    
    def play_receive_sound(self):
        """Воспроизвести звук получения сообщения (нежный колокольчик)"""
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Two-tone chime: 523 Hz (C5) + 659 Hz (E5)
        note = (np.sin(523 * t * 2 * np.pi) + np.sin(659 * t * 2 * np.pi)) * 0.15
        
        # Apply decay envelope
        envelope = np.exp(-t * 15)
        note *= envelope
        
        sd.play(note.astype(np.float32), self.sample_rate)
    
    def play_click_sound(self):
        """Тихий клик при нажатии на элементы интерфейса"""
        duration = 0.03
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Short tick: 1200 Hz
        note = np.sin(1200 * t * 2 * np.pi) * 0.08
        envelope = np.exp(-t * 80)
        note *= envelope
        
        sd.play(note.astype(np.float32), self.sample_rate)
    
    def play_success_sound(self):
        """Звук успешного выполнения (восходящий аккорд)"""
        duration = 0.25
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Major chord: C5-E5-G5 (523, 659, 784 Hz)
        note = (
            np.sin(523 * t * 2 * np.pi) * 0.12 +
            np.sin(659 * t * 2 * np.pi) * 0.10 +
            np.sin(784 * t * 2 * np.pi) * 0.08
        )
        envelope = np.exp(-t * 8)
        note *= envelope
        
        sd.play(note.astype(np.float32), self.sample_rate)
    
    def play_error_sound(self):
        """Звук ошибки (низкий гудок)"""
        duration = 0.2
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Low buzz: 200 Hz with slight modulation
        note = np.sin(200 * t * 2 * np.pi) * 0.15
        note += np.sin(220 * t * 2 * np.pi) * 0.05  # Slight dissonance
        envelope = np.exp(-t * 10)
        note *= envelope
        
        sd.play(note.astype(np.float32), self.sample_rate)


class StreamPlayer:
    """Потоковое воспроизведение аудио (MP3/PCM) через ffplay"""
    
    def __init__(self):
        self.process = None
        
    def start(self):
        """Запустить процесс плеера"""
        self.stop() # Ensure previous is stopped
        try:
            self.process = subprocess.Popen(
                ["ffplay", "-f", "mp3", "-nodisp", "-autoexit", "-loglevel", "info", "-"],
                stdin=subprocess.PIPE,
                stderr=None, # Show stderr for debugging
                stdout=subprocess.DEVNULL
            )
            print("[AUDIO] StreamPlayer started")
        except FileNotFoundError:
            print("ffplay not found. Please install ffmpeg.")
            
    def write(self, data: bytes):
        """Записать данные в поток"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data)
                self.process.stdin.flush()
            except BrokenPipeError:
                pass
            except Exception as e:
                print(f"Stream write error: {e}")
    
    def close_input(self):
        """Закрыть входной поток (EOF)"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.close()
            except Exception:
                pass

    def wait(self):
        """Ожидать завершения воспроизведения"""
        if self.process:
            try:
                self.process.wait()
            except Exception:
                pass

    def stop(self):
        """Остановить воспроизведение"""
        if self.process:
            self.close_input()
            try:
                self.process.terminate()
                self.process.wait(timeout=0.5)
            except Exception:
                self.process.kill()
            self.process = None


class AudioStream:
    """Потоковый захват аудио для wake-word detection"""
    
    def __init__(self, callback):
        self.sample_rate = config.SAMPLE_RATE
        self.channels = config.CHANNELS
        self.chunk_size = config.CHUNK_SIZE
        self.callback = callback
        self.stream = None
        self.level_buffer = deque(maxlen=10)
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback для аудио потока"""
        if status:
            print(f"Audio status: {status}")
        
        # Calculate level for visualization
        audio = indata[:, 0] if len(indata.shape) > 1 else indata
        rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        level = rms / 32768.0
        self.level_buffer.append(level)
        
        # Debug: показать уровень каждые 50 чанков
        if not hasattr(self, '_chunk_count'):
            self._chunk_count = 0
        self._chunk_count += 1
        # Debug disabled in production
        # if self._chunk_count % 50 == 0:
        #     print(f"[AUDIO] Chunk #{self._chunk_count}, raw_rms: {rms:.0f}, level: {level:.4f}")
        
        # Call user callback
        self.callback(audio.copy(), self.get_average_level())
    
    def get_average_level(self) -> float:
        """Получить усреднённый уровень громкости"""
        if not self.level_buffer:
            return 0.0
        # Scale up slightly for visualization responsiveness
        return min(1.0, np.mean(self.level_buffer) * 5.0)
    
    def start(self):
        """Запустить аудио поток"""
        # Starting audio stream silently
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.chunk_size,
            dtype=np.int16,
            callback=self._audio_callback
        )
        self.stream.start()
        # Audio stream started successfully
    
    def stop(self):
        """Остановить аудио поток"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
