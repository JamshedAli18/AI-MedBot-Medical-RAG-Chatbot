# app/services/guest.py
"""
Guest identity creation and question-quota tracking.
A guest's identity persists via their JWT (frontend stores it in
localStorage), so the count survives page reloads — the whole point
of tracking this server-side rather than trusting client state.
"""
import uuid
from datetime import datetime, timezone

from app.config import settings
from app.services.database import guest_usage_collection
from app.utils.logger import get_logger

logger = get_logger("medbot.guest")


async def create_guest() -> str:
    guest_id = str(uuid.uuid4())
    await guest_usage_collection.insert_one({
        "_id": guest_id,
        "question_count": 0,
        "created_at": datetime.now(timezone.utc),
        "last_used_at": datetime.now(timezone.utc),
    })
    logger.info(f"New guest created: {guest_id}")
    return guest_id


async def get_guest_usage(guest_id: str) -> int:
    doc = await guest_usage_collection.find_one({"_id": guest_id})
    if not doc:
        return settings.guest_question_limit  # unknown guest_id treated as exhausted, fail-safe
    return doc.get("question_count", 0)


async def increment_guest_usage(guest_id: str) -> int:
    result = await guest_usage_collection.find_one_and_update(
        {"_id": guest_id},
        {"$inc": {"question_count": 1}, "$set": {"last_used_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return result.get("question_count", settings.guest_question_limit) if result else settings.guest_question_limit


def guest_limit_reached(count: int) -> bool:
    return count >= settings.guest_question_limit
