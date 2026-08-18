# app/routers/admin.py
"""
Admin-only endpoints for viewing users and guest activity.
Access requires a valid admin token (obtained via POST /auth/admin-login).
"""
from fastapi import APIRouter, Depends

from app.dependencies import get_current_admin
from app.services.database import users_collection, guest_usage_collection
from app.models.auth_schemas import AdminStatsResponse, UserSummary, GuestSummary

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(_: dict = Depends(get_current_admin)):
    users_cursor = users_collection.find().sort("created_at", -1)
    users = [
        UserSummary(email=u["email"], auth_provider=u.get("auth_provider", "email"), created_at=u["created_at"])
        async for u in users_cursor
    ]

    guests_cursor = guest_usage_collection.find().sort("last_used_at", -1)
    guests = [
        GuestSummary(
            guest_id=str(g["_id"]),
            question_count=g.get("question_count", 0),
            created_at=g["created_at"],
            last_used_at=g["last_used_at"],
        )
        async for g in guests_cursor
    ]

    return AdminStatsResponse(
        total_users=len(users),
        total_guests=len(guests),
        users=users,
        guests=guests,
    )
