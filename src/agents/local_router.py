"""
Deterministic router for the local portfolio demo.

No LLM calls and no external dependencies.
"""

import re

from src.rag.metadata_filter import select_document_filters


ORDER_PATTERN = re.compile(
    r"\bORD-\d+\b",
    re.IGNORECASE,
)

CUSTOMER_PATTERN = re.compile(
    r"\bCUST-\d+\b",
    re.IGNORECASE,
)

POLICY_TERMS = (
    "return",
    "returns",
    "refund",
    "exchange",
    "retour",
    "remboursement",
    "rückgabe",
    "warranty",
    "guarantee",
    "garantie",
    "delivery policy",
    "shipping policy",
    "politique de livraison",
)


def route_question_local(question):
    order_match = ORDER_PATTERN.search(question)
    customer_match = CUSTOMER_PATTERN.search(question)

    order_id = (
        order_match.group(0).upper()
        if order_match
        else None
    )

    customer_id = (
        customer_match.group(0).upper()
        if customer_match
        else None
    )

    normalized = question.lower()

    has_policy_intent = any(
        re.search(
            rf"(?<!\w){re.escape(term)}(?!\w)",
            normalized,
        )
        for term in POLICY_TERMS
    )

    document_filters = select_document_filters(question)

    if order_id and (
        has_policy_intent
        or document_filters is not None
    ):
        route = "ORDER_RAG"

    elif order_id:
        route = "ORDER"

    elif customer_id:
        route = "CUSTOMER"

    elif document_filters is not None:
        route = "RAG"

    else:
        route = "UNKNOWN"

    return {
        "route": route,
        "order_id": order_id,
        "customer_id": customer_id,
    }
