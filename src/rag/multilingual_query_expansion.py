"""Controlled multilingual lexical query expansion."""

import re

from src.rag.metadata_filter import (
    RETURN_TERMS,
    DELIVERY_TERMS,
    WARRANTY_TERMS,
    contains_term,
)


TOPIC_EXPANSIONS = {
    "RETURN": (
        "return", "returns", "refund",
        "retour", "remboursement",
        "Rückgabe", "Erstattung",
    ),
    "DELIVERY": (
        "delivery", "shipping", "shipment",
        "livraison", "expédition",
        "Lieferung", "Standardlieferung",
        "Versand",
    ),
    "WARRANTY": (
        "warranty", "guarantee",
        "garantie", "Gewährleistung",
    ),
}


def expand_multilingual_query(question):
    """Add multilingual topic synonyms without removing original terms."""
    if not question or not question.strip():
        return question

    normalized = question.casefold()

    detected = []

    for topic, terms in (
        ("RETURN", RETURN_TERMS),
        ("DELIVERY", DELIVERY_TERMS),
        ("WARRANTY", WARRANTY_TERMS),
    ):
        if contains_term(normalized, terms):
            detected.append(topic)

    # Avoid broad expansion of ambiguous mixed-topic queries.
    if len(detected) != 1:
        return question

    topic = detected[0]

    existing = set(
        re.findall(r"\w+", normalized, flags=re.UNICODE)
    )

    additions = []

    for term in TOPIC_EXPANSIONS[topic]:
        if term.casefold() not in existing:
            additions.append(term)

    if not additions:
        return question

    return question + " " + " ".join(additions)
