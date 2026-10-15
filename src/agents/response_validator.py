"""
Conservative validation of LLM rewrites.

The deterministic answer is the reference.
This validator checks critical structured facts, not full
semantic equivalence or factual correctness.
"""

import re
from decimal import Decimal, InvalidOperation


IDENTIFIER_RE = re.compile(
    r"\b(?:ORD|CUST|PROD)-\d+\b",
    re.IGNORECASE,
)

DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
)

AMOUNT_RE = re.compile(
    r"\b(?:EUR\s*)?(\d+(?:[.,]\d+)?)\s*(?:EUR|€)\b",
    re.IGNORECASE,
)


def extract_amounts(text: str) -> set[Decimal]:
    amounts = set()

    for match in AMOUNT_RE.finditer(text):
        value = match.group(1).replace(",", ".")

        try:
            amounts.add(Decimal(value))
        except InvalidOperation:
            continue

    return amounts



# Business-critical values that must remain consistent.
ORDER_STATUSES = {
    "PENDING", "PROCESSING", "CONFIRMED",
    "SHIPPED", "DELIVERED", "CANCELLED",
    "CANCELED", "RETURNED", "REFUNDED",
}

LOYALTY_LEVELS = {
    "STANDARD", "SILVER", "GOLD",
    "PLATINUM", "BRONZE", "VIP",
}


def extract_business_terms(text: str) -> set[str]:
    words = {
        word.upper()
        for word in re.findall(r"\b[A-Za-z]+\b", text)
    }
    return words & (ORDER_STATUSES | LOYALTY_LEVELS)


def extract_numbers(text: str) -> set[Decimal]:
    # Exclude structured identifiers, dates and monetary amounts,
    # which are validated separately.
    cleaned = IDENTIFIER_RE.sub(" ", text)
    cleaned = DATE_RE.sub(" ", cleaned)
    cleaned = AMOUNT_RE.sub(" ", cleaned)

    numbers = set()
    for value in re.findall(r"(?<![\w.])\d+(?:[.,]\d+)?(?![\w.])", cleaned):
        try:
            numbers.add(Decimal(value.replace(",", ".")))
        except InvalidOperation:
            continue

    return numbers

def validate_llm_rewrite(
    reference_answer: str,
    generated_answer: str,
) -> bool:
    if not generated_answer or not generated_answer.strip():
        return False

    reference_ids = {
        value.upper()
        for value in IDENTIFIER_RE.findall(reference_answer)
    }
    generated_ids = {
        value.upper()
        for value in IDENTIFIER_RE.findall(generated_answer)
    }

    if reference_ids != generated_ids:
        return False

    reference_dates = set(DATE_RE.findall(reference_answer))
    generated_dates = set(DATE_RE.findall(generated_answer))

    if reference_dates != generated_dates:
        return False

    reference_amounts = extract_amounts(reference_answer)
    generated_amounts = extract_amounts(generated_answer)

    if reference_amounts != generated_amounts:
        return False

    if extract_business_terms(reference_answer) != extract_business_terms(
        generated_answer
    ):
        return False

    if extract_numbers(reference_answer) != extract_numbers(
        generated_answer
    ):
        return False

    return True
