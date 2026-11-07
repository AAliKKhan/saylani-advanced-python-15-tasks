"""
Task 08 | Cache Decorator with Expiration
Decorators, closures, functools, time

Problem: Implement @ttl_cache(seconds) that caches results for repeated
positional and keyword arguments and recomputes after expiration. Track cache
hits and misses.

Requirements:
  - Preserve function metadata with functools.wraps.
  - Handle equivalent keyword argument order.
  - Document behavior for unhashable inputs.
  - Use time.monotonic().

Sample / Expected Behavior:
  A call with x=2, y=3 followed by y=3, x=2 before expiry should return a
  cache hit.
"""

import functools
import time
from collections import namedtuple

CacheInfo = namedtuple("CacheInfo", "hits misses maxsize ttl currsize")

_MISSING = object()


def ttl_cache(seconds):
    """Cache decorator with a time-to-live in seconds.

    Key construction
      * positional arguments are used as given,
      * keyword arguments are sorted by name, so ``f(x=2, y=3)`` and
        ``f(y=3, x=2)`` share one entry.

    Unhashable arguments (lists, dicts, sets, ...) cannot be used as dict
    keys. When a key cannot be hashed the call is simply passed through to
    the wrapped function without caching, so the program keeps working
    instead of raising TypeError.

    Note that ``f(2, y=3)`` and ``f(x=2, y=3)`` are different keys, exactly
    like a normal function call.
    """
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError(f"ttl_cache needs a number of seconds, got {seconds!r}")
    if seconds <= 0:
        raise ValueError(f"ttl_cache seconds must be positive, got {seconds!r}")

    def decorator(func):
        store = {}
        stats = {"hits": 0, "misses": 0}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            try:
                hash(key)
            except TypeError:
                # Unhashable arguments: run uncached.
                return func(*args, **kwargs)

            now = time.monotonic()
            entry = store.get(key, _MISSING)
            if entry is not _MISSING and entry[1] > now:
                stats["hits"] += 1
                return entry[0]

            stats["misses"] += 1
            value = func(*args, **kwargs)
            store[key] = (value, time.monotonic() + seconds)
            return value

        def cache_info():
            return CacheInfo(hits=stats["hits"], misses=stats["misses"],
                             maxsize=None, ttl=seconds, currsize=len(store))

        def cache_clear():
            store.clear()
            stats["hits"] = 0
            stats["misses"] = 0

        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        wrapper.ttl_seconds = seconds
        return wrapper

    return decorator


_CALLS = []


@ttl_cache(60)
def slow_sum(x, y):
    """Sample cached function used by the demo below."""
    _CALLS.append((x, y))
    return x + y


if __name__ == "__main__":
    import time as _time

    slow_sum.cache_clear()

    # Keyword order must not matter.
    assert slow_sum(x=2, y=3) == 5
    assert slow_sum(y=3, x=2) == 5
    info = slow_sum.cache_info()
    assert info.hits == 1 and info.misses == 1, info
    assert len(_CALLS) == 1

    # Positional call is a different key.
    assert slow_sum(2, 3) == 5
    assert slow_sum.cache_info().misses == 2

    # Metadata preserved.
    assert slow_sum.__name__ == "slow_sum"
    assert slow_sum.__doc__.startswith("Sample cached function")

    # Expiry: a 0.05s ttl recomputes after sleeping.
    @ttl_cache(0.05)
    def tick(value):
        _CALLS.append(value)
        return value

    tick(1)
    tick(1)
    assert tick.cache_info().hits == 1
    _time.sleep(0.06)
    tick(1)
    assert tick.cache_info().misses == 2

    # Unhashable input does not raise; it just bypasses the cache.
    @ttl_cache(30)
    def join_all(items):
        _CALLS.append(tuple(items))
        return "".join(items)

    assert join_all(["a", "b"]) == "ab"
    assert join_all(["a", "b"]) == "ab"

    print("all sample cases passed")
