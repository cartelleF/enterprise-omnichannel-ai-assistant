"""Readable, deterministic formatting of retrieved RAG excerpts."""

import re

from src.agents.local_fact_extractor import extract_return_facts
from src.rag.metadata_filter import (
    extract_product_id,
    select_document_filters,
)


RETURN_CATEGORIES = (
    "return_window",
    "product_condition",
    "order_verification",
    "refund",
    "exceptions",
)


def format_rag_answer(documents, question=None):
    """Present retrieved evidence without inventing facts."""
    if question and select_document_filters(question) == {"topic": "WARRANTY"}:
        warranty_documents = [
            doc for doc in documents
            if doc.get("product_id")
            and str(doc.get("file_name", "")).lower().endswith("_warranty.txt")
        ]

        if (
            warranty_documents
            and len(warranty_documents) == len(documents)
            and all(doc.get("product_id") for doc in warranty_documents)
            and not extract_product_id(question)
        ):
            return (
                "Warranty information is available for specific products. "
                "Which product are you asking about? "
                "Please provide the product ID."
            )
    if question and re.search(
        r"\breturns?\b|\brefunds?\b",
        question,
        re.IGNORECASE,
    ):
        return_documents = [
            doc for doc in documents
            if (
                "return_policy" in str(doc.get("file_name", "")).lower()
                or "returns_faq" in str(doc.get("file_name", "")).lower()
            )
        ]

        if return_documents:
            facts = extract_return_facts(return_documents)

            if facts:
                return "\n\n".join(
                    facts[category]
                    for category in RETURN_CATEGORIES
                    if category in facts
                )

    paragraphs = []
    seen = set()

    for doc in documents:
        text = " ".join(
            str(doc.get("chunk_text", "")).split()
        ).strip()

        if not text:
            continue

        key = text.casefold()

        if key in seen:
            continue

        seen.add(key)
        paragraphs.append(text)

    if not paragraphs:
        return (
            "I could not find relevant information "
            "in the available documents."
        )

    return "\n\n".join(paragraphs)
