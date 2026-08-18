# app/graph/build.py
"""
Wires the node functions and routing logic from nodes.py/routing.py into
the compiled LangGraph StateGraph, exactly matching the pipeline diagram.
"""
from langgraph.graph import StateGraph, START, END

from app.graph.state import State
from app.graph import nodes, routing

g = StateGraph(State)

g.add_node("triage_message", nodes.triage_message)
g.add_node("quick_chat_response", nodes.quick_chat_response)
g.add_node("reformat_answer", nodes.reformat_answer)
g.add_node("contextualize_question", nodes.contextualize_question)
g.add_node("check_cache", nodes.check_cache)
g.add_node("retrieve_and_rerank", nodes.retrieve_and_rerank)
g.add_node("grade_chunks", nodes.grade_chunks)
g.add_node("generate_answer", nodes.generate_answer)
g.add_node("verify_groundedness", nodes.verify_groundedness)
g.add_node("rewrite_web_query", nodes.rewrite_web_query)
g.add_node("web_search_node", nodes.web_search_node)
g.add_node("generate_from_web", nodes.generate_from_web)

g.add_node("emergency_fallback", nodes.emergency_fallback)
g.add_node("weak_evidence_fallback", nodes.weak_evidence_fallback)
g.add_node("ungrounded_fallback", nodes.ungrounded_fallback)
g.add_node("service_busy_fallback", nodes.service_busy_fallback)
g.add_node("format_final_answer", nodes.format_final_answer)

g.add_edge(START, "triage_message")

g.add_conditional_edges(
    "triage_message",
    routing.route_after_triage,
    {
        "quick_chat_response": "quick_chat_response",
        "reformat_answer": "reformat_answer",
        "emergency_fallback": "emergency_fallback",
        "retrieve_and_rerank": "contextualize_question",
    },
)

g.add_edge("contextualize_question", "check_cache")

g.add_conditional_edges(
    "check_cache",
    routing.route_after_cache_check,
    {"format_final_answer": "format_final_answer", "retrieve_and_rerank": "retrieve_and_rerank"},
)

g.add_edge("retrieve_and_rerank", "grade_chunks")

g.add_conditional_edges(
    "grade_chunks", routing.route_after_grading,
    {
        "generate_answer": "generate_answer",
        "rewrite_web_query": "rewrite_web_query",
        "service_busy_fallback": "service_busy_fallback",
    },
)

g.add_edge("generate_answer", "verify_groundedness")

g.add_edge("rewrite_web_query", "web_search_node")
g.add_conditional_edges(
    "web_search_node", routing.route_after_web_search,
    {"generate_from_web": "generate_from_web", "weak_evidence_fallback": "weak_evidence_fallback"},
)
g.add_edge("generate_from_web", "verify_groundedness")

g.add_conditional_edges(
    "verify_groundedness", routing.route_after_verification,
    {"format_final_answer": "format_final_answer", "ungrounded_fallback": "ungrounded_fallback", "weak_evidence_fallback": "weak_evidence_fallback"},
)

g.add_edge("quick_chat_response", END)
g.add_edge("reformat_answer", END)
g.add_edge("emergency_fallback", END)
g.add_edge("weak_evidence_fallback", END)
g.add_edge("ungrounded_fallback", END)
g.add_edge("service_busy_fallback", END)
g.add_edge("format_final_answer", END)

app = g.compile()


def run_query(question: str, history: list = None, bypass_cache: bool = False) -> dict:
    return app.invoke({
        "question": question,
        "history": history or [],
        "bypass_cache": bypass_cache,
    })