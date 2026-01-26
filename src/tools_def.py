"""
Alyosha Tools Definition
Определение инструментов для Native Function Calling в Gemini API
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


def execute_bash(command: str):
    """
    Выполнить команду Bash в терминале Linux.
    Используй это для любых действий с системой: установка ПО, работа с файлами, мониторинг, настройки.

    Args:
        command: Точная bash команда. Для root прав (sudo) используй 'pkexec' (например 'pkexec apt install git'), чтобы у пользователя появилось окно ввода пароля. Обычный 'sudo' зависнет!
    """
    logger.info(f"Executing: {command}")

    # Auto-replace common hanging commands
    if command.strip().startswith("sudo ") and "pkexec" not in command:
        pass

    try:
        # Run command with timeout
        # Interactive commands (sudo, ping without count) will hang
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=300,  # Increased to 5 minutes for updates/installs
        )

        output = result.stdout
        error = result.stderr

        if result.returncode == 0:
            return f"Success:\n{output}" if output else "Success (no output)"
        else:
            return f"Error (Exit code {result.returncode}):\n{error}\n{output}"

    except subprocess.TimeoutExpired:
        msg = "Error: Command timed out (300s)."
        if "sudo" in command:
            msg += "\nPossible cause: 'sudo' was waiting for a password. Retry using 'pkexec' command (e.g., 'pkexec apt install ...') to show a GUI password dialog."
        if "ping" in command and "-c" not in command:
            msg += "\nPossible cause: 'ping' ran indefinitely. Use 'ping -c 4 ...'."
        return msg
    except Exception as e:
        return f"Execution failed: {str(e)}"


# Mark as potentially unsafe
execute_bash.SAFE = False


def control_audio(action: str, value: int = None):
    """
    Управление звуком системы, используя pactl (PulseAudio/PipeWire).
    Это ПРЕДПОЧТИТЕЛЬНЫЙ способ управления звуком.

    Args:
        action: 'mute' (выключить звук), 'unmute' (включить звук), 'set_volume' (установить громкость)
        value: Значение громкости в процентах (0-100) для action='set_volume'. Для mute/unmute игнорируется.
    """
    logger.info(f"Audio control: {action}, value={value}")
    try:
        if action == "mute":
            cmd = "pactl set-sink-mute @DEFAULT_SINK@ 1"
        elif action == "unmute":
            cmd = "pactl set-sink-mute @DEFAULT_SINK@ 0"
        elif action == "set_volume":
            if value is None:
                return "Error: value required for set_volume"
            # Limit volume to 150% to prevent damage, though UI says 0-100
            val = max(0, min(100, int(value)))
            cmd = f"pactl set-sink-volume @DEFAULT_SINK@ {val}%"
        else:
            return f"Unknown action: {action}"

        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode == 0:
            return f"Audio {action} executed successfully"
        else:
            # Fallback to amixer if pactl fails
            logger.warning(f"pactl failed: {result.stderr}, trying amixer")
            if action == "mute":
                cmd = "amixer set Master mute"
            elif action == "unmute":
                cmd = "amixer set Master unmute"
            elif action == "set_volume":
                cmd = f"amixer set Master {value}%"

            res_alsa = subprocess.run(cmd.split(), capture_output=True, text=True)
            return f"Fallback to amixer: {res_alsa.returncode == 0}"

    except Exception as e:
        return f"Audio control failed: {str(e)}"


control_audio.SAFE = True


def take_screenshot() -> str:
    """
    Сделать скриншот экрана.
    Используй это, если нужно "посмотреть" на экран, чтобы понять контекст или диагностировать ошибку.
    Returns:
        str: Путь к сохраненному файлу скриншота.
    """
    try:
        import pyautogui
        import tempfile
        import os
        from datetime import datetime

        # Create temp file
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(tempfile.gettempdir(), filename)

        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        logger.info(f"Screenshot taken: {path}")
        return path
    except ImportError:
        return "Error: pyautogui not installed. Please run: pip install pyautogui"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


take_screenshot.SAFE = True


def remember_info(category: str, info: str):
    """
    Запомнить информацию в долговременную память.
    Используй это, чтобы сохранить факты о пользователе, пути к папкам или предпочтения.

    Args:
        category: Категория информации ('fact', 'preference', 'path', 'app').
                  - 'fact': Общий факт (например: "любимый цвет - красный").
                  - 'preference': Настройка (например: "dark_mode=True").
                  - 'path': Путь к важной папке.
        info: Сама информация для запоминания.
    """
    try:
        from .personal_memory import PersonalMemory

        mem = PersonalMemory()

        if category == "fact":
            mem.add_fact(info)
        elif category == "preference":
            # Try to split info by = or :
            if "=" in info:
                k, v = info.split("=", 1)
                mem.set_preference(k.strip(), v.strip())
            else:
                mem.set_preference(info, "True")
        elif category == "list":  # Legacy support or generic add
            mem.add_fact(info)
        else:
            # Default to fact
            mem.add_fact(f"[{category}] {info}")

        return f"Zapomnil: {info} (Category: {category})"
    except Exception as e:
        return f"Error remembering info: {str(e)}"


remember_info.SAFE = True


# Список всех инструментов для передачи в модель
TOOL_DEFINITIONS = [execute_bash, control_audio, take_screenshot, remember_info]
