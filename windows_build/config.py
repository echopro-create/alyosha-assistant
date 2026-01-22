"""
Alyosha Configuration
Загрузка API ключей и настроек
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"
USER_AVATAR_PATH = ASSETS_DIR / "user_avatar.png"
SOUNDS_DIR = ASSETS_DIR / "sounds"
MEMORY_FILE = BASE_DIR / "memory.json"

import platform

# Logging
if platform.system() == "Windows":
    DATA_DIR = Path(os.getenv("APPDATA")) / "Alyosha"
else:
    DATA_DIR = Path.home() / ".alyosha"

LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "alyosha.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 3

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ErXwobaYiN019PkySvjV") # Antoni (Male)

# Vosk model path
VOSK_MODEL_PATH = MODELS_DIR / "vosk-model-small-ru-0.22"

# Wake word
WAKE_WORD = "алёша"

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 4000
BEEP_SOUND = SOUNDS_DIR / "beep.wav"

# UI settings
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 600
ANIMATION_FPS = 60

# LLM settings
MAX_CONTEXT_MESSAGES = 20

# Memory settings
MAX_MEMORY_MESSAGES = 500

# Voice System settings
# TTS Engine: "auto" (Piper offline, ElevenLabs if API key), "piper", "elevenlabs"
TTS_ENGINE = os.getenv("TTS_ENGINE", "auto")

# Piper TTS (free, offline)
PIPER_VOICE = os.getenv("PIPER_VOICE", "ru_RU-dmitri-medium")  # dmitri or irina
PIPER_MODEL_PATH = MODELS_DIR / "piper" / f"{PIPER_VOICE}.onnx"
PIPER_CONFIG_PATH = MODELS_DIR / "piper" / f"{PIPER_VOICE}.onnx.json"

# Whisper STT model size: "tiny", "small", "medium", "large-v3"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

def validate_config() -> tuple[bool, list[str]]:
    """Проверка наличия необходимых ключей"""
    errors = []
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append("GEMINI_API_KEY не установлен")
    
    # ElevenLabs is optional - only show as warning, not error
    
    return len(errors) == 0, errors


