"""
Alyosha Text-to-Speech 2026
Multi-engine TTS: Piper (free/offline) + ElevenLabs (premium)
"""
import subprocess
import tempfile
import os
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)


class PiperTTS:
    """Free, offline TTS using Piper (ONNX models)"""
    
    def __init__(self):
        self.voice = config.PIPER_VOICE
        self.model_path = config.PIPER_MODEL_PATH
        self.is_available = False
        
    def load(self) -> bool:
        """Check if Piper and model are available"""
        # Check piper binary
        try:
            result = subprocess.run(
                ["piper", "--help"],
                capture_output=True,
                timeout=5
            )
            piper_installed = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            piper_installed = False
            
        if not piper_installed:
            logger.warning("Piper not installed. Run: pip install piper-tts")
            return False
            
        # Check model file
        if not self.model_path.exists():
            logger.warning(f"Piper model not found: {self.model_path}")
            logger.info("Download with: piper --download-dir models/piper --model ru_RU-dmitri-medium")
            return False
            
        self.is_available = True
        logger.info(f"Piper TTS loaded: {self.voice}")
        return True
    
    def synthesize(self, text: str) -> bytes | None:
        """Synthesize speech using Piper"""
        if not self.is_available or not text.strip():
            return None
            
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                output_path = f.name
            
            # Run piper
            process = subprocess.run(
                [
                    "piper",
                    "--model", str(self.model_path),
                    "--output_file", output_path
                ],
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=30
            )
            
            if process.returncode != 0:
                logger.error(f"Piper error: {process.stderr.decode()}")
                return None
            
            # Read output and convert to MP3 for consistency
            with open(output_path, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            try:
                os.unlink(output_path)
            except OSError:
                pass
                
            return wav_data
            
        except subprocess.TimeoutExpired:
            logger.error("Piper synthesis timeout")
            return None
        except Exception as e:
            logger.error(f"Piper error: {e}")
            return None


class ElevenLabsTTS:
    """Premium TTS using ElevenLabs API"""
    
    def __init__(self):
        self.client = None
        self.voice_id = config.ELEVENLABS_VOICE_ID
        self.is_available = False
    
    def load(self) -> bool:
        """Initialize ElevenLabs client"""
        if not config.ELEVENLABS_API_KEY or config.ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
            logger.info("ElevenLabs API key not set, skipping")
            return False
        
        try:
            from elevenlabs import ElevenLabs
            self.client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
            self.is_available = True
            logger.info("ElevenLabs TTS loaded")
            return True
        except Exception as e:
            logger.error(f"ElevenLabs init failed: {e}")
            return False
    
    def synthesize(self, text: str) -> bytes | None:
        """Synthesize speech using ElevenLabs"""
        if not self.is_available or not text.strip():
            return None
        
        try:
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_flash_v2_5",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": False
                }
            )
            
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            return None


class TTS:
    """
    Multi-engine TTS with automatic fallback
    
    Priority (when TTS_ENGINE="auto"):
    1. ElevenLabs (if API key available) — highest quality
    2. Piper (if model available) — free, offline
    """
    
    def __init__(self):
        self.piper = PiperTTS()
        self.elevenlabs = ElevenLabsTTS()
        self.active_engine = None
        self.is_available = False
        self.output_format = "wav"  # Piper outputs WAV, ElevenLabs outputs MP3
    
    def load(self) -> bool:
        """Load TTS engines based on config"""
        engine = config.TTS_ENGINE.lower()
        
        if engine == "elevenlabs":
            # Force ElevenLabs only
            if self.elevenlabs.load():
                self.active_engine = "elevenlabs"
                self.output_format = "mp3"
                self.is_available = True
            else:
                logger.error("ElevenLabs requested but unavailable")
                
        elif engine == "piper":
            # Force Piper only
            if self.piper.load():
                self.active_engine = "piper"
                self.output_format = "wav"
                self.is_available = True
            else:
                logger.error("Piper requested but unavailable")
                
        else:  # "auto"
            # Try ElevenLabs first (premium), then Piper (free)
            if self.elevenlabs.load():
                self.active_engine = "elevenlabs"
                self.output_format = "mp3"
                self.is_available = True
                logger.info("Using ElevenLabs TTS (premium)")
            elif self.piper.load():
                self.active_engine = "piper"
                self.output_format = "wav"
                self.is_available = True
                logger.info("Using Piper TTS (free/offline)")
            else:
                logger.warning("No TTS engine available - voice disabled")
        
        return True  # Not a fatal error if no TTS
    
    def synthesize(self, text: str) -> bytes | None:
        """Synthesize speech using active engine"""
        if not self.is_available or not text.strip():
            return None
        
        if self.active_engine == "elevenlabs":
            return self.elevenlabs.synthesize(text)
        elif self.active_engine == "piper":
            return self.piper.synthesize(text)
        
        return None
    
    def synthesize_stream(self, text: str):
        """
        Stream synthesis (only ElevenLabs supports true streaming)
        For Piper, we synthesize fully then yield
        """
        if not self.is_available or not text.strip():
            return
        
        if self.active_engine == "elevenlabs" and self.elevenlabs.is_available:
            try:
                from elevenlabs import ElevenLabs
                audio_generator = self.elevenlabs.client.text_to_speech.convert(
                    voice_id=self.elevenlabs.voice_id,
                    output_format="mp3_44100_128",
                    text=text,
                    model_id="eleven_flash_v2_5"
                )
                for chunk in audio_generator:
                    yield chunk
            except Exception as e:
                logger.error(f"ElevenLabs stream error: {e}, falling back to Piper")
                # Fallback to Piper if ElevenLabs fails
                if self.piper.is_available:
                    audio = self.piper.synthesize(text)
                    if audio:
                        yield audio
        else:
            # Piper: synthesize fully then yield as one chunk
            audio = self.synthesize(text)
            if audio:
                yield audio
    
    def get_engine_name(self) -> str:
        """Get name of active engine for UI display"""
        if self.active_engine == "elevenlabs":
            return "ElevenLabs"
        elif self.active_engine == "piper":
            return "Piper"
        return "None"
