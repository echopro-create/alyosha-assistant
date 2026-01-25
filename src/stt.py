"""
Alyosha Speech-to-Text
Распознавание речи с помощью Whisper
"""
import numpy as np
from faster_whisper import WhisperModel
import tempfile
import wave
import config


class STT:
    """Speech-to-Text с использованием faster-whisper"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
    
    def load(self) -> bool:
        """Загрузить модель Whisper"""
        try:
            # Use configurable model size (default: small for better accuracy)
            model_size = config.WHISPER_MODEL_SIZE
            print(f"[STT] Loading Whisper model: {model_size}")
            
            self.model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"
            )
            self.is_loaded = True
            print(f"[STT] Whisper {model_size} loaded successfully")
            
            # Warmup: transcribe a short silent sample to pre-compile
            try:
                warmup_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
                list(self.model.transcribe(warmup_audio, language="ru", vad_filter=True))
                print("[STT] Model warmup complete")
            except Exception:
                pass  # Warmup is optional
            
            return True
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            return False
    
    def transcribe(self, audio: np.ndarray, sample_rate: int = None) -> str:
        """
        Преобразовать аудио в текст
        
        Args:
            audio: Аудио данные (int16 или float32)
            sample_rate: Частота дискретизации
        
        Returns:
            Распознанный текст
        """
        if not self.is_loaded:
            return ""
        
        sr = sample_rate or config.SAMPLE_RATE
        
        try:
            # Convert to float32 if needed
            if audio.dtype == np.int16:
                audio_float = audio.astype(np.float32) / 32768.0
            else:
                audio_float = audio.astype(np.float32)
            
            # Save to temporary WAV file
            print("[STT] Starting transcription...")
            
            # Transcribe with SPEED-OPTIMIZED settings for 2026
            segments, info = self.model.transcribe(
                audio_float, 
                beam_size=1,  # Was 5 — greedy decoding is much faster
                language="ru",
                vad_filter=False,  # Rely on assistant.py silence detection
                condition_on_previous_text=False,
                temperature=0.0,
                compression_ratio_threshold=2.4,  # Skip bad segments faster
                log_prob_threshold=-1.0,  # Accept all reasonable transcriptions
                no_speech_threshold=0.6,  # Higher = faster detection of silence
            )
            
            # Combine segments
            text = " ".join([segment.text for segment in segments]).strip()
            if text:
                print(f"[STT] Transcribed: '{text}'")
            else:
                 print(f"[STT] Empty transcription")
                
            return text
            
        except Exception as e:
            print(f"STT Error: {e}")
            return ""
    
    def _save_wav(self, path: str, audio: np.ndarray, sample_rate: int):
        """Сохранить аудио в WAV файл"""
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
