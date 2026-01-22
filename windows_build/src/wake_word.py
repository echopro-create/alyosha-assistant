"""
Alyosha Wake Word Detection
Детекция слова "Алёша" с помощью Vosk
"""
import json
import numpy as np
import subprocess
from vosk import Model, KaldiRecognizer
import config


class WakeWordDetector:
    """Детекция wake word 'Алёша' с помощью Vosk"""
    
    def __init__(self):
        self.model = None
        self.recognizer = None
        self.wake_word = config.WAKE_WORD.lower()
        self.is_loaded = False
        self.partial_buffer = ""
    
    def load(self) -> bool:
        """Загрузить модель Vosk"""
        try:
            model_path = str(config.VOSK_MODEL_PATH)
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, config.SAMPLE_RATE)
            self.recognizer.SetWords(True)
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Failed to load Vosk model: {e}")
            return False
    
    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Проверить наличие wake word в аудио чанке
        
        Args:
            audio_chunk: Аудио данные (int16)
        
        Returns:
            True если wake word обнаружен
        """
        if not self.is_loaded:
            return False
        
        try:
            # Convert to bytes
            audio_bytes = audio_chunk.tobytes()
            
            # Debug counter
            if not hasattr(self, '_detect_count'):
                self._detect_count = 0
                self._loud_chunks = 0
            self._detect_count += 1
            
            # VAD Check (WebRTC)
            # Only process if human voice is detected
            if not getattr(self, 'vad', None):
                from src.vad import VoiceActivityDetector
                self.vad = VoiceActivityDetector()
            
            if not self.vad.is_speech(audio_chunk):
                # No speech -> skip Vosk
                return False
            
            # Debug heartbeat
            print(".", end="", flush=True)

            # Основной метод: Vosk
            has_result = self.recognizer.AcceptWaveform(audio_bytes)
            
            if has_result:
                try:
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    if text:
                        print(f"[VOSK] Распознано: {text}")
                    
                    if self._contains_wake_word(text):
                        print(f"[WAKE] Wake word обнаружен!")
                        self._play_beep()
                        self.reset()
                        return True
                except json.JSONDecodeError:
                    pass
            else:
                # Check partial results
                try:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    
                    if partial_text:
                         # Debug only: print partials to see if it hears anything
                         if self._detect_count % 10 == 0:
                             print(f"[VOSK] Partial: '{partial_text}'")
                    
                    if self._contains_wake_word(partial_text):
                        print(f"[WAKE] Wake word обнаружен (partial)!")
                        self._play_beep()
                        self.reset()
                        return True
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Wake word detection error: {e}")
        
        return False
    
    def _contains_wake_word(self, text: str) -> bool:
        """Проверить наличие wake word в тексте"""
        if not text:
            return False
            
        # Множество вариаций (Vosk может криво распознать)
        variations = [
            # Точные
            "алёша", "алеша", "алёш", "алеш", "лёша", "леша",
            # Частые ошибки распознавания
            "алёшь", "алешь", "алёж", "алеж",
            "алёще", "алеще", "лёше", "леше",
            "олёша", "олеша", "алюша", "алиша",
            "а лёша", "а леша",  # С пробелом
            # Очень короткие
            "лёш", "леш", "ёша", "еша",
        ]
        
        for variant in variations:
            if variant in text:
                print(f"[WAKE] Найдено: '{variant}' в '{text}'")
                return True
        
        return False
    
    def reset(self):
        """Сбросить состояние распознавателя"""
        if self.recognizer:
            self.recognizer = KaldiRecognizer(self.model, config.SAMPLE_RATE)
            self.recognizer.SetWords(True)

    def _play_beep(self):
        """Воспроизвести звук активации"""
        try:
            # Try paplay (PulseAudio) first, then aplay (ALSA)
            subprocess.Popen(
                ["paplay", str(config.BEEP_SOUND)],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
        except FileNotFoundError:
            try:
                subprocess.Popen(
                    ["aplay", str(config.BEEP_SOUND)],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
            except Exception:
                pass
