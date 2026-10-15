from types import SimpleNamespace

import pytest

from src.api.local_ai_service import LocalAIService


class FakeLocalService:
    def __init__(self, answer):
        self.answer = answer

    def ask(self, question):
        return {
            "question": question,
            "route": "ORDER",
            "answer": self.answer,
            "sources": ["synthetic_sap.orders"],
        }


class FakeResponses:
    def __init__(self, generated_answer):
        self.generated_answer = generated_answer
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            status="completed",
            output_text=self.generated_answer,
        )


class FakeLLMClient:
    def __init__(self, generated_answer):
        self.responses = FakeResponses(generated_answer)


REFERENCE = (
    "Order ORD-10066 has status DELIVERED. "
    "It was placed on 2026-05-28 and delivered on 2026-06-02. "
    "The total amount is 2313.8 EUR."
)


@pytest.mark.parametrize(
    "incorrect_answer",
    [
        REFERENCE.replace("DELIVERED", "CANCELLED"),
        REFERENCE.replace("ORD-10066", "ORD-99999"),
        REFERENCE.replace("2026-06-02", "2026-06-03"),
        REFERENCE.replace("2313.8 EUR", "9999 EUR"),
    ],
)
def test_incorrect_llm_answer_triggers_fallback(incorrect_answer):
    llm = FakeLLMClient(incorrect_answer)

    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(REFERENCE),
    )

    result = service.ask("What is the status of order ORD-10066?")

    assert result["answer"] == REFERENCE
    assert result["generation_mode"] == "local_fallback"
    assert result["sources"] == ["synthetic_sap.orders"]
    assert llm.responses.calls == 1


def test_correct_llm_answer_is_accepted():
    generated = (
        "The status of ORD-10066 is DELIVERED. "
        "The order was placed on 2026-05-28 "
        "and delivered on 2026-06-02. "
        "Its total is 2313.80 EUR."
    )

    llm = FakeLLMClient(generated)

    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(REFERENCE),
    )

    result = service.ask("What is the status of order ORD-10066?")

    assert result["answer"] == generated
    assert result["generation_mode"] == "llm"
    assert llm.responses.calls == 1
