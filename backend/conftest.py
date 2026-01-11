"""
Pytest configuration and fixtures for the portfolio backend
"""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from django.test import Client


@pytest.fixture(scope="session")
def get_user_model():
    """Get user model fixture - session scoped as it never changes"""
    from django.contrib.auth import get_user_model

    return get_user_model()


@pytest.fixture
def client():
    """Django test client fixture"""
    return Client()


@pytest.fixture
def user(get_user_model):
    """Create a test user"""
    User = get_user_model
    user = User.objects.create_user(email="test@example.com")
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def admin_user(get_user_model):
    """Create a test admin user - tests create_superuser method"""
    User = get_user_model
    return User.objects.create_superuser(email="admin@example.com", password="adminpass123")


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
def clear_django_cache():
    """
    Automatically clear cache for all tests to ensure isolation.
    Lightweight and fast.
    """
    from django.core.cache import cache as django_cache

    django_cache.clear()
    yield
    django_cache.clear()


@pytest.fixture
def contact_form_settings(db):
    """
    Enable contact form and clear existing messages.
    Non-autouse to avoid DB overhead in unrelated tests.
    """
    from inbox.models import ContactFormSettings, ContactMessage

    # Enable contact form
    settings = ContactFormSettings.get_settings()
    if not settings.enabled:
        settings.enabled = True
        settings.save()

    # Clear existing contact messages
    ContactMessage.objects.all().delete()

    return settings


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


@pytest.fixture(autouse=True)
def mock_email_service():
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
def api_client():
    """Create a DRF APIClient instance"""
    return APIClient()


@pytest.fixture
def astro_image(db):
    """Create a sample AstroImage for testing"""
    from astrophotography.models import AstroImage

    return AstroImage.objects.create(
        capture_date="2023-01-01",
        location="Backyard",
        celestial_object="Deep Sky",
        path="test.jpg",
        name="Test Image",
    )
