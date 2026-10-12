"""
V6.1 — Streamlit performance metrics display.

Shows measurements collected by PerformanceTracker.
No synthetic latency values.
"""

import streamlit as st


OPERATION_LABELS = {
    "routing_ms": "Routing",
    "order_lookup_ms": "Order lookup (SQLite)",
    "customer_lookup_ms": "Customer lookup (SQLite)",
    "retrieval_ms": "Document retrieval",
    "assessment_ms": "Business assessment",
    "formatting_ms": "Response formatting",
}


def render_performance_metrics(result):
    metrics = result.get("performance")

    if not isinstance(metrics, dict):
        return

    total = metrics.get("total_ms")

    if not isinstance(total, (int, float)):
        return

    with st.expander("⏱️ Performance Metrics", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Latency", f"{total:.3f} ms")

        with col2:
            st.metric("Route", result.get("route", "UNKNOWN"))

        st.caption(
            "Measured locally with a monotonic clock. "
            "Values vary with execution conditions."
        )

        for key, label in OPERATION_LABELS.items():
            value = metrics.get(key)

            if not isinstance(value, (int, float)):
                continue

            st.write(f"**{label}:** {value:.3f} ms")

            fraction = (
                max(0.0, min(float(value) / total, 1.0))
                if total > 0
                else 0.0
            )

            st.progress(fraction)

        st.caption(
            "Operation timings do not necessarily sum to total "
            "latency because additional application processing "
            "is included."
        )
