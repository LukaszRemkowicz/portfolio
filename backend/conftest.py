# backend/conftest.py
"""
Root conftest.py for pytest
Imports shared fixtures from core.fixtures
"""

import uuid
from unittest.mock import patch

import pytest

# Import all fixtures from core.fixtures to make them available globally
from core.fixtures import *  # noqa: F401,F403
from translation.fixtures import *  # noqa: F401,F403


@pytest.fixture(autouse=True)
def global_translation_mock():
    """
    Globally mock the translation task delay to prevent EAGER execution
    during tests unless explicitly handled by the test.
    This prevents IntegrityErrors and slow tests on the host.
    """

    class MockTaskResult:
        def __init__(self, task_id):
            self.id = task_id

    with patch("translation.mixins.translate_instance_task.delay") as mock_delay:
        # Generate a unique ID for every call to delay()
        mock_delay.side_effect = lambda *args, **kwargs: MockTaskResult(str(uuid.uuid4()))
        yield mock_delay
