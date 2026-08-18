# app/graph/nodes.py
"""
Node functions for the MedBot CRAG graph. Each function takes State and
returns a partial state update (LangGraph merges these automatically).
"""
import re
from typing import List

from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
from app.services.llm import grading_llm, generation_llm, verifier_llm
from app.services.embeddings import embed_query
from app.services.vectorstore import query_vectorstore, RetrievedChunk
from app.services.reranker import rerank_chunks
from app.services.cache import get_cached_answer, set_cached_answer
from app.models.graph_types import TriageResult, DocGradeScore, GroundednessResult
from app.graph.state import State
from app.utils.logger import get_logger
from app.services.web_search import web_search, WebResult


logger = get_logger("medbot.nodes")

import re as _re

TREATMENT_KEYWORDS = _re.compile(
    r"\b(treat(ment|ing)?|medicat(e|ion)|drug|dose|dosage|dosing|cure|medicine|therapy|"
    r"prescri(be|ption)|antibiotic|antimalarial|regimen|pill|tablet|injection|remedy)\b",
    _re.IGNORECASE,
)

TREATMENT_WARNING = (
    "⚠️ **Before you read this:** the following describes possible treatments or medications for "
    "reference only. Drug choice, dosing, and suitability depend on individual factors — age, weight, "
    "allergies, other conditions — that only a qualified clinician can assess. Please consult a doctor "
    "or pharmacist before acting on this, and don't take it as a final answer — I can make mistakes.\n\n"
)


def is_treatment_related(text: str) -> bool:
    return bool(TREATMENT_KEYWORDS.search(text))


# =====================================================================
# 1. Triage (general vs medical) + emergency check
# =====================================================================
# app/graph/nodes.py — replace triage_prompt and triage_message

triage_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You triage incoming messages to a medical reference chatbot into exactly one of three types:\n\n"
     "- REFORMAT: the message asks to change how the PREVIOUS answer is presented — shorter, simpler, "
     "'in detail', 'explain more', 'bullet points', 'I don't understand, make it simple', 'make it easy' — "
     "without asking for new/different information. Only valid if the conversation history shows the "
     "assistant already gave a real answer just before this message.\n\n"
     "- GENERAL: greetings, thanks, small talk — e.g. 'hi', 'thank you', 'nice', 'bye' — with no "
     "connection to a prior medical topic.\n\n"
     "- MEDICAL: any question seeking new/different medical information, OR a follow-up that changes "
     "or extends the topic (e.g. 'what about kids', 'why', 'is that contagious') rather than just asking "
     "for the same content restyled.\n\n"
     "If history is empty or has no prior assistant answer, REFORMAT is never valid — use GENERAL or "
     "MEDICAL instead. When unsure between REFORMAT and MEDICAL, prefer REFORMAT if the message contains "
     "no new medical noun/topic of its own (e.g. 'make it simple' has no new topic — REFORMAT; "
     "'what about in children' introduces a new angle — MEDICAL).\n"
     "Output JSON only."),
    ("human", "Conversation history:\n{history}\n\nLatest message: {question}"),
])
triage_chain = triage_prompt | grading_llm.with_structured_output(TriageResult)


# Separate, focused emergency check — only invoked for messages already classified MEDICAL
emergency_only_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Does this message describe a potential ACUTE medical emergency happening right now "
     "(chest pain, can't breathe, severe bleeding, loss of consciousness, suicidal ideation, etc.)? "
     "General informational questions about a topic are NOT emergencies. "
     "Answer with exactly one word: YES or NO."),
    ("human", "Message: {question}"),
])


def triage_message(state: State) -> dict:
    history_text = format_history(state.get("history", []))
    try:
        result: TriageResult = triage_chain.invoke({"question": state["question"], "history": history_text})
    except Exception as e:
        logger.error(f"Triage failed, defaulting to MEDICAL (fail-safe): {e}")
        return {"message_type": "MEDICAL", "is_emergency": False, "emergency_reason": "Triage unavailable."}

    logger.info(f"Triage: type={result.message_type}")

    if result.message_type == "REFORMAT":
        return {"message_type": "REFORMAT", "is_emergency": False, "emergency_reason": ""}

    if result.message_type != "MEDICAL":
        return {"message_type": "GENERAL", "is_emergency": False, "emergency_reason": ""}

    # Only check for emergency on messages actually classified as MEDICAL
    try:
        emergency_result = (emergency_only_prompt | grading_llm).invoke({"question": state["question"]})
        is_emergency = "YES" in emergency_result.content.strip().upper()
    except Exception as e:
        logger.warning(f"Emergency check failed, defaulting to non-emergency: {e}")
        is_emergency = False

    logger.info(f"Emergency check: is_emergency={is_emergency}")
    return {"message_type": "MEDICAL", "is_emergency": is_emergency, "emergency_reason": ""}


def split_answer_sections(text: str):
    """Splits a rendered final_answer back into (main_body, citation_lines, disclaimer)."""
    parts = re.split(r"\n\n\*\*(?:Sources|Web sources):\*\*\n", text)
    main = parts[0]
    citation_block, disclaimer = "", ""
    if len(parts) > 1:
        rest = parts[1]
        disc_split = re.split(r"\n\n_", rest, maxsplit=1)
        citation_block = disc_split[0]
        disclaimer = ("_" + disc_split[1]) if len(disc_split) > 1 else ""
    return main.strip(), citation_block.strip(), disclaimer.strip()


reformat_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Rewrite the answer below according to the person's request (e.g. simpler, shorter, more detail, "
     "bullet points). Rules:\n"
     "1. Do NOT add any new facts, claims, or information not already present in the original answer.\n"
     "2. Only change phrasing, length, structure, or level of simplicity as requested.\n"
     "3. Keep [Excerpt N] markers as they are if you keep the sentences that use them.\n"
     "4. Use markdown bullets for lists, bold key terms, short paragraphs — matching the requested style.\n"
     "Output only the rewritten answer body, nothing else (no sources section, no disclaimer)."),
    ("human", "Request: {question}\n\nOriginal answer:\n{original}"),
])


def reformat_answer(state: State) -> dict:
    history = state.get("history", [])
    last_assistant = next((h["content"] for h in reversed(history) if h["role"] == "assistant"), None)

    if not last_assistant:
        # safety net: nothing to reformat, fall back to treating it as a fresh medical question
        logger.warning("REFORMAT triggered with no prior assistant answer — falling back to full pipeline")
        return {"message_type": "MEDICAL"}

    main, citation_block, disclaimer = split_answer_sections(last_assistant)
    # strip any existing treatment warning before reformatting, so it isn't duplicated/reformatted away
    main_clean = main.replace(TREATMENT_WARNING.strip(), "").strip()

    try:
        result = (reformat_prompt | grading_llm).invoke({"question": state["question"], "original": main_clean})
        new_main = result.content.strip()
    except Exception as e:
        logger.warning(f"Reformat failed, returning original answer unchanged: {e}")
        new_main = main_clean

    treatment_note = TREATMENT_WARNING if is_treatment_related(main_clean) else ""

    source_label = "Web sources" if "http" in citation_block else "Sources"
    final = f"{treatment_note}{new_main}\n\n**{source_label}:**\n{citation_block}\n\n{disclaimer}".strip()

    return {"final_answer": final, "fallback_reason": "reformatted"}


# app/graph/nodes.py — updated quick_chat_prompt and quick_chat_response
quick_chat_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are MedBot, a friendly medical reference assistant. Respond briefly and warmly to this "
     "general/conversational message, using the conversation history for context if relevant. "
     "Do not provide medical information here — if the person has a medical question, gently invite "
     "them to ask it. Keep it short, 1-2 sentences."),
    ("human", "History:\n{history}\n\nMessage: {question}"),
])


def quick_chat_response(state: State) -> dict:
    history_text = format_history(state.get("history", []))
    try:
        result = (quick_chat_prompt | grading_llm).invoke({"question": state["question"], "history": history_text})
        return {"final_answer": result.content}
    except Exception as e:
        logger.error(f"Quick chat response failed: {e}")
        return {"final_answer": "Hi! Ask me anything medical and I'll do my best to help, using the reference material I have."}


contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Given the conversation history and a follow-up question, rewrite the follow-up into a "
     "standalone question that includes all necessary context, so it makes sense without the history.\n"
     "If the question is already standalone (doesn't reference prior context), return it unchanged.\n"
     "Do NOT answer the question — only rewrite it. Output the rewritten question as plain text, nothing else."),
    ("human", "History:\n{history}\n\nFollow-up question: {question}\n\nStandalone question:"),
])


def contextualize_question(state: State) -> dict:
    history = state.get("history", [])
    if not history:
        return {"search_question": state["question"]}

    try:
        result = (contextualize_prompt | grading_llm).invoke({
            "question": state["question"], "history": format_history(history)
        })
        rewritten = result.content.strip()
        logger.info(f"Contextualized question: '{state['question']}' -> '{rewritten}'")
        return {"search_question": rewritten}
    except Exception as e:
        logger.warning(f"Contextualization failed, using original question: {e}")
        return {"search_question": state["question"]}


def check_cache(state: State) -> dict:
    if state.get("bypass_cache"):
        return {}
    if state.get("history"):  # follow-ups are context-dependent — never trust a bare-text cache lookup
        return {}
    q = state.get("search_question") or state["question"]
    hit = get_cached_answer(q)
    if hit:
        return {"final_answer": hit.final_answer, "fallback_reason": f"cache_{hit.source}"}
    return {}


# =====================================================================
# 2. Retrieve + rerank
# =====================================================================
def retrieve_and_rerank(state: State) -> dict:
    question = state.get("search_question") or state["question"]

    try:
        query_emb = embed_query(question)
        retrieved = query_vectorstore(query_emb, top_k=settings.retrieval_top_k)
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return {"retrieved_chunks": [], "reranked_chunks": []}

    if not retrieved:
        return {"retrieved_chunks": [], "reranked_chunks": []}

    try:
        reranked = rerank_chunks(question, retrieved, top_n=settings.rerank_top_n)
    except Exception as e:
        logger.warning(f"Rerank failed, falling back to embedding-order top-N: {e}")
        reranked = retrieved[: settings.rerank_top_n]

    return {"retrieved_chunks": retrieved, "reranked_chunks": reranked}


# =====================================================================
# 3. Grade chunks (CRAG core)
# =====================================================================
grade_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict retrieval evaluator for a medical reference RAG system.\n"
     "You will be given ONE retrieved chunk from a clinical guidelines manual and a question.\n"
     "IMPORTANT: chunks are combined with other chunks to build the final answer — you are NOT "
     "judging whether this chunk ALONE fully answers the question. Judge whether this chunk contains "
     "information that is directly useful and relevant for answering (all or part of) the question.\n"
     "Score in [0.0, 1.0]:\n"
     "- 1.0: chunk contains information directly relevant and useful toward answering the question "
     "(even if it only covers part of a multi-part question, e.g. only treatment, not symptoms)\n"
     "- 0.5: chunk is topically related but only loosely useful (e.g. a cross-reference, footnote, "
     "or a different sub-population/edge case)\n"
     "- 0.0: chunk is irrelevant to the question's topic entirely\n"
     "Be conservative about topic relevance, but do NOT penalize a chunk for only covering part of "
     "a multi-part question — that is expected and other chunks will cover the rest.\n"
     "Output JSON only."),
    ("human", "Question: {question}\n\nChunk:\n{chunk}"),
])
grade_chain = grade_prompt | grading_llm.with_structured_output(DocGradeScore)


def grade_chunks(state: State) -> dict:
    question = state.get("search_question") or state["question"]
    chunks: List[RetrievedChunk] = state.get("reranked_chunks", [])

    if not chunks:
        return {
            "chunk_grades": [], "strong_chunks": [],
            "verdict": "WEAK", "verdict_reason": "No chunks retrieved.",
        }

    grades: List[DocGradeScore] = []
    strong_chunks: List[RetrievedChunk] = []
    grading_failures = 0

    for chunk in chunks:
        try:
            grade: DocGradeScore = grade_chain.invoke({"question": question, "chunk": chunk.text})
        except Exception as e:
            logger.warning(f"Grading call failed for a chunk (infra issue, not a relevance signal): {e}")
            grading_failures += 1
            continue  # don't score this chunk at all — skip it, don't count it as "irrelevant"

        grades.append(grade)
        if grade.score >= settings.grade_upper_threshold:
            strong_chunks.append(chunk)

    # If most/all grading calls failed, this is an infra outage, not "book lacks content" —
    # don't let it fall through to web search; surface it honestly instead.
    if grading_failures > 0 and grading_failures >= len(chunks) * 0.6:
        return {
            "chunk_grades": grades,
            "strong_chunks": [],
            "verdict": "ERROR",
            "verdict_reason": f"Grading unavailable ({grading_failures}/{len(chunks)} calls failed — likely rate-limited).",
        }

    strong_count = len(strong_chunks)
    context_chunks = [c for c, g in zip(chunks, grades) if g.score >= settings.context_inclusion_threshold] if grades else []

    if strong_count >= settings.min_strong_chunks_for_correct:
        verdict = "CORRECT"
        verdict_reason = f"{strong_count} chunk(s) scored >= {settings.grade_upper_threshold}."
    else:
        verdict = "WEAK"
        verdict_reason = f"Only {strong_count} chunk(s) scored >= {settings.grade_upper_threshold}, need {settings.min_strong_chunks_for_correct}."

    logger.info(f"Grading verdict: {verdict} ({verdict_reason}) — {len(context_chunks)} chunks passed to context")
    return {
        "chunk_grades": grades,
        "strong_chunks": context_chunks,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }


# =====================================================================
# 4. Generate answer (only reached on CORRECT verdict)
# =====================================================================
generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a medical reference assistant answering ONLY from the excerpts provided below.\n\n"
     "CONTENT RULES:\n"
     "1. Use ONLY the provided context. Do not add information from general medical knowledge.\n"
     "2. If a specific number, dose, or detail is not in the context, explicitly say it isn't specified "
     "rather than estimating or guessing.\n"
     "3. When you state a specific fact, reference which excerpt it came from using [Excerpt N] markers.\n"
     "4. When copying numeric values (doses, ages, percentages, units) from the context, copy them "
     "EXACTLY as written — do not paraphrase, round, or change units.\n"
     "5. Do not diagnose the user personally — present information as general reference material.\n"
     "6. Use the conversation history only to understand context/follow-ups — never as a source of facts.\n\n"
     "FORMATTING RULES — always structure your answer, never a dense wall of text:\n"
     "- Use short paragraphs (2-3 sentences max) for explanations.\n"
     "- Use markdown bullet points ('- ') whenever listing symptoms, causes, steps, or any enumerable "
     "items — this is the default for most medical content, not an exception.\n"
     "- Bold (**term**) key clinical terms the first time they appear.\n"
     "- Use a short intro sentence before a bullet list, not the list cold.\n\n"
     "ADAPT TO HOW THE PERSON ASKED:\n"
     "- If they ask to explain it 'simply', 'in plain terms', or say they're confused/don't understand: "
     "use short sentences, plain everyday language, minimal jargon (or define jargon immediately), and "
     "keep it brief — a few short bullets or 2-3 short sentences is enough.\n"
     "- If they ask for 'detail', 'more detail', or 'explain fully': cover the topic thoroughly, still "
     "organized with bullets/short paragraphs, not a single dense block.\n"
     "- If they explicitly ask for 'bullet points' or 'a list': answer primarily in bullets, minimal prose.\n"
     "- Otherwise (no explicit format request): default to a brief intro sentence + organized bullets for "
     "any list-like content, moderate length — not maximal detail, not overly terse."),
    ("human", "Conversation so far:\n{history}\n\nQuestion: {question}\n\nContext:\n{context}"),
])


def build_context_and_citations(chunks: List[RetrievedChunk]) -> tuple:
    context_parts = []
    citations = []
    for i, c in enumerate(chunks, start=1):
        context_parts.append(f"[Excerpt {i}] (Page {c.page}, Section: {c.section})\n{c.text}")
        citations.append({"page": c.page, "chapter": c.chapter, "section": c.section})
    return "\n\n".join(context_parts), citations


def format_history(history: list) -> str:
    if not history:
        return "(no prior messages)"
    return "\n".join(f"{h['role']}: {h['content']}" for h in history)


def generate_answer(state: State) -> dict:
    question = state["question"]
    strong_chunks = state.get("strong_chunks", [])
    history_text = format_history(state.get("history", []))

    context, citations = build_context_and_citations(strong_chunks)

    try:
        result = (generation_prompt | generation_llm).invoke({
            "question": question, "context": context, "history": history_text
        })
        answer = result.content
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        answer = ""

    return {"context": context, "citations": citations, "answer": answer}


# =====================================================================
# 5. Verify groundedness (audits the generated answer)
# =====================================================================
verify_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict fact-checker auditing an AI-generated medical answer against its source context.\n"
     "For EVERY specific factual claim in the answer (doses, symptoms, treatment steps, numbers), "
     "verify it is directly supported by the provided context.\n"
     "If ANY claim is not directly supported — including any number or detail that appears to be "
     "invented, estimated, or drawn from outside the context — mark grounded=false and list the "
     "unsupported claims specifically.\n"
     "Be strict: this is medical content and ungrounded claims are dangerous.\n"
     "Output JSON only."),
    ("human", "Context:\n{context}\n\nGenerated Answer:\n{answer}"),
])
verify_chain = verify_prompt | verifier_llm.with_structured_output(GroundednessResult)

web_verify_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a fact-checker auditing an AI-generated answer against web search excerpts.\n"
     "Mark grounded=true if the answer's claims are reasonably supported by the excerpts, even if "
     "phrased differently or synthesized across multiple excerpts — web content is naturally less "
     "structured than a reference book, so exact wording matches aren't required.\n"
     "Mark grounded=false only if the answer states something the excerpts don't support at all, or "
     "invents specific numbers/facts not present anywhere in the excerpts.\n"
     "Output JSON only."),
    ("human", "Web excerpts:\n{context}\n\nGenerated Answer:\n{answer}"),
])
web_verify_chain = web_verify_prompt | verifier_llm.with_structured_output(GroundednessResult)


def verify_groundedness(state: State) -> dict:
    context = state.get("context", "")
    answer = state.get("answer", "")
    chain = web_verify_chain if state.get("used_web") else verify_chain

    if not answer.strip():
        return {"groundedness": GroundednessResult(grounded=False, unsupported_claims=[], reason="No answer was generated.")}

    try:
        result: GroundednessResult = chain.invoke({"context": context, "answer": answer})
    except Exception as e:
        logger.error(f"Groundedness verification failed, defaulting to ungrounded (fail-safe): {e}")
        result = GroundednessResult(grounded=False, unsupported_claims=[], reason="Verification call failed.")

    logger.info(f"Groundedness check: grounded={result.grounded}")
    return {"groundedness": result}


# --- Web query rewrite (only reached when book content is insufficient) ---
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Rewrite the user's medical question into a short, effective web search query (6-12 words). "
     "Keep it factual and specific. Do NOT answer the question — only rewrite it as a search query. "
     "Output plain text only, nothing else."),
    ("human", "Question: {question}"),
])


def rewrite_web_query(state: State) -> dict:
    q = state.get("search_question") or state["question"]
    try:
        result = (rewrite_prompt | grading_llm).invoke({"question": q})
        rewritten = result.content.strip()
    except Exception as e:
        logger.warning(f"Query rewrite failed, using original question: {e}")
        rewritten = q
    logger.info(f"Web search query: {rewritten}")
    return {"web_query": rewritten}


def web_search_node(state: State) -> dict:
    query = state.get("web_query") or state["question"]
    try:
        results = web_search(query)
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        results = []
    return {"web_results": results}


def build_web_context_and_citations(results: List[WebResult]):
    context_parts, citations = [], []
    for i, r in enumerate(results, start=1):
        context_parts.append(f"[Excerpt {i}] (Source: {r['title']}, {r['url']})\n{r['content']}")
        citations.append({"type": "web", "title": r["title"], "url": r["url"]})
    return "\n\n".join(context_parts), citations


web_generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a medical reference assistant. The reference book didn't cover this question, so you're "
     "answering from web search results instead.\n\n"
     "CONTENT RULES:\n"
     "1. Use ONLY the provided web excerpts. Do not add outside knowledge.\n"
     "2. If specific details aren't in the excerpts, say so rather than guessing.\n"
     "3. When you state a fact, reference which excerpt it came from using [Excerpt N] markers.\n"
     "4. Copy numeric values (doses, ages, units) EXACTLY as written — never paraphrase or round them.\n"
     "5. Present information as general reference material, never a personal diagnosis.\n"
     "6. Use conversation history only for context on follow-ups, never as a source of facts.\n\n"
     "FORMATTING RULES — always structure your answer, never a dense wall of text:\n"
     "- Short paragraphs (2-3 sentences max) for explanations.\n"
     "- Markdown bullet points ('- ') for symptoms, causes, steps, or any enumerable items — default, "
     "not an exception.\n"
     "- Bold (**term**) key clinical terms on first mention.\n"
     "- A short intro sentence before any bullet list.\n\n"
     "ADAPT TO HOW THE PERSON ASKED:\n"
     "- 'Simply' / plain terms / confused: short sentences, everyday language, brief.\n"
     "- 'Detail' / 'explain fully': thorough but still organized, not one dense block.\n"
     "- 'Bullet points' / 'list': primarily bullets, minimal prose.\n"
     "- No explicit request: brief intro + organized bullets, moderate length."),
    ("human", "Conversation so far:\n{history}\n\nQuestion: {question}\n\nWeb excerpts:\n{context}"),
])


def generate_from_web(state: State) -> dict:
    question = state["question"]
    results = state.get("web_results", [])
    history_text = format_history(state.get("history", []))

    if not results:
        return {"answer": "", "context": "", "citations": [], "used_web": True}

    context, citations = build_web_context_and_citations(results)
    try:
        result = (web_generation_prompt | generation_llm).invoke({
            "question": question, "context": context, "history": history_text
        })
        answer = result.content
    except Exception as e:
        logger.error(f"Web-grounded generation failed: {e}")
        answer = ""

    return {"context": context, "citations": citations, "answer": answer, "used_web": True}

# =====================================================================
# 6. Terminal nodes
# =====================================================================
# app/graph/nodes.py — replace format_final_answer
def format_final_answer(state: State) -> dict:
    if state.get("fallback_reason", "").startswith("cache_"):
        return {}

    answer = state.get("answer", "")
    citations = state.get("citations", [])
    used_web = state.get("used_web", False)
    question = state.get("search_question") or state["question"]

    lines = []
    for c in citations:
        if c.get("type") == "web":
            lines.append(f"- {c['title']} — {c['url']}")
        else:
            lines.append(f"- Page {c['page']}, {c['chapter']} — {c['section']}")
    citation_lines = "\n".join(lines)

    source_label = "Web sources" if used_web else "Sources"
    web_note = (
        "\n\n_Note: this topic wasn't covered in the reference book, so this answer is drawn from the web instead._"
        if used_web else ""
    )

    treatment_note = TREATMENT_WARNING if is_treatment_related(question) else ""

    final = (
        f"{treatment_note}{answer}{web_note}\n\n"
        f"**{source_label}:**\n{citation_lines}\n\n"
        f"_This is reference information only and not a substitute for professional medical care._"
    )

    if not state.get("history"):  # only cache genuinely standalone, context-free questions
        set_cached_answer(state["question"], final)

    return {"final_answer": final}


def emergency_fallback(state: State) -> dict:
    final = (
        "⚠️ This sounds like it could be a medical emergency. I'm not able to help with this — "
        "please seek emergency care or visit a doctor right away."
    )
    return {"final_answer": final, "fallback_reason": "emergency"}


def weak_evidence_fallback(state: State) -> dict:
    final = (
        "I couldn't find a confident answer in the reference book or the web. "
        "Please consult a medical professional or another reliable source."
    )
    return {"final_answer": final, "fallback_reason": "insufficient_evidence"}


def ungrounded_fallback(state: State) -> dict:
    g: GroundednessResult = state.get("groundedness")
    claims = "; ".join(g.unsupported_claims) if g and g.unsupported_claims else "unspecified"
    final = (
        "I found related information in the manual, but I couldn't verify that my generated answer "
        "was fully supported by it, so I'm not confident enough to present it. "
        "Please consult a medical professional or rephrase your question.\n\n"
        f"(Unverified claims: {claims})"
    )
    return {"final_answer": final, "fallback_reason": "ungrounded"}


def service_busy_fallback(state: State) -> dict:
    final = (
        "I'm temporarily unable to search the reference material right now — this looks like a "
        "capacity limit on my end, not a gap in the content. Please try again in a few minutes."
    )
    return {"final_answer": final, "fallback_reason": "service_busy"}



