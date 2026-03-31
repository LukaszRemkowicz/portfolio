from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from core.models import LandingPageSettings
from core.tests.factories import LandingPageSettingsFactory
from inbox.middleware import ContactFormKillSwitchMiddleware
from inbox.models import ContactMessage
from inbox.serializers import ContactMessageSerializer
from inbox.tests.factories import ContactMessageFactory


@pytest.fixture
def landing_page_settings() -> LandingPageSettings:
    """
    Get landing page settings fixture.
    """
    # Ensure single instance
    LandingPageSettings.objects.all().delete()
    return LandingPageSettingsFactory()


@pytest.fixture
def kill_switch_middleware() -> ContactFormKillSwitchMiddleware:
    """Create middleware instance for testing"""
    return ContactFormKillSwitchMiddleware(lambda request: None)


@pytest.fixture
def mock_email_service(mocker: MockerFixture) -> MagicMock:
    """
    Automatically mock email service for all tests.
    Prevents actual emails from being sent during tests.
    """
    mock_async = mocker.patch("inbox.services.send_notification_email_task.apply_async")
    mock_email_message = mocker.patch("inbox.tasks.EmailMessage")

    mock_async.return_value = None
    mock_email_message.return_value.send.return_value = 1
    return mock_async


@pytest.fixture
def contact_message() -> ContactMessage:
    """Create a unsaved ContactMessage instance for testing"""
    return ContactMessageFactory.build()


@pytest.fixture
def valid_contact_data() -> dict[str, str]:
    """Return a dictionary of valid contact message data for testing."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "subject": "Hello",
        "message": "This is a test message.",
    }


@pytest.fixture
def valid_contact_serializer(valid_contact_data: dict[str, str]) -> ContactMessageSerializer:
    """Return a validated ContactMessageSerializer instance."""
    serializer = ContactMessageSerializer(data=valid_contact_data)
    serializer.is_valid(raise_exception=True)
    return serializer


@pytest.fixture
def mock_inbox_send_mail(mocker: MockerFixture) -> MagicMock:
    """Legacy fixture kept for compatibility; send_mail is no longer used."""
    return mocker.MagicMock()


@pytest.fixture
def mock_inbox_email_message(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock EmailMessage in inbox.tasks."""
    return mocker.patch("inbox.tasks.EmailMessage")


@pytest.fixture
def mock_inbox_logger(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock logger in inbox.tasks or services."""
    # Note: We might need separate ones if paths differ, but let's see.
    # In test_services.py, it patches inbox.tasks.logger and inbox.services.logger
    return mocker.patch("inbox.tasks.logger")


@pytest.fixture
def mock_inbox_service_logger(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock logger in inbox.services."""
    return mocker.patch("inbox.services.logger")
