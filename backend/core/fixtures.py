from typing import TYPE_CHECKING, Generator

import pytest
from rest_framework.test import APIClient, APIRequestFactory

from django.core.cache import cache as django_cache
from django.test import Client, RequestFactory

if TYPE_CHECKING:
    # Removed redundant imports as they are now available globally
    pass


@pytest.fixture
def api_client() -> APIClient:
    """Create a DRF APIClient instance"""
    return APIClient()


@pytest.fixture
def client() -> Client:
    """Django test client fixture"""
    return Client()


@pytest.fixture(autouse=True)
def clear_django_cache() -> Generator[None, None, None]:
    """
    Automatically clear cache for all tests to ensure isolation.
    """
    django_cache.clear()
    yield
    django_cache.clear()


@pytest.fixture
def request_factory() -> RequestFactory:
    """Create RequestFactory instance for testing"""
    return RequestFactory()


@pytest.fixture
def api_request_factory() -> APIRequestFactory:
    """DRF API Request Factory fixture"""
    return APIRequestFactory()
