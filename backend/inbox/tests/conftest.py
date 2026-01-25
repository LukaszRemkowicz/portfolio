# backend/inbox/tests/conftest.py
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

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


@pytest.fixture(autouse=True)
def mock_email_service() -> Generator[MagicMock, None, None]:
    """
    Automatically mock email service for all tests.
    Prevents actual emails from being sent during tests.
    """
    with (
        patch(
            "inbox.services.ContactMessageEmailService.send_notification_email_async"
        ) as mock_async,
        patch("django.core.mail.send_mail") as mock_send_mail,
    ):
        mock_async.return_value = None
        mock_send_mail.return_value = 1
        yield mock_async


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
