import json
import logging
from typing import AsyncGenerator, Awaitable, Callable, Optional

from core.chat_service.gemini_service import gemini_service
from core.cv_analysis_service import cv_analysis_service
from core.session_store import session_store
from core.vector_store import vector_store


DisconnectChecker = Optional[Callable[[], Awaitable[bool]]]
logger = logging.getLogger(__name__)


class StreamingChatService:
    async def stream_chat(
        self,
        session_id: str,
        message: str = "",
        user_id: str | None = None,
        uploaded_filename: str | None = None,
        uploaded_content: bytes | None = None,
        is_disconnected: DisconnectChecker = None,
    ) -> AsyncGenerator[str, None]:
        final_text = ""
        current_message = (message or "").strip()

        try:
            session = session_store.require(session_id)
            yield self._sse({"type": "start", "session_id": session_id})

            if uploaded_filename and uploaded_content is not None:
                result = cv_analysis_service.analyze_and_save(
                    file_content=uploaded_content,
                    filename=uploaded_filename,
                    user_id=user_id or session.get("user_id"),
                    session_id=session_id,
                )
                yield self._sse(
                    {
                        "type": "analysis",
                        "session_id": session_id,
                        "filename": result["filename"],
                        "summary": result["summary"],
                        "ats": result["ats"].model_dump(),
                        "improvement_suggestions": result["improvement_suggestions"],
                    }
                )

            if not current_message:
                current_message = (
                    "حلل السيرة الذاتية المرفقة وقدم ملخصاً عملياً للتحسينات والوظائف المناسبة."
                    if uploaded_filename
                    else "ابدأ المحادثة وساعدني في تحسين سيرتي الذاتية."
                )

            session_payload = session_store.require(session_id)
            history = session_payload.get("chat_history", [])
            cv_text = session_payload.get("cv_text", "")
            query = f"{current_message}\n\nCV:\n{cv_text[:5000]}" if cv_text else current_message
            context = vector_store.search_context(query, top_k=6)

            yield self._sse(
                {
                    "type": "context",
                    "sources": [self._source_payload(item) for item in context],
                }
            )

            session_store.append_message(session_id, "user", current_message)
            for chunk in gemini_service.stream_chat(
                cv_text=cv_text,
                user_message=current_message,
                retrieved_context=context,
                history=history,
            ):
                if await self._client_disconnected(is_disconnected):
                    return
                final_text += chunk
                yield self._sse({"type": "delta", "content": chunk})

            if final_text:
                session_store.append_message(session_id, "assistant", final_text)
            yield self._sse({"type": "done", "session_id": session_id})
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.exception("Streaming chat failed for session %s", session_id)
            yield self._sse({"type": "error", "message": str(exc)})
            yield "data: [DONE]\n\n"

    async def _client_disconnected(self, is_disconnected: DisconnectChecker) -> bool:
        if not is_disconnected:
            return False
        try:
            return await is_disconnected()
        except Exception:
            return False

    def _sse(self, payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _source_payload(self, item: dict) -> dict:
        return {
            "title": item.get("title"),
            "company": item.get("company"),
            "category": item.get("category"),
            "link": item.get("link"),
            "score": item.get("_distance_score"),
        }


streaming_chat_service = StreamingChatService()
