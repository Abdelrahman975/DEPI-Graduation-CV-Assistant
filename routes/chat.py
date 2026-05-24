from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.chat_service.streaming_chat_service import streaming_chat_service
from core.session_store import session_store

router = APIRouter(prefix="/chat", tags=["Chat"])


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
