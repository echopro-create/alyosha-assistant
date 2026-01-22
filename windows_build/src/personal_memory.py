"""
Alyosha Personal Memory
Персональная память пользователя для хранения предпочтений
"""
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import config


class PersonalMemory:
    """Персональная память пользователя (персистентная)"""
    
    def __init__(self):
        self.profile_file = config.DATA_DIR / "user_profile.json"
        self.profile = {
            "name": None,
            "preferences": {},
            "favorite_apps": [],
            "frequent_commands": [],
            "command_history": [],
            "facts": [],  # Интересные факты о пользователе
            "created_at": None,
            "updated_at": None,
        }
        self._load()
    
    # --- Имя пользователя ---
    
    def set_name(self, name: str):
        """Установить имя пользователя"""
        self.profile["name"] = name
        self._save()
    
    def get_name(self) -> str | None:
        """Получить имя пользователя"""
        return self.profile.get("name")
    
    # --- Предпочтения ---
    
    def set_preference(self, key: str, value: str):
        """Установить предпочтение"""
        self.profile["preferences"][key] = value
        self._save()
    
    def get_preference(self, key: str) -> str | None:
        """Получить предпочтение"""
        return self.profile["preferences"].get(key)
    
    def get_all_preferences(self) -> dict:
        """Получить все предпочтения"""
        return self.profile["preferences"].copy()
    
    # --- Любимые приложения ---
    
    def add_favorite_app(self, app: str):
        """Добавить приложение в избранное"""
        if app not in self.profile["favorite_apps"]:
            self.profile["favorite_apps"].append(app)
            self._save()
    
    def remove_favorite_app(self, app: str):
        """Удалить приложение из избранного"""
        if app in self.profile["favorite_apps"]:
            self.profile["favorite_apps"].remove(app)
            self._save()
    
    def get_favorite_apps(self) -> list[str]:
        """Получить список избранных приложений"""
        return self.profile["favorite_apps"].copy()
    
    # --- Частые команды ---
    
    def track_command(self, command: str):
        """Отслеживать выполненную команду для статистики"""
        if not command or command.startswith("tool:"):
            return
        
        # Add to history
        self.profile["command_history"].append({
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 1000 commands
        if len(self.profile["command_history"]) > 1000:
            self.profile["command_history"] = self.profile["command_history"][-1000:]
        
        # Update frequent commands
        self._update_frequent_commands()
        self._save()
    
    def _update_frequent_commands(self):
        """Обновить список частых команд"""
        commands = [h["command"] for h in self.profile["command_history"]]
        counter = Counter(commands)
        self.profile["frequent_commands"] = [cmd for cmd, _ in counter.most_common(10)]
    
    def get_frequent_commands(self) -> list[str]:
        """Получить список частых команд"""
        return self.profile["frequent_commands"].copy()
    
    # --- Факты о пользователе ---
    
    def add_fact(self, fact: str):
        """Запомнить факт о пользователе"""
        if fact and fact not in self.profile["facts"]:
            self.profile["facts"].append(fact)
            # Keep max 50 facts
            if len(self.profile["facts"]) > 50:
                self.profile["facts"] = self.profile["facts"][-50:]
            self._save()
    
    def get_facts(self) -> list[str]:
        """Получить все факты о пользователе"""
        return self.profile["facts"].copy()
    
    # --- Суммаризация для контекста LLM ---
    
    def get_summary_for_llm(self) -> str:
        """Генерировать саммари профиля для контекста LLM"""
        lines = []
        
        name = self.get_name()
        if name:
            lines.append(f"Имя пользователя: {name}")
        
        prefs = self.get_all_preferences()
        if prefs:
            lines.append("Предпочтения:")
            for k, v in prefs.items():
                lines.append(f"  - {k}: {v}")
        
        apps = self.get_favorite_apps()
        if apps:
            lines.append(f"Любимые приложения: {', '.join(apps)}")
        
        cmds = self.get_frequent_commands()
        if cmds:
            lines.append(f"Часто используемые команды: {', '.join(cmds[:5])}")
        
        facts = self.get_facts()
        if facts:
            lines.append("Факты о пользователе:")
            for fact in facts[-5:]:  # Last 5 facts
                lines.append(f"  - {fact}")
        
        return "\n".join(lines) if lines else ""
    
    # --- Persistence ---
    
    def _load(self):
        """Загрузить профиль с диска"""
        if self.profile_file.exists():
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults
                    for key in self.profile:
                        if key in data:
                            self.profile[key] = data[key]
            except (json.JSONDecodeError, IOError) as e:
                print(f"[PROFILE] Ошибка загрузки: {e}")
    
    def _save(self):
        """Сохранить профиль на диск"""
        self.profile["updated_at"] = datetime.now().isoformat()
        if not self.profile["created_at"]:
            self.profile["created_at"] = self.profile["updated_at"]
        
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[PROFILE] Ошибка сохранения: {e}")
    
    def clear(self):
        """Очистить профиль"""
        self.profile = {
            "name": None,
            "preferences": {},
            "favorite_apps": [],
            "frequent_commands": [],
            "command_history": [],
            "facts": [],
            "created_at": None,
            "updated_at": None,
        }
        self._save()
