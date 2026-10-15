from fastapi.testclient import TestClient

from src.api.main import app, get_assistant_service


class FakeLocalService:
    def ask(self, question: str) -> dict:
        return {
            "question": question,
            "route": "RAG",
            "answer": "Returns are allowed within 30 days.",
            "sources": ["return_policy.txt"],
        }


def test_local_backend_returns_deterministic_generation_mode(monkeypatch):
    monkeypatch.setenv("ASSISTANT_BACKEND", "local")
    app.dependency_overrides[get_assistant_service] = lambda: FakeLocalService()

    try:
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"question": "What is the return policy?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["route"] == "RAG"
        assert data["generation_mode"] == "deterministic"
        assert data["sources"] == ["return_policy.txt"]
    finally:
        app.dependency_overrides.pop(get_assistant_service, None)
