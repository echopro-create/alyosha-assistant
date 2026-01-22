"""
Alyosha System Integration
Управление системными функциями (DBus, Volume, Power)
"""
import subprocess
import shutil
import time
import logging

logger = logging.getLogger(__name__)

class SystemControl:
    """Управление функциями ОС Linux"""
    
    @staticmethod
    def notify(title: str, message: str, icon: str = ""):
        """Отправить системное уведомление"""
        cmd = ["notify-send", title, message]
        if icon:
            cmd.extend(["-i", icon])
        
        try:
            subprocess.run(cmd, check=False)
        except FileNotFoundError:
            pass # notify-send not found

    @staticmethod
    def set_volume(level_percent: int):
        """Установить громкость (0-100)"""
        # Try pactl (PulseAudio/PipeWire)
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level_percent}%"], 
                check=False
            )
            return
        except FileNotFoundError:
            pass
            
        # Fallback to amixer (ALSA)
        try:
            subprocess.run(
                ["amixer", "-D", "pulse", "sset", "Master", f"{level_percent}%"], 
                check=False
            )
        except FileNotFoundError:
            pass

    @staticmethod
    def get_volume() -> int:
        """Получить текущую громкость"""
        # Simplified implementation using amixer
        try:
            res = subprocess.run(
                ["amixer", "-D", "pulse", "get", "Master"],
                capture_output=True, text=True
            )
            if "[" in res.stdout:
                # Extract 50% from [50%]
                return int(res.stdout.split("[")[1].split("%")[0])
        except Exception:
            pass
        return 0

    @staticmethod
    def open_url(url: str):
        """Открыть URL в браузере"""
        import webbrowser
        webbrowser.open(url)

    @staticmethod
    def take_screenshot() -> str:
        """Сделать скриншот и вернуть путь к файлу"""
        import tempfile
        from pathlib import Path
        
        # Create temp file
        temp_dir = Path(tempfile.gettempdir())
        screenshot_path = temp_dir / f"alyosha_screenshot_{int(time.time())}.png"
        
        try:
            # Use gnome-screenshot -f <file>
            subprocess.run(["gnome-screenshot", "-f", str(screenshot_path)], check=True)
            return str(screenshot_path)
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return ""

    @staticmethod
    def type_text(text: str):
        """Напечатать текст (эмуляция клавиатуры)"""
        try:
            import pyautogui
            # Safety delay
            time.sleep(0.5)
            # Type with small interval to simulate human typing
            pyautogui.write(text, interval=0.05)
        except ImportError:
            logger.error("pyautogui not installed")
        except Exception as e:
            logger.error(f"Typing error: {e}")

    @staticmethod
    def get_system_status() -> str:
        """Получить статус системы (CPU, RAM, Disk, Battery)"""
        status = []
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            status.append(f"CPU: {cpu_percent}%")
            
            # RAM
            mem = psutil.virtual_memory()
            status.append(f"RAM: {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)")
            
            # Disk
            disk = psutil.disk_usage('/')
            status.append(f"Disk (/): {disk.percent}% ({disk.free // (1024**3)}GB free)")
            
            # Battery
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    status.append(f"Battery: {battery.percent}% {'(Charging)' if battery.power_plugged else ''}")
            
        except ImportError:
            status.append("Error: psutil module not installed.")
        except Exception as e:
            status.append(f"Error reading status: {e}")
            
        return " | ".join(status)

    @staticmethod
    def media_control(action: str):
        """Управление медиа (play, pause, next, prev)"""
        import pyautogui
        try:
            if action in ["play", "pause", "playpause"]:
                pyautogui.press("playpause")
            elif action == "next":
                pyautogui.press("nexttrack")
            elif action == "prev":
                pyautogui.press("prevtrack")
            elif action == "stop":
                pyautogui.press("stop")
            elif action == "vol_up":
                pyautogui.press("volumeup")
            elif action == "vol_down":
                pyautogui.press("volumedown")
            elif action == "mute":
                pyautogui.press("volumemute")
        except Exception as e:
            logger.error(f"Media control error: {e}")

    @staticmethod
    def clipboard_control(action: str, text: str = "") -> str:
        """Управление буфером обмена"""
        try:
            import pyperclip
            if action == "get":
                return pyperclip.paste()
            elif action == "set":
                pyperclip.copy(text)
                return "Скопировано в буфер"
        except ImportError:
            return "Error: pyperclip module not installed"
        except Exception as e:
            return f"Clipboard error: {e}"
        return ""

    @staticmethod
    def window_control(action: str):
        """Управление окнами"""
        import pyautogui
        try:
            if action == "minimize":
                # Linux/Windows usually Super+D or Super+M. Super+D (Show Desktop) is safest toggle.
                pyautogui.hotkey('win', 'd') 
            elif action == "maximize":
                pyautogui.hotkey('win', 'up')
            elif action == "close":
                pyautogui.hotkey('alt', 'f4')
            elif action == "switch":
                pyautogui.hotkey('alt', 'tab')
        except Exception as e:
            logger.error(f"Window control error: {e}")
