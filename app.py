"""Public portfolio demo for the Enterprise Omni-Channel AI Assistant."""

import streamlit as st

from src.api.demo_bootstrap import prepare_demo_data
from src.api.local_demo_service import LocalDemoService


st.set_page_config(
    page_title="Enterprise AI Assistant | Portfolio Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_service():
    prepare_demo_data()
    return LocalDemoService(
        multilingual_retrieval=True,
        multilingual_formatting=True,
    )


EXAMPLES = {
    "English": [
        "What is the standard return policy?",
        "Can I get a refund after 45 days?",
        "What is the warranty for product PROD-1006?",
    ],
    "Deutsch": [
        "Wie lange dauert die Standardlieferung?",
        "Wie lange gilt die Garantie für PROD-1003?",
    ],
    "Français": [
        "Quelle est la garantie du produit PROD-1006 ?",
        "Combien de temps prend la livraison standard ?",
    ],
}


def render_response(result):
    answer = result.get("answer") or "No answer available."
    route = result.get("route") or "UNKNOWN"
    sources = result.get("sources") or []

    st.markdown(answer)

    st.caption(f"Routing: {route}")

    if sources:
        with st.expander("📚 Retrieved sources"):
            for source in sources:
                st.markdown(f"- `{source}`")


st.title("🤖 Enterprise Omni-Channel AI Assistant")

st.markdown(
    "**Multilingual RAG · Intelligent Routing · "
    "SAP/CRM Simulation · Enterprise AI**"
)

st.info(
    "Portfolio demonstration using synthetic enterprise data. "
    "No real customer information is used."
)

with st.sidebar:
    st.header("About this project")

    st.markdown(
        """
        **Enterprise AI Assistant**

        A demonstration of enterprise AI engineering,
        multilingual retrieval and business-system integration.

        **Capabilities**
        - Multilingual support: English, German, French
        - Retrieval-Augmented Generation (RAG)
        - Intelligent request routing
        - Synthetic SAP/CRM business scenarios
        - Source attribution

        **Technology**
        - Python
        - SQLite / BM25
        - RAG
        - Azure Databricks architecture
        """
    )

    st.divider()

    st.caption(
        "This is an offline-first demonstration. "
        "The production-oriented architecture is documented "
        "separately."
    )


# PORTFOLIO_V4
tab_assistant, tab_architecture, tab_engineering = st.tabs(
    [
        "💬 Live Assistant",
        "🏗️ Architecture",
        "🧪 Engineering & Evaluation",
    ]
)

with tab_assistant:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    if not st.session_state.messages:
        st.subheader("Try an example")

        language = st.selectbox(
            "Choose a language",
            list(EXAMPLES),
        )

        for index, example in enumerate(EXAMPLES[language]):
            if st.button(
                example,
                key=f"example_{language}_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_question = example
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_response(message["result"])
            else:
                st.markdown(message["content"])

    question = st.chat_input(
        "Ask about orders, returns, delivery or warranties..."
    )

    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

    if question:
        question = question.strip()

        if question:
            if len(question) > 500:
                st.warning("Please limit your question to 500 characters.")
                st.stop()

            st.session_state.messages.append(
                {"role": "user", "content": question}
            )

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching enterprise knowledge..."):
                    try:
                        result = get_service().ask(question)
                    except Exception:
                        st.error(
                            "The demo could not process this request. "
                            "Please try another question."
                        )
                        st.stop()

                render_response(result)

            st.session_state.messages.append(
                {"role": "assistant", "result": result}
            )


with tab_architecture:
    st.header("Enterprise AI Architecture")
    st.caption(
        "Public demo implementation and production-oriented "
        "Azure/Databricks architecture are shown separately."
    )

    st.subheader("Live portfolio demonstration")
    st.code(
        """User / Streamlit
        |
        v
LocalDemoService
        |
        +--> Intelligent Routing
        |       |
        |       +--> Document RAG (BM25)
        |       +--> Synthetic SAP/CRM scenarios
        |
        +--> Grounded Answer + Sources

Synthetic JSON -> In-memory SQLite
Documents -> Local Retrieval""",
        language="text",
    )

    st.info(
        "This public application uses synthetic datasets and "
        "local retrieval. It does not require live SAP, CRM, "
        "Azure Databricks or paid LLM services."
    )

    st.subheader("Production-oriented architecture")
    st.code(
        """SAP / CRM / Documents / APIs
             |
             v
      Azure Data Lake Gen2
             |
             v
      Azure Databricks
      Bronze -> Silver -> Gold
             |
             v
   RAG / Agent Orchestration
             |
             v
    APIs / Enterprise Apps

Security | CI/CD | Evaluation | Monitoring""",
        language="text",
    )

    st.caption(
        "Architecture blueprint: not all production integrations "
        "are active in this public demonstration."
    )

with tab_engineering:
    st.header("Engineering & Evaluation")

    st.subheader("Implemented demo capabilities")
    st.markdown(
        """
- Multilingual question handling: English, German and French
- Document retrieval and source attribution
- Intelligent request routing
- Synthetic enterprise data and in-memory SQLite
- Offline-first execution without a paid LLM API
        """
    )

    st.subheader("Engineering practices")
    st.markdown(
        """
- Modular Python components
- Automated tests
- Retrieval and answer-quality evaluation
- Separation between demonstration and production architecture
- Git-based version control and reproducible deployment
        """
    )

    st.subheader("Evaluation dimensions")
    st.markdown(
        """
| Layer | Example metrics |
|---|---|
| Retrieval | Precision, Recall, MRR |
| Answer quality | Factual correctness, groundedness |
| Routing | Intent and route accuracy |
| End-to-end | Task completion, answer correctness |
        """
    )

    st.caption(
        "Evaluation dimensions describe the project's methodology. "
        "They are not claims of independently verified production performance."
    )
