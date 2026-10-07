from src.evaluation.agent_eval import (
    calculate_agent_metrics,
    check_expected_terms,
    evaluate_agent,
    normalize_text,
)


def test_normalize_text_handles_unicode_hyphen_and_markdown():
    text = "**Delivered on 2026-06-02**"

    assert normalize_text(text) == "delivered on 2026-06-02"


def test_check_expected_terms():
    answer = "Order ORD-10066 is **DELIVERED**."

    assert check_expected_terms(
        answer,
        ["ORD-10066", "DELIVERED"],
    )


def test_check_expected_terms_with_no_terms():
    assert check_expected_terms("Any answer", [])


def test_evaluate_agent_success():
    def fake_assistant(question):
        return {
            "route": "ORDER",
            "answer": "Order ORD-10066 is DELIVERED.",
            "sources": ["gold.order_360"],
        }

    cases = [
        {
            "question": "What is the status of order ORD-10066?",
            "expected_route": "ORDER",
            "expected_terms": ["ORD-10066", "DELIVERED"],
        }
    ]

    results = evaluate_agent(
        fake_assistant,
        cases,
    )

    assert len(results) == 1
    assert results[0]["route_correct"] is True
    assert results[0]["execution_success"] is True
    assert results[0]["answer_correct"] is True
    assert results[0]["task_completed"] is True


def test_evaluate_agent_wrong_route():
    def fake_assistant(question):
        return {
            "route": "RAG",
            "answer": "Order ORD-10066 is DELIVERED.",
            "sources": [],
        }

    cases = [
        {
            "question": "What is the status of order ORD-10066?",
            "expected_route": "ORDER",
            "expected_terms": ["DELIVERED"],
        }
    ]

    results = evaluate_agent(
        fake_assistant,
        cases,
    )

    assert results[0]["route_correct"] is False
    assert results[0]["task_completed"] is False


def test_evaluate_agent_handles_exception():
    def failing_assistant(question):
        raise RuntimeError("LLM unavailable")

    cases = [
        {
            "question": "Test question",
            "expected_route": "RAG",
            "expected_terms": [],
        }
    ]

    results = evaluate_agent(
        failing_assistant,
        cases,
    )

    assert results[0]["execution_success"] is False
    assert results[0]["task_completed"] is False
    assert "LLM unavailable" in results[0]["error"]


def test_calculate_agent_metrics():
    results = [
        {
            "route_correct": True,
            "execution_success": True,
            "task_completed": True,
        },
        {
            "route_correct": True,
            "execution_success": True,
            "task_completed": False,
        },
    ]

    metrics = calculate_agent_metrics(results)

    assert metrics["number_of_tests"] == 2
    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["tool_execution_success_rate"] == 1.0
    assert metrics["task_completion_rate"] == 0.5
