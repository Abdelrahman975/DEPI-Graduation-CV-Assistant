import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from core.chat_service.gemini_service import gemini_service
from core.cv_analysis_service import cv_analysis_service
from core.session_store import session_store
from core.vector_store import vector_store
from dto.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    try:
        session = session_store.require(request.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    cv_text = session.get("cv_text", "")
    query = f"{request.message}\n\nCV:\n{cv_text[:5000]}" if cv_text else request.message
    context = vector_store.search_context(query, top_k=request.top_k)
    history = session.get("chat_history", [])
    answer = gemini_service.chat(
        cv_text=cv_text,
        user_message=request.message,
        retrieved_context=context,
        history=history,
    )

    session_store.append_message(request.session_id, "user", request.message)
    session_store.append_message(request.session_id, "assistant", answer)

    sources = [
        {
            "title": item.get("title"),
            "company": item.get("company"),
            "category": item.get("category"),
            "link": item.get("link"),
            "score": item.get("_distance_score"),
        }
        for item in context
    ]
    return ChatResponse(session_id=request.session_id, answer=answer, sources=sources)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/stream", summary="Stream chat response using SSE")
async def chat_stream(
    session_id: str = Form(...),
    message: str = Form(default=""),
    user_id: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    try:
        session = session_store.require(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    uploaded_filename = file.filename if file and file.filename else None
    uploaded_content = await file.read() if uploaded_filename else None

    async def event_generator():
        final_text = ""
        current_message = (message or "").strip()

        try:
            if uploaded_filename and uploaded_content is not None:
                result = cv_analysis_service.analyze_and_save(
                    file_content=uploaded_content,
                    filename=uploaded_filename,
                    user_id=user_id or session.get("user_id"),
                    session_id=session_id,
                )
                session_payload = result["payload"]
                yield _sse(
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

            session_store.append_message(session_id, "user", current_message)
            for chunk in gemini_service.stream_chat(
                cv_text=cv_text,
                user_message=current_message,
                retrieved_context=context,
                history=history,
            ):
                final_text += chunk
                yield _sse({"type": "delta", "content": chunk})

            session_store.append_message(session_id, "assistant", final_text)
            yield _sse({"type": "done", "session_id": session_id})
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
