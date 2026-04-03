import uuid
from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.fixtures import (
    api_client,
    api_request_factory,
    clear_django_cache,
    client,
    request_factory,
)
from translation.fixtures import mock_get_available_languages, mock_translate_task

__all__ = [
    "api_client",
    "api_request_factory",
    "clear_django_cache",
    "client",
    "request_factory",
    "mock_get_available_languages",
    "mock_translate_task",
]


@pytest.fixture(autouse=True)
def execute_on_commit() -> Generator[None]:
    """
    Ensure transaction.on_commit hooks execute immediately in tests.
    By default, they don't run in standard TestCase/TestCase-like tests.
    """
    with patch("django.db.transaction.on_commit", side_effect=lambda func: func()):
        yield


@pytest.fixture(autouse=True)
def global_translation_mock():
    """
    Globally mock the translation task delay to prevent EAGER execution
    during tests unless explicitly handled by the test.
    This prevents IntegrityErrors and slow tests on the host.
    """

    with patch("translation.mixins.translate_instance_task.delay") as mock_delay:

        def mock_task_result(*args, **kwargs):  # noqa: ARG001
            return SimpleNamespace(id=str(uuid.uuid4()))

        # Generate a unique ID for every call to delay()
        mock_delay.side_effect = mock_task_result
        yield mock_delay
