import time
from functools import wraps
from typing import Any, Callable, Hashable, Tuple

DEFAULT_TTL_SECONDS = 60


def _make_key(args: Tuple[Any, ...], kwargs: dict[str, Any]) -> Hashable:
    return (args, tuple(sorted(kwargs.items())))


def ttl_cache(ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """
    Simple TTL cache decorator. Keeps the implementation local to avoid adding
    a heavy dependency. Suitable for read-heavy tools like reference lookups.
    """

    def decorator(fn: Callable):
        store: dict[Hashable, tuple[float, Any]] = {}

        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            now = time.time()
            if key in store:
                ts, value = store[key]
                if now - ts < ttl_seconds:
                    return value
                store.pop(key, None)
            result = fn(*args, **kwargs)
            store[key] = (now, result)
            return result

        return wrapper

    return decorator








