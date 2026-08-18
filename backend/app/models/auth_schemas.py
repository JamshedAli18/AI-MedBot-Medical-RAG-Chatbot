from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    identity_type: str  # "user" | "guest"
    email: str | None = None


class AdminLoginRequest(BaseModel):
    password: str


class UserSummary(BaseModel):
    email: str
    auth_provider: str
    created_at: datetime


class GuestSummary(BaseModel):
    guest_id: str
    question_count: int
    created_at: datetime
    last_used_at: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_guests: int
    users: list[UserSummary]
    guests: list[GuestSummary]
