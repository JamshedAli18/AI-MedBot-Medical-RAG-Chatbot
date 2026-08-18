# app/services/chat_sessions.py
"""
Persisted, per-user chat sessions (registered users only — guests keep
the simpler in-memory single-session flow in session_memory.py).
Each session caps at settings.session_message_limit user messages;
past that, /chat rejects further messages on that session and the
frontend prompts the user to start a new one.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings
from app.services.database import chat_sessions_collection
from app.utils.logger import get_logger

logger = get_logger("medbot.chat_sessions")

DEFAULT_TITLE = "New chat"
TITLE_MAX_LEN = 48


def make_title(first_message: str) -> str:
    text = first_message.strip()
    if len(text) <= TITLE_MAX_LEN:
        return text or DEFAULT_TITLE
    return text[:TITLE_MAX_LEN].rsplit(" ", 1)[0] + "..."


async def create_session(user_id: str) -> dict:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc = {
        "_id": session_id,
        "user_id": user_id,
        "title": DEFAULT_TITLE,
        "messages": [],
        "message_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    await chat_sessions_collection.insert_one(doc)
    logger.info(f"Created session {session_id} for user {user_id}")
    return doc


async def list_sessions(user_id: str) -> List[dict]:
    cursor = chat_sessions_collection.find(
        {"user_id": user_id}, {"messages": 0}  # exclude message bodies from the list view
    ).sort("updated_at", -1)
    return [doc async for doc in cursor]


async def get_session(session_id: str, user_id: str) -> Optional[dict]:
    return await chat_sessions_collection.find_one({"_id": session_id, "user_id": user_id})


async def append_message(session_id: str, role: str, content: str) -> None:
    now = datetime.now(timezone.utc)
    update = {
        "$push": {"messages": {"role": role, "content": content, "created_at": now}},
        "$set": {"updated_at": now},
    }
    if role == "user":
        update["$inc"] = {"message_count": 1}

    await chat_sessions_collection.update_one({"_id": session_id}, update)


async def maybe_set_title(session_id: str, first_user_message: str) -> None:
    doc = await chat_sessions_collection.find_one({"_id": session_id}, {"title": 1})
    if doc and doc.get("title") == DEFAULT_TITLE:
        await chat_sessions_collection.update_one(
            {"_id": session_id}, {"$set": {"title": make_title(first_user_message)}}
        )


async def delete_session(session_id: str, user_id: str) -> bool:
    result = await chat_sessions_collection.delete_one({"_id": session_id, "user_id": user_id})
    return result.deleted_count > 0


def session_limit_reached(message_count: int) -> bool:
    return message_count >= settings.session_message_limit


def get_history_for_context(session_doc: dict, max_messages: int = 10) -> List[dict]:
    """Last N messages, formatted for the graph's history input."""
    msgs = session_doc.get("messages", [])[-max_messages:]
    return [{"role": m["role"], "content": m["content"]} for m in msgs]
