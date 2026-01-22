#!/bin/bash
# Alyosha Voice Assistant - System Dependencies Installer

echo "🤖 Установка системных зависимостей для Алёши..."

# Update package list
sudo apt-get update

# Audio dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Qt6 dependencies
sudo apt-get install -y libxcb-cursor0

# Build tools
sudo apt-get install -y python3-dev python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download Vosk model for Russian
VOSK_MODEL="vosk-model-small-ru-0.22"
VOSK_URL="https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"

if [ ! -d "models/${VOSK_MODEL}" ]; then
    echo "📥 Скачивание модели Vosk для русского языка..."
    mkdir -p models
    wget -q --show-progress -O "models/${VOSK_MODEL}.zip" "$VOSK_URL"
    unzip -q "models/${VOSK_MODEL}.zip" -d models/
    rm "models/${VOSK_MODEL}.zip"
fi

echo "✅ Установка завершена!"
echo "📝 Не забудьте добавить API ключи в файл .env"
echo "🚀 Запуск: python main.py"
