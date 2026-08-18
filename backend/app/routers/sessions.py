# app/routers/sessions.py
"""
Session management endpoints — registered users only. Guests are
rejected here since they use the simpler single-session in-memory flow.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_identity
from app.models.session_schemas import (
    SessionSummary, SessionMessagesResponse, SessionMessage, CreateSessionResponse,
)
from app.services import chat_sessions
from app.utils.logger import get_logger

logger = get_logger("medbot.sessions_router")

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _require_user(identity: dict) -> str:
    if identity["type"] != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sessions are only available for registered users.")
    return identity["user_id"]


@router.post("", response_model=CreateSessionResponse)
async def create_session(identity: dict = Depends(get_current_identity)):
    user_id = _require_user(identity)
    doc = await chat_sessions.create_session(user_id)
    return CreateSessionResponse(id=doc["_id"], title=doc["title"])


@router.get("", response_model=list[SessionSummary])
async def list_sessions(identity: dict = Depends(get_current_identity)):
    user_id = _require_user(identity)
    docs = await chat_sessions.list_sessions(user_id)
    return [
        SessionSummary(
            id=d["_id"], title=d["title"], message_count=d.get("message_count", 0),
            created_at=d["created_at"], updated_at=d["updated_at"],
        )
        for d in docs
    ]


@router.get("/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(session_id: str, identity: dict = Depends(get_current_identity)):
    user_id = _require_user(identity)
    doc = await chat_sessions.get_session(session_id, user_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return SessionMessagesResponse(
        id=doc["_id"],
        title=doc["title"],
        messages=[SessionMessage(**m) for m in doc.get("messages", [])],
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str, identity: dict = Depends(get_current_identity)):
    user_id = _require_user(identity)
    deleted = await chat_sessions.delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return {"deleted": True}
