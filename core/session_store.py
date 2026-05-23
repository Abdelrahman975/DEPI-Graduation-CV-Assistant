import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.safety import safe_identifier


class SessionStore:
    def __init__(self, session_dir: Path | None = None):
        self.session_dir = session_dir or settings.SESSION_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.backend = "files"
        self.db_error: str | None = None
        self._connection = None
        if settings.CONN_STR and settings.SESSION_BACKEND.lower() in {"auto", "postgres", "postgresql"}:
            self._connect_postgres()

    def save(self, session_id: str, payload: Dict[str, Any]) -> None:
        payload["updated_at"] = datetime.utcnow().isoformat()
        if self.backend == "postgres":
            self._pg_save(session_id, payload)
            return
        path = self._path(session_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.backend == "postgres":
            return self._pg_load(session_id)
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
        user_id = safe_identifier(user_id) if user_id else f"user-{uuid.uuid4()}"
        if self.backend == "postgres":
            return self._pg_create_user(user_id, display_name)
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
        if self.backend == "postgres":
            return self._pg_list_chats(user_id)
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
        if self.backend == "postgres":
            if not session:
                return False
            with self._connection.cursor() as cur:
                cur.execute("DELETE FROM cv_assistant_sessions WHERE session_id = %s", (session_id,))
        elif not path.exists():
            return False
        else:
            path.unlink()
        upload_path = session.get("upload_path") if session else None
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
        safe = safe_identifier(session_id)
        return self.session_dir / f"{safe}.json"

    def _connect_postgres(self) -> None:
        try:
            import psycopg

            self._connection = psycopg.connect(settings.CONN_STR)
            self._connection.autocommit = True
            self._ensure_postgres_schema()
            self.backend = "postgres"
        except Exception as exc:
            self.db_error = str(exc)
            self._connection = None
            self.backend = "files"

    def _ensure_postgres_schema(self) -> None:
        with self._connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(hashtext('cv_assistant_schema'))")
            try:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cv_assistant_users (
                        user_id TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cv_assistant_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
            finally:
                cur.execute("SELECT pg_advisory_unlock(hashtext('cv_assistant_schema'))")

    def _pg_save(self, session_id: str, payload: Dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cv_assistant_sessions (session_id, user_id, payload, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    session_id,
                    payload.get("user_id", "anonymous"),
                    Jsonb(payload),
                    payload.get("created_at") or datetime.utcnow().isoformat(),
                    payload["updated_at"],
                ),
            )

    def _pg_load(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT payload FROM cv_assistant_sessions WHERE session_id = %s",
                (session_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        payload = row[0]
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    def _pg_create_user(self, user_id: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cv_assistant_users (user_id, display_name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id, display_name or "Local User", now),
            )
            cur.execute(
                "SELECT user_id, display_name, created_at FROM cv_assistant_users WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        return {"user_id": row[0], "display_name": row[1], "created_at": row[2]}

    def _pg_list_chats(self, user_id: str) -> List[Dict[str, Any]]:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT payload
                FROM cv_assistant_sessions
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
        chats = []
        for row in rows:
            payload = row[0]
            chats.append(json.loads(payload) if isinstance(payload, str) else payload)
        return chats


session_store = SessionStore()
