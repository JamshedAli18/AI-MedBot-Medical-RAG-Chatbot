# app/services/embeddings.py
"""
Query-time embedding. Note the asymmetry with ingestion:
ingest.py uses input_type="search_document" when embedding chunks,
this module uses input_type="search_query" when embedding the user's question.
Cohere's v3 embed models are trained for this asymmetry — mixing them up
silently degrades retrieval quality without throwing any error.
"""
from typing import List
import cohere

from app.config import settings
from app.utils.retry import with_retry
from app.utils.logger import get_logger

logger = get_logger("medbot.embeddings")

_client = cohere.Client(settings.cohere_api_key)


@with_retry(retries=3, base_wait=2.0, label="Cohere query embedding")
def embed_query(text: str) -> List[float]:
    """Embed a single user question for retrieval. Always search_query type."""
    resp = _client.embed(
        texts=[text],
        model=settings.cohere_embed_model,
        input_type="search_query",
    )
    return resp.embeddings[0]


@with_retry(retries=3, base_wait=2.0, label="Cohere document embedding")
def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed one or more documents (used outside ingest.py if ever needed at runtime)."""
    resp = _client.embed(
        texts=texts,
        model=settings.cohere_embed_model,
        input_type="search_document",
    )
    return resp.embeddings