from datetime import datetime
from pydantic import BaseModel


class SessionSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionMessage(BaseModel):
    role: str
    content: str
    created_at: datetime


class SessionMessagesResponse(BaseModel):
    id: str
    title: str
    messages: list[SessionMessage]


class CreateSessionResponse(BaseModel):
    id: str
    title: str
