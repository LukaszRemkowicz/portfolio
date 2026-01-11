"""
Pytest configuration and fixtures for the portfolio backend
"""

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client, RequestFactory

User = get_user_model()


@pytest.fixture
def client() -> Client:
    """Django test client fixture"""
    return Client()


@pytest.fixture
def user(db: Any) -> AbstractBaseUser:
    """
    Create the singleton admin user.
    In this app, there is only one user who is also the admin.
    """
    return User.objects.create_superuser(
        email="admin@example.com",
        password="password123",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_client(client: Client, user: AbstractBaseUser) -> Client:
    """Admin test client"""
    client.force_login(user)
    return client


@pytest.fixture(autouse=True)
def clear_django_cache() -> Generator[None, None, None]:
    """
    Automatically clear cache for all tests to ensure isolation.
    Lightweight and fast.
    """
    from django.core.cache import cache as django_cache

    django_cache.clear()
    yield
    django_cache.clear()


@pytest.fixture
def contact_form_settings(db: Any) -> Any:
    """
    Get contact form settings fixture.
    """
    from inbox.models import ContactFormSettings

    return ContactFormSettings.get_settings()


@pytest.fixture
def kill_switch_middleware() -> Any:
    """Create middleware instance for testing"""
    from inbox.middleware import ContactFormKillSwitchMiddleware

    return ContactFormKillSwitchMiddleware(lambda request: None)


@pytest.fixture
def request_factory() -> RequestFactory:
    """Create RequestFactory instance for testing"""
    from django.test import RequestFactory

    return RequestFactory()


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
def api_client() -> APIClient:
    """Create a DRF APIClient instance"""
    return APIClient()


@pytest.fixture
def astro_image(db: Any) -> Any:
    """Create a sample AstroImage for testing"""
    from astrophotography.models import AstroImage

    return AstroImage.objects.create(
        capture_date="2023-01-01",
        location="Backyard",
        celestial_object="Deep Sky",
        path="test.jpg",
        name="Test Image",
    )
