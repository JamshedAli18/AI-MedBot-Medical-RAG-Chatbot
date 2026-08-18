# app/services/reranker.py
"""
Cohere Rerank: reorders the wide-net retrieval results by actual
query-relevance rather than raw embedding similarity. As seen in the
manual test — bee-sting content outranked the core anaphylaxis protocol
on embedding score alone; rerank corrects exactly this kind of ordering.
"""
from typing import List, Optional
import cohere

from app.config import settings
from app.services.vectorstore import RetrievedChunk
from app.utils.retry import with_retry
from app.utils.logger import get_logger

logger = get_logger("medbot.reranker")

_client = cohere.Client(settings.cohere_api_key)


# app/services/reranker.py — updated rerank_chunks
@with_retry(retries=2, base_wait=2.0, label="Cohere rerank")
def rerank_chunks(query: str, chunks: List[RetrievedChunk], top_n: Optional[int] = None) -> List[RetrievedChunk]:
    """Reranks retrieved chunks by relevance to the query. Returns the
    top_n chunks in reranked order, with updated .score values from rerank.

    Documents are given to the reranker WITH chapter/section context prepended
    (matching the contextual embedding used at ingest time) — without this,
    template-structured books (identical "A.1 Symptoms suggesting X" headers
    across every chapter) can't be disambiguated by rerank, which only sees
    the raw chunk text otherwise.
    """
    if not chunks:
        return []

    n = top_n or settings.rerank_top_n
    documents = [f"{c.chapter} - {c.section}\n\n{c.text}" for c in chunks]

    resp = _client.rerank(
        query=query,
        documents=documents,
        model=settings.cohere_rerank_model,
        top_n=min(n, len(documents)),
    )

    reranked = []
    for result in resp.results:
        original = chunks[result.index]
        original.score = result.relevance_score
        reranked.append(original)

    logger.info(f"Reranked {len(chunks)} -> top {len(reranked)} chunks")
    return reranked