"""
Pytest configuration and fixtures for the portfolio backend
"""

import pytest
from unittest.mock import patch

from django.test import Client


@pytest.fixture
def get_user_model():
    """Get user model fixture - lazy import"""
    from django.contrib.auth import get_user_model

    return get_user_model()


@pytest.fixture
def client():
    """Django test client fixture"""
    return Client()


@pytest.fixture
def user(get_user_model):
    """Create a test user"""
    User = get_user_model()
    user = User(email="test@example.com")
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def admin_user(get_user_model):
    """Create a test admin user - tests create_superuser method"""
    User = get_user_model()
    return User.objects.create_superuser(
        email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def authenticated_client(client, user):
    """Authenticated test client"""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Admin test client"""
    client.force_login(admin_user)
    return client


@pytest.fixture(autouse=True)
def enable_contact_form_and_clear_cache(db):
    """
    Enable contact form and clear cache/messages for all view tests.
    Automatically runs before each test to ensure consistent test state.
    """
    from inbox.models import ContactFormSettings, ContactMessage
    from django.core.cache import cache as django_cache

    # Enable contact form
    settings = ContactFormSettings.get_settings()
    settings.enabled = True
    settings.save()

    # Clear cache to avoid throttling issues between tests
    django_cache.clear()

    # Clear existing contact messages to avoid duplicate detection
    ContactMessage.objects.all().delete()

    yield

    # Cleanup
    django_cache.clear()
    ContactMessage.objects.all().delete()


@pytest.fixture
def middleware():
    """Create middleware instance for testing"""
    from inbox.middleware import ContactFormKillSwitchMiddleware
    return ContactFormKillSwitchMiddleware(lambda request: None)


@pytest.fixture
def request_factory():
    """Create RequestFactory instance for testing"""
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def contact_form_settings(db):
    """Create or get contact form settings instance for testing"""
    from inbox.models import ContactFormSettings
    return ContactFormSettings.get_settings()


@pytest.fixture(autouse=True)
def mock_email_service():
    """
    Automatically mock email service for all tests.
    Prevents actual emails from being sent during tests.
    Mocks both the service method and Django's send_mail to ensure no emails are sent.
    """
    with patch("inbox.views.ContactMessageEmailService.send_notification_email_async") as mock_async, \
         patch("django.core.mail.send_mail") as mock_send_mail:
        mock_async.return_value = None
        mock_send_mail.return_value = 1  # send_mail returns number of emails sent
        yield mock_async
