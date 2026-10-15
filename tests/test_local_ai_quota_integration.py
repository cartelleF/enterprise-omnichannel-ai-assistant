from types import SimpleNamespace

from src.api.llm_quota import DailyLLMQuota
from src.api.local_ai_service import LocalAIService


class FakeLocalService:
    def __init__(self, route="RAG", sources=None):
        self.route = route
        self.sources = (
            ["return_policy.txt"] if sources is None else sources
        )

    def ask(self, question):
        return {
            "route": self.route,
            "answer": "The return window is 30 days.",
            "sources": self.sources,
        }


class FakeResponses:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            status="completed",
            output_text="The return window is 30 days.",
        )


class FakeLLMClient:
    def __init__(self):
        self.responses = FakeResponses()


def build_service(tmp_path, max_calls, route="RAG", sources=None):
    client = FakeLLMClient()
    quota = DailyLLMQuota(
        tmp_path / "quota.db",
        max_calls=max_calls,
    )
    service = LocalAIService(
        llm_client=client,
        model_name="fake-model",
        local_service=FakeLocalService(
            route=route,
            sources=sources,
        ),
        llm_quota=quota,
    )
    return service, client


def test_llm_called_when_quota_available(tmp_path):
    service, client = build_service(tmp_path, max_calls=1)

    result = service.ask("What is the return policy?")

    assert result["generation_mode"] == "llm"
    assert client.responses.calls == 1


def test_exhausted_quota_prevents_llm_call(tmp_path):
    service, client = build_service(tmp_path, max_calls=1)

    first = service.ask("What is the return policy?")
    second = service.ask("What is the return policy?")

    assert first["generation_mode"] == "llm"
    assert second["generation_mode"] == "local_fallback"
    assert second["answer"] == "The return window is 30 days."
    assert client.responses.calls == 1


def test_zero_quota_blocks_llm(tmp_path):
    service, client = build_service(tmp_path, max_calls=0)

    result = service.ask("What is the return policy?")

    assert result["generation_mode"] == "local_fallback"
    assert client.responses.calls == 0


def test_order_rag_does_not_consume_quota(tmp_path):
    service, client = build_service(
        tmp_path,
        max_calls=1,
        route="ORDER_RAG",
    )

    result = service.ask("Can I return order ORD-10066?")

    assert result["generation_mode"] == "deterministic"
    assert client.responses.calls == 0

    # The quota must still be available for a later RAG request.
    service.local_service = FakeLocalService()
    later = service.ask("What is the return policy?")

    assert later["generation_mode"] == "llm"
    assert client.responses.calls == 1


def test_no_sources_does_not_consume_quota(tmp_path):
    service, client = build_service(
        tmp_path,
        max_calls=1,
        sources=[],
    )

    result = service.ask("Unknown question")

    assert result["generation_mode"] == "deterministic"
    assert client.responses.calls == 0


def test_quota_database_failure_blocks_llm(tmp_path):
    service, client = build_service(tmp_path, max_calls=1)

    class BrokenQuota:
        def try_reserve(self):
            raise RuntimeError("Database unavailable")

    service.llm_quota = BrokenQuota()

    result = service.ask("What is the return policy?")

    assert result["generation_mode"] == "local_fallback"
    assert client.responses.calls == 0
