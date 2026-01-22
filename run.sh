#!/bin/bash
# Запуск Алёши
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
python main.py
