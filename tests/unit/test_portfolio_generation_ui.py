"""Tests for generation-mode labels."""

from unittest.mock import patch

from src.api.portfolio_generation_ui import render_generation_mode


def test_deterministic_mode():
    with patch("src.api.portfolio_generation_ui.st.caption") as caption:
        render_generation_mode({})
        caption.assert_called_once_with(
            "💻 Generation mode: Offline deterministic"
        )


def test_llm_mode():
    with patch("src.api.portfolio_generation_ui.st.caption") as caption:
        render_generation_mode({"generation_mode": "llm"})
        caption.assert_called_once_with(
            "🤖 Generation mode: LLM-assisted response"
        )


def test_local_fallback_mode():
    with patch("src.api.portfolio_generation_ui.st.caption") as caption:
        render_generation_mode({"generation_mode": "local_fallback"})
        caption.assert_called_once_with(
            "🛡️ Generation mode: Local fallback"
        )
