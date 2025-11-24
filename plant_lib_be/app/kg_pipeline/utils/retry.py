import time
from functools import wraps

from app.kg_pipeline.config.logging_config import get_logger

logger = get_logger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(exc)[:100]}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
            logger.error(f"{func.__name__} failed after {max_retries} attempts")
            raise last_exception

        return wrapper

    return decorator
