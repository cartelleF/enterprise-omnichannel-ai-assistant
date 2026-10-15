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
                    nodesep=0.6,
                    ranksep=0.7
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
                ROUTER [label="Intent Router", shape=diamond];

                TOOL [label="Business Tools"];
                RAG [label="Metadata-aware RAG"];

                DB [label="Synthetic SQLite Data"];
                BM25 [label="Local BM25 Search"];

                EVIDENCE [label="Business Facts / Evidence"];
                MODE [label="Response Mode", shape=diamond];

                DET [label="Deterministic Answer"];
                LLM [label="GPT-4.1 mini / OpenAI API"];

                ANSWER [
                    label="Answer + Sources",
                    fillcolor="#DCFCE7"
                ];

                EVAL [
                    label="Evaluation / Observability",
                    style="rounded,dashed",
                    fillcolor="#F3F4F6"
                ];

                UI -> SERVICE -> ROUTER;

                ROUTER -> TOOL [label="Business query"];
                ROUTER -> RAG [label="Document question"];

                TOOL -> DB;
                RAG -> BM25;

                DB -> EVIDENCE;
                BM25 -> EVIDENCE;

                EVIDENCE -> MODE;

                MODE -> DET [label="Local"];
                MODE -> LLM [label="Local AI"];

                DET -> ANSWER;
                LLM -> ANSWER;

                ANSWER -> EVAL [style=dashed];

                {rank=same; TOOL; RAG;}
                {rank=same; DB; BM25;}
                {rank=same; DET; LLM;}
            }
            """,
            use_container_width=True,
        )

        st.info(
            "Local mode uses synthetic datasets, BM25 retrieval and SQLite "
            "without requiring an external LLM. Optional Local AI mode "
            "uses GPT-4.1 mini through the OpenAI API, with a configured "
            "daily limit of five LLM calls. No live SAP or CRM connection "
            "is required."
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
                LLM [
                    label="GPT-OSS-20B\\nAzure Development",
                    fillcolor="#FEF3C7"
                ];
                APIS [
                    label="Enterprise APIs / Applications",
                    fillcolor="#DCFCE7"
                ];

                SOURCES -> ADLS -> DATABRICKS;
                DATABRICKS -> SEARCH -> AGENT;
                AGENT -> LLM [label="LLM-assisted generation"];
                LLM -> APIS;
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
