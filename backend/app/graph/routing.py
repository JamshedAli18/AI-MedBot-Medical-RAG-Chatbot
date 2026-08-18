# app/graph/routing.py
"""
Conditional edge functions — pure functions of State, returning the name
of the next node/branch. No side effects, no LLM calls here.
"""
from app.graph.state import State


def route_after_triage(state: State) -> str:
    mtype = state.get("message_type")
    if mtype == "REFORMAT":
        return "reformat_answer"
    if mtype == "GENERAL":
        return "quick_chat_response"
    if state.get("is_emergency"):
        return "emergency_fallback"
    return "retrieve_and_rerank"


def route_after_cache_check(state: State) -> str:
    return "format_final_answer" if state.get("final_answer") else "retrieve_and_rerank"


def route_after_grading(state: State) -> str:
    verdict = state.get("verdict")
    if verdict == "CORRECT":
        return "generate_answer"
    if verdict == "ERROR":
        return "service_busy_fallback"
    return "rewrite_web_query"  # only genuine WEAK goes to web


def route_after_web_search(state: State) -> str:
    return "generate_from_web" if state.get("web_results") else "weak_evidence_fallback"


def route_after_verification(state: State) -> str:
    g = state.get("groundedness")
    if g and g.grounded:
        return "format_final_answer"
    return "weak_evidence_fallback" if state.get("used_web") else "ungrounded_fallback"