import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings


class SessionStore:
    def __init__(self, session_dir: Path | None = None):
        self.session_dir = session_dir or settings.SESSION_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, payload: Dict[str, Any]) -> None:
        payload["updated_at"] = datetime.utcnow().isoformat()
        path = self._path(session_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def require(self, session_id: str) -> Dict[str, Any]:
        session = self.load(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' was not found.")
        return session

    def create_user(self, user_id: Optional[str] = None, display_name: Optional[str] = None) -> Dict[str, Any]:
        user_id = self._safe_id(user_id) if user_id else f"user-{uuid.uuid4()}"
        user_path = self.session_dir / "users.json"
        users = {}
        if user_path.exists():
            users = json.loads(user_path.read_text(encoding="utf-8"))
        if user_id not in users:
            users[user_id] = {
                "user_id": user_id,
                "display_name": display_name or "Local User",
                "created_at": datetime.utcnow().isoformat(),
            }
            user_path.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
        return users[user_id]

    def create_chat(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title or "محادثة جديدة",
            "created_at": now,
            "updated_at": now,
            "filename": None,
            "upload_path": None,
            "cv_text": "",
            "summary": None,
            "ats": None,
            "improvement_suggestions": [],
            "chat_history": [],
        }
        self.save(session_id, payload)
        return payload

    def list_chats(self, user_id: str) -> List[Dict[str, Any]]:
        chats = []
        for path in self.session_dir.glob("*.json"):
            if path.name == "users.json":
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if payload.get("user_id") == user_id:
                chats.append(payload)
        return sorted(chats, key=lambda item: item.get("updated_at", ""), reverse=True)

    def delete_chat(self, session_id: str) -> bool:
        session = self.load(session_id)
        path = self._path(session_id)
        if not path.exists():
            return False
        upload_path = session.get("upload_path") if session else None
        path.unlink()
        if upload_path:
            try:
                upload = Path(upload_path).resolve()
                upload_dir = settings.UPLOAD_DIR.resolve()
                if upload.is_relative_to(upload_dir) and upload.exists():
                    upload.unlink()
            except Exception:
                pass
        return True

    def append_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        session = self.require(session_id)
        session.setdefault("chat_history", []).append({"role": role, "content": content})
        self.save(session_id, session)
        return session

    def _path(self, session_id: str) -> Path:
        safe = self._safe_id(session_id)
        return self.session_dir / f"{safe}.json"

    def _safe_id(self, value: str) -> str:
        return "".join(ch for ch in value if ch.isalnum() or ch in "-_")


session_store = SessionStore()
