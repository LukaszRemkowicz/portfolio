from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_translate_task(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock the submit() call that dispatches translate_instance_task."""
    return mocker.patch("translation.mixins.submit")


@pytest.fixture
def mock_get_available_languages(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock get_available_languages reliably across tests."""
    return mocker.patch(
        "translation.services.TranslationService.get_available_languages",
        return_value=["en", "pl"],
    )
