"""Verify safe fallback when the LLM provider fails."""

from unittest.mock import Mock

from src.api.llm_quota import DailyLLMQuota
from src.api.local_ai_service import LocalAIService


def test_provider_failure_returns_deterministic_answer(tmp_path):
    quota = DailyLLMQuota(
        db_path=tmp_path / "quota.db",
        max_calls=5,
    )

    local_service = Mock()
    local_service.ask.return_value = {
        "question": "What is the warranty for PROD-1001?",
        "answer": (
            "The warranty for product PROD-1001 is 24 months. "
            "The warranty covers manufacturing defects."
        ),
        "route": "RAG",
        "sources": ["PROD-1001_warranty.txt"],
    }

    llm_client = Mock()
    llm_client.responses.create.side_effect = RuntimeError(
        "Simulated OpenAI service failure"
    )

    service = LocalAIService(
        llm_client=llm_client,
        model_name="fake-model",
        local_service=local_service,
        llm_quota=quota,
    )

    result = service.ask(
        "What is the warranty for PROD-1001?"
    )

    assert result["generation_mode"] == "local_fallback"
    assert "24 months" in result["answer"]
    assert result["sources"] == ["PROD-1001_warranty.txt"]

    llm_client.responses.create.assert_called_once()


def test_provider_failure_consumes_one_quota_reservation(tmp_path):
    quota = DailyLLMQuota(
        db_path=tmp_path / "quota.db",
        max_calls=1,
    )

    local_service = Mock()
    local_service.ask.return_value = {
        "question": "What is the warranty for PROD-1001?",
        "answer": "The warranty is 24 months.",
        "route": "RAG",
        "sources": ["PROD-1001_warranty.txt"],
    }

    llm_client = Mock()
    llm_client.responses.create.side_effect = RuntimeError(
        "Simulated provider failure"
    )

    service = LocalAIService(
        llm_client=llm_client,
        model_name="fake-model",
        local_service=local_service,
        llm_quota=quota,
    )

    first = service.ask("Warranty for PROD-1001?")
    second = service.ask("Warranty for PROD-1001?")

    assert first["generation_mode"] == "local_fallback"
    assert second["generation_mode"] == "local_fallback"

    # The second request must not reach the provider.
    assert llm_client.responses.create.call_count == 1
