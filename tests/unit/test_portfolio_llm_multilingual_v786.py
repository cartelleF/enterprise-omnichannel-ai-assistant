"""Multilingual configuration tests for the optional LLM backend."""

from unittest.mock import Mock, patch

from src.api.local_ai_runtime import build_local_ai_service_from_env


def test_llm_runtime_preserves_multilingual_configuration(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("LOCAL_AI_API_KEY", "fake-test-key")
    monkeypatch.setenv("LOCAL_AI_MODEL", "fake-model")
    monkeypatch.setenv("LOCAL_AI_DAILY_LIMIT", "5")
    monkeypatch.setenv(
        "LOCAL_AI_QUOTA_DB",
        str(tmp_path / "quota.db"),
    )

    with patch("src.api.local_ai_runtime.OpenAI") as mock_openai:
        mock_openai.return_value = Mock()
        service = build_local_ai_service_from_env()

    assert service.local_service.multilingual_retrieval is True
    assert service.local_service.multilingual_formatting is True
    assert service.llm_quota.max_calls == 5


def test_llm_runtime_uses_five_as_default_quota(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("LOCAL_AI_API_KEY", "fake-test-key")
    monkeypatch.setenv("LOCAL_AI_MODEL", "fake-model")
    monkeypatch.delenv("LOCAL_AI_DAILY_LIMIT", raising=False)
    monkeypatch.setenv(
        "LOCAL_AI_QUOTA_DB",
        str(tmp_path / "quota.db"),
    )

    with patch("src.api.local_ai_runtime.OpenAI"):
        service = build_local_ai_service_from_env()

    assert service.llm_quota.max_calls == 5
