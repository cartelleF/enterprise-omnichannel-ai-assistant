"""Evaluation utilities for the Enterprise Omni-Channel AI Assistant."""

import re
import time
import unicodedata


def normalize_text(text):
    """Normalize text before comparing expected terms with an answer."""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()

    text = re.sub(
        r"[\u2010\u2011\u2012\u2013\u2014\u2212]",
        "-",
        text,
    )

    text = (
        text.replace("**", "")
        .replace("__", "")
        .replace("`", "")
    )

    return " ".join(text.split())


def check_expected_terms(answer, expected_terms):
    """Return True when all expected terms occur in the answer."""
    if not expected_terms:
        return True

    normalized_answer = normalize_text(answer)

    return all(
        normalize_text(term) in normalized_answer
        for term in expected_terms
    )


def evaluate_agent(
    assistant_fn,
    evaluation_questions,
    delay_seconds=0,
):
    """
    Evaluate routing, execution and task completion.

    Each evaluation case should contain:
        question
        expected_route
        expected_terms

    assistant_fn must accept a question and return a dictionary containing:
        route
        answer
        sources

    Optional:
        error
    """
    results = []

    for case in evaluation_questions:
        question = case["question"]
        expected_route = case["expected_route"]
        expected_terms = case.get("expected_terms", [])

        try:
            response = assistant_fn(question)

            predicted_route = response.get("route")
            answer = response.get("answer", "")
            sources = response.get("sources", [])

            route_correct = predicted_route == expected_route
            execution_success = response.get("error") in (None, "")
            answer_correct = check_expected_terms(
                answer,
                expected_terms,
            )

            task_completed = (
                route_correct
                and execution_success
                and answer_correct
            )

            error = response.get("error")

        except Exception as exc:
            predicted_route = None
            answer = ""
            sources = []
            route_correct = False
            execution_success = False
            answer_correct = False
            task_completed = False
            error = str(exc)

        results.append(
            {
                "question": question,
                "expected_route": expected_route,
                "predicted_route": predicted_route,
                "route_correct": route_correct,
                "execution_success": execution_success,
                "answer_correct": answer_correct,
                "task_completed": task_completed,
                "answer": answer,
                "sources": sources,
                "error": error,
            }
        )

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return results


def calculate_agent_metrics(results):
    """Calculate aggregate agent evaluation metrics."""
    number_of_tests = len(results)

    if number_of_tests == 0:
        return {
            "number_of_tests": 0,
            "tool_selection_accuracy": 0.0,
            "tool_execution_success_rate": 0.0,
            "task_completion_rate": 0.0,
        }

    return {
        "number_of_tests": number_of_tests,
        "tool_selection_accuracy": sum(
            result["route_correct"] for result in results
        ) / number_of_tests,
        "tool_execution_success_rate": sum(
            result["execution_success"] for result in results
        ) / number_of_tests,
        "task_completion_rate": sum(
            result["task_completed"] for result in results
        ) / number_of_tests,
    }
