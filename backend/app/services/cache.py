# app/services/cache.py
"""
Two-tier response cache:
1. Exact-match: normalized question string -> cached answer, instant lookup
2. Semantic: query embedding compared against cached question embeddings via
   Pinecone, catches paraphrases above a high similarity threshold

Only CORRECT + grounded answers are cached — fallback/ungrounded responses
are never cached, since we don't want to serve a bad answer faster.

In-memory + a dedicated Pinecone namespace for now (matches the "session
memory for now" scope) — swap to Redis-backed exact-match cache later if
running multiple server instances.
"""
import hashlib
import time
from dataclasses import dataclass
from typing import Optional

from pinecone import Pinecone

from app.config import settings
from app.services.embeddings import embed_query
from app.utils.logger import get_logger

logger = get_logger("medbot.cache")

CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
SEMANTIC_SIMILARITY_THRESHOLD = 0.93  # conservative — only near-duplicate questions match
CACHE_NAMESPACE = "qa-cache"

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(settings.pinecone_index_name)

# --- Tier 1: exact-match, in-memory ---
_exact_cache: dict[str, dict] = {}


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().split())


def _cache_key(question: str) -> str:
    return hashlib.sha256(_normalize(question).encode()).hexdigest()


@dataclass
class CacheHit:
    final_answer: str
    source: str  # "exact" | "semantic"


def get_cached_answer(question: str) -> Optional[CacheHit]:
    # Tier 1: exact match
    key = _cache_key(question)
    entry = _exact_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        logger.info("Cache hit (exact match)")
        return CacheHit(final_answer=entry["final_answer"], source="exact")

    # Tier 2: semantic match via Pinecone namespace
    try:
        emb = embed_query(question)
        results = _index.query(
            vector=emb, top_k=1, include_metadata=True, namespace=CACHE_NAMESPACE
        )
        matches = results.get("matches", [])
        if matches and matches[0]["score"] >= SEMANTIC_SIMILARITY_THRESHOLD:
            logger.info(f"Cache hit (semantic, score={matches[0]['score']:.3f})")
            return CacheHit(final_answer=matches[0]["metadata"]["final_answer"], source="semantic")
    except Exception as e:
        logger.warning(f"Semantic cache lookup failed, skipping: {e}")

    return None


def set_cached_answer(question: str, final_answer: str):
    key = _cache_key(question)
    _exact_cache[key] = {"final_answer": final_answer, "ts": time.time()}

    try:
        emb = embed_query(question)
        _index.upsert(
            vectors=[{
                "id": key,
                "values": emb,
                "metadata": {"final_answer": final_answer, "question": question},
            }],
            namespace=CACHE_NAMESPACE,
        )
        logger.info("Cached answer (exact + semantic)")
    except Exception as e:
        logger.warning(f"Semantic cache write failed (exact-match cache still saved): {e}")