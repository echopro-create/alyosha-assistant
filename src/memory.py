"""
Alyosha Memory System
Хранение контекста и истории разговоров
"""
import json
from pathlib import Path
from datetime import datetime
import config


class Memory:
    """Память разговоров с сохранением на диск"""
    
    def __init__(self):
        self.messages: list[dict] = []
        self.memory_file = config.MEMORY_FILE
        self._load()
    
    def add_user_message(self, content: str):
        """Добавить сообщение пользователя"""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._rotate()
        self._save()

    def add_system_message(self, content: str):
        """Добавить системное сообщение (результат инструмента)"""
        self.messages.append({
            "role": "user", # Using user role to provide context to LLM in history
            "content": f"[SYSTEM INFO]: {content}",
            "timestamp": datetime.now().isoformat()
        })
        self._rotate()
        self._save()
    
    def add_assistant_message(self, content: str, command: str = ""):
        """Добавить сообщение ассистента"""
        self.messages.append({
            "role": "assistant",
            "content": content,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        self._rotate()
        self._save()

    def _rotate(self):
        """Ротация памяти"""
        if len(self.messages) > config.MAX_MEMORY_MESSAGES:
            self.messages = self.messages[-config.MAX_MEMORY_MESSAGES:]
            
    def search(self, query: str) -> list[dict]:
        """Поиск по истории сообщений"""
        query = query.lower()
        results = []
        for msg in self.messages:
            if query in msg.get("content", "").lower():
                results.append(msg)
        return results

    def export_markdown(self) -> str:
        """Экспорт истории в Markdown"""
        lines = ["# История переписки с Алёшей\n"]
        for msg in self.messages:
            role = "Я" if msg["role"] == "user" else "Алёша"
            time = msg.get("timestamp", "")
            content = msg.get("content", "")
            lines.append(f"**{role}** ({time}):\n{content}\n")
            if msg.get("command"):
                lines.append(f"> Команда: `{msg['command']}`\n")
            lines.append("---\n")
        return "".join(lines)
    
    def get_context(self, max_messages: int = None) -> list[dict]:
        """Получить контекст для LLM"""
        limit = max_messages or config.MAX_CONTEXT_MESSAGES
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages[-limit:]
        ]
    
    def get_last_message(self) -> dict | None:
        """Получить последнее сообщение"""
        if self.messages:
            return self.messages[-1]
        return None
    
    def clear(self):
        """Очистить память"""
        self.messages = []
        self._save()
    
    def _load(self):
        """Загрузить память с диска"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
            except (json.JSONDecodeError, IOError):
                self.messages = []
    
    def _save(self):
        """Сохранить память на диск"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"messages": self.messages}, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Failed to save memory: {e}")
