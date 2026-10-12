"""Portfolio architecture diagrams for Streamlit."""

import streamlit as st


def render_architecture():
    st.header("Enterprise AI Architecture")

    demo_tab, enterprise_tab = st.tabs(
        ["Live Demo Architecture", "Enterprise Blueprint"]
    )

    with demo_tab:
        st.subheader("Live public demonstration")

        st.graphviz_chart(
            """
            digraph Demo {
                graph [
                    rankdir=TB,
                    bgcolor="transparent",
                    pad=0.3,
                    nodesep=0.5,
                    ranksep=0.6
                ];

                node [
                    shape=box,
                    style="rounded,filled",
                    fillcolor="#EAF2FF",
                    color="#7DA6DC",
                    fontname="Arial",
                    fontsize=12,
                    margin="0.22,0.15"
                ];

                edge [color="#6B7280", arrowsize=0.7];

                UI [label="Streamlit UI"];
                SERVICE [label="LocalDemoService"];
                ROUTER [label="Intelligent Routing"];
                RAG [label="Document RAG\\nBM25 Retrieval"];
                SAP [label="SAP Simulation\\nSQLite in Memory"];
                DOCS [label="Synthetic Documents"];
                JSON [label="Synthetic SAP JSON"];
                ANSWER [label="Answer + Route + Sources",
                        fillcolor="#DCFCE7"];

                UI -> SERVICE -> ROUTER;
                ROUTER -> RAG;
                ROUTER -> SAP;
                DOCS -> RAG;
                JSON -> SAP;
                RAG -> ANSWER;
                SAP -> ANSWER;

                {rank=same; RAG; SAP;}
            }
            """,
            use_container_width=True,
        )

        st.info(
            "Running implementation: synthetic datasets, "
            "local retrieval and in-memory SQLite. "
            "No live enterprise connection or paid LLM is required."
        )

    with enterprise_tab:
        st.subheader("Production-oriented architecture blueprint")

        st.graphviz_chart(
            """
            digraph Enterprise {
                graph [
                    rankdir=TB,
                    bgcolor="transparent",
                    pad=0.3,
                    nodesep=0.5,
                    ranksep=0.65
                ];

                node [
                    shape=box,
                    style="rounded,filled",
                    fillcolor="#EAF2FF",
                    color="#7DA6DC",
                    fontname="Arial",
                    fontsize=12,
                    margin="0.22,0.15"
                ];

                edge [color="#6B7280", arrowsize=0.7];

                SOURCES [label="SAP / CRM / Documents / APIs"];
                ADLS [label="Azure Data Lake Gen2"];
                DATABRICKS [
                    label="Azure Databricks\\nBronze / Silver / Gold"
                ];
                SEARCH [
                    label="RAG Retrieval\\nHybrid Search + Reranking"
                ];
                AGENT [
                    label="Agent Orchestration\\nRouting + Tool Calling"
                ];
                APIS [
                    label="Enterprise APIs / Applications",
                    fillcolor="#DCFCE7"
                ];

                SOURCES -> ADLS -> DATABRICKS;
                DATABRICKS -> SEARCH -> AGENT -> APIS;
            }
            """,
            use_container_width=True,
        )

        st.warning(
            "Architecture blueprint: these enterprise components "
            "are not all active in the public Streamlit demonstration."
        )

        st.markdown(
            "**Cross-cutting concerns:** Identity & access, "
            "PII protection, CI/CD, evaluation, observability "
            "and cost monitoring."
        )
