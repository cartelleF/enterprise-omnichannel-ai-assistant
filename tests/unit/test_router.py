from unittest.mock import MagicMock

from src.agents.router import (
    build_router_prompt,
    parse_router_response,
    route_question,
)


def test_build_router_prompt():
    prompt = build_router_prompt(
        "What is the status of order ORD-10066?"
    )

    assert "ORD-10066" in prompt
    assert "ORDER_RAG" in prompt
    assert "UNKNOWN" in prompt


def test_parse_router_response_order():
    content = """
    {
        "route": "ORDER",
        "order_id": "ORD-10066",
        "customer_id": null
    }
    """

    result = parse_router_response(content)

    assert result["route"] == "ORDER"
    assert result["order_id"] == "ORD-10066"
    assert result["customer_id"] is None


def test_parse_router_response_markdown():
    content = """```json
{
    "route": "CUSTOMER",
    "order_id": null,
    "customer_id": "CUST-1019"
}
```"""

    result = parse_router_response(content)

    assert result["route"] == "CUSTOMER"
    assert result["customer_id"] == "CUST-1019"


def test_parse_router_response_invalid_json():
    result = parse_router_response(
        "This is not JSON"
    )

    assert result["route"] == "UNKNOWN"
    assert result["order_id"] is None
    assert result["customer_id"] is None


def test_parse_router_response_invalid_route():
    content = """
    {
        "route": "WEATHER",
        "order_id": null,
        "customer_id": null
    }
    """

    result = parse_router_response(content)

    assert result["route"] == "UNKNOWN"


def test_route_question():
    llm_client = MagicMock()

    response = MagicMock()
    response.output_text = """
    {
        "route": "ORDER_RAG",
        "order_id": "ORD-10066",
        "customer_id": null
    }
    """

    llm_client.responses.create.return_value = response

    result = route_question(
        llm_client,
        "enterprise_rag_llm",
        "Can I still return order ORD-10066?"
    )

    assert result["route"] == "ORDER_RAG"
    assert result["order_id"] == "ORD-10066"

    llm_client.responses.create.assert_called_once()
