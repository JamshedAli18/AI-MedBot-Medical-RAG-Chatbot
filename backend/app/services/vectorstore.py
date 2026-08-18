# app/services/vectorstore.py
"""
Pinecone query wrapper. Retrieval-only at runtime — ingestion's own upsert
logic lives in ingest.py since it's a one-time/administrative operation,
not part of the request-serving path.
"""
from typing import List, Optional
from dataclasses import dataclass
from pinecone import Pinecone

from app.config import settings
from app.utils.retry import with_retry
from app.utils.logger import get_logger

logger = get_logger("medbot.vectorstore")

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(settings.pinecone_index_name)


@dataclass
class RetrievedChunk:
    text: str
    page: int
    chapter: str
    section: str
    chunk_index: int
    is_table_like: bool
    score: float


@with_retry(retries=2, base_wait=1.5, label="Pinecone query")
def query_vectorstore(query_embedding: List[float], top_k: Optional[int] = None) -> List[RetrievedChunk]:
    """Runs a similarity query and returns typed, ready-to-use chunk objects."""
    k = top_k or settings.retrieval_top_k
    results = _index.query(vector=query_embedding, top_k=k, include_metadata=True)

    chunks = []
    for match in results.get("matches", []):
        m = match["metadata"]
        chunks.append(RetrievedChunk(
            text=m.get("text", ""),
            page=m.get("page", -1),
            chapter=m.get("chapter", "unknown"),
            section=m.get("section", "unknown"),
            chunk_index=m.get("chunk_index", -1),
            is_table_like=m.get("is_table_like", False),
            score=match.get("score", 0.0),
        ))

    logger.info(f"Retrieved {len(chunks)} chunks (top_k={k})")
    return chunks