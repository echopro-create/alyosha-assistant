#!/bin/bash
# Download Piper TTS Russian voice model
# Run this once to enable free, offline TTS

set -e

MODELS_DIR="$(dirname "$0")/models/piper"
VOICE="ru_RU-dmitri-medium"

echo "=== Piper TTS Model Downloader ==="
echo ""

# Create directory
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

# Check if already downloaded
if [ -f "${VOICE}.onnx" ]; then
    echo "✓ Model already exists: ${VOICE}.onnx"
    exit 0
fi

echo "Downloading Piper voice: $VOICE"
echo "This may take a few minutes..."
echo ""

# Download model and config from Hugging Face
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium"

echo "Downloading model..."
wget -q --show-progress "${BASE_URL}/ru_RU-dmitri-medium.onnx" -O "${VOICE}.onnx"

echo "Downloading config..."
wget -q --show-progress "${BASE_URL}/ru_RU-dmitri-medium.onnx.json" -O "${VOICE}.onnx.json"

echo ""
echo "✓ Piper voice downloaded successfully!"
echo "  Model: $MODELS_DIR/${VOICE}.onnx"
echo ""
echo "Now install piper: pip install piper-tts"
