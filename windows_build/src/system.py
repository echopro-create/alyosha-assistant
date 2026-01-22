"""
Alyosha System Integration (Windows)
Управление системными функциями (Volume, Notification, Screenshot)
"""
import logging
import time
import subprocess
import webbrowser

logger = logging.getLogger(__name__)

class SystemControl:
    """Управление функциями Windows"""
    
    @staticmethod
    def notify(title: str, message: str, icon: str = ""):
        """Отправить системное уведомление"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            # Threaded to not block UI
            toaster.show_toast(title, message, icon_path=icon if icon else None, duration=3, threaded=True)
        except Exception as e:
            logger.error(f"Notification error: {e}")

    @staticmethod
    def set_volume(level_percent: int):
        """Установить громкость (0-100)"""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Scalar is 0.0 to 1.0
            volume.SetMasterVolumeLevelScalar(level_percent / 100.0, None)
        except Exception as e:
            logger.error(f"Set volume error: {e}")

    @staticmethod
    def get_volume() -> int:
        """Получить текущую громкость"""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            return int(volume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return 0

    @staticmethod
    def open_url(url: str):
        """Открыть URL в браузере"""
        webbrowser.open(url)

    @staticmethod
    def take_screenshot() -> str:
        """Сделать скриншот и вернуть путь к файлу"""
        try:
            import pyautogui
            import tempfile
            from pathlib import Path
            
            temp_dir = Path(tempfile.gettempdir())
            path = temp_dir / f"alyosha_screenshot_{int(time.time())}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(path))
            return str(path)
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return ""
