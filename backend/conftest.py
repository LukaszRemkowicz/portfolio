"""
Pytest configuration and fixtures for the portfolio backend
"""

import pytest

from django.core.management import call_command
from django.test import Client


@pytest.fixture(scope="session", autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database with migrations automatically"""
    with django_db_blocker.unblock():
        # Run migrations on test database
        call_command("migrate", verbosity=0, interactive=False)


@pytest.fixture(scope="function", autouse=True)
def clear_test_data(django_db_blocker):
    """Clear all data between tests"""
    yield  # Run test
    with django_db_blocker.unblock():
        # Clear data after each test
        call_command("flush", verbosity=0, interactive=False)


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
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def admin_user(get_user_model):
    """Create a test admin user"""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
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
