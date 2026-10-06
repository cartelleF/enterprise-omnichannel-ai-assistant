from datetime import date
from unittest.mock import MagicMock

from src.rag.generation import (
    generate_from_order_and_rag,
    generate_from_rag_context,
    generate_from_structured_context,
)


def make_llm_client(answer):
    client = MagicMock()
    response = MagicMock()
    response.output_text = answer
    client.responses.create.return_value = response
    return client


def test_generate_from_rag_context():
    client = make_llm_client(
        "Products can be returned within 30 days."
    )

    answer = generate_from_rag_context(
        client,
        "enterprise_rag_llm",
        "What is the return policy?",
        "Products can be returned within 30 days.",
    )

    assert answer == "Products can be returned within 30 days."
    client.responses.create.assert_called_once()


def test_generate_from_rag_context_empty():
    client = MagicMock()

    answer = generate_from_rag_context(
        client,
        "enterprise_rag_llm",
        "What is the return policy?",
        "",
    )

    assert "could not find enough information" in answer
    client.responses.create.assert_not_called()


def test_generate_from_structured_context():
    client = make_llm_client(
        "Order ORD-10066 has been delivered."
    )

    context = {
        "order_id": "ORD-10066",
        "order_status": "DELIVERED",
    }

    answer = generate_from_structured_context(
        client,
        "enterprise_rag_llm",
        "What is the status of order ORD-10066?",
        context,
    )

    assert "DELIVERED" in answer or "delivered" in answer
    client.responses.create.assert_called_once()


def test_generate_from_order_and_rag():
    client = make_llm_client(
        "The order can no longer be returned because the 30-day return period has expired."
    )

    order_data = {
        "order_id": "ORD-10066",
        "delivery_date": "2026-06-02",
        "order_status": "DELIVERED",
    }

    rag_context = (
        "Products can be returned within 30 days "
        "after delivery."
    )

    answer = generate_from_order_and_rag(
        client,
        "enterprise_rag_llm",
        "Can I still return order ORD-10066?",
        order_data,
        rag_context,
        reference_date=date(2026, 9, 30),
    )

    assert "30-day" in answer
    assert "expired" in answer

    call = client.responses.create.call_args
    prompt = call.kwargs["input"]

    assert "ORD-10066" in prompt
    assert "2026-06-02" in prompt
    assert "2026-09-30" in prompt
    assert "30 days" in prompt


def test_generate_from_structured_context_empty():
    client = MagicMock()

    answer = generate_from_structured_context(
        client,
        "enterprise_rag_llm",
        "What is my order status?",
        None,
    )

    assert "could not find enough structured enterprise data" in answer
    client.responses.create.assert_not_called()
