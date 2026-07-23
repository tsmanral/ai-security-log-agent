"""
Bounded sliding-window rate limiter (§6 #5).

The previous per-endpoint rate limiters used an unbounded ``defaultdict`` keyed
by device_id / client IP, so every distinct — including dead or spoofed —
identifier added a permanent entry: a slow memory-exhaustion vector. This
limiter keeps at most ``max_keys`` windows (LRU eviction) and opportunistically
drops idle keys whose window has fully aged out.

Not thread-safe on its own; callers touch it synchronously under the FastAPI
event loop, which is sufficient here. Persistence is descoped to M1.
"""

from collections import OrderedDict, deque


class SlidingWindowRateLimiter:
    """Fixed-window-per-key limiter with a hard LRU cap on the number of keys."""

    def __init__(self, limit: int, window_seconds: float = 60.0, max_keys: int = 10_000):
        self._limit = limit
        self._window = float(window_seconds)
        self._max_keys = max_keys
        self._hits: "OrderedDict[str, deque]" = OrderedDict()
        self._last_sweep = 0.0

    def allow(self, key: str, now: float) -> bool:
        """Record a hit for ``key`` at time ``now``; return False if over limit."""
        window = self._hits.get(key)
        if window is None:
            window = deque()
            self._hits[key] = window          # inserted as most-recently-used
        else:
            self._hits.move_to_end(key)        # mark most-recently-used

        cutoff = now - self._window
        while window and window[0] <= cutoff:
            window.popleft()

        allowed = len(window) < self._limit
        if allowed:
            window.append(now)

        self._maybe_sweep(now)
        self._enforce_cap()
        return allowed

    def _maybe_sweep(self, now: float) -> None:
        """Throttled idle-key eviction (at most once per window)."""
        if now - self._last_sweep < self._window:
            return
        self._last_sweep = now
        cutoff = now - self._window
        stale = [k for k, w in self._hits.items() if not w or w[-1] <= cutoff]
        for k in stale:
            del self._hits[k]

    def _enforce_cap(self) -> None:
        """Hard bound: evict least-recently-used keys beyond ``max_keys``."""
        while len(self._hits) > self._max_keys:
            self._hits.popitem(last=False)

    def __len__(self) -> int:
        return len(self._hits)

    def __contains__(self, key: str) -> bool:
        return key in self._hits
