from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_translate_task(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock translate_instance_task reliably across tests."""
    return mocker.patch("translation.mixins.translate_instance_task")


@pytest.fixture
def mock_get_available_languages(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock get_available_languages reliably across tests."""
    return mocker.patch(
        "translation.services.TranslationService.get_available_languages",
        return_value=["en", "pl"],
    )
