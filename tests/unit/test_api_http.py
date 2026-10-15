import pytest
from fastapi.testclient import TestClient

from src.api.main import app, get_assistant_service
from src.api.rate_limit import rate_limiter


class FakeAssistantService:
    def __init__(self, generation_mode="llm"):
        self.generation_mode = generation_mode

    def ask(self, question):
        return {
            "question": question,
            "route": "RAG",
            "answer": "Customers have 30 days to request a return.",
            "sources": ["return_policy.txt"],
            "generation_mode": self.generation_mode,
        }


@pytest.fixture
def client():
    with rate_limiter.lock:
        rate_limiter.requests.clear()

    app.dependency_overrides[get_assistant_service] = (
        lambda: FakeAssistantService()
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_assistant_service, None)
        with rate_limiter.lock:
            rate_limiter.requests.clear()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint(client):
    response = client.post(
        "/chat",
        json={"question": "What is the return policy?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "RAG"
    assert data["generation_mode"] == "llm"
    assert data["sources"] == ["return_policy.txt"]
    assert "30 days" in data["answer"]


@pytest.mark.parametrize(
    "mode",
    ["llm", "deterministic", "local_fallback"],
)
def test_generation_mode(client, mode):
    app.dependency_overrides[get_assistant_service] = (
        lambda: FakeAssistantService(mode)
    )

    response = client.post(
        "/chat",
        json={"question": "What is the return policy?"},
    )

    assert response.status_code == 200
    assert response.json()["generation_mode"] == mode


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "a"},
        {"question": "a" * 1001},
        {},
    ],
)
def test_invalid_chat_request(client, payload):
    response = client.post("/chat", json=payload)

    assert response.status_code == 422
