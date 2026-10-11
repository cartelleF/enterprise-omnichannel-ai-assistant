"""Conservative fact extraction from retrieved documents."""

import re


FACT_PATTERNS = {
    "return_window": (
        r"\breturn\b.*\bwithin\b.*\bafter delivery\b",
    ),
    "product_condition": (
        r"\b(?:acceptable|good) condition\b",
    ),
    "order_verification": (
        r"\bverify the original order\b",
    ),
    "refund": (
        r"\brefunds?\b.*\binspect",
    ),
    "exceptions": (
        r"\bspecific return conditions\b",
    ),
}


def extract_return_facts(documents):
    """Extract supported return-policy facts without rewriting them."""
    facts = {}
    seen = set()

    for doc in documents:
        text = str(doc.get("chunk_text", ""))

        # Normalize whitespace while preserving sentence content.
        text = " ".join(text.split())

        # Remove known document headings only when at the start.
        text = re.sub(
            r"^(?:Return Policy|Returns FAQ)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        )

        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            normalized = sentence.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)

            for category, patterns in FACT_PATTERNS.items():
                if category in facts:
                    continue

                if any(
                    re.search(pattern, sentence, re.IGNORECASE)
                    for pattern in patterns
                ):
                    facts[category] = sentence
                    break

    return facts
