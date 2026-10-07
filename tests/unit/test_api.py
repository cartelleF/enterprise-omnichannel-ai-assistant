from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "enterprise-omnichannel-ai-assistant",
    }


def test_chat():
    response = client.post(
        "/chat",
        json={
            "question": "Can I still return order ORD-10066?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == (
        "Can I still return order ORD-10066?"
    )
    assert data["route"] == "DEMO"
    assert "API is running successfully" in data["answer"]
    assert data["sources"] == []


def test_chat_rejects_empty_question():
    response = client.post(
        "/chat",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_chat_rejects_too_long_question():
    response = client.post(
        "/chat",
        json={"question": "A" * 1001},
    )

    assert response.status_code == 422
