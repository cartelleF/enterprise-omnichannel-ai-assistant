from fastapi.testclient import TestClient

from src.api.main import app, get_assistant_service
from src.api.rate_limit import (
    InMemoryRateLimiter,
    enforce_rate_limit,
)


class FakeAssistantService:
    def ask(self, question):
        return {
            "route": "RAG",
            "answer": "Customers have 30 days to request a return.",
            "sources": ["return_policy.txt"],
            "generation_mode": "deterministic",
        }


def test_chat_rate_limit_returns_429():
    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    def limited_request():
        limiter.check("test-client")

    app.dependency_overrides[get_assistant_service] = (
        lambda: FakeAssistantService()
    )
    app.dependency_overrides[enforce_rate_limit] = limited_request

    try:
        with TestClient(app) as client:
            responses = [
                client.post(
                    "/chat",
                    json={"question": "What is the return policy?"},
                )
                for _ in range(3)
            ]

            assert [r.status_code for r in responses] == [
                200, 200, 429
            ]
            assert "Retry-After" in responses[2].headers

            # Health checks remain accessible.
            health = client.get("/health")
            assert health.status_code == 200

    finally:
        app.dependency_overrides.pop(enforce_rate_limit, None)
        app.dependency_overrides.pop(get_assistant_service, None)
