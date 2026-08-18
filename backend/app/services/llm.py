# app/services/llm.py
"""
Centralized LLM clients, one per task, each pointed at its designated model/provider.
Nodes should import from here, never construct ChatGroq directly.
"""
import logging
from langchain_groq import ChatGroq

from app.config import settings

logger = logging.getLogger("medbot.llm")

# --- Grading LLM: Groq, high call volume (one per chunk), needs speed ---
# reasoning_effort="none" disables Qwen's thinking mode — grading needs a fast score, not reasoning traces
grading_llm = ChatGroq(
    model=settings.grading_model,
    api_key=settings.groq_api_key,
    temperature=0,
    timeout=30,
    max_retries=2,
    reasoning_effort="none",
)

# --- Generation LLM: Groq, careful/accurate final answers ---
generation_llm = ChatGroq(
    model=settings.generation_model,
    api_key=settings.groq_api_key,
    temperature=0.1,
    timeout=30,
    max_retries=2,
)

# --- Verifier LLM: Groq, strongest reasoning, audits generation output ---
verifier_llm = ChatGroq(
    model=settings.verifier_model,
    api_key=settings.groq_api_key,
    temperature=0,
    timeout=30,
    max_retries=2,
)


def get_llm(task: str):
    mapping = {
        "grading": grading_llm,
        "generation": generation_llm,
        "verifier": verifier_llm,
    }
    if task not in mapping:
        raise ValueError(f"Unknown LLM task '{task}'. Valid: {list(mapping.keys())}")
    return mapping[task]