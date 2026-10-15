from types import SimpleNamespace

from src.api.local_ai_service import LocalAIService


class FakeLocalService:
    def __init__(self, route="RAG", sources=None):
        self.route = route
        self.sources = (
            ["return_policy.txt"]
            if sources is None
            else sources
        )

    def ask(self, question):
        return {
            "question": question,
            "route": self.route,
            "answer": "Customers have 30 days to request a return.",
            "sources": self.sources,
        }


class FakeResponses:
    def __init__(self, text="Customers may request a return within 30 days."):
        self.text = text
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            status="completed",
            output_text=self.text,
        )


class FakeLLMClient:
    def __init__(self, text="Customers may request a return within 30 days."):
        self.responses = FakeResponses(text)


def test_llm_rewrites_local_answer():
    llm = FakeLLMClient()
    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(),
    )

    result = service.ask("What is the return policy?")

    assert result["route"] == "RAG"
    assert "within 30 days" in result["answer"]
    assert result["sources"] == ["return_policy.txt"]
    assert llm.responses.calls == 1


def test_order_rag_does_not_call_llm():
    llm = FakeLLMClient()
    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(route="ORDER_RAG"),
    )

    result = service.ask("Can I return ORD-10001?")

    assert result["route"] == "ORDER_RAG"
    assert llm.responses.calls == 0


def test_no_sources_skips_llm():
    llm = FakeLLMClient()
    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(sources=[]),
    )

    result = service.ask("Unknown question")

    assert result["sources"] == []
    assert llm.responses.calls == 0


def test_empty_llm_response_falls_back():
    llm = FakeLLMClient(text="")
    service = LocalAIService(
        llm_client=llm,
        model_name="fake-model",
        local_service=FakeLocalService(),
    )

    result = service.ask("What is the return policy?")

    assert result["answer"] == (
        "Customers have 30 days to request a return."
    )
