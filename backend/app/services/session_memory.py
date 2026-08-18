# app/services/session_memory.py
"""
In-memory session history, last N messages per session. Scoped as "for now"
per plan — swap to Redis/DB-backed storage later if running multiple server
instances or needing persistence across restarts.
"""
from collections import deque
from typing import List, Dict
import threading

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("medbot.session_memory")

MAX_HISTORY = 10  # last 10 messages (5 user + 5 assistant turns, roughly)

_sessions: Dict[str, deque] = {}
_lock = threading.Lock()


def get_history(session_id: str) -> List[Dict[str, str]]:
    with _lock:
        return list(_sessions.get(session_id, []))


def add_turn(session_id: str, role: str, content: str):
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = deque(maxlen=MAX_HISTORY)
        _sessions[session_id].append({"role": role, "content": content})


def clear_session(session_id: str):
    with _lock:
        _sessions.pop(session_id, None)
        logger.info(f"Cleared session {session_id}")