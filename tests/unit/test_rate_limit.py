import pytest
from fastapi import HTTPException

from src.api.rate_limit import InMemoryRateLimiter


def test_requests_within_limit_are_accepted():
    limiter = InMemoryRateLimiter(
        max_requests=3,
        window_seconds=60,
    )

    for _ in range(3):
        limiter.check("client-a")


def test_exceeding_limit_returns_429():
    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    limiter.check("client-a")
    limiter.check("client-a")

    with pytest.raises(HTTPException) as exc:
        limiter.check("client-a")

    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_clients_have_separate_limits():
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    limiter.check("client-a")
    limiter.check("client-b")

    with pytest.raises(HTTPException) as exc:
        limiter.check("client-a")

    assert exc.value.status_code == 429


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        InMemoryRateLimiter(max_requests=0)
