import pytest

from src.api.llm_quota import DailyLLMQuota


def test_quota_allows_calls_within_limit(tmp_path):
    quota = DailyLLMQuota(
        tmp_path / "quota.db",
        max_calls=3,
    )

    assert quota.try_reserve() is True
    assert quota.try_reserve() is True
    assert quota.try_reserve() is True


def test_quota_rejects_excess_calls(tmp_path):
    quota = DailyLLMQuota(
        tmp_path / "quota.db",
        max_calls=2,
    )

    assert quota.try_reserve() is True
    assert quota.try_reserve() is True
    assert quota.try_reserve() is False


def test_quota_persists_between_instances(tmp_path):
    path = tmp_path / "quota.db"

    first = DailyLLMQuota(path, max_calls=1)
    assert first.try_reserve() is True

    second = DailyLLMQuota(path, max_calls=1)
    assert second.try_reserve() is False


def test_zero_quota_blocks_all_calls(tmp_path):
    quota = DailyLLMQuota(
        tmp_path / "quota.db",
        max_calls=0,
    )

    assert quota.try_reserve() is False


def test_negative_quota_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        DailyLLMQuota(
            tmp_path / "quota.db",
            max_calls=-1,
        )
