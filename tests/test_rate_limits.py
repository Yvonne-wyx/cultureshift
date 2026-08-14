from datetime import UTC, datetime, timedelta

from cultureshift.rate_limits import FixedWindowRateLimiter


def test_fixed_window_limiter_isolated_by_key_and_resets() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window=timedelta(minutes=1))
    now = datetime(2026, 8, 14, 9, 0, tzinfo=UTC)

    assert limiter.allow("client-a", now=now) is True
    assert limiter.allow("client-a", now=now) is True
    assert limiter.allow("client-a", now=now) is False
    assert limiter.allow("client-b", now=now) is True
    assert limiter.allow("client-a", now=now + timedelta(minutes=1)) is True
