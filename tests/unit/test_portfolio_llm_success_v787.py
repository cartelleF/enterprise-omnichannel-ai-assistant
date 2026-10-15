"""Verify successful LLM rewriting without external API calls."""

from unittest.mock import Mock

from src.api.local_ai_service import LocalAIService


def test_valid_llm_rewrite_preserves_sources():
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
    llm_client.responses.create.return_value.output_text = (
        "The warranty for product PROD-1001 is 24 months. "
        "It covers manufacturing defects."
    )

    service = LocalAIService(
        llm_client=llm_client,
        model_name="fake-model",
        local_service=local_service,
    )

    result = service.ask("What is the warranty for PROD-1001?")

    assert result["generation_mode"] == "llm"
    assert "24 months" in result["answer"]
    assert result["sources"] == ["PROD-1001_warranty.txt"]

    llm_client.responses.create.assert_called_once()
