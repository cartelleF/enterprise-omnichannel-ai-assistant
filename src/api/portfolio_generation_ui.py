"""Generation-mode display for the portfolio."""

import streamlit as st


def render_generation_mode(result):
    """Show how the assistant response was generated."""
    mode = result.get("generation_mode", "deterministic")

    if mode == "llm":
        st.caption("🤖 Generation mode: LLM-assisted response")

    elif mode == "local_fallback":
        st.caption("🛡️ Generation mode: Local fallback")

    else:
        st.caption("💻 Generation mode: Offline deterministic")
