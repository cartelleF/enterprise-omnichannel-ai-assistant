"""
V6.1 — Local performance instrumentation.

Measures real elapsed time using a monotonic clock.
No cloud services, external telemetry, or LLM calls.
"""

from contextlib import contextmanager
from time import perf_counter


class PerformanceTracker:
    def __init__(self):
        self._start = perf_counter()
        self._timings = {}

    @contextmanager
    def measure(self, operation):
        start = perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            self._timings[operation] = (
                self._timings.get(operation, 0.0) + elapsed_ms
            )

    def summary(self):
        result = {
            key: round(value, 3)
            for key, value in self._timings.items()
        }
        result["total_ms"] = round(
            (perf_counter() - self._start) * 1000, 3
        )
        return result
