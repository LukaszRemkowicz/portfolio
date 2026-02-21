from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_llm_provider(mocker: MockerFixture) -> MagicMock:
    mock = mocker.MagicMock()
    return mock


@pytest.fixture
def mock_task_infrastructure(mocker: MockerFixture):
    mock_get_model = mocker.patch("translation.tasks.apps.get_model")
    mock_service = mocker.patch("translation.tasks.TranslationService")
    mock_task_model = mocker.patch("translation.tasks.TranslationTask")
    mock_content_type = mocker.patch("translation.tasks.ContentType")

    return {
        "get_model": mock_get_model,
        "service": mock_service,
        "task_model": mock_task_model,
        "content_type": mock_content_type,
    }


@pytest.fixture
def astro_image_factory():
    from astrophotography.tests.factories import AstroImageFactory

    return AstroImageFactory


@pytest.fixture
def place_factory():
    from astrophotography.tests.factories import PlaceFactory

    return PlaceFactory


@pytest.fixture
def tag_factory():
    from astrophotography.tests.factories import TagFactory

    return TagFactory


@pytest.fixture
def user_factory():
    from users.tests.factories import UserFactory

    return UserFactory
