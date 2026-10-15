"""Backend selection for the portfolio Streamlit application."""

import os

from src.api.local_demo_service import LocalDemoService


def select_portfolio_service(
    mode="deterministic",
    *,
    allow_local_llm=False,
):
    """Select a safe portfolio backend.

    The LLM backend requires explicit local authorization.
    """
    if mode == "deterministic":
        return LocalDemoService(
            multilingual_retrieval=True,
            multilingual_formatting=True,
        )

    if mode != "llm":
        raise ValueError(f"Unsupported portfolio mode: {mode}")

    if not allow_local_llm:
        raise PermissionError(
            "LLM mode is disabled for the public portfolio."
        )

    if os.getenv("PORTFOLIO_ENABLE_LOCAL_LLM") != "1":
        raise PermissionError(
            "Set PORTFOLIO_ENABLE_LOCAL_LLM=1 explicitly."
        )

    from src.api.local_ai_runtime import (
        build_local_ai_service_from_env,
    )

    return build_local_ai_service_from_env()


def select_portfolio_service_from_env():
    """Select the portfolio backend using explicit server configuration."""
    mode = os.getenv(
        "PORTFOLIO_BACKEND", "deterministic"
    ).strip().lower()

    if mode == "deterministic":
        return select_portfolio_service("deterministic")

    if mode == "llm":
        if os.getenv("PORTFOLIO_ENABLE_LOCAL_LLM") != "1":
            raise PermissionError(
                "Local LLM mode requires explicit authorization."
            )

        return select_portfolio_service(
            "llm",
            allow_local_llm=True,
        )

    raise ValueError(f"Unsupported portfolio mode: {mode}")
