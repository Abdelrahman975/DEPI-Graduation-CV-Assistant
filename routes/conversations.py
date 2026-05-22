from fastapi import APIRouter, HTTPException
from dto.schemas import MessageResponse

from core.session_store import session_store
from dto.schemas import (
    ChatCreateRequest,
    ChatSessionResponse,
    ChatSummary,
    UserCreateRequest,
    UserResponse,
)

router = APIRouter(tags=["Users and Conversations"])


def _chat_summary(payload: dict) -> ChatSummary:
    return ChatSummary(
        session_id=payload["session_id"],
        user_id=payload.get("user_id", "unknown"),
        title=payload.get("title") or "محادثة",
        created_at=payload.get("created_at", ""),
        updated_at=payload.get("updated_at", payload.get("created_at", "")),
        has_cv=bool(payload.get("cv_text")),
        filename=payload.get("filename"),
        messages_count=len(payload.get("chat_history", [])),
    )


@router.post("/users", response_model=UserResponse)
async def create_or_get_user(request: UserCreateRequest):
    user = session_store.create_user(request.user_id, request.display_name)
    return UserResponse(**user)


@router.post("/chats", response_model=ChatSummary)
async def create_chat(request: ChatCreateRequest):
    session_store.create_user(request.user_id)
    payload = session_store.create_chat(request.user_id, request.title)
    return _chat_summary(payload)


@router.get("/users/{user_id}/chats", response_model=list[ChatSummary])
async def list_user_chats(user_id: str):
    session_store.create_user(user_id)
    return [_chat_summary(chat) for chat in session_store.list_chats(user_id)]


@router.get("/chats/{session_id}", response_model=ChatSessionResponse)
async def get_chat(session_id: str):
    try:
        payload = session_store.require(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    summary = _chat_summary(payload)
    return ChatSessionResponse(
        **summary.model_dump(),
        messages=payload.get("chat_history", []),
        summary=payload.get("summary"),
        ats=payload.get("ats"),
        improvement_suggestions=payload.get("improvement_suggestions", []),
    )


@router.delete("/chats/{session_id}", response_model=MessageResponse)
async def delete_chat(session_id: str):
    deleted = session_store.delete_chat(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' was not found.")
    return MessageResponse(message="Chat deleted.")
