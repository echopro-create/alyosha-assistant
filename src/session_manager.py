"""
Alyosha Session Manager
Управление историей сессий чата
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import config


class SessionManager:
    """Менеджер сессий для сохранения/загрузки истории чата"""
    
    def __init__(self):
        self.sessions_dir = config.DATA_DIR / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.messages: list[dict] = []
    
    def create_session(self) -> str:
        """Создать новую сессию"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = session_id
        self.messages = []
        return session_id
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение в текущую сессию"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        # Auto-save after each message
        self.save_session()
    
    def save_session(self) -> bool:
        """Сохранить текущую сессию"""
        if not self.current_session_id or not self.messages:
            return False
        
        session_data = {
            "id": self.current_session_id,
            "title": self._generate_title(),
            "created_at": self.messages[0]["timestamp"] if self.messages else datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": self.messages
        }
        
        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[SESSION] Ошибка сохранения: {e}")
            return False
    
    def load_session(self, session_id: str) -> bool:
        """Загрузить сессию по ID"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_session_id = data["id"]
            self.messages = data.get("messages", [])
            return True
        except Exception as e:
            print(f"[SESSION] Ошибка загрузки: {e}")
            return False
    
    def load_latest_session(self) -> bool:
        """Загрузить последнюю сессию"""
        sessions = self.list_sessions()
        if not sessions:
            return False
        
        # Sessions sorted by updated_at descending
        latest = sessions[0]
        return self.load_session(latest["id"])
    
    def list_sessions(self, limit: int = 20) -> list[dict]:
        """Получить список сессий (последние N)"""
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "title": data.get("title", "Без названия"),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "message_count": len(data.get("messages", []))
                })
            except Exception:
                continue
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """Удалить сессию"""
        session_file = self.sessions_dir / f"{session_id}.json"
        try:
            if session_file.exists():
                session_file.unlink()
                if self.current_session_id == session_id:
                    self.current_session_id = None
                    self.messages = []
                return True
        except Exception as e:
            print(f"[SESSION] Ошибка удаления: {e}")
        return False
    
    def get_messages(self) -> list[dict]:
        """Получить все сообщения текущей сессии"""
        return self.messages.copy()
    
    def clear_messages(self):
        """Очистить сообщения текущей сессии"""
        self.messages = []
        self.save_session()
    
    def _generate_title(self) -> str:
        """Генерировать заголовок из первого сообщения"""
        if not self.messages:
            return "Новый чат"
        
        # Find first user message
        for msg in self.messages:
            if msg["role"] == "user":
                text = msg["content"]
                # Truncate to 50 chars
                if len(text) > 50:
                    return text[:47] + "..."
                return text
        
        return "Чат " + self.current_session_id
