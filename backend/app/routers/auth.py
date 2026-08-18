# app/routers/auth.py
"""
Email/password auth endpoints. Google OAuth and guest mode are added
in later steps, in separate routes within this same router.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from app.models.auth_schemas import SignupRequest, LoginRequest, TokenResponse, AdminLoginRequest
from app.services.database import users_collection
from app.services.auth import hash_password, verify_password, create_access_token
from app.services.guest import create_guest
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("medbot.auth_router")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest):
    existing = await users_collection.find_one({"email": req.email})
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user_doc = {
        "email": req.email,
        "password_hash": hash_password(req.password),
        "google_id": None,
        "auth_provider": "email",
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token({"type": "user", "user_id": user_id, "email": req.email})
    logger.info(f"New signup: {req.email}")
    return TokenResponse(access_token=token, identity_type="user", email=req.email)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await users_collection.find_one({"email": req.email})
    if not user or not user.get("password_hash"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token({"type": "user", "user_id": str(user["_id"]), "email": req.email})
    logger.info(f"Login: {req.email}")
    return TokenResponse(access_token=token, identity_type="user", email=req.email)


@router.post("/guest", response_model=TokenResponse)
async def guest_login():
    guest_id = await create_guest()
    token = create_access_token({"type": "guest", "guest_id": guest_id})
    logger.info(f"Guest session issued: {guest_id}")
    return TokenResponse(access_token=token, identity_type="guest", email=None)


@router.post("/admin-login", response_model=TokenResponse)
async def admin_login(req: AdminLoginRequest):
    if req.password != settings.admin_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect admin password.")

    token = create_access_token({"type": "admin"}, expires_minutes=480)  # 8-hour admin session
    logger.info("Admin login successful")
    return TokenResponse(access_token=token, identity_type="admin", email=None)
