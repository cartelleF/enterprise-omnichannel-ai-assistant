import pytest

from src.agents.response_validator import validate_llm_rewrite


REFERENCE = (
    "Order ORD-10066 was placed on 2026-05-28 "
    "and delivered on 2026-06-02. "
    "The total amount is 2313.8 EUR."
)


@pytest.mark.parametrize(
    "generated",
    [
        (
            "Order ORD-10066 was placed on 2026-05-28 "
            "and delivered on 2026-06-02. "
            "The amount is 2313.80 EUR."
        ),
        (
            "The total for ORD-10066 is 2313.8 EUR. "
            "It was delivered on 2026-06-02 "
            "after being placed on 2026-05-28."
        ),
    ],
)
def test_accepts_preserved_facts(generated):
    assert validate_llm_rewrite(REFERENCE, generated)


@pytest.mark.parametrize(
    "generated",
    [
        REFERENCE.replace("ORD-10066", "ORD-10067"),
        REFERENCE.replace("2026-06-02", "2026-06-03"),
        REFERENCE.replace("2313.8 EUR", "2318 EUR"),
        REFERENCE.replace("ORD-10066", ""),
        REFERENCE.replace("2313.8 EUR", ""),
        REFERENCE + " Customer CUST-9999 is responsible.",
        "",
    ],
)
def test_rejects_changed_or_missing_facts(generated):
    assert not validate_llm_rewrite(REFERENCE, generated)


def test_accepts_policy_paraphrase_without_structured_facts():
    assert validate_llm_rewrite(
        "Customers have 30 days to request a return.",
        "Customers may request a return within 30 days.",
    )
