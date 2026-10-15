import sys
from unittest.mock import patch

from src.api.main import get_assistant_service
from src.api.local_demo_service import LocalDemoService


def test_local_backend_is_default_without_databricks():
    get_assistant_service.cache_clear()

    try:
        with patch.dict("os.environ", {"ASSISTANT_BACKEND": "local"}):
            with patch.dict(
                sys.modules,
                {"src.api.runtime": None},
            ):
                service = get_assistant_service()

        assert isinstance(service, LocalDemoService)
    finally:
        get_assistant_service.cache_clear()


def test_local_backend_is_default_when_env_is_missing():
    get_assistant_service.cache_clear()

    try:
        with patch.dict("os.environ", {}, clear=True):
            service = get_assistant_service()

        assert isinstance(service, LocalDemoService)
    finally:
        get_assistant_service.cache_clear()
