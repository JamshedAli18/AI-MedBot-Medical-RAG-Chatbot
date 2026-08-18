# app/dependencies.py
"""
FastAPI dependency that authenticates every /chat request.
Returns an identity dict the endpoint can use to know who's asking
and whether they're allowed to proceed.
"""
from fastapi import Header, HTTPException, status

from app.services.auth import decode_access_token
from app.services.guest import get_guest_usage, increment_guest_usage, guest_limit_reached
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("medbot.dependencies")


async def get_current_identity(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    identity_type = payload.get("type")

    if identity_type == "user":
        return {"type": "user", "user_id": payload.get("user_id"), "email": payload.get("email")}

    if identity_type == "guest":
        guest_id = payload.get("guest_id")
        current_count = await get_guest_usage(guest_id)
        return {
            "type": "guest",
            "guest_id": guest_id,
            "question_count": current_count,
            "limit_reached": guest_limit_reached(current_count),
        }

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Unrecognized token type.")


async def get_current_admin(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin access required.")

    return {"type": "admin"}
