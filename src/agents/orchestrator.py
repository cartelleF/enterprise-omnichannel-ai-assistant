"""
Orchestration layer for the Enterprise Omni-Channel AI Assistant.

The orchestrator coordinates:
- LLM routing
- structured enterprise tools
- RAG retrieval
- grounded answer generation
"""

from src.agents.router import route_question
from src.tools.order_tool import get_order
from src.tools.customer_tool import get_customer
from src.rag.retrieval import retrieve_documents, build_rag_context, extract_sources
from src.rag.generation import generate_from_rag_context, generate_from_structured_context, generate_from_order_and_rag


UNKNOWN_ANSWER = (
    "I cannot answer this question using the available enterprise data "
    "and capabilities."
)


def enterprise_assistant(
    question,
    spark,
    llm_client,
    search_client,
    model_name,
    index_name,
    order_table,
    customer_table,
    reference_date=None,
    top_k=3,
):
    """
    Execute one end-to-end assistant request.

    Returns
    -------
    dict
        {
            "question": str,
            "route": str,
            "answer": str,
            "sources": list[str]
        }
    """

    routing = route_question(
        llm_client,
        model_name,
        question,
    )

    route = routing["route"]
    order_id = routing.get("order_id")
    customer_id = routing.get("customer_id")

    if route == "RAG":
        documents = retrieve_documents(
            search_client,
            index_name,
            question,
            top_k=top_k,
        )

        context = build_rag_context(documents)

        answer = generate_from_rag_context(
            llm_client,
            model_name,
            question,
            context,
        )

        return {
            "question": question,
            "route": route,
            "answer": answer,
            "sources": extract_sources(documents),
        }

    if route == "ORDER":
        if not order_id:
            return {
                "question": question,
                "route": route,
                "answer": "No order ID was provided.",
                "sources": [],
            }

        order_result = get_order(
            spark,
            order_table,
            order_id,
        )

        if not order_result["found"]:
            return {
                "question": question,
                "route": route,
                "answer": f"Order {order_id} was not found.",
                "sources": [],
            }

        answer = generate_from_structured_context(
            llm_client,
            model_name,
            question,
            order_result["data"],
        )

        return {
            "question": question,
            "route": route,
            "answer": answer,
            "sources": ["gold.order_360"],
        }

    if route == "CUSTOMER":
        if not customer_id:
            return {
                "question": question,
                "route": route,
                "answer": "No customer ID was provided.",
                "sources": [],
            }

        customer_result = get_customer(
            spark,
            customer_table,
            customer_id,
        )

        if not customer_result["found"]:
            return {
                "question": question,
                "route": route,
                "answer": f"Customer {customer_id} was not found.",
                "sources": [],
            }

        answer = generate_from_structured_context(
            llm_client,
            model_name,
            question,
            customer_result["data"],
        )

        return {
            "question": question,
            "route": route,
            "answer": answer,
            "sources": ["gold.customer_360"],
        }

    if route == "ORDER_RAG":
        if not order_id:
            return {
                "question": question,
                "route": route,
                "answer": "No order ID was provided.",
                "sources": [],
            }

        order_result = get_order(
            spark,
            order_table,
            order_id,
        )

        if not order_result["found"]:
            return {
                "question": question,
                "route": route,
                "answer": f"Order {order_id} was not found.",
                "sources": [],
            }

        documents = retrieve_documents(
            search_client,
            index_name,
            question,
            top_k=top_k,
        )

        rag_context = build_rag_context(documents)

        answer = generate_from_order_and_rag(
            llm_client,
            model_name,
            question,
            order_result["data"],
            rag_context,
            reference_date=reference_date,
        )

        return {
            "question": question,
            "route": route,
            "answer": answer,
            "sources": ["gold.order_360"] + extract_sources(documents),
        }

    return {
        "question": question,
        "route": "UNKNOWN",
        "answer": UNKNOWN_ANSWER,
        "sources": [],
    }
