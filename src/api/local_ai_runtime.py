"""
Runtime configuration for the optional local AI backend.

No Databricks dependency or configuration required.
"""

import os

from openai import OpenAI

from src.api.local_ai_service import LocalAIService
from src.api.local_demo_service import LocalDemoService
from src.api.llm_quota import DailyLLMQuota


def build_local_ai_service_from_env():
    api_key = os.getenv("LOCAL_AI_API_KEY", "").strip()
    model_name = os.getenv("LOCAL_AI_MODEL", "").strip()
    base_url = os.getenv("LOCAL_AI_BASE_URL", "").strip()

    if not api_key:
        raise ValueError(
            "LOCAL_AI_API_KEY must be configured "
            "for ASSISTANT_BACKEND=local_ai."
        )

    if not model_name:
        raise ValueError(
            "LOCAL_AI_MODEL must be configured "
            "for ASSISTANT_BACKEND=local_ai."
        )

    client_kwargs = {
        "api_key": api_key,
        "timeout": 20.0,
        "max_retries": 0,
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    llm_client = OpenAI(**client_kwargs)

    quota = DailyLLMQuota(
        db_path=os.getenv(
            "LOCAL_AI_QUOTA_DB",
            "data/runtime/llm_quota.db",
        ),
        max_calls=int(os.getenv("LOCAL_AI_DAILY_LIMIT", "5")),
    )

    return LocalAIService(
        llm_client=llm_client,
        model_name=model_name,
        llm_quota=quota,
        local_service=LocalDemoService(
            multilingual_retrieval=True,
            multilingual_formatting=True,
        ),
    )
