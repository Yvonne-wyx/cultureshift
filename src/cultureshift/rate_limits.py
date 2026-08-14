from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Lock


class FixedWindowRateLimiter:
    def __init__(self, *, limit: int, window: timedelta) -> None:
        if limit < 1 or window <= timedelta(0):
            raise ValueError("limit and window must be positive")
        self._limit = limit
        self._window = window
        self._entries: dict[str, tuple[datetime, int]] = {}
        self._lock = Lock()

    def allow(self, key: str, *, now: datetime | None = None) -> bool:
        if not key:
            raise ValueError("rate-limit key is required")
        checked_at = now or datetime.now(UTC)
        if checked_at.tzinfo is None or checked_at.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        with self._lock:
            window_start, count = self._entries.get(key, (checked_at, 0))
            if checked_at >= window_start + self._window:
                window_start, count = checked_at, 0
            if count >= self._limit:
                return False
            self._entries[key] = (window_start, count + 1)
            return True
