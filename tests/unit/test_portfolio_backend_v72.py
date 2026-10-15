"""Safety tests for portfolio backend selection."""

import pytest

from src.api.portfolio_backend import select_portfolio_service
from src.api.local_demo_service import LocalDemoService


def test_deterministic_backend_is_default():
    service = select_portfolio_service()
    assert isinstance(service, LocalDemoService)


def test_unknown_backend_is_rejected():
    with pytest.raises(ValueError, match="Unsupported portfolio mode"):
        select_portfolio_service("unknown")


def test_llm_requires_explicit_authorization(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_ENABLE_LOCAL_LLM", "1")

    with pytest.raises(PermissionError, match="disabled"):
        select_portfolio_service("llm")


def test_llm_requires_environment_flag(monkeypatch):
    monkeypatch.delenv("PORTFOLIO_ENABLE_LOCAL_LLM", raising=False)

    with pytest.raises(PermissionError, match="PORTFOLIO_ENABLE_LOCAL_LLM"):
        select_portfolio_service(
            "llm",
            allow_local_llm=True,
        )
