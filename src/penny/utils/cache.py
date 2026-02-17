"""TTL-based function result caching."""

from __future__ import annotations

import functools
import time
from typing import Any


def cache_with_ttl(ttl: int = 300):
    """Decorator that caches function results for *ttl* seconds."""

    def decorator(func):  # type: ignore[type-arg]
        cache: dict[Any, tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                result, ts = cache[key]
                if now - ts < ttl:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
