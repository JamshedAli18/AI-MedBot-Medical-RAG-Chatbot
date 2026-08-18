# app/graph/state.py
"""
LangGraph state definition. Mirrors the finalized pipeline diagram:
user question -> safety check -> retrieve+rerank -> grade -> generate -> verify -> final answer/fallback.
"""
from typing import List, Optional, TypedDict
from app.services.vectorstore import RetrievedChunk
from app.models.graph_types import DocGradeScore, GroundednessResult


class State(TypedDict, total=False):
    # --- Input ---
    question: str
    history: List[dict]       # [{"role": "user"|"assistant", "content": str}, ...]
    search_question: str      # contextualized standalone question used for cache/retrieval/grading
    bypass_cache: bool

    # --- Triage ---
    message_type: str          # "GENERAL" | "MEDICAL"
    is_emergency: bool
    emergency_reason: Optional[str]

    # --- Retrieval ---
    retrieved_chunks: List[RetrievedChunk]
    reranked_chunks: List[RetrievedChunk]

    # --- Grading ---
    chunk_grades: List[DocGradeScore]
    strong_chunks: List[RetrievedChunk]
    verdict: str              # "CORRECT" | "WEAK"
    verdict_reason: str

    # --- Generation ---
    context: str               # concatenated text of strong_chunks, fed to generation prompt
    citations: List[dict]      # [{"page": int, "section": str, "chapter": str}, ...]
    answer: str                # raw generated answer, pre-verification

    # --- Verification ---
    groundedness: GroundednessResult

    # --- Output ---
    final_answer: str
    fallback_reason: Optional[str]
    
    # app/graph/state.py — add these fields to State
    web_query: str
    web_results: list          # List[WebResult]
    used_web: bool