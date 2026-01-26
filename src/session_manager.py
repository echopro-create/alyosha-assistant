"""
Alyosha Session Manager
Управление историей сессий чата
"""
import json
from datetime import datetime
from typing import Optional
import config


class SessionManager:
    """Менеджер сессий для сохранения/загрузки истории чата"""
    
    def __init__(self):
        self.sessions_dir = config.DATA_DIR / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.sessions_dir / "index.json"
        
        self.current_session_id: Optional[str] = None
        self.messages: list[dict] = []
        
        # Build index if not exists or invalid
        if not self.index_file.exists():
            self._rebuild_index()

    def _rebuild_index(self):
        """Полная перестройка индекса сессий"""
        try:
            index_data = []
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.name == "index.json":
                    continue
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    index_data.append({
                        "id": data.get("id", session_file.stem),
                        "title": data.get("title", "Без названия"),
                        "updated_at": data.get("updated_at", ""),
                        "created_at": data.get("created_at", "")
                    })
                except Exception:
                    continue
            
            # Sort by update time
            index_data.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            self._save_index(index_data)
        except Exception as e:
            print(f"[SESSION] Rebuild index error: {e}")

    def _save_index(self, data: list):
        """Сохранить индекс на диск"""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SESSION] Index save error: {e}")

    def _load_index(self) -> list[dict]:
        """Загрузить индекс"""
        if not self.index_file.exists():
            self._rebuild_index()
            
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _update_index_entry(self, entry: dict):
        """Обновить или добавить запись в индекс"""
        index = self._load_index()
        # Remove existing if present
        index = [item for item in index if item["id"] != entry["id"]]
        # Add new (at top)
        index.insert(0, entry)
        # Sort again just in case
        index.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        self._save_index(index)

    def _remove_from_index(self, session_id: str):
        """Удалить из индекса"""
        index = self._load_index()
        index = [item for item in index if item["id"] != session_id]
        self._save_index(index)

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
        
        try:
            title = self._generate_title()
            updated_at = datetime.now().isoformat()
            created_at = self.messages[0]["timestamp"] if self.messages else updated_at
            
            session_data = {
                "id": self.current_session_id,
                "title": title,
                "created_at": created_at,
                "updated_at": updated_at,
                "messages": self.messages
            }
            
            session_file = self.sessions_dir / f"{self.current_session_id}.json"
            
            # 1. Save File
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
            # 2. Update Index
            self._update_index_entry({
                "id": self.current_session_id,
                "title": title,
                "created_at": created_at,
                "updated_at": updated_at
            })
            
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
        sessions = self.list_sessions(limit=1)
        if not sessions:
            return False
        return self.load_session(sessions[0]["id"])
    
    def list_sessions(self, limit: int = 50) -> list[dict]:
        """Получить список сессий из индекса (мгновенно)"""
        try:
            index = self._load_index()
            return index[:limit]
        except Exception:
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Удалить сессию"""
        session_file = self.sessions_dir / f"{session_id}.json"
        try:
            if session_file.exists():
                session_file.unlink()
                
            self._remove_from_index(session_id)
            
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
