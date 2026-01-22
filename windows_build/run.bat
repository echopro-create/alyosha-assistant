@echo off
chcp 65001 > nul
echo Starting Alyosha Assistant...

if not exist ".env" (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and set your API keys.
    pause
    exit /b 1
)

python main.py
if %errorlevel% neq 0 (
    echo Application exited with error.
    pause
)
