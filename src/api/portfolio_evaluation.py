
"""Evaluation dashboard for the public AI portfolio."""

import json
from pathlib import Path

import streamlit as st


def pct(value, digits=1):
    if value is None:
        return "N/A"
    return f"{value:.{digits}%}"


def render_evaluation_dashboard():
    path = (
        Path(__file__).resolve().parents[2]
        / "deployment"
        / "evaluation_summary.json"
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    versions = data["generation_versions"]

    st.subheader("AI Engineering & Evaluation")
    st.caption(
        "Offline deterministic benchmarks using synthetic "
        "enterprise data. Not a production performance claim."
    )

    v3 = versions["V3_multilingual_assistant"]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Routing Accuracy",
        pct(v3.get("routing_accuracy")),
    )
    c2.metric(
        "Fact Coverage",
        pct(v3.get("fact_coverage")),
    )
    c3.metric(
        "Source Coverage",
        pct(v3.get("source_coverage")),
    )

    st.caption(
        f"Generation evaluation: {v3['cases']} synthetic "
        "test cases in V3."
    )

    st.markdown("#### Evolution from V1 to V3")

    names = {
        "V1_baseline": "V1 Baseline",
        "V2_multilingual_retrieval": "V2 Multilingual Retrieval",
        "V3_multilingual_assistant": "V3 Multilingual Assistant",
    }

    metric_keys = {
        "Fact coverage": "fact_coverage",
        "Source coverage": "source_coverage",
        "Intent satisfaction": "intent_satisfaction",
        "Required information": "required_information_coverage",
    }

    rows = {}

    for version_name, label in names.items():
        version = versions.get(version_name, {})
        rows[label] = {
            display: (
                round(100 * version[key], 2)
                if version.get(key) is not None
                else None
            )
            for display, key in metric_keys.items()
        }

    st.line_chart(
        {
            metric: {
                version: values.get(metric)
                for version, values in rows.items()
            }
            for metric in metric_keys
        }
    )

    st.caption(
        "Percentage scores across the same 10 synthetic "
        "generation scenarios. Missing values are not "
        "replaced by zero."
    )

    with st.expander("Detailed generation metrics"):
        st.table({
            label: {
                display: pct(versions[name].get(key))
                for display, key in metric_keys.items()
            }
            for name, label in names.items()
        })

    st.markdown("#### RAG Retrieval Benchmark")

    rag = data["rag_summary"]

    rag_rows = {}

    for strategy, scores in rag.items():
        rag_rows[strategy.replace("LOCAL_", "")] = {
            "Precision@3":
                100 * scores["precision_at_k"],
            "Retrieved Precision@3":
                100 * scores["retrieved_precision_at_k"],
            "Recall@3":
                100 * scores["recall_at_k"],
            "MRR":
                100 * scores["mrr"],
        }

    st.bar_chart(
        {
            metric: {
                strategy: values.get(metric)
                for strategy, values in rag_rows.items()
            }
            for metric in (
                "Precision@3",
                "Retrieved Precision@3",
                "Recall@3",
                "MRR",
            )
        },
        stack=False,
    )

    st.caption(
        "Local BM25 benchmark: 5 questions per strategy, "
        "k=3. Scores displayed on a 0–100 scale."
    )

    st.markdown("#### Multilingual Retrieval Evaluation")

    multilingual = data["multilingual_summary"]

    strategy = st.selectbox(
        "Retrieval strategy",
        list(multilingual.keys()),
        key="portfolio_eval_strategy",
    )

    language_rows = {}

    for language, result in multilingual[strategy].items():
        metrics = result["metrics"]

        language_rows[language.upper()] = {
            "Precision@3":
                100 * metrics["precision_at_k"],
            "Recall@3":
                100 * metrics["recall_at_k"],
            "MRR":
                100 * metrics["reciprocal_rank"],
        }

    st.bar_chart(
        {
            metric: {
                language: values.get(metric)
                for language, values in language_rows.items()
            }
            for metric in ("Precision@3", "Recall@3", "MRR")
        },
        stack=False,
    )

    st.caption(
        "8 multilingual questions across EN, DE and FR. "
        "Three retrieval strategies evaluated."
    )

    st.markdown("#### Software Engineering")

    st.markdown(
        """
- **290 automated tests passed** in the last verified local run.
- Modular Python architecture.
- Synthetic SAP/CRM integration scenarios.
- Multilingual retrieval and response formatting.
- Git-based development and automated testing.
"""
    )

    st.markdown("#### Evaluation Limitations")

    st.info(
        "These are small, synthetic, deterministic benchmarks. "
        "They do not establish production accuracy, LLM "
        "faithfulness, enterprise-scale performance, "
        "or real-world robustness. Routing accuracy is "
        "measured on the evaluated scenarios only."
    )
