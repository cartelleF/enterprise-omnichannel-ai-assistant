"""
Orchestration layer for the Enterprise Omni-Channel AI Assistant.

Coordinates:
- LLM routing
- Structured enterprise data access
- Metadata-aware RAG retrieval
- Grounded answer generation
"""

from src.agents.router import route_question
from src.rag.metadata_filter import select_document_filters
from src.rag.retrieval import (
    retrieve_documents,
    retrieve_documents_with_metadata,
    build_rag_context,
    extract_sources,
)
from src.rag.generation import (
    generate_from_rag_context,
    generate_from_structured_context,
    generate_from_order_and_rag,
)


UNKNOWN_ANSWER = (
    "I cannot answer this question using the available enterprise data "
    "and capabilities."
)

SEARCH_UNAVAILABLE_ANSWER = (
    "The document search service is currently unavailable. "
    "Please try again later."
)

NO_DOCUMENTS_ANSWER = (
    "I could not find sufficient information "
    "in the available documents."
)


def get_relevant_documents(
    search_client,
    index_name,
    question,
    top_k,
):
    filters = select_document_filters(question)

    return retrieve_documents(
        search_client,
        index_name,
        question,
        top_k=top_k,
        filters=filters,
    )


def get_relevant_documents_with_metadata(
    search_client,
    index_name,
    question,
    top_k,
):
    filters = select_document_filters(question)

    return retrieve_documents_with_metadata(
        search_client,
        index_name,
        question,
        top_k=top_k,
        filters=filters,
    )


def retrieval_failure_response(
    question,
    route,
    retrieval_result,
):
    """
    Return a safe response when document retrieval fails
    or returns no usable evidence.

    Never call the generation LLM without valid RAG context.
    """

    retrieval = retrieval_result["retrieval"]
    documents = retrieval_result["documents"]

    if retrieval["status"] != "success":
        return {
            "question": question,
            "route": route,
            "answer": SEARCH_UNAVAILABLE_ANSWER,
            "sources": [],
            "retrieval": retrieval,
        }

    if not any(doc.get("chunk_text") for doc in documents):
        return {
            "question": question,
            "route": route,
            "answer": NO_DOCUMENTS_ANSWER,
            "sources": [],
            "retrieval": retrieval,
        }

    return None


def enterprise_assistant(
    question,
    data_client,
    llm_client,
    search_client,
    model_name,
    index_name,
    reference_date=None,
    top_k=3,
):
    routing = route_question(
        llm_client,
        model_name,
        question,
    )

    route = routing["route"]
    order_id = routing.get("order_id")
    customer_id = routing.get("customer_id")

    # --------------------------------------------------
    # RAG: Document-based questions
    # --------------------------------------------------
    if route == "RAG":
        retrieval_result = get_relevant_documents_with_metadata(
            search_client,
            index_name,
            question,
            top_k,
        )

        failure = retrieval_failure_response(
            question,
            route,
            retrieval_result,
        )

        if failure is not None:
            return failure

        documents = retrieval_result["documents"]
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
            "retrieval": retrieval_result["retrieval"],
        }

    # --------------------------------------------------
    # ORDER: Structured order data
    # --------------------------------------------------
    if route == "ORDER":
        if not order_id:
            return {
                "question": question,
                "route": route,
                "answer": "No order ID was provided.",
                "sources": [],
            }

        order_result = data_client.get_order(order_id)

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

    # --------------------------------------------------
    # CUSTOMER: Structured customer data
    # --------------------------------------------------
    if route == "CUSTOMER":
        if not customer_id:
            return {
                "question": question,
                "route": route,
                "answer": "No customer ID was provided.",
                "sources": [],
            }

        customer_result = data_client.get_customer(customer_id)

        if not customer_result["found"]:
            return {
                "question": question,
                "route": route,
                "answer": (
                    f"Customer {customer_id} was not found."
                ),
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

    # --------------------------------------------------
    # ORDER_RAG: Structured order + documents
    # --------------------------------------------------
    if route == "ORDER_RAG":
        if not order_id:
            return {
                "question": question,
                "route": route,
                "answer": "No order ID was provided.",
                "sources": [],
            }

        order_result = data_client.get_order(order_id)

        if not order_result["found"]:
            return {
                "question": question,
                "route": route,
                "answer": f"Order {order_id} was not found.",
                "sources": [],
            }

        retrieval_result = get_relevant_documents_with_metadata(
            search_client,
            index_name,
            question,
            top_k,
        )

        failure = retrieval_failure_response(
            question,
            route,
            retrieval_result,
        )

        if failure is not None:
            return failure

        documents = retrieval_result["documents"]
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
            "sources": (
                ["gold.order_360"]
                + extract_sources(documents)
            ),
            "retrieval": retrieval_result["retrieval"],
        }

    # --------------------------------------------------
    # UNKNOWN: Unsupported questions
    # --------------------------------------------------
    return {
        "question": question,
        "route": "UNKNOWN",
        "answer": UNKNOWN_ANSWER,
        "sources": [],
    }
