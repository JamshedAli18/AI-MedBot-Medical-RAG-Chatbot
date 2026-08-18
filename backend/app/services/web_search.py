# app/services/web_search.py
"""
Tavily web search — used ONLY as a fallback when the book's own content
doesn't cover a question (verdict=WEAK). Never used as a first resort,
so book-grounded answers always stay preferred over the open web.
"""
from typing import List, TypedDict
from tavily import TavilyClient

from app.config import settings
from app.utils.retry import with_retry
from app.utils.logger import get_logger

logger = get_logger("medbot.web_search")

_client = TavilyClient(api_key=settings.tavily_api_key)


class WebResult(TypedDict):
    title: str
    url: str
    content: str


@with_retry(retries=2, base_wait=2.0, label="Tavily search")
def web_search(query: str) -> List[WebResult]:
    resp = _client.search(query=query, max_results=settings.tavily_max_results)
    results = resp.get("results", [])
    logger.info(f"Web search returned {len(results)} results for: {query}")
    return [
        {"title": r.get("title", "Untitled"), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in results
    ]