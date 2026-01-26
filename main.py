#!/usr/bin/env python3
"""
Алёша — Голосовой Ассистент для Linux Mint
2026 Edition с премиальным UI

Запуск: python main.py
Горячая клавиша: Ctrl+Shift+Space
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFontDatabase

import logging
from logging.handlers import RotatingFileHandler
import config
from ui.main_window import MainWindow


def setup_logging():
    """Настройка логирования"""
    log_dir = config.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = config.LOG_FILE
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler, logging.StreamHandler(sys.stdout)]
    )
    
    logging.info("Alyosha started")


def check_api_keys() -> tuple[bool, list[str]]:
    """Проверить наличие API ключей"""
    errors = []
    
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append("❌ GEMINI_API_KEY не установлен в .env")
    
    if not config.ELEVENLABS_API_KEY or config.ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
        errors.append("⚠️ ELEVENLABS_API_KEY не установлен (голос будет отключён)")
    
    # Only Gemini is required
    has_critical_error = not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here"
    
    return not has_critical_error, errors


def check_vosk_model() -> bool:
    """Проверить наличие модели Vosk"""
    return config.VOSK_MODEL_PATH.exists()


def show_error_dialog(title: str, message: str):
    """Показать диалог ошибки"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_warning_dialog(title: str, message: str):
    """Показать диалог предупреждения"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def load_premium_fonts():
    """Загрузить премиальные шрифты из assets/fonts"""
    fonts_dir = config.ASSETS_DIR / "fonts"
    if not fonts_dir.exists():
        return
    
    loaded = 0
    for font_file in fonts_dir.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id >= 0:
            loaded += 1
    
    # Also try .otf files
    for font_file in fonts_dir.glob("*.otf"):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id >= 0:
            loaded += 1
    
    if loaded > 0:
        logging.info(f"Loaded {loaded} premium fonts")


def main():
    """Точка входа"""
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Алёша")
    app.setStyle("Fusion")
    
    # Load premium fonts
    load_premium_fonts()
    
    # Check API keys
    valid, errors = check_api_keys()
    if not valid:
        show_error_dialog(
            "Ошибка конфигурации",
            "Добавьте API ключи в файл .env:\n\n" + "\n".join(errors)
        )
        return 1
    
    # Show warnings
    if errors:
        print("Предупреждения:")
        for err in errors:
            print(f"  {err}")
    
    # Check Vosk model
    if not check_vosk_model():
        show_error_dialog(
            "Модель не найдена",
            f"Модель Vosk не найдена: {config.VOSK_MODEL_PATH}\n\n"
            "Запустите install.sh для скачивания модели."
        )
        return 1
    
    # Create main window
    window = MainWindow()
    
    # Initialize assistant
    # Initialize assistant (async)
    # Initialize assistant (async) - Moved to __init__
    # window.init_assistant()
    
    # Start assistant and show window
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
