# app/models/graph_types.py
"""
Pydantic models used for LLM structured outputs inside the graph.
Separate from app/models/schemas.py (API-facing request/response shapes) —
these are internal contracts between nodes and their LLM calls.
"""
from typing import List
from pydantic import BaseModel, Field


class EmergencyCheckResult(BaseModel):
    is_emergency: bool = Field(..., description="True if the question describes a potential acute medical emergency")
    reason: str = Field(..., description="Brief explanation of the classification")


class TriageResult(BaseModel):
    message_type: str = Field(
        ...,
        description="'GENERAL' for greetings/thanks/small talk, or 'MEDICAL' for anything requiring medical reference lookup",
    )
    reason: str = Field(..., description="Brief explanation")


class DocGradeScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance of this chunk to the question, 0.0-1.0")
    reason: str = Field(..., description="Brief justification for the score")


class GroundednessResult(BaseModel):
    grounded: bool = Field(..., description="True only if every claim in the answer is supported by the provided context")
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Any specific claims in the answer that are NOT directly supported by the context. Empty if grounded=True."
    )
    reason: str = Field(..., description="Brief explanation of the groundedness verdict")