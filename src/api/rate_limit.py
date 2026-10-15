"""
Simple in-memory rate limiting for the portfolio demo.

Suitable for a single application process.
Not a distributed or production-grade rate limiter.
"""

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        if max_requests < 1 or window_seconds <= 0:
            raise ValueError("Invalid rate limit configuration")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, client_id: str):
        now = time.monotonic()

        with self.lock:
            timestamps = self.requests[client_id]

            while timestamps and now - timestamps[0] >= self.window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = max(
                    1,
                    int(self.window_seconds - (now - timestamps[0])) + 1,
                )

                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)


rate_limiter = InMemoryRateLimiter(
    max_requests=int(os.getenv("API_RATE_LIMIT", "10")),
    window_seconds=60,
)


def enforce_rate_limit(request: Request):
    # Use the directly connected client address.
    # Do not trust X-Forwarded-For from arbitrary callers.
    client_id = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    rate_limiter.check(client_id)
