"""Test LLM quota fallback without external API calls."""

from unittest.mock import Mock

from src.api.llm_quota import DailyLLMQuota
from src.api.local_ai_service import LocalAIService


def test_exhausted_quota_prevents_llm_call(tmp_path):
    quota = DailyLLMQuota(
        db_path=tmp_path / "quota.db",
        max_calls=0,
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

    llm_client.responses.create.assert_not_called()
