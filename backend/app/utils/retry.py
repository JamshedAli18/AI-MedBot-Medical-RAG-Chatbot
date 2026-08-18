# app/utils/retry.py
import time
import functools
from app.utils.logger import get_logger

logger = get_logger("medbot.retry")


def with_retry(retries: int = 2, base_wait: float = 1.0, label: str = "call"):
    """Decorator: retries a function on any exception with exponential backoff.
    Re-raises the final exception after all retries are exhausted (caller decides fallback)."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    wait = base_wait * (2 ** (attempt - 1))
                    logger.warning(f"{label} failed (attempt {attempt}/{retries}): {e}. Retrying in {wait:.1f}s")
                    if attempt < retries:
                        time.sleep(wait)
            logger.error(f"{label} failed after {retries} attempts")
            raise last_exc
        return wrapper
    return decorator