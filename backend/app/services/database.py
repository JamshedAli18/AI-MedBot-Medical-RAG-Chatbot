# app/services/database.py
"""
MongoDB (Motor async client) connection, shared across the app.
Two collections: users, guest_usage.
"""
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("medbot.database")

_client = AsyncIOMotorClient(settings.mongodb_uri)
db = _client[settings.mongodb_db_name]

users_collection = db["users"]
guest_usage_collection = db["guest_usage"]
chat_sessions_collection = db["chat_sessions"]


async def ensure_indexes():
    """Call once at startup — unique email index prevents duplicate signups."""
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("google_id", sparse=True)
    await chat_sessions_collection.create_index([("user_id", 1), ("updated_at", -1)])
    logger.info("MongoDB indexes ensured.")
