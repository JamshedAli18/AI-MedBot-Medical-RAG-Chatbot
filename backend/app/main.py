# app/main.py
import asyncio
import json
import time
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.dependencies import get_current_identity
from app.graph.build import app as graph_app
from app.models.schemas import ChatRequest, HealthResponse, HomeResponse
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.sessions import router as sessions_router
from app.services import chat_sessions
from app.services.database import ensure_indexes
from app.services.guest import increment_guest_usage
from app.services.session_memory import get_history, add_turn
from app.utils.logger import get_logger

logger = get_logger("medbot.main")

app = FastAPI(title="MedBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend domain before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(sessions_router)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    logger.info("Startup complete — MongoDB indexes ensured.")

STAGE_LABELS = {
    "triage_message": "Checking your message",
    "check_cache": "Checking cache",
    "contextualize_question": "Understanding your question",
    "retrieve_and_rerank": "Searching reference material",
    "grade_chunks": "Evaluating sources",
    "rewrite_web_query": "Checking the web",
    "web_search_node": "Searching the web",
    "generate_from_web": "Drafting answer",
    "generate_answer": "Drafting answer",
    "verify_groundedness": "Verifying accuracy",
    "reformat_answer": "Adjusting the answer",
}

# Nodes whose output IS the final answer — stream the text once these fire
TERMINAL_NODES = {
    "quick_chat_response", "emergency_fallback", "weak_evidence_fallback",
    "ungrounded_fallback", "service_busy_fallback", "format_final_answer",
    "check_cache", "reformat_answer",
}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/", response_model=HomeResponse)
async def home():
    return HomeResponse(
        service="MedBot API",
        version="1.0.0",
        endpoints=["/", "/health", "/chat (POST, streaming SSE)"],
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    # extend this with real dependency checks (Pinecone/Groq/Cohere ping) if needed later
    return HealthResponse(status="ok", service="medbot-api")


@app.post("/chat")
async def chat(req: ChatRequest, identity: dict = Depends(get_current_identity)):
    # --- Guest path: unchanged from before ---
    if identity["type"] == "guest":
        if identity["limit_reached"]:
            async def guest_limit_stream():
                msg = (
                    "You've reached the 10-question limit for guest mode. "
                    "Please sign up (it's free) to keep chatting with no limit."
                )
                yield sse("done", {"final_answer": msg})
            logger.info(f"Guest {identity['guest_id']} blocked — limit reached")
            return StreamingResponse(guest_limit_stream(), media_type="text/event-stream")

        await increment_guest_usage(identity["guest_id"])
        history = get_history(req.session_id)

    # --- Registered user path: real persisted session, 20-message cap ---
    else:
        session_doc = await chat_sessions.get_session(req.session_id, identity["user_id"])
        if not session_doc:
            async def not_found_stream():
                yield sse("error", {"message": "Session not found. Please start a new chat."})
            return StreamingResponse(not_found_stream(), media_type="text/event-stream")

        if chat_sessions.session_limit_reached(session_doc.get("message_count", 0)):
            async def session_limit_stream():
                msg = (
                    "This chat has reached its 20-question limit. "
                    "Please start a new chat to continue."
                )
                yield sse("done", {"final_answer": msg})
            logger.info(f"Session {req.session_id} blocked — 20-message limit reached")
            return StreamingResponse(session_limit_stream(), media_type="text/event-stream")

        history = chat_sessions.get_history_for_context(session_doc)

    # --- shared debug trace state, request timing, node sequence (unchanged) ---
    request_start = time.time()
    node_sequence = []
    node_timings = {}
    debug = {
        "session_id": req.session_id,
        "message": req.message,
        "message_type": None,
        "is_emergency": None,
        "used_cache": False,
        "cache_source": None,
        "search_question": None,
        "verdict": None,
        "used_web": False,
        "web_query": None,
        "grounded": None,
        "fallback_reason": None,
    }
    last_node_start = time.time()

    async def event_stream():
        nonlocal last_node_start
        final_answer = None
        seen_stages = set()

        logger.info(f"[chat:{req.session_id}] >>> incoming message: {req.message!r}")

        try:
            async for update in graph_app.astream({"question": req.message, "history": history}):
                for node_name, partial in update.items():
                    now = time.time()
                    elapsed = now - last_node_start
                    last_node_start = now
                    node_sequence.append(node_name)
                    node_timings[node_name] = round(elapsed, 2)
                    logger.info(f"[chat:{req.session_id}] node fired: {node_name} (+{elapsed:.2f}s)")

                    label = STAGE_LABELS.get(node_name)
                    if label and node_name not in seen_stages:
                        seen_stages.add(node_name)
                        yield sse("stage", {"stage": label})

                    if not partial:
                        continue

                    # --- capture debug signals as they appear in graph state updates ---
                    if "message_type" in partial:
                        debug["message_type"] = partial["message_type"]
                    if "is_emergency" in partial:
                        debug["is_emergency"] = partial["is_emergency"]
                    if "search_question" in partial:
                        debug["search_question"] = partial["search_question"]
                    if "verdict" in partial:
                        debug["verdict"] = partial["verdict"]
                    if "web_query" in partial:
                        debug["web_query"] = partial["web_query"]
                        debug["used_web"] = True
                    if "used_web" in partial:
                        debug["used_web"] = partial["used_web"]
                    if partial.get("fallback_reason"):
                        debug["fallback_reason"] = partial["fallback_reason"]
                        if str(partial["fallback_reason"]).startswith("cache_"):
                            debug["used_cache"] = True
                            debug["cache_source"] = partial["fallback_reason"].replace("cache_", "")
                    if "groundedness" in partial and partial["groundedness"] is not None:
                        debug["grounded"] = partial["groundedness"].grounded

                    if node_name in TERMINAL_NODES and partial.get("final_answer"):
                        final_answer = partial["final_answer"]

            if final_answer is None:
                final_answer = "Something went wrong generating a response. Please try again."
                debug["fallback_reason"] = debug["fallback_reason"] or "no_final_answer_produced"

            # stream the finished, verified answer progressively for a typing effect
            chunk_size = 40
            for i in range(0, len(final_answer), chunk_size):
                yield sse("token", {"text": final_answer[i:i + chunk_size]})
                await asyncio.sleep(0.015)

            yield sse("done", {"final_answer": final_answer})

            # --- persist the turn, depending on identity type ---
            if identity["type"] == "guest":
                add_turn(req.session_id, "user", req.message)
                add_turn(req.session_id, "assistant", final_answer)
            else:
                await chat_sessions.append_message(req.session_id, "user", req.message)
                await chat_sessions.append_message(req.session_id, "assistant", final_answer)
                await chat_sessions.maybe_set_title(req.session_id, req.message)

        except Exception as e:
            logger.error(f"[chat:{req.session_id}] Chat stream failed: {e}")
            debug["fallback_reason"] = f"exception: {e}"
            yield sse("error", {"message": "An error occurred processing your request."})

        finally:
            total_time = round(time.time() - request_start, 2)
            path = " -> ".join(node_sequence) if node_sequence else "(none)"

            logger.info(
                "\n"
                f"[chat:{req.session_id}] === DEBUG SUMMARY ===\n"
                f"  message           : {debug['message']!r}\n"
                f"  message_type      : {debug['message_type']}\n"
                f"  is_emergency      : {debug['is_emergency']}\n"
                f"  used_cache        : {debug['used_cache']} (source={debug['cache_source']})\n"
                f"  search_question   : {debug['search_question']}\n"
                f"  verdict           : {debug['verdict']}\n"
                f"  used_web          : {debug['used_web']} (query={debug['web_query']})\n"
                f"  grounded          : {debug['grounded']}\n"
                f"  fallback_reason   : {debug['fallback_reason']}\n"
                f"  node path         : {path}\n"
                f"  node timings (s)  : {node_timings}\n"
                f"  total time        : {total_time}s\n"
                f"======================================"
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")