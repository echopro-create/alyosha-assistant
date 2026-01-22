"""
Alyosha Tools
Инструменты и утилиты
"""
import math
from .system import SystemControl

class Tools:
    """Набор инструментов для ассистента"""
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Безопасный калькулятор"""
        # Allowed globals
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round})
        
        # Clean expression
        expression = expression.replace("^", "**")
        
        try:
            # Dangerous but controlled environment
            # In a real production app, use a parser library
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Ошибка вычисления: {e}"

    @staticmethod
    def open_browser(query: str):
        """Инструмент открытия БРАУЗЕРА (используй только если просят 'открыть' или 'найти в гугле')"""
        url = f"https://www.google.com/search?q={query}"
        SystemControl.open_url(url)
        return f"Открываю браузер: {query}"
        
    @staticmethod
    def get_weather(city: str = ""):
        """Погода (текстовый отчет)"""
        import subprocess
        try:
            # Use wttr.in for text weather (v2 for better layout, or format=3 for one-liner)
            city_param = city.replace(" ", "+") if city else ""
            # Increased timeout to 10s and added user-agent to ensure text output
            cmd = f"curl -s -m 10 -H 'User-Agent: curl' 'wttr.in/{city_param}?format=3'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
            if result.returncode == 0 and result.stdout.strip():
                return f"Погода: {result.stdout.strip()}"
            
            # Fallback to more detailed one if format=3 fails
            cmd = f"curl -s -m 10 -H 'User-Agent: curl' 'wttr.in/{city_param}?0'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
            
            # Strip ANSI again just in case (though executor does it, this is a tool)
            import re
            output = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', result.stdout)
            return output.strip() if output.strip() else "Не удалось получить данные о погоде."
        except Exception as e:
            return f"Ошибка получения погоды: {e}"

    @staticmethod
    def get_currency(base: str = "EUR", target: str = "USD"):
        """Курс валют (текстовый отчет)"""
        import subprocess
        import json
        try:
            base = base.upper().strip()
            target = target.upper().strip()
            # Use free exchangerate-api fallback
            cmd = f"curl -s 'https://open.er-api.com/v6/latest/{base}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("result") == "success":
                    rate = data.get("rates", {}).get(target)
                    if rate:
                        return f"Курс {base}/{target}: {rate}"
            return f"Не удалось найти курс для {base}/{target}"
        except Exception as e:
            return f"Ошибка валюты: {e}"
