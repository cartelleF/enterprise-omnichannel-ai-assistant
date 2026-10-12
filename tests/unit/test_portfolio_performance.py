import pytest

from src.api.portfolio_performance import PerformanceTracker
from src.api.local_demo_service import LocalDemoService


def make_service():
    return LocalDemoService(
        multilingual_retrieval=True,
        multilingual_formatting=True,
        reference_date="2026-10-12",
    )


def assert_performance(result, expected_operations):
    assert "performance" in result
    metrics = result["performance"]

    assert "total_ms" in metrics
    assert metrics["total_ms"] >= 0

    for operation in expected_operations:
        assert operation in metrics
        assert isinstance(metrics[operation], (int, float))
        assert metrics[operation] >= 0

    measured = sum(
        value for key, value in metrics.items()
        if key != "total_ms"
    )

    # Allow a small rounding tolerance.
    assert metrics["total_ms"] + 0.01 >= measured


@pytest.mark.parametrize(
    "question,route,operations",
    [
        (
            "What is the status of order ORD-10001?",
            "ORDER",
            ["routing_ms", "order_lookup_ms"],
        ),
        (
            "Can I return the items from order ORD-10003?",
            "ORDER_RAG",
            [
                "routing_ms",
                "order_lookup_ms",
                "retrieval_ms",
                "assessment_ms",
            ],
        ),
        (
            "What is the standard return policy?",
            "RAG",
            ["routing_ms", "retrieval_ms", "formatting_ms"],
        ),
        (
            "What is the status of order ORD-99999?",
            "ORDER",
            ["routing_ms", "order_lookup_ms"],
        ),
    ],
)
def test_route_performance(question, route, operations):
    result = make_service().ask(question)

    assert result["route"] == route
    assert_performance(result, operations)


def test_tracker_accumulates_repeated_operations():
    tracker = PerformanceTracker()

    with tracker.measure("retrieval_ms"):
        pass

    with tracker.measure("retrieval_ms"):
        pass

    metrics = tracker.summary()

    assert "retrieval_ms" in metrics
    assert metrics["retrieval_ms"] >= 0
    assert metrics["total_ms"] >= metrics["retrieval_ms"]


def test_performance_is_request_scoped():
    service = make_service()

    order_result = service.ask(
        "What is the status of order ORD-10001?"
    )
    rag_result = service.ask(
        "What is the standard return policy?"
    )

    assert "order_lookup_ms" in order_result["performance"]
    assert "order_lookup_ms" not in rag_result["performance"]

    assert "retrieval_ms" in rag_result["performance"]
    assert "retrieval_ms" not in order_result["performance"]
