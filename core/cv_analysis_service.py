import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import settings
from core.ats_service import ats_service
from core.chat_service.gemini_service import gemini_service
from core.cv_parser import cv_parser
from core.session_store import session_store


class CVAnalysisService:
    def analyze_and_save(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        safe_name = Path(filename or "cv.txt").name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in cv_parser.SUPPORTED_EXTENSIONS:
            raise ValueError("Please upload a PDF, DOCX, or TXT CV.")

        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(file_content) > max_bytes:
            raise ValueError(f"CV is too large. Max size is {settings.MAX_UPLOAD_MB} MB.")

        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or "anonymous"
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        upload_path = settings.UPLOAD_DIR / f"{session_id}_{safe_name}"
        upload_path.write_bytes(file_content)

        cv_text = cv_parser.parse(upload_path)
        summary_data = cv_parser.summarize(cv_text)
        ats = ats_service.evaluate(cv_text, top_jobs=settings.DEFAULT_TOP_JOBS)
        suggestions = gemini_service.suggest_cv_improvements(cv_text, ats.model_dump())

        existing = session_store.load(session_id) or {}
        now = datetime.utcnow().isoformat()
        chat_history = existing.get("chat_history", [])
        chat_history.extend(
            [
                {"role": "user", "content": f"رفعت ملف السيرة الذاتية: {safe_name}"},
                {
                    "role": "assistant",
                    "content": (
                        f"تم تحليل السيرة الذاتية. ATS score: {ats.score} ({ats.label}). "
                        "يمكنك الآن طلب تحسينات، أسئلة مقابلة، أو وظائف مناسبة."
                    ),
                },
            ]
        )

        payload = {
            **existing,
            "session_id": session_id,
            "user_id": user_id,
            "title": existing.get("title") or safe_name,
            "filename": safe_name,
            "created_at": existing.get("created_at") or now,
            "upload_path": str(upload_path),
            "cv_text": cv_text,
            "summary": summary_data,
            "ats": ats.model_dump(),
            "improvement_suggestions": suggestions,
            "chat_history": chat_history,
        }
        session_store.save(session_id, payload)

        return {
            "session_id": session_id,
            "user_id": user_id,
            "filename": safe_name,
            "summary": summary_data,
            "ats": ats,
            "improvement_suggestions": suggestions,
            "cv_text": cv_text,
            "payload": payload,
        }


cv_analysis_service = CVAnalysisService()
