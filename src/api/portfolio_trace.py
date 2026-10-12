"""Readable execution-path explanation for the offline demo."""

import streamlit as st


ROUTE_INFO = {
    "ORDER": {
        "name": "Synthetic SAP order lookup",
        "steps": ["Order lookup", "Response"],
        "operation": "LocalDemoService.data_client.get_order",
        "response": "Order response assembled from the lookup result",
    },
    "CUSTOMER": {
        "name": "Synthetic SAP customer lookup",
        "steps": ["Customer lookup", "Response"],
        "operation": "LocalDemoService.data_client.get_customer",
        "response": "Customer response assembled from the lookup result",
    },
    "RAG": {
        "name": "Local document retrieval",
        "steps": ["Document search", "Response"],
        "operation": "get_relevant_documents_with_metadata",
        "response": "Document response or retrieval fallback",
    },
    "ORDER_RAG": {
        "name": "Order lookup and policy retrieval",
        "steps": ["Order lookup", "Policy search", "Assessment"],
        "operation": (
            "LocalDemoService.data_client.get_order; "
            "get_relevant_documents_with_metadata "
            "(when order exists)"
        ),
        "response": (
            "Return-policy assessment when sufficient data exists"
        ),
    },
}


def render_execution_trace(result: dict) -> None:
    """Render a descriptive path, not an instrumented event log."""

    route = str(result.get("route") or "UNKNOWN")
    sources = result.get("sources") or []
    answer = str(result.get("answer") or "")
    info = ROUTE_INFO.get(route)

    st.markdown("##### 🔎 Agent Execution")

    route_col, source_col = st.columns([1, 2])

    with route_col:
        st.markdown(f"**Route:** `{route}`")

    with source_col:
        st.caption(
            f"Reported sources: {len(sources)}"
        )

    if info is None:
        st.caption("No documented execution path for this route.")
        return

    steps = list(info["steps"])

    # A missing order returns before policy retrieval.
    if route == "ORDER_RAG" and "was not found" in answer.lower():
        steps = ["Order lookup", "Not found"]

    st.markdown(
        "**Logical path:** "
        + " → ".join(steps)
    )

    if sources:
        st.caption(
            "Sources: " + " · ".join(str(s) for s in sources)
        )
    else:
        st.caption("No sources reported for this response.")

    with st.expander(
        "View detailed execution path",
        expanded=False,
    ):
        st.caption(
            "Explanation derived from the backend response "
            "and implemented workflow. This is not an "
            "instrumented event-by-event execution log."
        )

        st.markdown("**1. Request processing**")
        st.write(
            "The submitted question was processed "
            "by the local demo."
        )

        st.markdown("**2. Routing decision**")
        st.code(route, language=None)
        st.write(info["name"])

        st.markdown("**3. Backend operations**")
        st.code(info["operation"], language=None)

        if route in ("RAG", "ORDER_RAG"):
            st.caption(
                "Document retrieval uses local search "
                "with top_k=3. For ORDER_RAG, retrieval "
                "is skipped when the order does not exist."
            )

        st.markdown("**4. Response construction**")
        st.write(info["response"])

        if route == "RAG":
            st.caption(
                "When documents are available, the configured "
                "multilingual or standard formatter is used."
            )
        elif route == "ORDER_RAG":
            st.caption(
                "Return-window assessment is conditional on "
                "successful order lookup and document retrieval."
            )

        st.markdown("**5. Reported sources**")

        if sources:
            for source in sources:
                st.write(f"• {source}")
        else:
            st.caption(
                "No sources were reported for this response."
            )

        st.caption(
            "Offline deterministic demonstration. "
            "No paid LLM or live enterprise SAP/CRM connection."
        )
