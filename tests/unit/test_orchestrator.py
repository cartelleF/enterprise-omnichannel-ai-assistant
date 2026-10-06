from unittest.mock import MagicMock, patch

from src.agents.orchestrator import enterprise_assistant


COMMON_ARGS = {
    "spark": MagicMock(),
    "llm_client": MagicMock(),
    "search_client": MagicMock(),
    "model_name": "enterprise_rag_llm",
    "index_name": "catalog.genai.document_chunks_index",
    "order_table": "catalog.gold.order_360",
    "customer_table": "catalog.gold.customer_360",
}


@patch("src.agents.orchestrator.generate_from_rag_context")
@patch("src.agents.orchestrator.extract_sources")
@patch("src.agents.orchestrator.build_rag_context")
@patch("src.agents.orchestrator.retrieve_documents")
@patch("src.agents.orchestrator.route_question")
def test_rag_route(mock_route, mock_retrieve, mock_context, mock_sources, mock_generate):
    mock_route.return_value = {
        "route": "RAG",
        "order_id": None,
        "customer_id": None,
    }

    mock_retrieve.return_value = [{"file_name": "return_policy.txt"}]
    mock_context.return_value = "Return policy context"
    mock_sources.return_value = ["return_policy.txt"]
    mock_generate.return_value = "Returns are allowed within 30 days."

    result = enterprise_assistant(
        "What is the return policy?",
        **COMMON_ARGS,
    )

    assert result["route"] == "RAG"
    assert result["sources"] == ["return_policy.txt"]
    assert "30 days" in result["answer"]


@patch("src.agents.orchestrator.generate_from_structured_context")
@patch("src.agents.orchestrator.get_order")
@patch("src.agents.orchestrator.route_question")
def test_order_route(mock_route, mock_get_order, mock_generate):
    mock_route.return_value = {
        "route": "ORDER",
        "order_id": "ORD-10066",
        "customer_id": None,
    }

    mock_get_order.return_value = {
        "found": True,
        "data": {
            "order_id": "ORD-10066",
            "order_status": "DELIVERED",
        },
    }

    mock_generate.return_value = "Order ORD-10066 has been delivered."

    result = enterprise_assistant(
        "What is the status of order ORD-10066?",
        **COMMON_ARGS,
    )

    assert result["route"] == "ORDER"
    assert result["sources"] == ["gold.order_360"]
    assert "delivered" in result["answer"].lower()


@patch("src.agents.orchestrator.generate_from_structured_context")
@patch("src.agents.orchestrator.get_customer")
@patch("src.agents.orchestrator.route_question")
def test_customer_route(mock_route, mock_get_customer, mock_generate):
    mock_route.return_value = {
        "route": "CUSTOMER",
        "order_id": None,
        "customer_id": "CUST-1019",
    }

    mock_get_customer.return_value = {
        "found": True,
        "data": {
            "customer_id": "CUST-1019",
            "loyalty_level": "SILVER",
        },
    }

    mock_generate.return_value = "The customer's loyalty level is SILVER."

    result = enterprise_assistant(
        "What is the loyalty level of customer CUST-1019?",
        **COMMON_ARGS,
    )

    assert result["route"] == "CUSTOMER"
    assert result["sources"] == ["gold.customer_360"]
    assert "SILVER" in result["answer"]


@patch("src.agents.orchestrator.generate_from_order_and_rag")
@patch("src.agents.orchestrator.extract_sources")
@patch("src.agents.orchestrator.build_rag_context")
@patch("src.agents.orchestrator.retrieve_documents")
@patch("src.agents.orchestrator.get_order")
@patch("src.agents.orchestrator.route_question")
def test_order_rag_route(mock_route, mock_get_order, mock_retrieve, mock_context, mock_sources, mock_generate):
    mock_route.return_value = {
        "route": "ORDER_RAG",
        "order_id": "ORD-10066",
        "customer_id": None,
    }

    mock_get_order.return_value = {
        "found": True,
        "data": {
            "order_id": "ORD-10066",
            "delivery_date": "2026-06-02",
        },
    }

    mock_retrieve.return_value = [{"file_name": "return_policy.txt"}]
    mock_context.return_value = "Returns are allowed within 30 days."
    mock_sources.return_value = ["return_policy.txt"]
    mock_generate.return_value = "The return period has expired."

    result = enterprise_assistant(
        "Can I still return order ORD-10066?",
        reference_date="2026-09-30",
        **COMMON_ARGS,
    )

    assert result["route"] == "ORDER_RAG"
    assert result["sources"] == [
        "gold.order_360",
        "return_policy.txt",
    ]
    assert "expired" in result["answer"]


@patch("src.agents.orchestrator.route_question")
def test_unknown_route(mock_route):
    mock_route.return_value = {
        "route": "UNKNOWN",
        "order_id": None,
        "customer_id": None,
    }

    result = enterprise_assistant(
        "What is the weather tomorrow?",
        **COMMON_ARGS,
    )

    assert result["route"] == "UNKNOWN"
    assert result["sources"] == []
    assert "cannot answer" in result["answer"].lower()


@patch("src.agents.orchestrator.get_order")
@patch("src.agents.orchestrator.route_question")
def test_order_not_found(mock_route, mock_get_order):
    mock_route.return_value = {
        "route": "ORDER",
        "order_id": "ORD-999999",
        "customer_id": None,
    }

    mock_get_order.return_value = {
        "found": False,
        "order_id": "ORD-999999",
    }

    result = enterprise_assistant(
        "What is the status of order ORD-999999?",
        **COMMON_ARGS,
    )

    assert result["route"] == "ORDER"
    assert "not found" in result["answer"].lower()
    assert result["sources"] == []
