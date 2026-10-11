"""
Metadata filters for Databricks AI Search.

Supports:
- RETURN topic
- DELIVERY topic
- WARRANTY topic
- Product-specific warranty filtering
- Multilingual keyword detection
- Conservative fallback for ambiguous questions
"""

import re


RETURN_TERMS = (
    "return", "returns", "refund", "exchange",
    "retour", "retours", "remboursement",
    "rückgabe", "retoure", "erstattung",
)

DELIVERY_TERMS = (
    "delivery", "shipping", "shipment",
    "livraison", "expédition",
    "lieferung", "versand",
)

WARRANTY_TERMS = (
    "warranty", "guarantee",
    "garantie", "gewährleistung",
)

PRODUCT_ID_PATTERN = re.compile(
    r"(?<!\w)PROD-\d+(?!\w)",
    re.IGNORECASE,
)


def contains_term(text, terms):
    return any(
        re.search(
            r"(?<!\w)" + re.escape(term) + r"(?!\w)",
            text,
        )
        for term in terms
    )


def extract_product_id(question):
    if not question:
        return None

    match = PRODUCT_ID_PATTERN.search(question)

    if match:
        return match.group(0).upper()

    return None


def select_document_filters(question):
    if not question or not question.strip():
        return None

    normalized = question.casefold()

    is_return = contains_term(normalized, RETURN_TERMS)
    is_delivery = contains_term(normalized, DELIVERY_TERMS)
    is_warranty = contains_term(normalized, WARRANTY_TERMS)

    detected_topics = []

    if is_return:
        detected_topics.append("RETURN")

    if is_delivery:
        detected_topics.append("DELIVERY")

    if is_warranty:
        detected_topics.append("WARRANTY")

    # Multiple topics: avoid excluding potentially relevant
    # documents from another topic.
    if len(detected_topics) > 1:
        return None

    if not detected_topics:
        return None

    topic = detected_topics[0]

    filters = {"topic": topic}

    if topic == "WARRANTY":
        product_id = extract_product_id(question)

        if product_id:
            filters["product_id"] = product_id

    return filters
