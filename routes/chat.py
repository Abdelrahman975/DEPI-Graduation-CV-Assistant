from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.chat_service.gemini_service import gemini_service
from core.chat_service.streaming_chat_service import streaming_chat_service
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


@router.post("/stream", summary="Stream chat response using SSE")
async def chat_stream(
    request: Request,
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

    return StreamingResponse(
        streaming_chat_service.stream_chat(
            session_id=session_id,
            message=message,
            user_id=user_id,
            uploaded_filename=uploaded_filename,
            uploaded_content=uploaded_content,
            is_disconnected=request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
