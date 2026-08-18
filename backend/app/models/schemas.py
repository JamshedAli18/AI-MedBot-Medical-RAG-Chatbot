from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
	message: str = Field(..., min_length=1, max_length=2000)
	session_id: str = Field(..., min_length=1, max_length=128)


class HealthResponse(BaseModel):
	status: str
	service: str


class HomeResponse(BaseModel):
	service: str
	version: str
	endpoints: list[str]
