"""Portfolio LLM quota tests without external API calls."""

from unittest.mock import Mock

from src.api.llm_quota import DailyLLMQuota
from src.api.local_ai_service import LocalAIService


def test_daily_quota_allows_five_calls(tmp_path):
    quota = DailyLLMQuota(
        db_path=tmp_path / "quota.db",
        max_calls=5,
    )

    results = [quota.try_reserve() for _ in range(6)]

    assert results == [
        True, True, True, True, True, False
    ]


def test_daily_quota_persists_across_instances(tmp_path):
    db_path = tmp_path / "quota.db"

    first = DailyLLMQuota(db_path=db_path, max_calls=2)

    assert first.try_reserve() is True

    second = DailyLLMQuota(db_path=db_path, max_calls=2)

    assert second.try_reserve() is True
    assert second.try_reserve() is False


def test_zero_quota_blocks_all_calls(tmp_path):
    quota = DailyLLMQuota(
        db_path=tmp_path / "quota.db",
        max_calls=0,
    )

    assert quota.try_reserve() is False
