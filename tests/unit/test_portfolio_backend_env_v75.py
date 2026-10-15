"""Environment selection tests without paid LLM calls."""

from unittest.mock import patch
import pytest

from src.api.local_demo_service import LocalDemoService
from src.api.portfolio_backend import (
    select_portfolio_service_from_env,
)


def test_default_backend_is_deterministic(monkeypatch):
    monkeypatch.delenv("PORTFOLIO_BACKEND", raising=False)
    monkeypatch.delenv("PORTFOLIO_ENABLE_LOCAL_LLM", raising=False)

    service = select_portfolio_service_from_env()

    assert isinstance(service, LocalDemoService)


def test_explicit_deterministic_backend(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_BACKEND", "deterministic")

    service = select_portfolio_service_from_env()

    assert isinstance(service, LocalDemoService)


def test_llm_blocked_without_authorization(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_BACKEND", "llm")
    monkeypatch.delenv("PORTFOLIO_ENABLE_LOCAL_LLM", raising=False)

    with pytest.raises(PermissionError):
        select_portfolio_service_from_env()


def test_authorized_llm_uses_existing_runtime(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_BACKEND", "llm")
    monkeypatch.setenv("PORTFOLIO_ENABLE_LOCAL_LLM", "1")

    fake_service = object()

    with patch(
        "src.api.local_ai_runtime.build_local_ai_service_from_env",
        return_value=fake_service,
    ) as mocked_builder:
        service = select_portfolio_service_from_env()

    assert service is fake_service
    mocked_builder.assert_called_once_with()


def test_invalid_backend_rejected(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_BACKEND", "invalid")

    with pytest.raises(ValueError, match="Unsupported portfolio mode"):
        select_portfolio_service_from_env()
