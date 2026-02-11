from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_translate_task(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock translate_instance_task reliably across tests."""
    import uuid

    class MockTaskResult:
        def __init__(self, task_id):
            self.id = task_id

    mock = mocker.patch("translation.mixins.translate_instance_task")
    mock.delay.side_effect = lambda *args, **kwargs: MockTaskResult(str(uuid.uuid4()))
    return mock


@pytest.fixture
def mock_get_available_languages(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock get_available_languages reliably across tests."""
    return mocker.patch(
        "translation.services.TranslationService.get_available_languages",
        return_value=["en", "pl"],
    )
